"""Embedding service — abstract interface + OpenAI implementation."""

import logging
from abc import ABC, abstractmethod

from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

_ZERO_VECTOR = [0.0] * 1536


class EmbeddingService(ABC):
    @abstractmethod
    async def embed_text(self, text: str) -> list[float]: ...

    @abstractmethod
    async def embed_batch(self, texts: list[str]) -> list[list[float]]: ...


class OpenAIEmbeddingService(EmbeddingService):
    def __init__(self, api_key: str, model: str = "text-embedding-3-small") -> None:
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def embed_text(self, text: str) -> list[float]:
        if not text or not text.strip():
            logger.warning("embed_text called with empty string — returning zero vector")
            return _ZERO_VECTOR

        response = await self.client.embeddings.create(input=[text], model=self.model)
        return response.data[0].embedding

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        results: list[list[float]] = []
        chunk_size = 100

        for i in range(0, len(texts), chunk_size):
            chunk = texts[i : i + chunk_size]
            # Replace empty strings with a space to avoid API errors
            sanitized = [t if t and t.strip() else " " for t in chunk]
            response = await self.client.embeddings.create(input=sanitized, model=self.model)
            # Response items are ordered by index
            chunk_embeddings = sorted(response.data, key=lambda x: x.index)
            results.extend(item.embedding for item in chunk_embeddings)

        return results
