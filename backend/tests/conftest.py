"""Shared test fixtures for Phase 6 integration tests."""

from datetime import datetime, timezone
from typing import Optional
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.dependencies import get_db, get_embedding_service, get_intake_service
from app.main import app
from app.models.feedback import Feedback
from app.models.kb_article import KBArticle
from app.models.ticket import Ticket
from app.models.triage_decision import TriageDecision
from app.schemas.triage import TriageResponse

TENANT_ID = "patil_group"
TENANT_B_ID = "other_tenant"
FIXED_NOW = datetime(2026, 3, 30, 12, 0, 0, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# Response / ORM object factories
# ---------------------------------------------------------------------------

def make_triage_response(
    ticket_id: str = "INC-2026-test001",
    decision_id: str = "dec-test-001",
    module: str = "FI",
    priority: str = "P2",
    confidence: float = 0.88,
    manual_review_required: bool = False,
    review_reason: Optional[str] = None,
    rules_applied: Optional[list] = None,
    classification_source: str = "llm",
) -> TriageResponse:
    return TriageResponse(
        decision_id=decision_id,
        ticket_id=ticket_id,
        module=module,
        priority=priority,
        issue_type="Technical Issue",
        root_cause_hypothesis="FB50 document posting blocked by authorization",
        recommended_solution="Grant role with authorization for company code 1000",
        assign_to="SAP Finance Team",
        confidence=confidence,
        confidence_calibrated=confidence,
        classification_source=classification_source,
        model_version="claude-sonnet-4-20250514",
        rules_applied=rules_applied or [],
        similar_ticket_ids=[],
        similar_ticket_scores=[],
        kb_article_ids=[],
        manual_review_required=manual_review_required,
        review_reason=review_reason,
        latency_ms=250,
    )


def make_ticket_orm(
    id: str = "INC-2026-test001",
    tenant_id: str = TENANT_ID,
    source: str = "chat",
    raw_text: str = "FB50 posting error F5 301 in production",
    description: str = "FB50 posting error F5 301 in production",
    tcode: Optional[str] = None,
    error_code: Optional[str] = None,
    environment: Optional[str] = None,
    reporter: Optional[str] = None,
    status: str = "triaged",
) -> MagicMock:
    t = MagicMock(spec=Ticket)
    t.id = id
    t.tenant_id = tenant_id
    t.source = source
    t.raw_text = raw_text
    t.description = description
    t.tcode = tcode
    t.error_code = error_code
    t.environment = environment
    t.reporter = reporter
    t.status = status
    t.created_at = FIXED_NOW
    t.resolved_at = None
    return t


def make_triage_decision_orm(
    id: str = "dec-test-001",
    ticket_id: str = "INC-2026-test001",
    tenant_id: str = TENANT_ID,
    version: int = 1,
    module: str = "FI",
    priority: str = "P2",
    confidence: float = 0.88,
    manual_review_required: bool = False,
    review_reason: Optional[str] = None,
    rules_applied: Optional[list] = None,
) -> MagicMock:
    td = MagicMock(spec=TriageDecision)
    td.id = id
    td.ticket_id = ticket_id
    td.tenant_id = tenant_id
    td.version = version
    td.module = module
    td.priority = priority
    td.issue_type = "Technical Issue"
    td.root_cause_hypothesis = "FB50 blocked"
    td.recommended_solution = "Grant auth"
    td.assign_to = "SAP Finance Team"
    td.confidence = confidence
    td.confidence_calibrated = confidence
    td.classification_source = "llm"
    td.model_version = "claude-sonnet-4-20250514"
    td.rules_applied = rules_applied
    td.similar_ticket_ids = None
    td.similar_ticket_scores = None
    td.kb_article_ids = None
    td.manual_review_required = manual_review_required
    td.review_reason = review_reason
    td.latency_ms = 250
    return td


def make_kb_article_orm(
    id: str = "kb-test-001",
    tenant_id: str = TENANT_ID,
    title: str = "FB50 Posting Errors",
    content: str = "How to resolve FB50 posting errors in SAP FI.",
    module: str = "FI",
) -> MagicMock:
    a = MagicMock(spec=KBArticle)
    a.id = id
    a.tenant_id = tenant_id
    a.title = title
    a.content = content
    a.module = module
    a.error_codes = ["F5 301", "F5 302"]
    a.tcodes = ["FB50"]
    a.tags = ["fi", "posting"]
    a.created_at = FIXED_NOW
    a.embedding = [0.1] * 1536
    return a


def make_feedback_orm(
    id: str = "fb-test-001",
    ticket_id: str = "INC-2026-test001",
    triage_decision_id: str = "dec-test-001",
    tenant_id: str = TENANT_ID,
    action: str = "accepted",
    final_module: str = "FI",
    final_priority: str = "P2",
    is_correct_module: bool = True,
    is_correct_priority: bool = True,
) -> MagicMock:
    f = MagicMock(spec=Feedback)
    f.id = id
    f.ticket_id = ticket_id
    f.triage_decision_id = triage_decision_id
    f.tenant_id = tenant_id
    f.action = action
    f.overrides = None
    f.override_category = None
    f.comment = None
    f.consultant_id = "consultant-1"
    f.decided_at = FIXED_NOW
    f.final_module = final_module
    f.final_priority = final_priority
    f.final_assign_to = "SAP Finance Team"
    f.is_correct_module = is_correct_module
    f.is_correct_priority = is_correct_priority
    return f


# ---------------------------------------------------------------------------
# Mock DB execute result builder
# ---------------------------------------------------------------------------

def make_execute_result(
    scalar=None,
    scalars_list: Optional[list] = None,
    rows: Optional[list] = None,
    one_result=None,
    iterable: Optional[list] = None,
) -> MagicMock:
    """Build a mock result that handles common SQLAlchemy result access patterns."""
    result = MagicMock()

    result.scalar_one.return_value = scalar
    result.scalar_one_or_none.return_value = scalar
    result.one.return_value = one_result

    scalars_proxy = MagicMock()
    scalars_proxy.all.return_value = scalars_list or []
    # Support iteration directly on scalars()
    scalars_proxy.__iter__ = lambda s: iter(scalars_list or [])
    result.scalars.return_value = scalars_proxy

    result.fetchall.return_value = rows or []

    # Support direct iteration on the result (used in dashboard module_accuracy)
    _iter_data = iterable or []
    result.__iter__ = lambda s: iter(_iter_data)

    return result


# ---------------------------------------------------------------------------
# Core fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_intake():
    svc = AsyncMock()
    svc.process_ticket = AsyncMock(return_value=make_triage_response())
    return svc


@pytest.fixture
def mock_embedding():
    svc = AsyncMock()
    svc.embed_text = AsyncMock(return_value=[0.1] * 1536)
    return svc


@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()

    async def smart_refresh(obj):
        """Set server_default datetime fields that would be set by PostgreSQL."""
        for field in ("decided_at", "created_at", "updated_at"):
            if hasattr(obj, field) and getattr(obj, field) is None:
                setattr(obj, field, FIXED_NOW)

    db.refresh = AsyncMock(side_effect=smart_refresh)
    db.execute = AsyncMock(return_value=make_execute_result())
    return db


@pytest_asyncio.fixture
async def client(mock_intake, mock_embedding, mock_db):
    """AsyncClient with all external dependencies overridden."""

    async def _override_db():
        yield mock_db

    app.dependency_overrides[get_db] = _override_db
    app.dependency_overrides[get_intake_service] = lambda: mock_intake
    app.dependency_overrides[get_embedding_service] = lambda: mock_embedding

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers={"X-Tenant-Id": TENANT_ID},
    ) as ac:
        yield ac

    app.dependency_overrides.clear()
