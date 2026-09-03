"""Heartbeat monitor: scans RUNNING workers and flags stale ones as failed.

Simple last-seen timestamp check against a threshold; no distributed
consensus. Runs on a background thread in the scheduler loop.

A worker is considered dead if its heartbeat_time is older than
HEARTBEAT_TIMEOUT_SECONDS (default 30s). The first time a worker is seen
as stale, it is marked FAILED and a Failure row is recorded (deduped by
worker_id so repeated scans don't create duplicate Failure rows).
"""
import logging
import os
import threading
import time
from datetime import datetime, timedelta, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import state_machine as sm
from app.failure_classifier import classify_heartbeat_timeout

logger = logging.getLogger("scheduler.heartbeat")

HEARTBEAT_TIMEOUT_SECONDS = float(os.getenv("HEARTBEAT_TIMEOUT_SECONDS", "30"))
SCAN_INTERVAL_SECONDS = float(os.getenv("HEARTBEAT_SCAN_INTERVAL_SECONDS", "10"))


class HeartbeatMonitor:
    """Background monitor that watches RUNNING workers for missed heartbeats."""

    def __init__(self, database_url: str, on_failure) -> None:
        self.engine = create_engine(database_url, pool_pre_ping=True)
        self.SessionLocal = sessionmaker(bind=self.engine)
        self.on_failure = on_failure
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        """Start the background scan thread."""
        self._thread = threading.Thread(target=self._run, daemon=True, name="heartbeat-monitor")
        self._thread.start()
        logger.info("Heartbeat monitor started (timeout=%ss, scan=%ss)",
                     HEARTBEAT_TIMEOUT_SECONDS, SCAN_INTERVAL_SECONDS)

    def stop(self) -> None:
        """Signal the monitor to stop and wait for the thread to finish."""
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=5)

    def _run(self) -> None:
        while not self._stop_event.is_set():
            try:
                self._scan()
            except Exception:
                logger.exception("Heartbeat scan failed")
            self._stop_event.wait(timeout=SCAN_INTERVAL_SECONDS)

    def _scan(self) -> None:
        """Find RUNNING workers whose heartbeat is stale and report them."""
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=HEARTBEAT_TIMEOUT_SECONDS)
        with self.SessionLocal() as session:
            from app.models import Worker

            stale_workers = (
                session.query(Worker)
                .filter(Worker.status == sm.RUNNING)
                .filter(
                    (Worker.heartbeat_time < cutoff) | (Worker.heartbeat_time.is_(None))
                )
                .all()
            )
            for worker in stale_workers:
                logger.warning("Worker %s heartbeat timed out (last seen: %s)",
                               worker.worker_id, worker.heartbeat_time)
                worker.status = sm.FAILED
                session.commit()
                error_type, message, retryable = classify_heartbeat_timeout()
                self.on_failure(
                    worker_id=worker.worker_id,
                    job_id=worker.job_id,
                    error_type=error_type,
                    message=message,
                    retryable=retryable,
                )
