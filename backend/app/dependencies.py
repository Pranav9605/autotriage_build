"""FastAPI dependency injection — singletons and per-request dependencies."""

from functools import lru_cache
from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.tenant_config import TenantConfig, load_tenant_config
from app.database import get_db
from app.services.embedding import EmbeddingService, OpenAIEmbeddingService
from app.services.intake import IntakeService
from app.services.retrieval import RetrievalService
from app.services.rule_engine import RuleEngine
from app.services.triage_engine import ClaudeTriageEngine, TriageEngine

__all__ = ["get_db"]


# ---------------------------------------------------------------------------
# Singletons (created once per process)
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def _embedding_service_singleton() -> EmbeddingService:
    settings = get_settings()
    return OpenAIEmbeddingService(api_key=settings.OPENAI_API_KEY)


@lru_cache(maxsize=1)
def _triage_engine_singleton() -> TriageEngine:
    settings = get_settings()
    return ClaudeTriageEngine(api_key=settings.ANTHROPIC_API_KEY)


# ---------------------------------------------------------------------------
# Per-request dependencies
# ---------------------------------------------------------------------------

def get_tenant_id(request: Request) -> str:
    """Extract tenant_id from request state (set by TenantMiddleware)."""
    return getattr(request.state, "tenant_id", get_settings().DEFAULT_TENANT_ID)


def get_tenant_config(tenant_id: str = Depends(get_tenant_id)) -> TenantConfig:
    return load_tenant_config(tenant_id)


def get_embedding_service() -> EmbeddingService:
    return _embedding_service_singleton()


def get_triage_engine() -> TriageEngine:
    return _triage_engine_singleton()


def get_retrieval_service(
    db: AsyncSession = Depends(get_db),
    embedding_service: EmbeddingService = Depends(get_embedding_service),
) -> RetrievalService:
    return RetrievalService(db=db, embedding_service=embedding_service)


def get_rule_engine(
    tenant_config: TenantConfig = Depends(get_tenant_config),
) -> RuleEngine:
    return RuleEngine(tenant_config=tenant_config)


def get_intake_service(
    db: AsyncSession = Depends(get_db),
    embedding_service: EmbeddingService = Depends(get_embedding_service),
    retrieval_service: RetrievalService = Depends(get_retrieval_service),
    triage_engine: TriageEngine = Depends(get_triage_engine),
) -> IntakeService:
    return IntakeService(
        db=db,
        embedding_service=embedding_service,
        retrieval_service=retrieval_service,
        triage_engine=triage_engine,
        rule_engine_factory=RuleEngine,
    )
