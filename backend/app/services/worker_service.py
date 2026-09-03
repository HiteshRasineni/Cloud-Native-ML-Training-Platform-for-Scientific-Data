"""Worker business logic: registration, lookups, heartbeat, status updates."""
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.worker import Worker, WorkerStatus


def register_worker(db: Session, worker_id: str, job_id: str, container_id: str | None = None) -> Worker:
    worker = Worker(
        worker_id=worker_id,
        job_id=job_id,
        status=WorkerStatus.SCHEDULING,
        container_id=container_id,
    )
    db.add(worker)
    db.commit()
    db.refresh(worker)
    return worker


def list_workers(db: Session) -> list[Worker]:
    return db.query(Worker).order_by(Worker.created_at.desc()).all()


def get_worker(db: Session, worker_id: str) -> Worker | None:
    return db.get(Worker, worker_id)


def list_workers_for_job(db: Session, job_id: str) -> list[Worker]:
    return db.query(Worker).filter(Worker.job_id == job_id).order_by(Worker.created_at).all()


def mark_started(db: Session, worker_id: str, hostname: str | None = None) -> Worker | None:
    worker = get_worker(db, worker_id)
    if worker is None:
        return None
    worker.status = WorkerStatus.RUNNING
    worker.started_at = datetime.now(timezone.utc)
    if hostname:
        worker.hostname = hostname
    db.commit()
    db.refresh(worker)
    return worker


def heartbeat(db: Session, worker_id: str) -> Worker | None:
    worker = get_worker(db, worker_id)
    if worker is None:
        return None
    worker.heartbeat_time = datetime.now(timezone.utc)
    if worker.status == WorkerStatus.SCHEDULING:
        worker.status = WorkerStatus.RUNNING
    db.commit()
    db.refresh(worker)
    return worker


def set_status(db: Session, worker_id: str, status: str) -> Worker | None:
    worker = get_worker(db, worker_id)
    if worker is None:
        return None
    worker.status = status
    db.commit()
    db.refresh(worker)
    return worker
