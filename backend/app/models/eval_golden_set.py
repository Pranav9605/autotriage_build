from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TenantMixin

if TYPE_CHECKING:
    from app.models.tenant import Tenant


class EvalGoldenSet(TenantMixin, Base):
    __tablename__ = "eval_golden_set"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(
        String, ForeignKey("tenants.id"), nullable=False, index=True
    )
    ticket_text: Mapped[str] = mapped_column(Text, nullable=False)
    structured_fields: Mapped[dict] = mapped_column(JSON, nullable=False)
    true_module: Mapped[str] = mapped_column(String, nullable=False)
    true_priority: Mapped[str] = mapped_column(String, nullable=False)
    source: Mapped[str] = mapped_column(String, nullable=False)
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Relationships
    tenant: Mapped["Tenant"] = relationship(back_populates="eval_golden_sets")
