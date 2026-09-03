"""Pydantic schemas for datasets and artifacts."""
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class DatasetCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    version: str = Field(min_length=1, max_length=64)
    format: str = Field(pattern="^(parquet|csv)$", default="parquet")
    storage_location: str = Field(min_length=1)  # e.g. s3://mlplatform/datasets/cms-run2015/v1/data.parquet
    metadata: dict[str, Any] = Field(default_factory=dict)
    size: int | None = Field(default=None, ge=0)
    checksum: str | None = None


class DatasetOut(BaseModel):
    dataset_id: str
    name: str
    version: str
    format: str
    storage_location: str
    # ORM attribute is `meta` (DB column `metadata`); `metadata` on the model
    # collides with SQLAlchemy's MetaData for from_attributes reads.
    metadata: dict[str, Any] = Field(default_factory=dict, validation_alias="meta")
    size: int | None = None
    checksum: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class ArtifactCreate(BaseModel):
    artifact_type: str = Field(pattern="^(checkpoint|model|dataset|log|metric)$", default="checkpoint")
    storage_path: str = Field(min_length=1)
    epoch: int | None = None


class ArtifactOut(BaseModel):
    artifact_id: str
    experiment_id: str
    artifact_type: str
    storage_path: str
    epoch: int | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
