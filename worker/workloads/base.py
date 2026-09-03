"""Workload interface. Real ML workloads are added in later phases."""
from abc import ABC, abstractmethod
from typing import Any


class Workload(ABC):
    def __init__(self, experiment_id: str) -> None:
        self.experiment_id = experiment_id

    @abstractmethod
    def setup(self, spec: dict[str, Any]) -> None: ...

    @abstractmethod
    def train_epoch(self, epoch: int) -> dict[str, float]:
        """Run one epoch and return metrics (e.g. loss, accuracy)."""

    @abstractmethod
    def teardown(self) -> None: ...
