"""Pydantic schemas for failures."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class FailureCreate(BaseModel):
    error_type: str = Field(min_length=1, max_length=64)
    error_message: str | None = None
    retryable: bool = True
    worker_id: str | None = None
    dedupe_key: str | None = None


class FailureOut(BaseModel):
    failure_id: str
    job_id: str
    worker_id: str | None = None
    error_type: str
    error_message: str | None = None
    retryable: bool
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)
