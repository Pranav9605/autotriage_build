"""Dashboard Pydantic schemas."""

from typing import Optional

from pydantic import BaseModel


class DashboardKPIs(BaseModel):
    total_tickets: int
    triaged_tickets: int
    accuracy_rate: float        # accepted / (accepted + overridden)
    override_rate: float        # overridden / total_feedback
    avg_confidence: float
    avg_latency_ms: float
    manual_review_count: int
    mttr_hours: Optional[float]  # mean time to resolution


class ModuleAccuracy(BaseModel):
    module: str
    total: int
    correct: int
    accuracy: float
    override_count: int
    most_common_override_category: Optional[str]


class ConfidenceBucket(BaseModel):
    bucket: str           # e.g. "0.5-0.6"
    count: int
    actual_accuracy: float
