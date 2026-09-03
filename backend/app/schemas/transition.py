"""Pydantic schemas for transition history."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TransitionOut(BaseModel):
    id: int
    from_status: str | None = None
    to_status: str
    message: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
