"""Prometheus metrics for short-lived workers, pushed before exit."""
import os
from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram, push_to_gateway

registry = CollectorRegistry()
worker_active = Gauge("worker_active", "Whether this worker is currently active", registry=registry)
worker_failures_total = Counter("worker_failures_total", "Worker failures", ("error_type",), registry=registry)
worker_heartbeat_failures_total = Counter("worker_heartbeat_failures_total", "Failed heartbeat sends", registry=registry)
worker_training_epoch_duration_seconds = Histogram(
    "worker_training_epoch_duration_seconds", "Training epoch duration", registry=registry
)


def push_metrics() -> None:
    gateway = os.getenv("PUSHGATEWAY_URL", "http://pushgateway:9091")
    worker_id = os.getenv("WORKER_ID", "unknown")
    try:
        push_to_gateway(gateway, job="ml-worker", grouping_key={"worker_id": worker_id}, registry=registry)
    except Exception:  # noqa: BLE001
        pass


def classify_failure(exc: BaseException) -> str:
    text = str(exc).lower()
    if "dataset" in text or "version" in text and "not found" in text:
        return "dataset_resolution_error"
    if "minio" in text or "s3" in text or "object storage" in text:
        return "object_storage_unavailable"
    return "training_exception"