"""Tests for the RetrievalService.

These tests mock the embedding service and the database so they run without
a live PostgreSQL instance.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.schemas.triage import RetrievalResult
from app.services.embedding import EmbeddingService
from app.services.retrieval import RetrievalService


_FIXED_VECTOR = [0.1] * 1536


class MockEmbeddingService(EmbeddingService):
    async def embed_text(self, text: str) -> list[float]:
        return _FIXED_VECTOR

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [_FIXED_VECTOR for _ in texts]


def _make_mock_row(
    result_id="INC-2026-abc123",
    result_type="ticket",
    title="INC-2026-abc123",
    content="FB50 posting error",
    final_score=0.85,
    semantic_score=0.82,
    lexical_score=0.70,
    exact_boost=0.3,
):
    row = MagicMock()
    row.result_id = result_id
    row.result_type = result_type
    row.title = title
    row.content = content
    row.final_score = final_score
    row.semantic_score = semantic_score
    row.lexical_score = lexical_score
    row.exact_boost = exact_boost
    return row


@pytest.fixture
def mock_db():
    db = AsyncMock()
    return db


@pytest.fixture
def embedding_service():
    return MockEmbeddingService()


@pytest.fixture
def retrieval_service(mock_db, embedding_service):
    return RetrievalService(db=mock_db, embedding_service=embedding_service)


@pytest.mark.asyncio
async def test_search_returns_results(retrieval_service, mock_db):
    rows = [_make_mock_row()]
    mock_result = MagicMock()
    mock_result.fetchall.return_value = rows
    mock_db.execute.return_value = mock_result

    results = await retrieval_service.search_similar(
        tenant_id="patil_group",
        query_text="FB50 posting error",
        error_code="F5 301",
    )

    assert len(results) == 1
    assert isinstance(results[0], RetrievalResult)
    assert results[0].result_id == "INC-2026-abc123"
    assert results[0].final_score == 0.85


@pytest.mark.asyncio
async def test_search_empty_results(retrieval_service, mock_db):
    """When the function returns no rows, we get an empty list — not an error."""
    mock_result = MagicMock()
    mock_result.fetchall.return_value = []
    mock_db.execute.return_value = mock_result

    results = await retrieval_service.search_similar(
        tenant_id="patil_group",
        query_text="completely unrelated text",
        min_score=0.99,
    )

    assert results == []


@pytest.mark.asyncio
async def test_search_tenant_isolation(retrieval_service, mock_db):
    """tenant_id must be passed through to the SQL query."""
    mock_result = MagicMock()
    mock_result.fetchall.return_value = []
    mock_db.execute.return_value = mock_result

    await retrieval_service.search_similar(
        tenant_id="other_tenant",
        query_text="some query",
    )

    call_kwargs = mock_db.execute.call_args
    params = call_kwargs[0][1]
    assert params["tenant_id"] == "other_tenant"


@pytest.mark.asyncio
async def test_search_passes_error_code(retrieval_service, mock_db):
    """error_code and tcode must be forwarded to the SQL function."""
    mock_result = MagicMock()
    mock_result.fetchall.return_value = []
    mock_db.execute.return_value = mock_result

    await retrieval_service.search_similar(
        tenant_id="patil_group",
        query_text="F5 301 error",
        error_code="F5 301",
        tcode="FB50",
    )

    params = mock_db.execute.call_args[0][1]
    assert params["error_code"] == "F5 301"
    assert params["tcode"] == "FB50"


@pytest.mark.asyncio
async def test_search_raises_retrieval_error_on_db_failure(retrieval_service, mock_db):
    """DB errors are wrapped in RetrievalError."""
    from app.core.exceptions import RetrievalError

    mock_db.execute.side_effect = Exception("connection lost")

    with pytest.raises(RetrievalError):
        await retrieval_service.search_similar(
            tenant_id="patil_group",
            query_text="some query",
        )


@pytest.mark.asyncio
async def test_search_multiple_results_ordered(retrieval_service, mock_db):
    """Multiple rows are returned in the order given by the DB."""
    rows = [
        _make_mock_row(result_id="T1", final_score=0.92),
        _make_mock_row(result_id="T2", result_type="kb_article", final_score=0.85),
        _make_mock_row(result_id="T3", final_score=0.80),
    ]
    mock_result = MagicMock()
    mock_result.fetchall.return_value = rows
    mock_db.execute.return_value = mock_result

    results = await retrieval_service.search_similar(
        tenant_id="patil_group",
        query_text="test",
    )

    assert len(results) == 3
    assert results[0].result_id == "T1"
    assert results[1].result_type == "kb_article"
    assert results[2].final_score == 0.80
