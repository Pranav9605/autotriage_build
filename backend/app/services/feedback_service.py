"""Feedback service — persists consultant feedback and computes derived fields."""

import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import TicketNotFoundError
from app.models.feedback import Feedback
from app.models.triage_decision import TriageDecision
from app.schemas.feedback import FeedbackCreate, FeedbackResponse
from app.utils.id_generator import generate_uuid

logger = logging.getLogger(__name__)


class FeedbackService:
    async def create_feedback(
        self,
        db: AsyncSession,
        triage_decision_id: str,
        feedback: FeedbackCreate,
        tenant_id: str,
    ) -> FeedbackResponse:
        """Load the triage decision, compute derived fields, persist feedback."""
        result = await db.execute(
            select(TriageDecision).where(
                TriageDecision.id == triage_decision_id,
                TriageDecision.tenant_id == tenant_id,
            )
        )
        decision = result.scalar_one_or_none()
        if decision is None:
            raise TicketNotFoundError(triage_decision_id)

        overrides = feedback.overrides or {}

        final_module = overrides.get("module", decision.module)
        final_priority = overrides.get("priority", decision.priority)
        final_assign_to = overrides.get("assign_to", decision.assign_to)

        is_correct_module = feedback.action == "accepted" or "module" not in overrides
        is_correct_priority = feedback.action == "accepted" or "priority" not in overrides

        record = Feedback(
            id=generate_uuid(),
            ticket_id=decision.ticket_id,
            triage_decision_id=triage_decision_id,
            tenant_id=tenant_id,
            action=feedback.action,
            overrides=overrides or None,
            override_category=feedback.override_category,
            comment=feedback.comment,
            consultant_id=feedback.consultant_id,
            final_module=final_module,
            final_priority=final_priority,
            final_assign_to=final_assign_to,
            is_correct_module=is_correct_module,
            is_correct_priority=is_correct_priority,
        )
        db.add(record)
        await db.commit()
        await db.refresh(record)

        logger.info(
            "Feedback created: decision=%s action=%s tenant=%s",
            triage_decision_id,
            feedback.action,
            tenant_id,
        )

        return FeedbackResponse(
            id=record.id,
            ticket_id=record.ticket_id,
            action=record.action,
            overrides=record.overrides,
            override_category=record.override_category,
            comment=record.comment,
            consultant_id=record.consultant_id,
            decided_at=record.decided_at,
            final_module=record.final_module,
            final_priority=record.final_priority,
            is_correct_module=record.is_correct_module,
            is_correct_priority=record.is_correct_priority,
        )
