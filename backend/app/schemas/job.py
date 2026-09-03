"""Pydantic schemas for jobs."""
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class JobOut(BaseModel):
    job_id: str
    experiment_id: str
    status: str
    worker_count: int
    retry_count: int
    error_message: str | None = None
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
