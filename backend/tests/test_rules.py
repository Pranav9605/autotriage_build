"""Tests for the RuleEngine."""

from app.core.tenant_config import (
    AIConfig,
    EscalationConfig,
    HardRule,
    HardRuleCondition,
    HardRuleOverride,
    TenantConfig,
)
from app.schemas.triage import TriageDecisionSchema
from app.services.rule_engine import RuleEngine


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_decision(**kwargs) -> TriageDecisionSchema:
    defaults = dict(
        module="FI",
        priority="P3",
        issue_type="Technical Issue",
        root_cause_hypothesis="Hypothesis",
        recommended_solution="Solution",
        assign_to="SAP Finance Team",
        confidence=0.90,
        manual_review_required=False,
        similar_ticket_ids=[],
    )
    defaults.update(kwargs)
    return TriageDecisionSchema(**defaults)


def _make_config(rules: list[HardRule]) -> TenantConfig:
    return TenantConfig(
        tenant_id="test",
        display_name="Test Tenant",
        modules_active=["FI", "MM", "ABAP", "BASIS"],
        teams={
            "FI": "SAP Finance Team",
            "MM": "SAP MM/Procurement Team",
            "ABAP": "ABAP Development Team",
            "DEFAULT": "General SAP Support",
        },
        hard_rules=rules,
        escalation=EscalationConfig(),
        ai_config=AIConfig(),
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_no_rules_returns_decision_unchanged():
    engine = RuleEngine(_make_config([]))
    decision = _make_decision()
    result, fired = engine.apply_rules(decision, "chat", "QAS", None)
    assert result == decision
    assert fired == []


def test_abap_prd_escalates_to_p1():
    rule = HardRule(
        name="ABAP in production is always P1",
        condition=HardRuleCondition(module="ABAP", environment="PRD"),
        override=HardRuleOverride(priority="P1", manual_review_required=True, review_reason="rule_triggered"),
    )
    engine = RuleEngine(_make_config([rule]))
    decision = _make_decision(module="ABAP", priority="P3")

    result, fired = engine.apply_rules(decision, "solman", "PRD", None)

    assert result.priority == "P1"
    assert result.manual_review_required is True
    assert result.review_reason == "rule_triggered"
    assert "ABAP in production is always P1" in fired


def test_abap_non_prd_does_not_trigger_rule():
    rule = HardRule(
        name="ABAP in production is always P1",
        condition=HardRuleCondition(module="ABAP", environment="PRD"),
        override=HardRuleOverride(priority="P1"),
    )
    engine = RuleEngine(_make_config([rule]))
    decision = _make_decision(module="ABAP", priority="P3")

    result, fired = engine.apply_rules(decision, "solman", "QAS", None)

    assert result.priority == "P3"
    assert fired == []


def test_f5_error_code_routes_to_fi():
    rule = HardRule(
        name="F5 errors route to Finance",
        condition=HardRuleCondition(error_code_prefix="F5"),
        override=HardRuleOverride(module="FI", assign_to="SAP Finance Team"),
    )
    engine = RuleEngine(_make_config([rule]))
    decision = _make_decision(module="MM", assign_to="SAP MM/Procurement Team")

    result, fired = engine.apply_rules(decision, "chat", None, "F5 301")

    assert result.module == "FI"
    assert result.assign_to == "SAP Finance Team"
    assert "F5 errors route to Finance" in fired


def test_f5_error_no_match_when_error_code_missing():
    rule = HardRule(
        name="F5 errors route to Finance",
        condition=HardRuleCondition(error_code_prefix="F5"),
        override=HardRuleOverride(module="FI"),
    )
    engine = RuleEngine(_make_config([rule]))
    decision = _make_decision(module="MM")

    result, fired = engine.apply_rules(decision, "chat", None, None)

    assert result.module == "MM"
    assert fired == []


def test_whatsapp_low_confidence_requires_review():
    rule = HardRule(
        name="WhatsApp low-confidence needs review",
        condition=HardRuleCondition(source="whatsapp", confidence_below=0.70),
        override=HardRuleOverride(manual_review_required=True, review_reason="low_confidence_whatsapp"),
    )
    engine = RuleEngine(_make_config([rule]))
    decision = _make_decision(confidence=0.55)

    result, fired = engine.apply_rules(decision, "whatsapp", None, None)

    assert result.manual_review_required is True
    assert result.review_reason == "low_confidence_whatsapp"
    assert "WhatsApp low-confidence needs review" in fired


def test_whatsapp_high_confidence_no_review():
    rule = HardRule(
        name="WhatsApp low-confidence needs review",
        condition=HardRuleCondition(source="whatsapp", confidence_below=0.70),
        override=HardRuleOverride(manual_review_required=True),
    )
    engine = RuleEngine(_make_config([rule]))
    decision = _make_decision(confidence=0.85)

    result, fired = engine.apply_rules(decision, "whatsapp", None, None)

    assert result.manual_review_required is False
    assert fired == []


def test_multiple_rules_all_fire():
    # Both rules evaluate against the ORIGINAL decision (conditions are independent).
    # Rule 1 fires on module=ABAP + environment=PRD.
    # Rule 2 fires on environment=PRD (no module or priority constraint).
    # Last rule wins on conflicting fields.
    rules = [
        HardRule(
            name="ABAP in production is always P1",
            condition=HardRuleCondition(module="ABAP", environment="PRD"),
            override=HardRuleOverride(priority="P1", manual_review_required=True),
        ),
        HardRule(
            name="PRD requires review",
            condition=HardRuleCondition(environment="PRD"),
            override=HardRuleOverride(manual_review_required=True, review_reason="production_critical"),
        ),
    ]
    engine = RuleEngine(_make_config(rules))
    decision = _make_decision(module="ABAP", priority="P3")

    result, fired = engine.apply_rules(decision, "solman", "PRD", None)

    assert result.priority == "P1"
    assert result.manual_review_required is True
    assert result.review_reason == "production_critical"  # last rule wins
    assert len(fired) == 2


def test_last_rule_wins_on_conflicting_fields():
    rules = [
        HardRule(
            name="Rule A",
            condition=HardRuleCondition(module="FI"),
            override=HardRuleOverride(priority="P1"),
        ),
        HardRule(
            name="Rule B",
            condition=HardRuleCondition(module="FI"),
            override=HardRuleOverride(priority="P2"),
        ),
    ]
    engine = RuleEngine(_make_config(rules))
    decision = _make_decision(module="FI", priority="P4")

    result, fired = engine.apply_rules(decision, "chat", None, None)

    assert result.priority == "P2"  # Rule B wins
    assert len(fired) == 2


def test_priority_in_condition():
    rule = HardRule(
        name="PRD critical gets escalation",
        condition=HardRuleCondition(environment="PRD", priority_in=["P1", "P2"]),
        override=HardRuleOverride(manual_review_required=True, review_reason="production_critical"),
    )
    engine = RuleEngine(_make_config([rule]))

    # P1 in PRD — fires
    decision_p1 = _make_decision(priority="P1")
    result, fired = engine.apply_rules(decision_p1, "solman", "PRD", None)
    assert result.manual_review_required is True
    assert "PRD critical gets escalation" in fired

    # P3 in PRD — does not fire
    decision_p3 = _make_decision(priority="P3")
    result2, fired2 = engine.apply_rules(decision_p3, "solman", "PRD", None)
    assert result2.manual_review_required is False
    assert fired2 == []
