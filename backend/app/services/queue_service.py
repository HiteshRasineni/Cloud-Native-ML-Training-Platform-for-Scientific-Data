"""Redis queue operations for experiment jobs."""
import json
from typing import Any

import redis

from app.core.config import get_settings


def get_redis() -> redis.Redis:
    return redis.Redis.from_url(get_settings().redis_url, decode_responses=True)


def enqueue_experiment(experiment_id: str, job_id: str, spec: dict[str, Any]) -> None:
    r = get_redis()
    payload = {"experiment_id": experiment_id, "job_id": job_id, "spec": spec}
    r.rpush(get_settings().experiment_queue, json.dumps(payload))


def pop_experiment(block: bool = True, timeout: int = 5) -> dict[str, Any] | None:
    """Pop the next queued job (used by the scheduler consumer)."""
    r = get_redis()
    item = r.blpop(get_settings().experiment_queue, timeout=timeout if block else 0)
    if item is None:
        return None
    return json.loads(item[1])


def set_worker_status(experiment_id: str, status: str, message: str = "") -> None:
    r = get_redis()
    r.hset(f"experiment:{experiment_id}:status", mapping={"status": status, "message": message})


def get_worker_status(experiment_id: str) -> dict[str, str]:
    r = get_redis()
    return {k: v for k, v in r.hgetall(f"experiment:{experiment_id}:status").items()}
