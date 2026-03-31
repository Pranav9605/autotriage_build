"""Feedback Pydantic schemas."""

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, model_validator


class FeedbackCreate(BaseModel):
    action: Literal["accepted", "overridden"]
    overrides: Optional[dict] = None
    override_category: Optional[Literal[
        "wrong_module", "wrong_priority", "wrong_team",
        "missing_context", "known_issue", "duplicate", "other",
    ]] = None
    comment: Optional[str] = None
    consultant_id: str

    @model_validator(mode="after")
    def validate_override(self) -> "FeedbackCreate":
        if self.action == "overridden":
            if not self.overrides or len(self.overrides) == 0:
                raise ValueError("Override must include at least one changed field")
            if not self.override_category:
                raise ValueError("Override category is required when overriding")
        return self


class FeedbackResponse(BaseModel):
    id: str
    ticket_id: str
    action: str
    overrides: Optional[dict]
    override_category: Optional[str]
    comment: Optional[str]
    consultant_id: str
    decided_at: datetime
    final_module: str
    final_priority: str
    is_correct_module: bool
    is_correct_priority: bool

    model_config = {"from_attributes": True}
