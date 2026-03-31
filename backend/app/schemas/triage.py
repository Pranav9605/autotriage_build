"""Triage-related Pydantic schemas."""

from typing import Literal, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Retrieval (Phase 2)
# ---------------------------------------------------------------------------

class RetrievalResult(BaseModel):
    result_id: str
    result_type: str  # "ticket" or "kb_article"
    title: str
    content: str
    final_score: float
    semantic_score: float
    lexical_score: float
    exact_boost: float


# ---------------------------------------------------------------------------
# Triage Engine I/O (Phase 3)
# ---------------------------------------------------------------------------

class TriageRequest(BaseModel):
    """Input to the triage engine."""
    ticket_id: str
    tenant_id: str
    description: str
    tcode: Optional[str] = None
    error_code: Optional[str] = None
    environment: Optional[str] = None
    source: str
    similar_tickets: list[RetrievalResult] = []
    kb_articles: list[RetrievalResult] = []
    tenant_config: dict  # serialized TenantConfig


class TriageDecisionSchema(BaseModel):
    """Structured output the LLM must return (validated by Pydantic)."""
    module: Literal["FI", "MM", "SD", "PP", "BASIS", "ABAP", "PI_PO", "HR", "CUSTOM"]
    priority: Literal["P1", "P2", "P3", "P4"]
    issue_type: Literal[
        "Technical Issue",
        "Configuration",
        "Performance",
        "Integration",
        "User Access",
        "Development",
    ]
    root_cause_hypothesis: str
    recommended_solution: str
    assign_to: str
    confidence: float = Field(ge=0.0, le=1.0)
    manual_review_required: bool
    review_reason: Optional[str] = None
    similar_ticket_ids: list[str] = []


class TriageResponse(BaseModel):
    """Full response returned to the API caller after triage."""
    decision_id: str
    ticket_id: str
    module: str
    priority: str
    issue_type: str
    root_cause_hypothesis: str
    recommended_solution: str
    assign_to: str
    confidence: float
    confidence_calibrated: Optional[float]
    classification_source: str
    model_version: str
    rules_applied: list[str]
    similar_ticket_ids: list[str]
    similar_ticket_scores: list[float]
    kb_article_ids: list[str]
    manual_review_required: bool
    review_reason: Optional[str]
    latency_ms: int
