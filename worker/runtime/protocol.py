"""Defines how the scheduler communicates with running workers.

Phase 1: Redis keys for progress.
Phase 3: workers also send heartbeats via the backend API
(POST /workers/{id}/heartbeat) on a background thread.
"""
import json
import logging
import threading
import time
from typing import Any

import httpx
from runtime.observability import worker_heartbeat_failures_total, push_metrics

RUNNING: str = "RUNNING"
COMPLETED: str = "COMPLETED"
FAILED: str = "FAILED"

logger = logging.getLogger("worker.protocol")

HEARTBEAT_INTERVAL_SECONDS = float(__import__("os").getenv("HEARTBEAT_INTERVAL_SECONDS", "10"))


def status_key(experiment_id: str) -> str:
    return f"experiment:{experiment_id}:status"


def progress_key(experiment_id: str) -> str:
    return f"experiment:{experiment_id}:progress"


class HeartbeatThread:
    """Background thread that sends periodic heartbeats to the backend.

    The worker reads WORKER_ID and BACKEND_URL from the environment. If
    WORKER_ID is not set (e.g. Phase 1 single-worker mode), heartbeats
    are skipped.
    """

    def __init__(self, worker_id: str | None, backend_url: str) -> None:
        self.worker_id = worker_id
        self.backend_url = backend_url.rstrip("/")
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self.worker_id is None:
            logger.info("No WORKER_ID set, heartbeats disabled")
            return
        self._thread = threading.Thread(target=self._run, daemon=True, name="heartbeat")
        self._thread.start()
        logger.info("Heartbeat thread started for worker %s", self.worker_id)

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=5)

    def _run(self) -> None:
        while not self._stop_event.is_set():
            try:
                self._send()
            except Exception:  # noqa: BLE001
                worker_heartbeat_failures_total.inc()
                push_metrics()
                logger.debug("Heartbeat send failed (will retry)")
            self._stop_event.wait(timeout=HEARTBEAT_INTERVAL_SECONDS)

    def _send(self) -> None:
        with httpx.Client(timeout=5.0) as client:
            resp = client.post(
                f"{self.backend_url}/workers/{self.worker_id}/heartbeat"
            )
            if resp.status_code == 404:
                logger.warning("Worker %s not found by backend, stopping heartbeats", self.worker_id)
                self.stop()
            elif resp.status_code >= 400:
                worker_heartbeat_failures_total.inc()
                push_metrics()
                logger.debug("Heartbeat returned %s", resp.status_code)
            else:
                push_metrics()
