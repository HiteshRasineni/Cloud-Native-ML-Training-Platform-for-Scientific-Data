"""Worker entrypoint: receives config via env, dispatches the requested workload."""
import json
import logging
import os
from time import monotonic

from workloads import get_workload
from runtime.protocol import HeartbeatThread
from runtime.observability import (
    classify_failure,
    push_metrics,
    worker_active,
    worker_failures_total,
    worker_training_epoch_duration_seconds,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("worker")


def main() -> None:
    experiment_id = os.getenv("EXPERIMENT_ID", "local-dev")
    config_path = os.getenv("EXPERIMENT_CONFIG_PATH", "/etc/platform/experiment.json")
    if os.path.exists(config_path):
        with open(config_path, encoding="utf-8") as config_file:
            spec = json.load(config_file)
    else:
        spec = json.loads(os.getenv("EXPERIMENT_SPEC", "{}"))
    worker_id = os.getenv("WORKER_ID")
    if worker_id is None:
        worker_index = os.getenv("WORKER_INDEX")
        worker_ids = spec.get("_worker_ids", [])
        if worker_index is not None and worker_ids:
            worker_id = worker_ids[int(worker_index)]

    model_type = spec.get("model", {}).get("type", "dummy")
    checkpointing = spec.get("checkpointing", {})
    workload = get_workload(model_type, experiment_id, spec.get("training", {}))
    heartbeat = HeartbeatThread(worker_id, os.getenv("BACKEND_URL", "http://backend:8000"))
    heartbeat.start()
    worker_active.set(1)
    push_metrics()

    try:
        logger.info("Starting experiment %s (workload=%s)", experiment_id, model_type)
        workload.setup(spec)
        from runtime.metrics_reporter import MetricsReporter
        reporter = MetricsReporter(experiment_id)
        for epoch in range(1, workload.epochs + 1):
            epoch_started = monotonic()
            metrics = workload.train_epoch(epoch)
            worker_training_epoch_duration_seconds.observe(monotonic() - epoch_started)
            reporter.report_progress(epoch, metrics)
            if checkpointing.get("enabled") and epoch % int(checkpointing.get("interval", 1)) == 0:
                if hasattr(workload, "checkpoint_if_needed"):
                    workload.checkpoint_if_needed(epoch, int(checkpointing.get("interval", 1)))
        workload.teardown()
        reporter.report_completion()
        logger.info("Experiment %s finished", experiment_id)
    except Exception as exc:
        worker_failures_total.labels(error_type=classify_failure(exc)).inc()
        push_metrics()
        raise
    finally:
        worker_active.set(0)
        push_metrics()
        heartbeat.stop()


if __name__ == "__main__":
    main()
