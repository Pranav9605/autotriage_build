"""Ticket Pydantic schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.triage import TriageResponse


class TicketCreate(BaseModel):
    source: str = "chat"
    raw_text: str = Field(min_length=10, max_length=5000)
    reporter: Optional[str] = None


class TicketResponse(BaseModel):
    id: str
    tenant_id: str
    source: str
    description: str
    tcode: Optional[str]
    error_code: Optional[str]
    environment: Optional[str]
    reporter: Optional[str]
    status: str
    created_at: datetime
    triage: Optional[TriageResponse] = None

    model_config = {"from_attributes": True}


class TicketListResponse(BaseModel):
    tickets: list[TicketResponse]
    total: int
    page: int
    page_size: int
