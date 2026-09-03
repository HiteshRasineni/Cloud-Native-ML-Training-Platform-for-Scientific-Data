"""Prometheus metrics for scheduler lifecycle events."""
from prometheus_client import Counter, Gauge, Histogram

scheduler_jobs_queued = Gauge("scheduler_jobs_queued", "Jobs currently waiting in Redis")
scheduler_jobs_running = Gauge("scheduler_jobs_running", "Jobs currently being executed")
scheduler_jobs_completed_total = Counter("scheduler_jobs_completed_total", "Completed jobs")
scheduler_jobs_failed_total = Counter("scheduler_jobs_failed_total", "Failed jobs")
scheduler_job_retries_total = Counter(
    "scheduler_job_retries_total", "Job retries by failure type", ("error_type",)
)
scheduler_job_duration_seconds = Histogram(
    "scheduler_job_duration_seconds", "Time from scheduling to job terminal state"
)