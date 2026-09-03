"""Failure business logic, with idempotent recording.

A Failure is keyed idempotently by (job_id, dedupe_key). The scheduler builds
dedupe_key as '{worker_id}:{error_type}' (worker_id is unique per launch
attempt), so the same incident can only be recorded once even if failure
detection (container poll + heartbeat monitor) fires multiple times.
"""
from typing import Any

from sqlalchemy.orm import Session

from app.models.failure import Failure


def _dedupe_key(worker_id: str | None, error_type: str) -> str:
    return f"{worker_id or 'job'}:{error_type}"


def record_failure(db: Session, job_id: str, error_type: str, *, error_message: str | None = None,
                   retryable: bool = True, worker_id: str | None = None, dedupe_key: str | None = None) -> Failure:
    """Record a failure idempotently. Returns the existing row if already present."""
    key = dedupe_key or _dedupe_key(worker_id, error_type)
    existing = (
        db.query(Failure)
        .filter(Failure.job_id == job_id, Failure.dedupe_key == key)
        .first()
    )
    if existing is not None:
        return existing
    failure = Failure(
        job_id=job_id,
        worker_id=worker_id,
        error_type=error_type,
        error_message=error_message,
        retryable=retryable,
        dedupe_key=key,
    )
    db.add(failure)
    db.commit()
    db.refresh(failure)
    return failure


def list_for_job(db: Session, job_id: str) -> list[Failure]:
    return db.query(Failure).filter(Failure.job_id == job_id).order_by(Failure.timestamp).all()


def list_for_worker(db: Session, worker_id: str) -> list[Failure]:
    return db.query(Failure).filter(Failure.worker_id == worker_id).order_by(Failure.timestamp).all()


def list_for_experiment(db: Session, experiment_id: str) -> list[Failure]:
    from app.models.job import Job

    job = db.query(Job).filter(Job.experiment_id == experiment_id).first()
    if job is None:
        return []
    return list_for_job(db, job.job_id)
