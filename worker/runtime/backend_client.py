"""Talks to the backend API to record artifacts."""
import os

import httpx

BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000")


def register_artifact(experiment_id: str, artifact_type: str, storage_path: str, epoch: int | None = None) -> dict:
    """Record an artifact via the backend POST /experiments/{id}/artifacts."""
    payload = {"artifact_type": artifact_type, "storage_path": storage_path}
    if epoch is not None:
        payload["epoch"] = epoch
    with httpx.Client(timeout=10.0) as client:
        res = client.post(f"{BACKEND_URL}/experiments/{experiment_id}/artifacts", json=payload)
        res.raise_for_status()
        return res.json()
