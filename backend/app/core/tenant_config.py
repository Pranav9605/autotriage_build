"""Tenant configuration loader — reads YAML config files and caches them."""

import logging
from functools import lru_cache
from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Pydantic models mirroring config/patil_group.yaml
# ---------------------------------------------------------------------------

class HardRuleCondition(BaseModel):
    module: Optional[str] = None
    environment: Optional[str] = None
    error_code_prefix: Optional[str] = None
    source: Optional[str] = None
    confidence_below: Optional[float] = None
    priority_in: Optional[list[str]] = None


class HardRuleOverride(BaseModel):
    priority: Optional[str] = None
    module: Optional[str] = None
    assign_to: Optional[str] = None
    manual_review_required: Optional[bool] = None
    review_reason: Optional[str] = None


class HardRule(BaseModel):
    name: str
    condition: HardRuleCondition
    override: HardRuleOverride


class EscalationConfig(BaseModel):
    p1_sla_minutes: int = 30
    p2_sla_minutes: int = 240
    p3_sla_minutes: int = 1440
    p4_sla_minutes: int = 4320
    p1_outside_hours: str = "page_oncall"
    sla_breach_action: str = "escalate_to_manager"


class AIConfig(BaseModel):
    confidence_threshold: float = 0.80
    local_model_enabled: bool = False
    local_model_threshold: float = 0.90
    llm_provider: str = "anthropic"
    llm_model: str = "claude-sonnet-4-20250514"
    embedding_model: str = "text-embedding-3-small"
    max_similar_tickets: int = 3
    max_kb_articles: int = 3
    similarity_min_score: float = 0.78


class TenantConfig(BaseModel):
    tenant_id: str
    display_name: str
    modules_active: list[str]
    teams: dict[str, str]
    hard_rules: list[HardRule] = []
    escalation: EscalationConfig = EscalationConfig()
    ai_config: AIConfig = AIConfig()


# ---------------------------------------------------------------------------
# Loader
# ---------------------------------------------------------------------------

_CONFIG_DIR = Path(__file__).parent.parent.parent / "config"


@lru_cache(maxsize=32)
def load_tenant_config(tenant_id: str) -> TenantConfig:
    """Load and cache tenant config from config/{tenant_id}.yaml."""
    config_path = _CONFIG_DIR / f"{tenant_id}.yaml"
    if not config_path.exists():
        from app.core.exceptions import TenantNotFoundError
        raise TenantNotFoundError(tenant_id)

    with open(config_path) as f:
        raw = yaml.safe_load(f)

    config = TenantConfig.model_validate(raw)
    logger.info("Loaded tenant config: %s", tenant_id)
    return config


def get_team_for_module(config: TenantConfig, module: str) -> str:
    """Return the team responsible for a given SAP module, falling back to DEFAULT."""
    return config.teams.get(module, config.teams.get("DEFAULT", "General SAP Support"))
