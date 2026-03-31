from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, TenantMixin

if TYPE_CHECKING:
    from app.models.ticket import Ticket
    from app.models.tenant import Tenant
    from app.models.feedback import Feedback


class TriageDecision(TenantMixin, Base):
    __tablename__ = "triage_decisions"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    ticket_id: Mapped[str] = mapped_column(
        String, ForeignKey("tickets.id"), nullable=False, index=True
    )
    tenant_id: Mapped[str] = mapped_column(
        String, ForeignKey("tenants.id"), nullable=False, index=True
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    module: Mapped[str] = mapped_column(String, nullable=False)
    priority: Mapped[str] = mapped_column(String, nullable=False)
    issue_type: Mapped[str] = mapped_column(String, nullable=False)
    root_cause_hypothesis: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    recommended_solution: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    assign_to: Mapped[str] = mapped_column(String, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    confidence_calibrated: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    classification_source: Mapped[str] = mapped_column(String, nullable=False)
    model_version: Mapped[str] = mapped_column(String, nullable=False)
    rules_applied: Mapped[Optional[list[str]]] = mapped_column(ARRAY(String), nullable=True)
    similar_ticket_ids: Mapped[Optional[list[str]]] = mapped_column(ARRAY(String), nullable=True)
    similar_ticket_scores: Mapped[Optional[list[float]]] = mapped_column(ARRAY(Float), nullable=True)
    kb_article_ids: Mapped[Optional[list[str]]] = mapped_column(ARRAY(String), nullable=True)
    manual_review_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    review_reason: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    llm_tokens_used: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        __import__("sqlalchemy").DateTime(timezone=True),
        server_default=__import__("sqlalchemy").func.now(),
        nullable=False,
    )

    # Relationships
    ticket: Mapped["Ticket"] = relationship(back_populates="triage_decisions")
    feedback: Mapped[list["Feedback"]] = relationship(back_populates="triage_decision")

    __table_args__ = (UniqueConstraint("ticket_id", "version", name="uq_triage_ticket_version"),)
