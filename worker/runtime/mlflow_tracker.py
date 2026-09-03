"""MLflow tracking wrapper for worker runs."""
import os

import mlflow

MLFLOW_RUN_TAG = "platform_experiment_id"


class MLflowTracker:
    """Thin wrapper around the MLflow client so workloads can start/end runs
    and log params/metrics/artifacts without touching mlflow directly."""

    def __init__(self, experiment_id: str) -> None:
        self.experiment_id = experiment_id
        self.tracking_uri = os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000")
        mlflow.set_tracking_uri(self.tracking_uri)
        self._run_id: str | None = None

    def start(self, params: dict | None = None) -> None:
        run = mlflow.start_run(tags={MLFLOW_RUN_TAG: self.experiment_id})
        self._run_id = run.info.run_id

    def log_params(self, params: dict) -> None:
        # Batch in chunks of 100 to stay under MLflow's per-request limit.
        items = list(params.items())
        for i in range(0, len(items), 100):
            mlflow.log_params(dict(items[i : i + 100]))

    def log_epoch(self, epoch: int, metrics: dict[str, float]) -> None:
        mlflow.log_metrics(metrics, step=epoch)

    def log_artifact(self, local_path: str) -> None:
        mlflow.log_artifact(local_path)

    def end(self, status: str = "FINISHED") -> None:
        mlflow.end_run(status=status)
