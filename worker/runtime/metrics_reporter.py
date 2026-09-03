"""Reports progress to Redis keys so the platform can inspect running jobs."""
import json
import os
from typing import Any

import redis


class MetricsReporter:
    def __init__(self, experiment_id: str) -> None:
        self.experiment_id = experiment_id
        self.redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
        self._client: redis.Redis | None = None

    @property
    def client(self) -> redis.Redis:
        if self._client is None:
            self._client = redis.Redis.from_url(self.redis_url, decode_responses=True)
        return self._client

    def report_progress(self, epoch: int, metrics: dict[str, float]) -> None:
        try:
            self.client.hset(
                f"experiment:{self.experiment_id}:progress",
                mapping={"epoch": str(epoch), "metrics": json.dumps(metrics)},
            )
        except Exception:  # noqa: BLE001
            pass  # metrics reporting is best-effort in Phase 1

    def report_completion(self) -> None:
        try:
            self.client.hset(
                f"experiment:{self.experiment_id}:status",
                mapping={"status": "COMPLETED", "message": "workload finished"},
            )
        except Exception:  # noqa: BLE001
            pass
