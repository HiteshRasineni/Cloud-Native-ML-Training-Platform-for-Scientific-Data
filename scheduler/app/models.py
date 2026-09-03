"""Scheduler-side ORM mirrors of the backend tables (read/update only)."""
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase

from app import state_machine as sm


class Base(DeclarativeBase):
    pass


class Experiment(Base):
    __tablename__ = "experiments"

    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    status = Column(String(32), default=sm.QUEUED, nullable=False)
    spec = Column(JSONB, nullable=False)
    attempts = Column(Integer, default=0, nullable=False)
    error_message = Column(Text, nullable=True)
    checkpointing_enabled = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class Job(Base):
    __tablename__ = "jobs"

    job_id = Column(String(36), primary_key=True)
    experiment_id = Column(String(36), ForeignKey("experiments.id"), nullable=False, index=True)
    status = Column(String(32), default="CREATED", nullable=False)
    worker_count = Column(Integer, default=1, nullable=False)
    retry_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)


class Worker(Base):
    __tablename__ = "workers"

    worker_id = Column(String(36), primary_key=True)
    job_id = Column(String(36), ForeignKey("jobs.job_id"), nullable=False, index=True)
    status = Column(String(32), default="CREATED", nullable=False)
    hostname = Column(String(255), nullable=True)
    container_id = Column(String(128), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    heartbeat_time = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class Failure(Base):
    __tablename__ = "failures"
    __table_args__ = (UniqueConstraint("job_id", "dedupe_key", name="uq_failure_job_dedupe"),)

    failure_id = Column(String(36), primary_key=True)
    job_id = Column(String(36), ForeignKey("jobs.job_id"), nullable=False, index=True)
    worker_id = Column(String(36), ForeignKey("workers.worker_id"), nullable=True, index=True)
    error_type = Column(String(64), nullable=False)
    error_message = Column(Text, nullable=True)
    retryable = Column(Boolean, default=True, nullable=False)
    dedupe_key = Column(String(128), nullable=False)
    timestamp = Column(DateTime(timezone=True), default=datetime.utcnow)


class ExperimentTransition(Base):
    __tablename__ = "experiment_transitions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    experiment_id = Column(String(36), ForeignKey("experiments.id"), nullable=False, index=True)
    from_status = Column(String(32), nullable=True)
    to_status = Column(String(32), nullable=False)
    message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
