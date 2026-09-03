"""Executor interface. Kubernetes executor will implement this in a later phase."""
from abc import ABC, abstractmethod
from typing import Any


class Executor(ABC):
    """Launches and tracks a single experiment workload container."""

    @abstractmethod
    def launch(self, experiment_id: str, spec: dict[str, Any]) -> str:
        """Start the workload. Returns an executor-specific handle/container id."""

    @abstractmethod
    def poll(self, handle: str) -> str:
        """Return one of: RUNNING | COMPLETED | FAILED."""

    @abstractmethod
    def cleanup(self, handle: str) -> None:
        """Release resources for a finished run."""
