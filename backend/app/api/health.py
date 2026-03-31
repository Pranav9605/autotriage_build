"""Health check endpoint."""

import logging

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_triage_engine

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["health"])


@router.get("/health")
async def health_check(
    db: AsyncSession = Depends(get_db),
):
    components: dict = {}

    # Database
    try:
        await db.execute(text("SELECT 1"))
        components["database"] = "healthy"
    except Exception as exc:
        logger.error("DB health check failed: %s", exc)
        components["database"] = "unhealthy"

    # LLM engine (just verify client initialized)
    try:
        engine = get_triage_engine()
        components["llm"] = "healthy" if engine else "unhealthy"
    except Exception as exc:
        logger.error("LLM health check failed: %s", exc)
        components["llm"] = "unhealthy"

    # Embedding service
    try:
        from app.dependencies import get_embedding_service
        emb = get_embedding_service()
        components["embedding"] = "healthy" if emb else "unhealthy"
    except Exception as exc:
        logger.error("Embedding health check failed: %s", exc)
        components["embedding"] = "unhealthy"

    components["local_model"] = "disabled"

    unhealthy = [k for k, v in components.items() if v == "unhealthy"]
    if unhealthy:
        overall = "unhealthy" if "database" in unhealthy else "degraded"
    else:
        overall = "healthy"

    return {"status": overall, "components": components}
