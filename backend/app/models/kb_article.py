from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, TenantMixin

from pgvector.sqlalchemy import Vector

if TYPE_CHECKING:
    from app.models.tenant import Tenant


class KBArticle(TenantMixin, TimestampMixin, Base):
    __tablename__ = "kb_articles"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(
        String, ForeignKey("tenants.id"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    module: Mapped[str] = mapped_column(String, nullable=False)
    error_codes: Mapped[Optional[list[str]]] = mapped_column(ARRAY(String), nullable=True)
    tcodes: Mapped[Optional[list[str]]] = mapped_column(ARRAY(String), nullable=True)
    tags: Mapped[Optional[list[str]]] = mapped_column(ARRAY(String), nullable=True)
    embedding: Mapped[Optional[Any]] = mapped_column(Vector(1536), nullable=True)
    search_vector: Mapped[Optional[Any]] = mapped_column(TSVECTOR, nullable=True)

    # Relationships
    tenant: Mapped["Tenant"] = relationship(back_populates="kb_articles")

    __table_args__ = (
        Index("ix_kb_articles_search_vector", "search_vector", postgresql_using="gin"),
    )
