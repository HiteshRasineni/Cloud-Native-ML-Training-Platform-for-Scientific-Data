"""Job business logic: creation, lookups, status, retry_count."""
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.job import Job


def create_job_for_experiment(db: Session, experiment: object, worker_count: int) -> Job:
    """Create the (single) Job row backing an experiment run."""
    job = Job(experiment_id=experiment.id, worker_count=worker_count, status="CREATED")
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def get_job(db: Session, job_id: str) -> Job | None:
    return db.get(Job, job_id)


def get_job_for_experiment(db: Session, experiment_id: str) -> Job | None:
    return db.query(Job).filter(Job.experiment_id == experiment_id).first()


def set_status(db: Session, job_id: str, status: str, error_message: str | None = None) -> Job | None:
    job = get_job(db, job_id)
    if job is None:
        return None
    job.status = status
    job.error_message = error_message
    now = datetime.now(timezone.utc)
    if status == "SCHEDULING" and job.started_at is None:
        job.started_at = now
    if status in ("COMPLETED", "FAILED"):
        job.completed_at = now
    db.commit()
    db.refresh(job)
    return job


def increment_retry(db: Session, job_id: str) -> Job | None:
    job = get_job(db, job_id)
    if job is None:
        return None
    job.retry_count += 1
    db.commit()
    db.refresh(job)
    return job
