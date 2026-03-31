from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TenantMixin

if TYPE_CHECKING:
    from app.models.tenant import Tenant


class ModelVersion(TenantMixin, Base):
    __tablename__ = "model_versions"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(
        String, ForeignKey("tenants.id"), nullable=False, index=True
    )
    model_type: Mapped[str] = mapped_column(String, nullable=False)
    version: Mapped[str] = mapped_column(String, nullable=False)
    training_samples: Mapped[int] = mapped_column(Integer, nullable=False)
    holdout_accuracy: Mapped[float] = mapped_column(Float, nullable=False)
    module_f1_weighted: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    priority_exact_match: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    calibration_error: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    trained_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Relationships
    tenant: Mapped["Tenant"] = relationship(back_populates="model_versions")
