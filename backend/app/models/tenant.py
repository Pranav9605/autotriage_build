from typing import TYPE_CHECKING

from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.ticket import Ticket
    from app.models.kb_article import KBArticle
    from app.models.model_version import ModelVersion
    from app.models.eval_golden_set import EvalGoldenSet


class Tenant(TimestampMixin, Base):
    __tablename__ = "tenants"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    config: Mapped[dict] = mapped_column(JSON, nullable=False)

    tickets: Mapped[list["Ticket"]] = relationship(back_populates="tenant")
    kb_articles: Mapped[list["KBArticle"]] = relationship(back_populates="tenant")
    model_versions: Mapped[list["ModelVersion"]] = relationship(back_populates="tenant")
    eval_golden_sets: Mapped[list["EvalGoldenSet"]] = relationship(back_populates="tenant")
