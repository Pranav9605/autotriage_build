"""Rule engine — applies YAML-defined hard rules after AI classification."""

import logging
from typing import Optional

from app.core.tenant_config import TenantConfig
from app.schemas.triage import TriageDecisionSchema

logger = logging.getLogger(__name__)


class RuleEngine:
    def __init__(self, tenant_config: TenantConfig) -> None:
        self.rules = tenant_config.hard_rules

    def apply_rules(
        self,
        decision: TriageDecisionSchema,
        ticket_source: str,
        ticket_environment: Optional[str],
        ticket_error_code: Optional[str],
    ) -> tuple[TriageDecisionSchema, list[str]]:
        """Apply hard rules AFTER AI classification.

        Rules are evaluated in order; ALL matching rules fire (AND logic within
        each condition, independent rules accumulate).  If multiple rules set the
        same field, the last one wins.

        Returns:
            (modified_decision, list_of_rule_names_that_fired)
        """
        fired: list[str] = []
        # Work with a mutable copy of the decision fields
        overrides: dict = {}

        for rule in self.rules:
            if self._evaluate_condition(
                rule.condition.model_dump(exclude_none=True),
                decision,
                ticket_source,
                ticket_environment,
                ticket_error_code,
            ):
                logger.info("Rule fired: %s", rule.name)
                fired.append(rule.name)
                # Accumulate overrides; last rule wins on conflicts
                for field, value in rule.override.model_dump(exclude_none=True).items():
                    overrides[field] = value

        if not overrides:
            return decision, fired

        # Apply accumulated overrides by rebuilding the schema
        updated = decision.model_dump()
        updated.update(overrides)
        return TriageDecisionSchema.model_validate(updated), fired

    def _evaluate_condition(
        self,
        condition: dict,
        decision: TriageDecisionSchema,
        source: str,
        env: Optional[str],
        error_code: Optional[str],
    ) -> bool:
        """Return True only if ALL condition fields match (AND logic)."""
        for key, expected in condition.items():
            if key == "module":
                if decision.module != expected:
                    return False
            elif key == "environment":
                if env != expected:
                    return False
            elif key == "error_code_prefix":
                if not error_code or not error_code.startswith(expected):
                    return False
            elif key == "source":
                if source != expected:
                    return False
            elif key == "confidence_below":
                if decision.confidence >= expected:
                    return False
            elif key == "priority_in":
                if decision.priority not in expected:
                    return False
            else:
                logger.debug("Unknown rule condition key ignored: %s", key)
        return True
