"""Pydantic schemas validating the experiment spec (YAML-shaped)."""
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.failure import FailureOut
from app.schemas.job import JobOut
from app.schemas.worker import WorkerOut


class ExperimentInfo(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class DatasetSpec(BaseModel):
    name: str = Field(min_length=1)
    version: str = Field(min_length=1)


class ModelSpec(BaseModel):
    type: str = Field(pattern="^(normalizing-flow|classifier|dummy)$")
    architecture: dict[str, Any] = Field(
        default_factory=dict,
        description="Workload-specific architecture params, e.g. {transforms, hidden_features}",
    )


class ResourcesSpec(BaseModel):
    workers: int = Field(ge=1, le=1024, default=1)
    cpu: str = Field(default="1", description="K8s CPU request/limit e.g. 500m")
    gpu: int = Field(ge=0, le=8, default=0, description="GPUs per worker")
    node_selector: dict = Field(default_factory=dict)
    memory: str = Field(pattern=r"^\d+(Mi|Gi)$", default="1Gi")


class TrainingSpec(BaseModel):
    epochs: int = Field(ge=1, le=100000, default=10)
    batch_size: int = Field(ge=1, le=65536, default=64)
    learning_rate: float = Field(gt=0, default=1e-4)


class CheckpointingSpec(BaseModel):
    enabled: bool = False
    interval: int = Field(ge=1, default=1, description="Save a checkpoint every N epochs")


class RetrySpec(BaseModel):
    max_attempts: int = Field(ge=1, le=10, default=3)


class ExperimentSpec(BaseModel):
    """Top-level spec matching the documented YAML schema."""

    model_config = ConfigDict(populate_by_name=True)

    experiment: ExperimentInfo
    dataset: DatasetSpec
    model: ModelSpec
    resources: ResourcesSpec
    training: TrainingSpec
    checkpointing: CheckpointingSpec = CheckpointingSpec()
    retry: RetrySpec = RetrySpec(max_attempts=3)


class ExperimentCreate(BaseModel):
    spec: ExperimentSpec


class ExperimentOut(BaseModel):
    id: str
    name: str
    status: str
    attempts: int
    error_message: str | None = None
    spec: dict[str, Any]
    job: JobOut | None = None
    workers: list[WorkerOut] = Field(default_factory=list)
    failures: list[FailureOut] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
