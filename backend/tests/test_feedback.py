"""FeedbackService unit tests — Phase 6."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.core.exceptions import TicketNotFoundError
from app.schemas.feedback import FeedbackCreate
from app.services.feedback_service import FeedbackService

from tests.conftest import FIXED_NOW, TENANT_ID, make_execute_result, make_triage_decision_orm


def _make_db(td=None):
    db = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()

    async def smart_refresh(obj):
        for field in ("decided_at", "created_at"):
            if hasattr(obj, field) and getattr(obj, field) is None:
                setattr(obj, field, FIXED_NOW)

    db.refresh = AsyncMock(side_effect=smart_refresh)
    db.execute = AsyncMock(return_value=make_execute_result(scalar=td))
    return db


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_feedback_service_accept():
    td = make_triage_decision_orm(module="FI", priority="P2")
    db = _make_db(td)

    svc = FeedbackService()
    result = await svc.create_feedback(
        db=db,
        triage_decision_id="dec-test-001",
        feedback=FeedbackCreate(action="accepted", consultant_id="consultant-1"),
        tenant_id=TENANT_ID,
    )

    assert result.action == "accepted"
    assert result.final_module == "FI"
    assert result.final_priority == "P2"
    assert result.is_correct_module is True
    assert result.is_correct_priority is True
    db.add.assert_called_once()
    db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_feedback_service_override_module():
    td = make_triage_decision_orm(module="FI", priority="P2")
    db = _make_db(td)

    svc = FeedbackService()
    result = await svc.create_feedback(
        db=db,
        triage_decision_id="dec-test-001",
        feedback=FeedbackCreate(
            action="overridden",
            overrides={"module": "MM"},
            override_category="wrong_module",
            consultant_id="consultant-1",
        ),
        tenant_id=TENANT_ID,
    )

    assert result.action == "overridden"
    assert result.final_module == "MM"
    assert result.final_priority == "P2"     # unchanged
    assert result.is_correct_module is False
    assert result.is_correct_priority is True


@pytest.mark.asyncio
async def test_feedback_service_override_priority():
    td = make_triage_decision_orm(module="FI", priority="P2")
    db = _make_db(td)

    svc = FeedbackService()
    result = await svc.create_feedback(
        db=db,
        triage_decision_id="dec-test-001",
        feedback=FeedbackCreate(
            action="overridden",
            overrides={"priority": "P1"},
            override_category="wrong_priority",
            consultant_id="consultant-1",
        ),
        tenant_id=TENANT_ID,
    )

    assert result.final_module == "FI"       # unchanged
    assert result.final_priority == "P1"
    assert result.is_correct_module is True
    assert result.is_correct_priority is False


@pytest.mark.asyncio
async def test_feedback_service_missing_decision_raises():
    db = _make_db(td=None)  # decision not found

    svc = FeedbackService()
    with pytest.raises(TicketNotFoundError):
        await svc.create_feedback(
            db=db,
            triage_decision_id="nonexistent",
            feedback=FeedbackCreate(action="accepted", consultant_id="consultant-1"),
            tenant_id=TENANT_ID,
        )


@pytest.mark.asyncio
async def test_feedback_both_fields_overridden():
    td = make_triage_decision_orm(module="FI", priority="P2")
    db = _make_db(td)

    svc = FeedbackService()
    result = await svc.create_feedback(
        db=db,
        triage_decision_id="dec-test-001",
        feedback=FeedbackCreate(
            action="overridden",
            overrides={"module": "BASIS", "priority": "P1"},
            override_category="wrong_module",
            consultant_id="consultant-1",
        ),
        tenant_id=TENANT_ID,
    )

    assert result.final_module == "BASIS"
    assert result.final_priority == "P1"
    assert result.is_correct_module is False
    assert result.is_correct_priority is False
