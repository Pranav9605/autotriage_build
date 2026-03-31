"""Triage API — re-triage and version history."""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_intake_service, get_tenant_id
from app.models.ticket import Ticket
from app.models.triage_decision import TriageDecision
from app.schemas.triage import TriageResponse
from app.services.intake import IntakeService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/tickets/{ticket_id}/triage", tags=["triage"])


@router.post("", response_model=TriageResponse, status_code=201)
async def retriage_ticket(
    ticket_id: str,
    tenant_id: str = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
    intake_service: IntakeService = Depends(get_intake_service),
):
    """Re-triage an existing ticket (creates a new version)."""
    result = await db.execute(
        select(Ticket).where(
            Ticket.id == ticket_id,
            Ticket.tenant_id == tenant_id,
        )
    )
    ticket = result.scalar_one_or_none()
    if ticket is None:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")

    triage = await intake_service.process_ticket(
        tenant_id=tenant_id,
        source=ticket.source,
        raw_text=ticket.raw_text,
        reporter=ticket.reporter,
    )
    return triage


@router.get("", response_model=list[TriageResponse])
async def list_triage_versions(
    ticket_id: str,
    tenant_id: str = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    """Return all triage decision versions for a ticket, newest first."""
    ticket_result = await db.execute(
        select(Ticket.id).where(
            Ticket.id == ticket_id,
            Ticket.tenant_id == tenant_id,
        )
    )
    if ticket_result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")

    td_result = await db.execute(
        select(TriageDecision)
        .where(
            TriageDecision.ticket_id == ticket_id,
            TriageDecision.tenant_id == tenant_id,
        )
        .order_by(TriageDecision.version.desc())
    )
    decisions = td_result.scalars().all()

    return [
        TriageResponse(
            decision_id=td.id,
            ticket_id=td.ticket_id,
            module=td.module,
            priority=td.priority,
            issue_type=td.issue_type,
            root_cause_hypothesis=td.root_cause_hypothesis or "",
            recommended_solution=td.recommended_solution or "",
            assign_to=td.assign_to,
            confidence=td.confidence,
            confidence_calibrated=td.confidence_calibrated,
            classification_source=td.classification_source,
            model_version=td.model_version,
            rules_applied=td.rules_applied or [],
            similar_ticket_ids=td.similar_ticket_ids or [],
            similar_ticket_scores=td.similar_ticket_scores or [],
            kb_article_ids=td.kb_article_ids or [],
            manual_review_required=td.manual_review_required,
            review_reason=td.review_reason,
            latency_ms=td.latency_ms or 0,
        )
        for td in decisions
    ]
