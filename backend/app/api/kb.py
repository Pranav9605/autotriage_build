"""Knowledge Base API — articles CRUD + semantic search."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_embedding_service, get_tenant_id
from app.models.kb_article import KBArticle
from app.schemas.kb import KBArticleCreate, KBArticleResponse, KBSearchResponse
from app.services.embedding import EmbeddingService
from app.utils.id_generator import generate_uuid

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/kb", tags=["knowledge-base"])


@router.get("/search", response_model=KBSearchResponse)
async def search_kb(
    q: str = Query(..., min_length=3),
    tenant_id: str = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
    embedding_service: EmbeddingService = Depends(get_embedding_service),
    limit: int = Query(5, ge=1, le=20),
):
    """Semantic search over KB articles using pgvector cosine similarity."""
    from sqlalchemy import text

    embedding = await embedding_service.embed_text(q)
    vector_literal = "[" + ",".join(str(v) for v in embedding) + "]"

    sql = text("""
        SELECT id, title, content, module, error_codes, tcodes, tags, created_at,
               1 - (embedding <=> :emb ::vector(1536)) AS score
        FROM kb_articles
        WHERE tenant_id = :tenant_id
          AND embedding IS NOT NULL
        ORDER BY embedding <=> :emb ::vector(1536)
        LIMIT :limit
    """)

    result = await db.execute(
        sql,
        {"tenant_id": tenant_id, "emb": vector_literal, "limit": limit},
    )
    rows = result.fetchall()

    articles = [
        KBArticleResponse(
            id=row.id,
            title=row.title,
            content=row.content,
            module=row.module,
            error_codes=row.error_codes or [],
            tcodes=row.tcodes or [],
            tags=row.tags or [],
            created_at=row.created_at,
        )
        for row in rows
    ]
    return KBSearchResponse(results=articles, query=q)


@router.post("/articles", response_model=KBArticleResponse, status_code=201)
async def create_article(
    body: KBArticleCreate,
    tenant_id: str = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
    embedding_service: EmbeddingService = Depends(get_embedding_service),
):
    embedding = await embedding_service.embed_text(f"{body.title}\n{body.content}")
    article = KBArticle(
        id=generate_uuid(),
        tenant_id=tenant_id,
        title=body.title,
        content=body.content,
        module=body.module,
        error_codes=body.error_codes or None,
        tcodes=body.tcodes or None,
        tags=body.tags or None,
        embedding=embedding,
    )
    db.add(article)
    await db.commit()
    await db.refresh(article)
    return _to_response(article)


@router.put("/articles/{article_id}", response_model=KBArticleResponse)
async def update_article(
    article_id: str,
    body: KBArticleCreate,
    tenant_id: str = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
    embedding_service: EmbeddingService = Depends(get_embedding_service),
):
    result = await db.execute(
        select(KBArticle).where(
            KBArticle.id == article_id,
            KBArticle.tenant_id == tenant_id,
        )
    )
    article = result.scalar_one_or_none()
    if article is None:
        raise HTTPException(status_code=404, detail=f"KB article {article_id} not found")

    article.title = body.title
    article.content = body.content
    article.module = body.module
    article.error_codes = body.error_codes or None
    article.tcodes = body.tcodes or None
    article.tags = body.tags or None
    article.embedding = await embedding_service.embed_text(f"{body.title}\n{body.content}")

    await db.commit()
    await db.refresh(article)
    return _to_response(article)


@router.get("/articles", response_model=list[KBArticleResponse])
async def list_articles(
    tenant_id: str = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
    module: str = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    q = (
        select(KBArticle)
        .where(KBArticle.tenant_id == tenant_id)
        .order_by(KBArticle.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    if module:
        q = q.where(KBArticle.module == module)
    result = await db.execute(q)
    return [_to_response(a) for a in result.scalars()]


@router.get("/articles/{article_id}", response_model=KBArticleResponse)
async def get_article(
    article_id: str,
    tenant_id: str = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(KBArticle).where(
            KBArticle.id == article_id,
            KBArticle.tenant_id == tenant_id,
        )
    )
    article = result.scalar_one_or_none()
    if article is None:
        raise HTTPException(status_code=404, detail=f"KB article {article_id} not found")
    return _to_response(article)


def _to_response(a: KBArticle) -> KBArticleResponse:
    return KBArticleResponse(
        id=a.id,
        title=a.title,
        content=a.content,
        module=a.module,
        error_codes=a.error_codes or [],
        tcodes=a.tcodes or [],
        tags=a.tags or [],
        created_at=a.created_at,
    )
