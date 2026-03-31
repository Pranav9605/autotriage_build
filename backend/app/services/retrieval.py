"""Retrieval service — hybrid search using the PostgreSQL hybrid_search function."""

import logging
from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import RetrievalError
from app.schemas.triage import RetrievalResult
from app.services.embedding import EmbeddingService

logger = logging.getLogger(__name__)


class RetrievalService:
    def __init__(self, db: AsyncSession, embedding_service: EmbeddingService) -> None:
        self.db = db
        self.embedding_service = embedding_service

    async def search_similar(
        self,
        tenant_id: str,
        query_text: str,
        error_code: Optional[str] = None,
        tcode: Optional[str] = None,
        environment: Optional[str] = None,
        min_score: float = 0.78,
        limit: int = 3,
    ) -> list[RetrievalResult]:
        """Execute hybrid search and return ranked results above min_score.

        Returns an empty list (not an error) when nothing meets the threshold.
        """
        try:
            embedding = await self.embedding_service.embed_text(query_text)
        except Exception as exc:
            logger.error("Embedding failed during retrieval: %s", exc)
            raise RetrievalError(f"Embedding failed: {exc}") from exc

        # Format the vector as a PostgreSQL literal string '[0.1, 0.2, ...]'
        vector_literal = "[" + ",".join(str(v) for v in embedding) + "]"

        sql = text("""
            SELECT
                result_id,
                result_type,
                title,
                content,
                final_score,
                semantic_score,
                lexical_score,
                exact_boost
            FROM hybrid_search(
                :tenant_id,
                :embedding ::vector(1536),
                :query_text,
                :error_code,
                :tcode,
                :environment,
                :min_score,
                :limit
            )
        """)

        try:
            result = await self.db.execute(
                sql,
                {
                    "tenant_id": tenant_id,
                    "embedding": vector_literal,
                    "query_text": query_text,
                    "error_code": error_code,
                    "tcode": tcode,
                    "environment": environment,
                    "min_score": min_score,
                    "limit": limit,
                },
            )
            rows = result.fetchall()
        except Exception as exc:
            logger.error("hybrid_search SQL failed: %s", exc)
            raise RetrievalError(f"Hybrid search query failed: {exc}") from exc

        results = [
            RetrievalResult(
                result_id=row.result_id,
                result_type=row.result_type,
                title=row.title,
                content=row.content,
                final_score=float(row.final_score),
                semantic_score=float(row.semantic_score),
                lexical_score=float(row.lexical_score),
                exact_boost=float(row.exact_boost),
            )
            for row in rows
        ]

        logger.debug(
            "hybrid_search returned %d results for tenant=%s", len(results), tenant_id
        )
        return results
