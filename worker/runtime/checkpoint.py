"""Reusable checkpoint service: save locally, upload to MinIO.

Object layout (per experiment):
    experiments/{experiment_id}/checkpoints/epoch_{n}.pt
Not coupled to any specific workload; callers pass a serializable state dict.
"""
import os
import tempfile
from typing import Any

from runtime.storage import get_s3_client, split_s3_uri

CHECKPOINT_BUCKET = os.getenv("MINIO_BUCKET", "mlplatform")


def checkpoint_key(experiment_id: str, epoch: int) -> str:
    """Build the canonical MinIO key for a checkpoint artifact."""
    return f"experiments/{experiment_id}/checkpoints/epoch_{epoch}.pt"


def checkpoint_uri(experiment_id: str, epoch: int) -> str:
    return f"s3://{CHECKPOINT_BUCKET}/{checkpoint_key(experiment_id, epoch)}"


def save_and_upload(experiment_id: str, epoch: int, state: dict[str, Any]) -> str:
    """Serialize `state` (torch.load-able) to a temp file, upload to MinIO,
    return the s3:// URI."""
    import torch

    local_path = os.path.join(
        tempfile.gettempdir(), f"ckpt_{experiment_id}_{epoch}.pt"
    )
    torch.save(state, local_path)
    try:
        bucket, key = split_s3_uri(f"s3://{CHECKPOINT_BUCKET}/x")
        get_s3_client().upload_file(local_path, bucket, checkpoint_key(experiment_id, epoch))
    finally:
        if os.path.exists(local_path):
            os.remove(local_path)
    return checkpoint_uri(experiment_id, epoch)
