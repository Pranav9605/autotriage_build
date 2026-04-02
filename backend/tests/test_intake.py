"""Additional IntakeService tests — Phase 6.

These complement tests/test_triage.py which covers the full pipeline.
Here we verify enrichment extraction and that the right data is persisted.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.core.tenant_config import AIConfig, EscalationConfig, TenantConfig
from app.models.ticket import Ticket
from app.schemas.triage import TriageDecisionSchema
from app.services.intake import IntakeService
from app.services.rule_engine import RuleEngine

from tests.conftest import make_execute_result


_VALID_DECISION = dict(
    module="MM",
    priority="P3",
    issue_type="Technical Issue",
    root_cause_hypothesis="ME21N failing due to missing authorization",
    recommended_solution="Grant MM authorization object",
    assign_to="SAP MM/Procurement Team",
    confidence=0.87,
    manual_review_required=False,
    similar_ticket_ids=[],
)


def _make_tenant_config() -> TenantConfig:
    return TenantConfig(
        tenant_id="patil_group",
        display_name="Patil Group",
        modules_active=["FI", "MM", "ABAP", "BASIS"],
        teams={
            "FI": "SAP Finance Team",
            "MM": "SAP MM/Procurement Team",
            "DEFAULT": "General SAP Support",
        },
        hard_rules=[],
        escalation=EscalationConfig(),
        ai_config=AIConfig(confidence_threshold=0.80),
    )


def _make_deps():
    db = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.commit = AsyncMock()
    db.execute = AsyncMock(return_value=make_execute_result(scalar=None))

    embedding_svc = AsyncMock()
    embedding_svc.embed_text = AsyncMock(return_value=[0.1] * 1536)

    retrieval_svc = AsyncMock()
    retrieval_svc.search_similar = AsyncMock(return_value=[])

    decision = TriageDecisionSchema(**_VALID_DECISION)
    triage_engine = AsyncMock()
    triage_engine.classify = AsyncMock(return_value=(decision, 150))
    triage_engine.model = "claude-sonnet-4-20250514"

    return {
        "db": db,
        "embedding_svc": embedding_svc,
        "retrieval_svc": retrieval_svc,
        "triage_engine": triage_engine,
    }


def _make_service(deps) -> IntakeService:
    return IntakeService(
        db=deps["db"],
        embedding_service=deps["embedding_svc"],
        retrieval_service=deps["retrieval_svc"],
        triage_engine=deps["triage_engine"],
        rule_engine_factory=lambda c: RuleEngine(c),
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_intake_tcode_extracted_and_stored():
    deps = _make_deps()
    svc = _make_service(deps)

    with patch("app.services.intake.load_tenant_config", return_value=_make_tenant_config()):
        await svc.process_ticket(
            tenant_id="patil_group",
            source="solman",
            raw_text="ME21N is failing with error M7 021 in QAS system",
        )

    added_tickets = [
        call.args[0]
        for call in deps["db"].add.call_args_list
        if isinstance(call.args[0], Ticket)
    ]
    assert len(added_tickets) == 1
    assert added_tickets[0].tcode == "ME21N"


@pytest.mark.asyncio
async def test_intake_error_code_extracted_and_stored():
    deps = _make_deps()
    svc = _make_service(deps)

    with patch("app.services.intake.load_tenant_config", return_value=_make_tenant_config()):
        await svc.process_ticket(
            tenant_id="patil_group",
            source="solman",
            raw_text="ME21N is failing with error M7 021 in QAS system",
        )

    ticket = next(
        call.args[0]
        for call in deps["db"].add.call_args_list
        if isinstance(call.args[0], Ticket)
    )
    assert ticket.error_code == "M7 021"


@pytest.mark.asyncio
async def test_intake_environment_extracted_and_stored():
    deps = _make_deps()
    svc = _make_service(deps)

    with patch("app.services.intake.load_tenant_config", return_value=_make_tenant_config()):
        await svc.process_ticket(
            tenant_id="patil_group",
            source="solman",
            raw_text="FB50 is giving error F5 301 in PRD system",
        )

    ticket = next(
        call.args[0]
        for call in deps["db"].add.call_args_list
        if isinstance(call.args[0], Ticket)
    )
    assert ticket.environment == "PRD"


@pytest.mark.asyncio
async def test_intake_reporter_stored():
    deps = _make_deps()
    svc = _make_service(deps)

    with patch("app.services.intake.load_tenant_config", return_value=_make_tenant_config()):
        await svc.process_ticket(
            tenant_id="patil_group",
            source="chat",
            raw_text="Some SAP issue with MIGO transaction",
            reporter="john.doe@patilgroup.com",
        )

    ticket = next(
        call.args[0]
        for call in deps["db"].add.call_args_list
        if isinstance(call.args[0], Ticket)
    )
    assert ticket.reporter == "john.doe@patilgroup.com"


@pytest.mark.asyncio
async def test_intake_embedding_called_with_raw_text():
    deps = _make_deps()
    svc = _make_service(deps)
    raw = "ME21N is failing with error M7 021 in QAS system"

    with patch("app.services.intake.load_tenant_config", return_value=_make_tenant_config()):
        await svc.process_ticket(
            tenant_id="patil_group",
            source="solman",
            raw_text=raw,
        )

    deps["embedding_svc"].embed_text.assert_called_once_with(raw)
