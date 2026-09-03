"""Experiment ORM model."""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class ExperimentStatus:
    CREATED = "CREATED"
    VALIDATING = "VALIDATING"
    VALIDATED = "VALIDATED"
    QUEUED = "QUEUED"
    SCHEDULING = "SCHEDULING"
    RUNNING = "RUNNING"
    CHECKPOINTING = "CHECKPOINTING"
    RETRYING = "RETRYING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


# Formalized lifecycle (see docs/experiment-lifecycle.md):
#   CREATED -> VALIDATING -> VALIDATED -> QUEUED -> SCHEDULING -> RUNNING
#     -> (CHECKPOINTING) -> COMPLETED
#   RUNNING/SCHEDULING -> FAILED; FAILED/RETRYING <-> (re)QUEUED/SCHEDULING.
VALID_TRANSITIONS: dict[str, set[str]] = {
    ExperimentStatus.CREATED: {ExperimentStatus.VALIDATING, ExperimentStatus.FAILED},
    ExperimentStatus.VALIDATING: {ExperimentStatus.VALIDATED, ExperimentStatus.FAILED},
    ExperimentStatus.VALIDATED: {ExperimentStatus.QUEUED, ExperimentStatus.FAILED},
    ExperimentStatus.QUEUED: {ExperimentStatus.SCHEDULING, ExperimentStatus.FAILED},
    ExperimentStatus.SCHEDULING: {ExperimentStatus.RUNNING, ExperimentStatus.FAILED},
    ExperimentStatus.RUNNING: {
        ExperimentStatus.COMPLETED,
        ExperimentStatus.FAILED,
        ExperimentStatus.CHECKPOINTING,
        ExperimentStatus.RETRYING,  # a worker failed mid-run -> retry
    },
    ExperimentStatus.CHECKPOINTING: {ExperimentStatus.RUNNING, ExperimentStatus.FAILED},
    ExperimentStatus.RETRYING: {
        ExperimentStatus.SCHEDULING,  # relaunch the failed worker(s)
        ExperimentStatus.FAILED,  # retries exhausted
    },
    ExperimentStatus.COMPLETED: set(),
    ExperimentStatus.FAILED: {ExperimentStatus.RETRYING},  # recorded failure that can retry
}


class Experiment(Base):
    __tablename__ = "experiments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), default=ExperimentStatus.QUEUED, nullable=False)
    spec: Mapped[dict] = mapped_column(JSONB, nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    checkpointing_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
