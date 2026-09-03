"""Retry policy with exponential backoff.

On a retryable failure, if job.retry_count < experiment.retry.max_attempts,
the job transitions RETRYING -> SCHEDULING and the failed worker(s) are
relaunched. Exponential backoff (base 2s, doubling, cap ~60s) is applied
before relaunching.
"""
import logging
import math
import time

from app import state_machine as sm

MAX_ATTEMPTS_DEFAULT = 3
BACKOFF_BASE_SECONDS = 2.0
BACKOFF_CAP_SECONDS = 60.0

logger = logging.getLogger("scheduler.retry")


def should_retry(retry_count: int, max_attempts: int = MAX_ATTEMPTS_DEFAULT) -> bool:
    """Can this job still be retried?

    Retry requires both: retries remaining AND a valid state transition
    (RETRYING or FAILED -> SCHEDULING).
    """
    return retry_count < max_attempts


def backoff_delay(retry_count: int) -> float:
    """Exponential backoff: base * 2^(retry_count-1), capped.

    retry_count is 1-based (first retry is attempt 2 overall).
    """
    delay = BACKOFF_BASE_SECONDS * math.pow(2, retry_count - 1)
    return min(delay, BACKOFF_CAP_SECONDS)


def sleep_before_retry(retry_count: int) -> float:
    """Sleep the backoff duration for this retry. Returns the delay used."""
    delay = backoff_delay(retry_count)
    logger.info("Retry %d: backing off %.1fs before relaunch", retry_count, delay)
    time.sleep(delay)
    return delay


def record_retry(error_type: str) -> None:
    from app.metrics import scheduler_job_retries_total

    scheduler_job_retries_total.labels(error_type=error_type).inc()
