"""Pydantic schemas for workers."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.failure import FailureOut


class WorkerOut(BaseModel):
    worker_id: str
    job_id: str
    status: str
    hostname: str | None = None
    container_id: str | None = None
    started_at: datetime | None = None
    heartbeat_time: datetime | None = None
    created_at: datetime
    failures: list[FailureOut] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class HeartbeatResponse(BaseModel):
    worker_id: str
    status: str
