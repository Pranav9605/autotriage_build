"""Tests for ClaudeTriageEngine and the IntakeService pipeline."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.tenant_config import (
    AIConfig,
    EscalationConfig,
    HardRule,
    HardRuleCondition,
    HardRuleOverride,
    TenantConfig,
)
from app.schemas.triage import (
    RetrievalResult,
    TriageDecisionSchema,
    TriageRequest,
    TriageResponse,
)
from app.services.rule_engine import RuleEngine
from app.services.triage_engine import ClaudeTriageEngine, _parse_decision


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

_VALID_DECISION_DICT = {
    "module": "FI",
    "priority": "P2",
    "issue_type": "Technical Issue",
    "root_cause_hypothesis": "FB50 document posting blocked by authorization object F_BKPF_BUK",
    "recommended_solution": "Grant user role with authorization for company code 1000",
    "assign_to": "SAP Finance Team",
    "confidence": 0.88,
    "manual_review_required": False,
    "similar_ticket_ids": [],
}

_VALID_DECISION_JSON = json.dumps(_VALID_DECISION_DICT)


def _make_triage_request(**kwargs) -> TriageRequest:
    defaults = dict(
        ticket_id="INC-2026-abc123",
        tenant_id="patil_group",
        description="FB50 is giving error F5 301 in production",
        tcode="FB50",
        error_code="F5 301",
        environment="PRD",
        source="solman",
        similar_tickets=[],
        kb_articles=[],
        tenant_config={
            "tenant_id": "patil_group",
            "display_name": "Patil Group",
            "modules_active": ["FI", "MM", "SD", "PP", "BASIS", "ABAP", "PI_PO"],
            "teams": {
                "FI": "SAP Finance Team",
                "MM": "SAP MM/Procurement Team",
                "DEFAULT": "General SAP Support",
            },
            "hard_rules": [],
            "escalation": {},
            "ai_config": {},
        },
    )
    defaults.update(kwargs)
    return TriageRequest(**defaults)


def _make_mock_anthropic_response(text: str, input_tokens: int = 100, output_tokens: int = 50):
    msg = MagicMock()
    content_block = MagicMock()
    content_block.text = text
    msg.content = [content_block]
    usage = MagicMock()
    usage.input_tokens = input_tokens
    usage.output_tokens = output_tokens
    msg.usage = usage
    return msg


# ---------------------------------------------------------------------------
# _parse_decision unit tests
# ---------------------------------------------------------------------------

def test_parse_decision_valid_json():
    result = _parse_decision(_VALID_DECISION_JSON)
    assert result is not None
    assert result.module == "FI"
    assert result.priority == "P2"
    assert result.confidence == 0.88


def test_parse_decision_strips_markdown_fences():
    fenced = f"```json\n{_VALID_DECISION_JSON}\n```"
    result = _parse_decision(fenced)
    assert result is not None
    assert result.module == "FI"


def test_parse_decision_returns_none_on_invalid_json():
    result = _parse_decision("This is not JSON at all.")
    assert result is None


def test_parse_decision_returns_none_on_schema_violation():
    bad = dict(_VALID_DECISION_DICT, module="INVALID_MODULE")
    result = _parse_decision(json.dumps(bad))
    assert result is None


# ---------------------------------------------------------------------------
# ClaudeTriageEngine tests (mocked API)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_engine_classify_success():
    engine = ClaudeTriageEngine(api_key="test-key")
    request = _make_triage_request()

    mock_response = _make_mock_anthropic_response(_VALID_DECISION_JSON)

    with patch.object(engine.client.messages, "create", new=AsyncMock(return_value=mock_response)):
        decision, tokens = await engine.classify(request)

    assert isinstance(decision, TriageDecisionSchema)
    assert decision.module == "FI"
    assert decision.priority == "P2"
    assert tokens == 150


@pytest.mark.asyncio
async def test_engine_classify_strips_markdown():
    engine = ClaudeTriageEngine(api_key="test-key")
    request = _make_triage_request()

    fenced = f"```json\n{_VALID_DECISION_JSON}\n```"
    mock_response = _make_mock_anthropic_response(fenced)

    with patch.object(engine.client.messages, "create", new=AsyncMock(return_value=mock_response)):
        decision, _ = await engine.classify(request)

    assert decision.module == "FI"


@pytest.mark.asyncio
async def test_engine_classify_retries_on_bad_json():
    """First call returns bad JSON; second call (correction) returns valid JSON."""
    engine = ClaudeTriageEngine(api_key="test-key")
    request = _make_triage_request()

    bad_response = _make_mock_anthropic_response("not json")
    good_response = _make_mock_anthropic_response(_VALID_DECISION_JSON)

    with patch.object(
        engine.client.messages,
        "create",
        new=AsyncMock(side_effect=[bad_response, good_response]),
    ):
        decision, _ = await engine.classify(request)

    assert decision.module == "FI"


@pytest.mark.asyncio
async def test_engine_classify_raises_after_two_bad_responses():
    from app.core.exceptions import TriageEngineError

    engine = ClaudeTriageEngine(api_key="test-key")
    request = _make_triage_request()

    bad_response = _make_mock_anthropic_response("still not json")

    with patch.object(
        engine.client.messages,
        "create",
        new=AsyncMock(side_effect=[bad_response, bad_response]),
    ):
        with pytest.raises(TriageEngineError):
            await engine.classify(request)


@pytest.mark.asyncio
async def test_engine_classify_raises_on_api_error():
    from app.core.exceptions import TriageEngineError

    engine = ClaudeTriageEngine(api_key="test-key")
    request = _make_triage_request()

    with patch.object(
        engine.client.messages,
        "create",
        new=AsyncMock(side_effect=Exception("API unavailable")),
    ):
        with pytest.raises(TriageEngineError):
            await engine.classify(request)


# ---------------------------------------------------------------------------
# IntakeService pipeline tests (mocked everything)
# ---------------------------------------------------------------------------

def _make_tenant_config() -> TenantConfig:
    return TenantConfig(
        tenant_id="patil_group",
        display_name="Patil Group",
        modules_active=["FI", "MM", "ABAP"],
        teams={"FI": "SAP Finance Team", "DEFAULT": "General SAP Support"},
        hard_rules=[],
        escalation=EscalationConfig(),
        ai_config=AIConfig(confidence_threshold=0.80),
    )


@pytest.fixture
def mock_intake_deps():
    """Returns a dict of all mocked dependencies for IntakeService."""
    db = AsyncMock()
    db.flush = AsyncMock()
    db.commit = AsyncMock()
    db.add = MagicMock()

    # Mock the version query: no existing decisions → version 1
    version_result = MagicMock()
    version_result.scalar_one_or_none.return_value = None
    db.execute = AsyncMock(return_value=version_result)

    embedding_svc = AsyncMock()
    embedding_svc.embed_text = AsyncMock(return_value=[0.1] * 1536)

    retrieval_svc = AsyncMock()
    retrieval_svc.search_similar = AsyncMock(return_value=[])

    mock_decision = TriageDecisionSchema(**_VALID_DECISION_DICT)
    triage_engine = AsyncMock()
    triage_engine.classify = AsyncMock(return_value=(mock_decision, 150))
    triage_engine.model = "claude-sonnet-4-20250514"

    return {
        "db": db,
        "embedding_svc": embedding_svc,
        "retrieval_svc": retrieval_svc,
        "triage_engine": triage_engine,
    }


@pytest.mark.asyncio
async def test_intake_full_pipeline_returns_triage_response(mock_intake_deps):
    from app.services.intake import IntakeService

    cfg = _make_tenant_config()
    engine = IntakeService(
        db=mock_intake_deps["db"],
        embedding_service=mock_intake_deps["embedding_svc"],
        retrieval_service=mock_intake_deps["retrieval_svc"],
        triage_engine=mock_intake_deps["triage_engine"],
        rule_engine_factory=lambda c: RuleEngine(c),
    )

    with patch("app.services.intake.load_tenant_config", return_value=cfg):
        response = await engine.process_ticket(
            tenant_id="patil_group",
            source="solman",
            raw_text="FB50 is giving error F5 301 in production",
        )

    assert isinstance(response, TriageResponse)
    assert response.module == "FI"
    assert response.priority == "P2"
    assert response.classification_source == "llm"
    assert response.ticket_id.startswith("INC-")


@pytest.mark.asyncio
async def test_intake_manual_review_when_low_confidence(mock_intake_deps):
    from app.services.intake import IntakeService

    cfg = _make_tenant_config()
    low_conf_decision = TriageDecisionSchema(
        **{**_VALID_DECISION_DICT, "confidence": 0.55, "manual_review_required": False}
    )
    mock_intake_deps["triage_engine"].classify = AsyncMock(
        return_value=(low_conf_decision, 100)
    )

    engine = IntakeService(
        db=mock_intake_deps["db"],
        embedding_service=mock_intake_deps["embedding_svc"],
        retrieval_service=mock_intake_deps["retrieval_svc"],
        triage_engine=mock_intake_deps["triage_engine"],
        rule_engine_factory=lambda c: RuleEngine(c),
    )

    with patch("app.services.intake.load_tenant_config", return_value=cfg):
        response = await engine.process_ticket(
            tenant_id="patil_group",
            source="chat",
            raw_text="Some issue",
        )

    assert response.manual_review_required is True
    assert response.review_reason == "low_confidence"


@pytest.mark.asyncio
async def test_intake_rule_applied_abap_prd(mock_intake_deps):
    from app.services.intake import IntakeService

    cfg = _make_tenant_config()
    cfg.hard_rules = [
        HardRule(
            name="ABAP in production is always P1",
            condition=HardRuleCondition(module="ABAP", environment="PRD"),
            override=HardRuleOverride(priority="P1", manual_review_required=True, review_reason="rule_triggered"),
        )
    ]

    abap_decision = TriageDecisionSchema(
        **{**_VALID_DECISION_DICT, "module": "ABAP", "priority": "P3"}
    )
    mock_intake_deps["triage_engine"].classify = AsyncMock(
        return_value=(abap_decision, 100)
    )

    engine = IntakeService(
        db=mock_intake_deps["db"],
        embedding_service=mock_intake_deps["embedding_svc"],
        retrieval_service=mock_intake_deps["retrieval_svc"],
        triage_engine=mock_intake_deps["triage_engine"],
        rule_engine_factory=lambda c: RuleEngine(c),
    )

    # Description contains "PRD" so enrichment will detect environment=PRD
    with patch("app.services.intake.load_tenant_config", return_value=cfg):
        response = await engine.process_ticket(
            tenant_id="patil_group",
            source="solman",
            raw_text="SE38 program failing in PRD system",
        )

    assert response.priority == "P1"
    assert response.manual_review_required is True
    assert "ABAP in production is always P1" in response.rules_applied


@pytest.mark.asyncio
async def test_intake_fallback_on_triage_engine_error(mock_intake_deps):
    from app.core.exceptions import TriageEngineError
    from app.services.intake import IntakeService

    cfg = _make_tenant_config()
    mock_intake_deps["triage_engine"].classify = AsyncMock(
        side_effect=TriageEngineError("LLM down")
    )

    engine = IntakeService(
        db=mock_intake_deps["db"],
        embedding_service=mock_intake_deps["embedding_svc"],
        retrieval_service=mock_intake_deps["retrieval_svc"],
        triage_engine=mock_intake_deps["triage_engine"],
        rule_engine_factory=lambda c: RuleEngine(c),
    )

    with patch("app.services.intake.load_tenant_config", return_value=cfg):
        response = await engine.process_ticket(
            tenant_id="patil_group",
            source="chat",
            raw_text="System error",
        )

    assert response.classification_source == "error"
    assert response.manual_review_required is True
    assert response.confidence == 0.0


@pytest.mark.asyncio
async def test_intake_includes_similar_ticket_ids(mock_intake_deps):
    from app.services.intake import IntakeService

    cfg = _make_tenant_config()
    similar = [
        RetrievalResult(
            result_id="INC-2026-old1",
            result_type="ticket",
            title="INC-2026-old1",
            content="FB50 error in FI module",
            final_score=0.92,
            semantic_score=0.90,
            lexical_score=0.80,
            exact_boost=0.3,
        )
    ]
    mock_intake_deps["retrieval_svc"].search_similar = AsyncMock(return_value=similar)

    engine = IntakeService(
        db=mock_intake_deps["db"],
        embedding_service=mock_intake_deps["embedding_svc"],
        retrieval_service=mock_intake_deps["retrieval_svc"],
        triage_engine=mock_intake_deps["triage_engine"],
        rule_engine_factory=lambda c: RuleEngine(c),
    )

    with patch("app.services.intake.load_tenant_config", return_value=cfg):
        response = await engine.process_ticket(
            tenant_id="patil_group",
            source="solman",
            raw_text="FB50 posting error F5 301",
        )

    assert "INC-2026-old1" in response.similar_ticket_ids
    assert len(response.similar_ticket_scores) == 1
