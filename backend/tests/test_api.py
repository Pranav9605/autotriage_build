"""Phase 6 — Full API integration tests (14 tests)."""

import pytest
from httpx import ASGITransport, AsyncClient
from app.dependencies import get_db, get_intake_service
from app.main import app

from tests.conftest import (
    TENANT_B_ID,
    TENANT_ID,
    make_execute_result,
    make_kb_article_orm,
    make_triage_decision_orm,
    make_triage_response,
    make_ticket_orm,
    FIXED_NOW,
)


# ---------------------------------------------------------------------------
# 1. Create ticket + triage
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_ticket_and_triage(client, mock_intake, mock_db):
    ticket = make_ticket_orm()
    mock_db.execute.return_value = make_execute_result(scalar=ticket)

    resp = await client.post(
        "/api/v1/tickets",
        json={"source": "chat", "raw_text": "FB50 posting error F5 301 in production"},
    )

    assert resp.status_code == 201
    body = resp.json()
    assert body["id"] == "INC-2026-test001"
    assert body["triage"]["module"] == "FI"
    assert body["triage"]["priority"] == "P2"
    assert body["triage"]["confidence"] == 0.88
    assert body["triage"]["decision_id"] == "dec-test-001"
    mock_intake.process_ticket.assert_called_once()


# ---------------------------------------------------------------------------
# 2. Create ticket enrichment fields pass through
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_ticket_enrichment(client, mock_intake, mock_db):
    enriched_ticket = make_ticket_orm(
        id="INC-2026-enrich001",
        tcode="ME21N",
        error_code="M7 021",
        environment="QAS",
    )
    mock_intake.process_ticket.return_value = make_triage_response(
        ticket_id="INC-2026-enrich001"
    )
    mock_db.execute.return_value = make_execute_result(scalar=enriched_ticket)

    resp = await client.post(
        "/api/v1/tickets",
        json={
            "source": "solman",
            "raw_text": "ME21N is failing with error M7 021 in QAS system",
        },
    )

    assert resp.status_code == 201
    body = resp.json()
    assert body["tcode"] == "ME21N"
    assert body["error_code"] == "M7 021"
    assert body["environment"] == "QAS"


# ---------------------------------------------------------------------------
# 3. Ticket list with status filter
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_ticket_list_with_filters(client, mock_db):
    t1 = make_ticket_orm(id="INC-001", status="triaged")
    t2 = make_ticket_orm(id="INC-002", status="triaged")
    td1 = make_triage_decision_orm(id="dec-001", ticket_id="INC-001")
    td2 = make_triage_decision_orm(id="dec-002", ticket_id="INC-002")

    mock_db.execute.side_effect = [
        make_execute_result(scalar=2),                        # count query
        make_execute_result(scalars_list=[t1, t2]),           # tickets
        make_execute_result(scalars_list=[td1, td2]),         # triage decisions
    ]

    resp = await client.get("/api/v1/tickets?status=triaged")

    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 2
    assert len(body["tickets"]) == 2
    ids = [t["id"] for t in body["tickets"]]
    assert "INC-001" in ids
    assert "INC-002" in ids


# ---------------------------------------------------------------------------
# 4. Feedback — accept
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_feedback_accept(client, mock_db):
    td = make_triage_decision_orm()
    mock_db.execute.return_value = make_execute_result(scalar=td)
    # After db.add + db.commit, db.refresh sets decided_at on the real Feedback obj
    # The FeedbackService creates a real Feedback instance and returns a FeedbackResponse

    resp = await client.post(
        "/api/v1/triage/dec-test-001/feedback",
        json={
            "action": "accepted",
            "consultant_id": "consultant-1",
        },
    )

    assert resp.status_code == 201
    body = resp.json()
    assert body["action"] == "accepted"
    assert body["is_correct_module"] is True
    assert body["is_correct_priority"] is True
    assert body["final_module"] == "FI"
    assert body["final_priority"] == "P2"


# ---------------------------------------------------------------------------
# 5. Feedback — override module
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_feedback_override(client, mock_db):
    td = make_triage_decision_orm(module="FI", priority="P2")
    mock_db.execute.return_value = make_execute_result(scalar=td)

    resp = await client.post(
        "/api/v1/triage/dec-test-001/feedback",
        json={
            "action": "overridden",
            "overrides": {"module": "MM"},
            "override_category": "wrong_module",
            "consultant_id": "consultant-1",
        },
    )

    assert resp.status_code == 201
    body = resp.json()
    assert body["action"] == "overridden"
    assert body["final_module"] == "MM"
    assert body["is_correct_module"] is False
    assert body["is_correct_priority"] is True  # priority not overridden


# ---------------------------------------------------------------------------
# 6. Feedback — validation errors
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_feedback_override_validation(client):
    # override without overrides dict → 422
    resp = await client.post(
        "/api/v1/triage/dec-001/feedback",
        json={
            "action": "overridden",
            "override_category": "wrong_module",
            "consultant_id": "consultant-1",
        },
    )
    assert resp.status_code == 422

    # override without override_category → 422
    resp = await client.post(
        "/api/v1/triage/dec-001/feedback",
        json={
            "action": "overridden",
            "overrides": {"module": "MM"},
            "consultant_id": "consultant-1",
        },
    )
    assert resp.status_code == 422

    # accept without overrides → valid
    # (no DB call needed since Pydantic validation runs first)


# ---------------------------------------------------------------------------
# 7. Rule engine — ABAP PRD escalates to P1
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_rule_engine_abap_prd(client, mock_intake, mock_db):
    rule_name = "ABAP in production is always P1"
    mock_intake.process_ticket.return_value = make_triage_response(
        module="ABAP",
        priority="P1",
        manual_review_required=True,
        review_reason="rule_triggered",
        rules_applied=[rule_name],
    )
    ticket = make_ticket_orm(description="SE38 program failing in PRD system")
    mock_db.execute.return_value = make_execute_result(scalar=ticket)

    resp = await client.post(
        "/api/v1/tickets",
        json={"source": "solman", "raw_text": "SE38 program failing in PRD system"},
    )

    assert resp.status_code == 201
    body = resp.json()
    assert body["triage"]["priority"] == "P1"
    assert body["triage"]["manual_review_required"] is True
    assert rule_name in body["triage"]["rules_applied"]


# ---------------------------------------------------------------------------
# 8. KB article CRUD
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_kb_article_crud(client, mock_embedding, mock_db):
    article = make_kb_article_orm()

    # POST create
    mock_db.execute.return_value = make_execute_result()  # not used in create
    resp = await client.post(
        "/api/v1/kb/articles",
        json={
            "title": "FB50 Posting Errors",
            "content": "How to resolve FB50 posting errors in SAP FI.",
            "module": "FI",
            "error_codes": ["F5 301"],
            "tcodes": ["FB50"],
            "tags": ["fi", "posting"],
        },
    )
    assert resp.status_code == 201
    created = resp.json()
    assert created["title"] == "FB50 Posting Errors"
    assert created["module"] == "FI"
    article_id = created["id"]

    # GET by id
    mock_db.execute.return_value = make_execute_result(scalar=article)
    resp = await client.get(f"/api/v1/kb/articles/{article_id}")
    assert resp.status_code == 200
    assert resp.json()["title"] == "FB50 Posting Errors"

    # PUT update
    mock_db.execute.return_value = make_execute_result(scalar=article)
    resp = await client.put(
        f"/api/v1/kb/articles/{article_id}",
        json={
            "title": "FB50 Posting Errors — Updated",
            "content": "Updated content.",
            "module": "FI",
        },
    )
    assert resp.status_code == 200

    # GET search
    from types import SimpleNamespace
    row = SimpleNamespace(
        id=article_id,
        title="FB50 Posting Errors",
        content="How to resolve FB50 posting errors in SAP FI.",
        module="FI",
        error_codes=["F5 301"],
        tcodes=["FB50"],
        tags=["fi", "posting"],
        created_at=FIXED_NOW,
    )
    mock_db.execute.return_value = make_execute_result(rows=[row])
    resp = await client.get("/api/v1/kb/search?q=posting error")
    assert resp.status_code == 200
    data = resp.json()
    assert data["query"] == "posting error"
    assert len(data["results"]) == 1


# ---------------------------------------------------------------------------
# 9. Dashboard KPIs
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_dashboard_kpis(client, mock_db):
    from types import SimpleNamespace

    mock_db.execute.side_effect = [
        make_execute_result(one_result=SimpleNamespace(total=5, triaged=4)),
        make_execute_result(
            one_result=SimpleNamespace(
                avg_confidence=0.85, avg_latency=200.0, manual_review=1
            )
        ),
        make_execute_result(
            one_result=SimpleNamespace(total_feedback=5, accepted=3, overridden=2)
        ),
        make_execute_result(scalar=None),  # mttr — no resolved tickets
    ]

    resp = await client.get("/api/v1/dashboard/kpis")

    assert resp.status_code == 200
    body = resp.json()
    assert body["total_tickets"] == 5
    assert body["triaged_tickets"] == 4
    assert body["accuracy_rate"] == 0.6       # 3/5
    assert body["override_rate"] == 0.4       # 2/5
    assert body["avg_confidence"] == 0.85
    assert body["mttr_hours"] is None


# ---------------------------------------------------------------------------
# 10. Module accuracy
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_module_accuracy(client, mock_db):
    from types import SimpleNamespace

    fi_row = SimpleNamespace(
        module="FI", total=3, correct=2, override_count=1,
        most_common_override="wrong_module",
    )
    mm_row = SimpleNamespace(
        module="MM", total=2, correct=2, override_count=0,
        most_common_override=None,
    )

    result_mock = make_execute_result()
    result_mock.__iter__ = lambda s: iter([fi_row, mm_row])
    mock_db.execute.return_value = result_mock

    resp = await client.get("/api/v1/dashboard/module-accuracy")

    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    modules = {r["module"]: r for r in data}
    assert modules["FI"]["accuracy"] == pytest.approx(2 / 3, abs=0.001)
    assert modules["MM"]["accuracy"] == 1.0


# ---------------------------------------------------------------------------
# 11. Health endpoint
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_health_endpoint(client, mock_db):
    mock_db.execute.return_value = make_execute_result(scalar=1)

    resp = await client.get("/api/v1/health")

    assert resp.status_code == 200
    body = resp.json()
    assert "status" in body
    assert body["status"] in ("healthy", "degraded", "unhealthy")
    assert "components" in body
    assert "database" in body["components"]


# ---------------------------------------------------------------------------
# 12. Tenant isolation — CRITICAL
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_tenant_isolation(mock_intake, mock_db):
    async def _override_db():
        yield mock_db

    app.dependency_overrides[get_db] = _override_db
    app.dependency_overrides[get_intake_service] = lambda: mock_intake

    try:
        ticket_id = "INC-2026-test001"

        # Tenant A can see its ticket — route makes two queries: ticket + triage_decision
        mock_db.execute.side_effect = [
            make_execute_result(scalar=make_ticket_orm(id=ticket_id, tenant_id=TENANT_ID)),
            make_execute_result(scalar=None),  # no triage decision yet
        ]
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            headers={"X-Tenant-Id": TENANT_ID},
        ) as ac_a:
            resp_a = await ac_a.get(f"/api/v1/tickets/{ticket_id}")
        assert resp_a.status_code == 200

        # Tenant B cannot see Tenant A's ticket (DB returns no row)
        mock_db.execute.side_effect = None
        mock_db.execute.return_value = make_execute_result(scalar=None)
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            headers={"X-Tenant-Id": TENANT_B_ID},
        ) as ac_b:
            resp_b = await ac_b.get(f"/api/v1/tickets/{ticket_id}")
        assert resp_b.status_code == 404

    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# 13. Manual review flag propagates
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_manual_review_flag(client, mock_intake, mock_db):
    mock_intake.process_ticket.return_value = make_triage_response(
        confidence=0.65,
        manual_review_required=True,
        review_reason="low_confidence",
    )
    ticket = make_ticket_orm()
    mock_db.execute.return_value = make_execute_result(scalar=ticket)

    resp = await client.post(
        "/api/v1/tickets",
        json={"source": "chat", "raw_text": "Some vague SAP issue I cannot describe"},
    )

    assert resp.status_code == 201
    body = resp.json()
    assert body["triage"]["manual_review_required"] is True
    assert body["triage"]["review_reason"] == "low_confidence"
    assert body["triage"]["confidence"] == 0.65


# ---------------------------------------------------------------------------
# 14. Re-triage creates new version, list returns all versions
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_retriage(client, mock_intake, mock_db):
    ticket_id = "INC-2026-test001"
    ticket = make_ticket_orm(id=ticket_id)
    td_v1 = make_triage_decision_orm(id="dec-v1", ticket_id=ticket_id, version=1)
    td_v2 = make_triage_decision_orm(id="dec-v2", ticket_id=ticket_id, version=2)
    mock_intake.process_ticket.return_value = make_triage_response(
        ticket_id=ticket_id, decision_id="dec-v2"
    )

    # POST retriage: fetch ticket → process
    mock_db.execute.return_value = make_execute_result(scalar=ticket)
    resp = await client.post(f"/api/v1/tickets/{ticket_id}/triage")
    assert resp.status_code == 201
    assert resp.json()["ticket_id"] == ticket_id

    # GET triage versions: check ticket exists → list decisions
    mock_db.execute.side_effect = [
        make_execute_result(scalar=ticket_id),              # exists check
        make_execute_result(scalars_list=[td_v2, td_v1]),  # decisions newest-first
    ]
    resp = await client.get(f"/api/v1/tickets/{ticket_id}/triage")
    assert resp.status_code == 200
    versions = resp.json()
    assert len(versions) == 2
    assert versions[0]["decision_id"] == "dec-v2"
    assert versions[1]["decision_id"] == "dec-v1"
