"""Failure ORM model. One row per worker/error-type incident.

Idempotency: a unique constraint on (job_id, dedupe_key) prevents the scheduler
recording the same incident twice when failure detection fires repeatedly.
"""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.experiment import Base


class Failure(Base):
    __tablename__ = "failures"
    __table_args__ = (
        UniqueConstraint("job_id", "dedupe_key", name="uq_failure_job_dedupe"),
    )

    failure_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    job_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("jobs.job_id"), nullable=False, index=True
    )
    worker_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("workers.worker_id"), nullable=True, index=True
    )
    error_type: Mapped[str] = mapped_column(String(64), nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    retryable: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    dedupe_key: Mapped[str] = mapped_column(String(128), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
