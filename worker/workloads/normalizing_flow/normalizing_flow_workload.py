"""Normalizing-flow training workload on a MinIO-resolved dataset."""
import logging
from typing import Any

import numpy as np
import pandas as pd
import torch
from torch.utils.data import DataLoader, TensorDataset

from runtime import checkpoint as checkpoint_service
from runtime.backend_client import register_artifact
from runtime.mlflow_tracker import MLflowTracker
from runtime.storage import download_to_temp
from workloads.base import Workload

from .flow import NormalizingFlow

logger = logging.getLogger("worker.nf")

FEATURES = ["pt", "eta", "phi", "energy"]


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

        storage_location = spec["dataset"].get("storage_location")
        if not storage_location:
            raise ValueError("spec.dataset.storage_location missing — dataset not resolved by backend")

        local_path = download_to_temp(storage_location)
        df = pd.read_parquet(local_path)
        data = df[FEATURES].to_numpy(dtype=np.float32)
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
                "features": ",".join(FEATURES),
            }
        )
        logger.info(
            "NF setup done: dim=%d transforms=%d hidden=%d rows=%d",
            self.dataset_dim, self.transforms, self.hidden_features, data.shape[0],
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
        torch.save({"model_state": self.flow.state_dict(), "features": FEATURES}, local_path)
        self.mlflow.log_artifact(local_path)
        os.remove(local_path)
        self.mlflow.end("FINISHED")
