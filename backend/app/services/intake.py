"""Intake service — orchestrates the full triage pipeline for a new ticket."""

import logging
import time
from typing import Callable, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import TriageEngineError
from app.core.tenant_config import TenantConfig, load_tenant_config
from app.models.ticket import Ticket
from app.models.triage_decision import TriageDecision
from app.schemas.triage import TriageRequest, TriageResponse
from app.services.embedding import EmbeddingService
from app.services.retrieval import RetrievalService
from app.services.rule_engine import RuleEngine
from app.services.triage_engine import TriageEngine
from app.utils.enrichment import enrich_ticket
from app.utils.id_generator import generate_ticket_id, generate_uuid

logger = logging.getLogger(__name__)


class IntakeService:
    """Orchestrates: enrich → embed → retrieve → classify → rules → persist."""

    def __init__(
        self,
        db: AsyncSession,
        embedding_service: EmbeddingService,
        retrieval_service: RetrievalService,
        triage_engine: TriageEngine,
        rule_engine_factory: Callable[[TenantConfig], RuleEngine],
    ) -> None:
        self.db = db
        self.embedding_service = embedding_service
        self.retrieval_service = retrieval_service
        self.triage_engine = triage_engine
        self.rule_engine_factory = rule_engine_factory

    async def process_ticket(
        self,
        tenant_id: str,
        source: str,
        raw_text: str,
        reporter: Optional[str] = None,
    ) -> TriageResponse:
        """Full pipeline — returns a TriageResponse with the persisted decision."""
        start_ms = int(time.time() * 1000)

        # 1. Generate ID
        ticket_id = generate_ticket_id()

        # 2. Enrich
        enriched = enrich_ticket(raw_text)
        tcode = enriched.get("tcode")
        error_code = enriched.get("error_code")
        environment = enriched.get("environment")

        # 3. Embed
        try:
            embedding = await self.embedding_service.embed_text(raw_text)
        except Exception as exc:
            logger.error("Embedding failed for ticket=%s: %s", ticket_id, exc)
            embedding = None

        # 4. Persist Ticket
        ticket = Ticket(
            id=ticket_id,
            tenant_id=tenant_id,
            source=source,
            raw_text=raw_text,
            description=raw_text,
            tcode=tcode,
            error_code=error_code,
            environment=environment,
            reporter=reporter,
            status="open",
            embedding=embedding,
        )
        self.db.add(ticket)
        await self.db.flush()  # get PK into DB without committing yet

        # 5. Retrieve similar tickets + KB articles
        tenant_cfg = load_tenant_config(tenant_id)
        ai_cfg = tenant_cfg.ai_config

        try:
            similar_results = await self.retrieval_service.search_similar(
                tenant_id=tenant_id,
                query_text=raw_text,
                error_code=error_code,
                tcode=tcode,
                environment=environment,
                min_score=ai_cfg.similarity_min_score,
                limit=ai_cfg.max_similar_tickets + ai_cfg.max_kb_articles,
            )
        except Exception as exc:
            logger.warning("Retrieval failed, continuing without context: %s", exc)
            similar_results = []

        similar_tickets = [r for r in similar_results if r.result_type == "ticket"][
            : ai_cfg.max_similar_tickets
        ]
        kb_articles = [r for r in similar_results if r.result_type == "kb_article"][
            : ai_cfg.max_kb_articles
        ]

        # 6. Build TriageRequest
        triage_request = TriageRequest(
            ticket_id=ticket_id,
            tenant_id=tenant_id,
            description=raw_text,
            tcode=tcode,
            error_code=error_code,
            environment=environment,
            source=source,
            similar_tickets=similar_tickets,
            kb_articles=kb_articles,
            tenant_config=tenant_cfg.model_dump(),
        )

        # 7. Classify
        classification_source = "llm"
        tokens_used = 0
        try:
            decision, tokens_used = await self.triage_engine.classify(triage_request)
        except TriageEngineError as exc:
            logger.error("Triage engine failed for ticket=%s: %s", ticket_id, exc)
            # Fallback — manual review, unknown module
            from app.schemas.triage import TriageDecisionSchema

            decision = TriageDecisionSchema(
                module="CUSTOM",
                priority="P3",
                issue_type="Technical Issue",
                root_cause_hypothesis="LLM classification failed — manual review required.",
                recommended_solution="Assign to a consultant for manual triage.",
                assign_to=tenant_cfg.teams.get("DEFAULT", "General SAP Support"),
                confidence=0.0,
                manual_review_required=True,
                similar_ticket_ids=[],
            )
            classification_source = "error"

        # 8. Apply rule overrides
        rule_engine = self.rule_engine_factory(tenant_cfg)
        decision, rules_fired = rule_engine.apply_rules(
            decision=decision,
            ticket_source=source,
            ticket_environment=environment,
            ticket_error_code=error_code,
        )

        # 9. Confidence calibration (POC: identity)
        confidence_calibrated = decision.confidence

        # 10. manual_review_required — set if below threshold OR rules set it
        manual_review = decision.manual_review_required or (
            decision.confidence < ai_cfg.confidence_threshold
        )
        if decision.manual_review_required:
            review_reason = decision.review_reason or "rule_triggered"
        elif decision.confidence < ai_cfg.confidence_threshold:
            review_reason = "low_confidence"
        else:
            review_reason = None

        # 11. Determine next version number for this ticket
        version = await _next_version(self.db, ticket_id)

        # 12. Persist TriageDecision
        decision_id = generate_uuid()
        similar_ids = [r.result_id for r in similar_tickets]
        similar_scores = [r.final_score for r in similar_tickets]
        kb_ids = [r.result_id for r in kb_articles]

        latency_ms = int(time.time() * 1000) - start_ms

        triage_record = TriageDecision(
            id=decision_id,
            ticket_id=ticket_id,
            tenant_id=tenant_id,
            version=version,
            module=decision.module,
            priority=decision.priority,
            issue_type=decision.issue_type,
            root_cause_hypothesis=decision.root_cause_hypothesis,
            recommended_solution=decision.recommended_solution,
            assign_to=decision.assign_to,
            confidence=decision.confidence,
            confidence_calibrated=confidence_calibrated,
            classification_source=classification_source,
            model_version=getattr(self.triage_engine, "model", "unknown"),
            rules_applied=rules_fired or None,
            similar_ticket_ids=similar_ids or None,
            similar_ticket_scores=similar_scores or None,
            kb_article_ids=kb_ids or None,
            manual_review_required=manual_review,
            review_reason=review_reason,
            latency_ms=latency_ms,
            llm_tokens_used=tokens_used or None,
        )
        self.db.add(triage_record)

        # 13. Update ticket status
        ticket.status = "triaged"
        await self.db.commit()

        return TriageResponse(
            decision_id=decision_id,
            ticket_id=ticket_id,
            module=decision.module,
            priority=decision.priority,
            issue_type=decision.issue_type,
            root_cause_hypothesis=decision.root_cause_hypothesis,
            recommended_solution=decision.recommended_solution,
            assign_to=decision.assign_to,
            confidence=decision.confidence,
            confidence_calibrated=confidence_calibrated,
            classification_source=classification_source,
            model_version=getattr(self.triage_engine, "model", "unknown"),
            rules_applied=rules_fired,
            similar_ticket_ids=similar_ids,
            similar_ticket_scores=similar_scores,
            kb_article_ids=kb_ids,
            manual_review_required=manual_review,
            review_reason=review_reason,
            latency_ms=latency_ms,
        )


async def _next_version(db: AsyncSession, ticket_id: str) -> int:
    """Return the next version number for a ticket's triage decisions."""
    result = await db.execute(
        select(TriageDecision.version)
        .where(TriageDecision.ticket_id == ticket_id)
        .order_by(TriageDecision.version.desc())
        .limit(1)
    )
    row = result.scalar_one_or_none()
    return (row or 0) + 1
