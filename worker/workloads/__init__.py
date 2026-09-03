"""Workload registry: maps model.type -> Workload class (lazy imports so that
importing a lightweight module like flow.py does not pull torch/pandas/mlflow)."""
from typing import Any

from workloads.base import Workload


def get_workload(model_type: str, experiment_id: str, training: dict) -> Workload:
    if model_type == "normalizing-flow":
        from workloads.normalizing_flow.normalizing_flow_workload import NormalizingFlowWorkload

        cls: type[Workload] = NormalizingFlowWorkload
    elif model_type == "dummy":
        from workloads.dummy.dummy_workload import DummyWorkload

        cls = DummyWorkload
    else:
        raise ValueError(f"Unknown workload type: {model_type}")
    return cls(
        experiment_id,
        epochs=int(training.get("epochs", 3)),
        batch_size=int(training.get("batch_size", 128)),
        learning_rate=float(training.get("learning_rate", 1e-3)),
    )


__all__ = ["Workload", "get_workload"]
