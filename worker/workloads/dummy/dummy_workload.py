"""No-op workload that sleeps and prints fake progress. Phase 1 slice."""
import time
from typing import Any

from workloads.base import Workload


class DummyWorkload(Workload):
    def __init__(self, experiment_id: str, epochs: int = 3, sleep_seconds: float = 2.0) -> None:
        super().__init__(experiment_id)
        self.epochs = epochs
        self.sleep_seconds = sleep_seconds

    def setup(self, spec: dict[str, Any]) -> None:
        print(f"[dummy] setup for {self.experiment_id}: {spec.get('dataset', {})}")

    def train_epoch(self, epoch: int) -> dict[str, float]:
        time.sleep(self.sleep_seconds)
        metrics = {"loss": 1.0 / epoch, "accuracy": min(1.0, epoch / self.epochs)}
        print(f"[dummy] {self.experiment_id} epoch {epoch}/{self.epochs} metrics={metrics}")
        return metrics

    def teardown(self) -> None:
        print(f"[dummy] teardown for {self.experiment_id}")
