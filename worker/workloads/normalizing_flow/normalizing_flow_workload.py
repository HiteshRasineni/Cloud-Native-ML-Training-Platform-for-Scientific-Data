"""Normalizing-flow training workload on a MinIO-resolved dataset."""
import logging
from typing import Any

import numpy as np
import pandas as pd
import torch
from torch.utils.data import DataLoader, TensorDataset

from runtime import checkpoint as checkpoint_service
from runtime.backend_client import register_artifact
from runtime.dataloader import load_dataframe
from runtime.mlflow_tracker import MLflowTracker
from runtime.storage import download_to_temp
from workloads.base import Workload

from .flow import NormalizingFlow

logger = logging.getLogger("worker.nf")

DEFAULT_FEATURES = ["pt", "eta", "phi", "energy"]


class NormalizingFlowWorkload(Workload):
    def __init__(self, experiment_id: str, epochs: int = 5, batch_size: int = 128, learning_rate: float = 1e-3) -> None:
        super().__init__(experiment_id)
        self.epochs = epochs
        self.batch_size = batch_size
        self.learning_rate = learning_rate

    def setup(self, spec: dict[str, Any]) -> None:
        # Architecture comes from the experiment spec — never hardcoded.
        arch = spec.get("model", {}).get("architecture", {})
        self.transforms = int(arch.get("transforms", 4))
        self.hidden_features = int(arch.get("hidden_features", 32))

        dataset = spec["dataset"]
        storage_location = dataset.get("storage_location")
        if not storage_location:
            raise ValueError("spec.dataset.storage_location missing — dataset not resolved by backend")

        # Format + branch selection are dataset metadata; the workload stays
        # format-agnostic and just asks the loader for a DataFrame.
        fmt = dataset.get("format", "parquet")
        meta = dataset.get("metadata") or {}
        tree = dataset.get("tree") or meta.get("tree", "Events")
        features = dataset.get("features") or meta.get("features") or DEFAULT_FEATURES
        self.features = list(features)

        local_path = download_to_temp(storage_location)
        df = load_dataframe(local_path, fmt, tree=tree)
        missing = [c for c in self.features if c not in df.columns]
        if missing:
            raise ValueError(
                f"dataset is missing required feature columns {missing}; "
                f"available: {list(df.columns)}"
            )
        data = df[self.features].to_numpy(dtype=np.float32)
        self.dataset_dim = data.shape[1]

        self.flow = NormalizingFlow(
            features=self.dataset_dim,
            transforms=self.transforms,
            hidden_features=self.hidden_features,
        )
        self.optimizer = torch.optim.Adam(self.flow.parameters(), lr=self.learning_rate)

        dataset = TensorDataset(torch.from_numpy(data))
        self.loader = DataLoader(dataset, batch_size=self.batch_size, shuffle=True)

        self.mlflow = MLflowTracker(self.experiment_id)
        self.mlflow.start(params={})
        self.mlflow.log_params(
            {
                "epochs": self.epochs,
                "batch_size": self.batch_size,
                "learning_rate": self.learning_rate,
                "transforms": self.transforms,
                "hidden_features": self.hidden_features,
                "dataset": f"{spec['dataset']['name']}:{spec['dataset']['version']}",
                "dataset_format": fmt,
                "features": ",".join(self.features),
            }
        )
        logger.info(
            "NF setup done: format=%s dim=%d transforms=%d hidden=%d rows=%d features=%s",
            fmt, self.dataset_dim, self.transforms, self.hidden_features, data.shape[0], self.features,
        )

    def train_epoch(self, epoch: int) -> dict[str, float]:
        self.flow.train()
        total_loss, batches = 0.0, 0
        for (x,) in self.loader:
            self.optimizer.zero_grad()
            _, log_prob = self.flow(x)
            loss = -log_prob.mean()
            loss.backward()
            self.optimizer.step()
            total_loss += loss.item()
            batches += 1
        metrics = {"loss": total_loss / max(batches, 1)}
        self.mlflow.log_epoch(epoch, metrics)
        return metrics

    def checkpoint_if_needed(self, epoch: int, interval: int) -> None:
        uri = checkpoint_service.save_and_upload(
            self.experiment_id,
            epoch,
            {"model_state": self.flow.state_dict(), "epoch": epoch},
        )
        register_artifact(self.experiment_id, "checkpoint", uri, epoch=epoch)
        logger.info("Uploaded checkpoint %s", uri)

    def teardown(self) -> None:
        # Final model artifact into the local temp dir, then MLflow + MinIO.
        import os
        import tempfile

        local_path = os.path.join(tempfile.gettempdir(), f"model_{self.experiment_id}.pt")
        torch.save({"model_state": self.flow.state_dict(), "features": self.features}, local_path)
        self.mlflow.log_artifact(local_path)
        os.remove(local_path)
        self.mlflow.end("FINISHED")
