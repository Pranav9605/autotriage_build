"""Knowledge Base Pydantic schemas."""

from datetime import datetime

from pydantic import BaseModel


class KBArticleCreate(BaseModel):
    title: str
    content: str
    module: str
    error_codes: list[str] = []
    tcodes: list[str] = []
    tags: list[str] = []


class KBArticleResponse(BaseModel):
    id: str
    title: str
    content: str
    module: str
    error_codes: list[str]
    tcodes: list[str]
    tags: list[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class KBSearchResponse(BaseModel):
    results: list[KBArticleResponse]
    query: str
