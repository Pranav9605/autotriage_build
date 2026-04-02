"""Feedback API — submit consultant feedback on triage decisions."""

import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_tenant_id
from app.models.feedback import Feedback
from app.schemas.feedback import FeedbackCreate, FeedbackResponse
from app.services.feedback_service import FeedbackService
from app import sse

logger = logging.getLogger(__name__)
router = APIRouter(tags=["feedback"])

_svc = FeedbackService()


@router.post(
    "/api/v1/triage/{triage_decision_id}/feedback",
    response_model=FeedbackResponse,
    status_code=201,
)
async def create_feedback(
    triage_decision_id: str,
    body: FeedbackCreate,
    tenant_id: str = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    """Record a consultant's accept/override decision on a triage result."""
    try:
        result = await _svc.create_feedback(
            db=db,
            triage_decision_id=triage_decision_id,
            feedback=body,
            tenant_id=tenant_id,
        )
    except Exception as exc:
        from app.core.exceptions import TicketNotFoundError
        if isinstance(exc, TicketNotFoundError):
            raise HTTPException(status_code=404, detail=str(exc))
        raise

    await sse.broadcast("feedback_received", {
        "ticket_id": result.ticket_id,
        "action": result.action,
        "override_category": result.override_category,
        "tenant_id": tenant_id,
    })
    return result


@router.get("/api/v1/feedback", response_model=list[FeedbackResponse])
async def list_feedback(
    tenant_id: str = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    """List all feedback for the tenant (for training pipeline consumption)."""
    result = await db.execute(
        select(Feedback)
        .where(Feedback.tenant_id == tenant_id)
        .order_by(Feedback.decided_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    records = result.scalars().all()
    return [
        FeedbackResponse(
            id=r.id,
            ticket_id=r.ticket_id,
            action=r.action,
            overrides=r.overrides,
            override_category=r.override_category,
            comment=r.comment,
            consultant_id=r.consultant_id,
            decided_at=r.decided_at,
            final_module=r.final_module,
            final_priority=r.final_priority,
            is_correct_module=r.is_correct_module,
            is_correct_priority=r.is_correct_priority,
        )
        for r in records
    ]
