from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, TenantMixin

try:
    from pgvector.sqlalchemy import Vector
    _vector_type = Vector(1536)
except ImportError:
    _vector_type = None  # type: ignore

if TYPE_CHECKING:
    from app.models.tenant import Tenant
    from app.models.triage_decision import TriageDecision
    from app.models.feedback import Feedback


class Ticket(TenantMixin, TimestampMixin, Base):
    __tablename__ = "tickets"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String, ForeignKey("tenants.id"), nullable=False, index=True)
    source: Mapped[str] = mapped_column(String, nullable=False)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    tcode: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    error_code: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    environment: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    system_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    reporter: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False, default="open")
    embedding: Mapped[Optional[Any]] = mapped_column(Vector(1536), nullable=True)
    search_vector: Mapped[Optional[Any]] = mapped_column(TSVECTOR, nullable=True)
    ground_truth_module: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    ground_truth_priority: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    tenant: Mapped["Tenant"] = relationship(back_populates="tickets")
    triage_decisions: Mapped[list["TriageDecision"]] = relationship(
        back_populates="ticket", order_by="TriageDecision.version"
    )
    feedback: Mapped[list["Feedback"]] = relationship(back_populates="ticket")

    __table_args__ = (
        Index("ix_tickets_tenant_status", "tenant_id", "status"),
        Index("ix_tickets_search_vector", "search_vector", postgresql_using="gin"),
        Index(
            "ix_tickets_error_code",
            "error_code",
            postgresql_where=mapped_column(String, name="error_code").isnot(None),
        ),
        Index(
            "ix_tickets_tcode",
            "tcode",
            postgresql_where=mapped_column(String, name="tcode").isnot(None),
        ),
    )
