"""Scheduler main loop: pull jobs from Redis, launch via executor, track state."""
import json
import logging
import os
import time
import uuid
from time import monotonic
from typing import Any

import redis
import httpx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from prometheus_client import start_http_server

from app import state_machine as sm
from app.retry_policy import record_retry, should_retry, sleep_before_retry
from app.metrics import (
    scheduler_job_duration_seconds,
    scheduler_jobs_completed_total,
    scheduler_jobs_failed_total,
    scheduler_jobs_queued,
    scheduler_jobs_running,
)
from executors.base import Executor
from executors.local.docker_executor import LocalDockerExecutor
from app.heartbeat_monitor import HeartbeatMonitor

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("scheduler")

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://mlplatform:mlplatform@postgres:5432/mlplatform")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
QUEUE = os.getenv("EXPERIMENT_QUEUE", "experiments:queued")
POLL_INTERVAL = float(os.getenv("SCHEDULER_POLL_INTERVAL", "2"))
METRICS_PORT = int(os.getenv("SCHEDULER_METRICS_PORT", "8001"))
EXECUTOR_BACKEND = os.getenv("EXECUTOR_BACKEND", "local").lower()
BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000").rstrip("/")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)


def _transition(session: Any, experiment_id: str, new_status: str, error_message: str | None = None) -> bool:
    from app.models import Experiment, ExperimentTransition

    exp = session.get(Experiment, experiment_id)
    if exp is None:
        logger.warning("Unknown experiment %s", experiment_id)
        return False
    if not sm.can_transition(exp.status, new_status):
        logger.warning("Invalid transition %s -> %s for %s", exp.status, new_status, experiment_id)
        return False
    old_status = exp.status
    exp.status = new_status
    exp.error_message = error_message
    if new_status == sm.QUEUED:
        exp.attempts += 1
    session.add(ExperimentTransition(
        experiment_id=experiment_id,
        from_status=old_status,
        to_status=new_status,
        message=error_message,
    ))
    session.commit()
    logger.info("Experiment %s -> %s", experiment_id, new_status)
    return True


def _register_workers(session: Any, job_id: str, worker_ids: list[str], handle: str | None = None) -> None:
    from app.models import Worker

    containers = json.loads(handle) if handle else {}
    by_worker = {worker_id: container_id for container_id, worker_id in containers.items()}
    now = __import__("datetime").datetime.now(__import__("datetime").timezone.utc)
    for worker_id in worker_ids:
        worker = session.get(Worker, worker_id)
        if worker is None:
            worker = Worker(worker_id=worker_id, job_id=job_id)
            session.add(worker)
        worker.status = sm.RUNNING if handle else "CREATED"
        worker.container_id = by_worker.get(worker_id)
        worker.started_at = now if handle else None
        if handle:
            worker.heartbeat_time = now
    session.commit()


def _record_failure(session: Any, job_id: str, worker_id: str | None, error_type: str,
                    message: str, retryable: bool) -> bool:
    from app.models import Failure

    dedupe_key = f"{worker_id or 'job'}:{error_type}"
    existing = session.query(Failure).filter(
        Failure.job_id == job_id, Failure.dedupe_key == dedupe_key
    ).first()
    if existing:
        return False
    session.add(Failure(
        failure_id=str(uuid.uuid4()), job_id=job_id, worker_id=worker_id,
        error_type=error_type, error_message=message, retryable=retryable,
        dedupe_key=dedupe_key,
    ))
    session.commit()
    return True


def _worker_states(executor: Executor, handle: str) -> dict[str, str]:
    states = getattr(executor, "worker_states", None)
    return states(handle) if states else {}


def process_job(r: redis.Redis, executor: Executor, job: dict[str, Any]) -> None:
    experiment_id = job["experiment_id"]
    job_id = job.get("job_id")
    started = monotonic()
    scheduler_jobs_running.inc()
    with SessionLocal() as session:
        _transition(session, experiment_id, sm.SCHEDULING)
        from app.models import Job
        db_job = session.get(Job, job_id) if job_id else None
        if db_job is None:
            logger.error("Job %s is missing for experiment %s", job_id, experiment_id)
            return
        worker_ids = [str(uuid.uuid4()) for _ in range(db_job.worker_count)]
        _register_workers(session, job_id, worker_ids)
        db_job.status = sm.SCHEDULING
        session.commit()
    launch_spec = dict(job["spec"])
    launch_spec["_worker_ids"] = worker_ids
    try:
        handle = executor.launch(experiment_id, launch_spec)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Failed to launch %s", experiment_id)
        with SessionLocal() as session:
            _record_failure(session, job_id, None, "container_crash", str(exc), True)
            from app.models import Job, Worker
            session.query(Worker).filter(Worker.job_id == job_id, Worker.status == "CREATED").update({"status": sm.FAILED})
            session.query(Job).filter(Job.job_id == job_id).update({"status": sm.FAILED, "error_message": str(exc)})
            _transition(session, experiment_id, sm.FAILED, str(exc))
        scheduler_jobs_running.dec()
        scheduler_jobs_failed_total.inc()
        scheduler_job_duration_seconds.observe(monotonic() - started)
        return

    with SessionLocal() as session:
        _transition(session, experiment_id, sm.RUNNING)
        from app.models import Job, Worker
        session.query(Job).filter(Job.job_id == job_id).update({"status": sm.RUNNING})
        _register_workers(session, job_id, worker_ids, handle)
        session.query(Worker).filter(Worker.job_id == job_id, Worker.worker_id.in_(worker_ids)).update({"status": sm.RUNNING})
        session.commit()
    while True:
        state = executor.poll(handle)
        if state == "RUNNING":
            from app.models import Worker
            with SessionLocal() as session:
                heartbeat_failed = session.query(Worker).filter(
                    Worker.job_id == job_id,
                    Worker.worker_id.in_(worker_ids),
                    Worker.status == sm.FAILED,
                ).count()
            if heartbeat_failed:
                state = "FAILED"
            else:
                time.sleep(POLL_INTERVAL)
                continue
        if state == "COMPLETED":
            executor.cleanup(handle)
            with SessionLocal() as session:
                from app.models import Job, Worker
                session.query(Worker).filter(Worker.job_id == job_id, Worker.worker_id.in_(worker_ids)).update({"status": sm.COMPLETED})
                remaining = session.query(Worker).filter(Worker.job_id == job_id, Worker.status != sm.COMPLETED).count()
                if remaining:
                    session.commit()
                    return
                session.query(Job).filter(Job.job_id == job_id).update({"status": sm.COMPLETED})
                session.commit()
                _transition(session, experiment_id, sm.COMPLETED)
            scheduler_jobs_running.dec()
            scheduler_jobs_completed_total.inc()
            scheduler_job_duration_seconds.observe(monotonic() - started)
            return
        # FAILED: record each failed worker, then retry only those workers.
        from app.models import Experiment

        with SessionLocal() as session:
            exp = session.get(Experiment, experiment_id)
            from app.models import Job, Worker
            db_job = session.get(Job, job_id)
            states = _worker_states(executor, handle)
            registry_failed = {
                worker.worker_id for worker in session.query(Worker).filter(
                    Worker.job_id == job_id,
                    Worker.worker_id.in_(worker_ids),
                    Worker.status == sm.FAILED,
                ).all()
            }
            failed_ids = [worker_id for worker_id in worker_ids
                          if worker_id in registry_failed or states.get(worker_id, "FAILED") == "FAILED"]
            if not failed_ids:
                failed_ids = worker_ids
            for failed_id in failed_ids:
                session.query(Worker).filter(Worker.worker_id == failed_id).update({"status": sm.FAILED})
                _record_failure(session, job_id, failed_id, "container_crash", "worker exited non-zero", True)
            if db_job is None:
                return
            max_attempts = exp.spec.get("retry", {}).get("max_attempts", 3) if exp else 3
            if should_retry(db_job.retry_count, max_attempts):
                db_job.retry_count += 1
                db_job.status = sm.RETRYING
                session.commit()
                _transition(session, experiment_id, sm.RETRYING, "worker failure; retrying")
                record_retry("container_crash")
                retry_number = db_job.retry_count
            else:
                db_job.status = sm.FAILED
                session.commit()
                _transition(session, experiment_id, sm.FAILED, "max attempts reached")
                scheduler_jobs_running.dec()
                scheduler_jobs_failed_total.inc()
                scheduler_job_duration_seconds.observe(monotonic() - started)
                retry_number = None
        if retry_number is not None:
            executor.cleanup(handle)
            sleep_before_retry(retry_number)
            retry_ids = [str(uuid.uuid4()) for _ in failed_ids]
            with SessionLocal() as session:
                _register_workers(session, job_id, retry_ids)
                launch_spec = dict(job["spec"])
                launch_spec["_worker_ids"] = retry_ids
                _transition(session, experiment_id, sm.SCHEDULING)
                session.query(Job).filter(Job.job_id == job_id).update({"status": sm.SCHEDULING})
                session.commit()
            handle = executor.launch(experiment_id, launch_spec)
            worker_ids = retry_ids
            with SessionLocal() as session:
                _register_workers(session, job_id, retry_ids, handle)
                _transition(session, experiment_id, sm.RUNNING)
            continue
        else:
            executor.cleanup(handle)
            with SessionLocal() as session:
                session.query(Worker).filter(Worker.job_id == job_id, Worker.status == sm.RUNNING).update({"status": sm.FAILED})
                session.commit()
        return


def record_monitor_failure(**failure: Any) -> None:
    """Send heartbeat failures through the backend's internal API."""
    try:
        with httpx.Client(timeout=5.0) as client:
            response = client.post(
                f"{BACKEND_URL}/jobs/{failure['job_id']}/failures",
                json={
                    "worker_id": failure.get("worker_id"),
                    "error_type": failure["error_type"],
                    "error_message": failure.get("message"),
                    "retryable": failure.get("retryable", True),
                    "dedupe_key": f"{failure.get('worker_id', 'job')}:{failure['error_type']}",
                },
            )
            response.raise_for_status()
    except Exception:  # noqa: BLE001
        logger.exception("Could not record heartbeat failure for %s", failure.get("worker_id"))



def main() -> None:
    r = redis.Redis.from_url(REDIS_URL, decode_responses=True)
    if EXECUTOR_BACKEND == "kubernetes":
        from executors.kubernetes import KubernetesExecutor

        executor: Executor = KubernetesExecutor()
    elif EXECUTOR_BACKEND == "local":
        executor = LocalDockerExecutor()
    else:
        raise ValueError(f"Unsupported EXECUTOR_BACKEND: {EXECUTOR_BACKEND}")
    start_http_server(METRICS_PORT)
    heartbeat_monitor = HeartbeatMonitor(DATABASE_URL, record_monitor_failure)
    heartbeat_monitor.start()
    logger.info("Scheduler started, consuming from %s", QUEUE)
    try:
        while True:
            item = r.blpop(QUEUE, timeout=5)
            if item is None:
                scheduler_jobs_queued.set(r.llen(QUEUE))
                continue
            scheduler_jobs_queued.set(r.llen(QUEUE))
            job = json.loads(item[1])
            try:
                process_job(r, executor, job)
            except Exception:  # noqa: BLE001
                logger.exception("Unhandled error processing %s", job.get("experiment_id"))
    finally:
        heartbeat_monitor.stop()


if __name__ == "__main__":
    main()
