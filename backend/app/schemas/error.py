"""Standard error response schema."""

from typing import Optional
from pydantic import BaseModel


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    code: str  # machine-readable: "TICKET_NOT_FOUND", "TRIAGE_FAILED", etc.
