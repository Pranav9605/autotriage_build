from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TenantMixin

if TYPE_CHECKING:
    from app.models.ticket import Ticket
    from app.models.triage_decision import TriageDecision
    from app.models.tenant import Tenant


class Feedback(TenantMixin, Base):
    __tablename__ = "feedback"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    ticket_id: Mapped[str] = mapped_column(
        String, ForeignKey("tickets.id"), nullable=False, index=True
    )
    triage_decision_id: Mapped[str] = mapped_column(
        String, ForeignKey("triage_decisions.id"), nullable=False, index=True
    )
    tenant_id: Mapped[str] = mapped_column(
        String, ForeignKey("tenants.id"), nullable=False, index=True
    )
    action: Mapped[str] = mapped_column(String, nullable=False)
    overrides: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    override_category: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    consultant_id: Mapped[str] = mapped_column(String, nullable=False)
    decided_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    decision_latency_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    final_module: Mapped[str] = mapped_column(String, nullable=False)
    final_priority: Mapped[str] = mapped_column(String, nullable=False)
    final_assign_to: Mapped[str] = mapped_column(String, nullable=False)
    is_correct_module: Mapped[bool] = mapped_column(Boolean, nullable=False)
    is_correct_priority: Mapped[bool] = mapped_column(Boolean, nullable=False)

    # Relationships
    ticket: Mapped["Ticket"] = relationship(back_populates="feedback")
    triage_decision: Mapped["TriageDecision"] = relationship(back_populates="feedback")
