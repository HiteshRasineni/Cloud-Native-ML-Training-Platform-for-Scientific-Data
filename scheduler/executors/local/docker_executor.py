"""Local Docker executor using the Docker SDK.

Supports multi-worker jobs: when resources.workers > 1, launch() creates
that many containers (each with a unique WORKER_ID). The handle is a
JSON-encoded dict of container_id -> worker_id, so poll() and cleanup()
operate on all containers for the job without the queue_consumer needing
to know multi-worker details.
"""
import json
import os
from typing import Any

import docker

from executors.base import Executor

WORKER_IMAGE = os.getenv("WORKER_IMAGE", "cloud-ml-platform-worker:latest")


class LocalDockerExecutor(Executor):
    def __init__(self) -> None:
        self.client = docker.from_env()

    def launch(self, experiment_id: str, spec: dict[str, Any]) -> str:
        """Start worker container(s). Returns a JSON handle.

        Args:
            experiment_id: the experiment being run.
            spec: the full experiment spec.
            Worker IDs are supplied in the scheduler-only ``_worker_ids``
            field so the public executor interface remains unchanged.
        """
        configured_count = spec.get("resources", {}).get("workers", 1)
        worker_ids = spec.get("_worker_ids") or [f"worker-{i}" for i in range(configured_count)]
        worker_count = len(worker_ids)

        containers: dict[str, str] = {}  # container_id -> worker_id
        for worker_id in worker_ids:
            container = self._launch_one(experiment_id, spec, worker_id)
            containers[container.id] = worker_id
        return json.dumps(containers)

    def _launch_one(self, experiment_id: str, spec: dict[str, Any],
                    worker_id: str) -> docker.models.containers.Container:
        """Launch a single worker container."""
        container = self.client.containers.run(
            WORKER_IMAGE,
            detach=True,
            environment={
                "EXPERIMENT_ID": experiment_id,
                "EXPERIMENT_SPEC": json.dumps(spec),
                "WORKER_ID": worker_id,
                "REDIS_URL": os.getenv("REDIS_URL", "redis://redis:6379/0"),
                "BACKEND_URL": os.getenv("BACKEND_URL", "http://backend:8000"),
                "PUSHGATEWAY_URL": os.getenv("PUSHGATEWAY_URL", "http://pushgateway:9091"),
                "MLFLOW_TRACKING_URI": os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000"),
                "MINIO_ENDPOINT": os.getenv("MINIO_ENDPOINT", "http://minio:9000"),
                "MINIO_ROOT_USER": os.getenv("MINIO_ROOT_USER", "mlplatform"),
                "MINIO_ROOT_PASSWORD": os.getenv("MINIO_ROOT_PASSWORD", "mlplatform-secret"),
                "MINIO_BUCKET": os.getenv("MINIO_BUCKET", "mlplatform"),
                "AWS_ACCESS_KEY_ID": os.getenv("AWS_ACCESS_KEY_ID", "mlplatform"),
                "AWS_SECRET_ACCESS_KEY": os.getenv("AWS_SECRET_ACCESS_KEY", "mlplatform-secret"),
                "MLFLOW_S3_ENDPOINT_URL": os.getenv("MLFLOW_S3_ENDPOINT_URL", "http://minio:9000"),
            },
            network=os.getenv("WORKER_NETWORK", "cloud-ml-platform_default"),
            labels={
                "platform.experiment_id": experiment_id,
                "platform.worker_id": worker_id,
            },
            auto_remove=False,
        )
        return container

    def poll(self, handle: str) -> str:
        """Return aggregate status across all workers for the job.

        Returns RUNNING if any worker is still running, COMPLETED if all
        workers exited 0, FAILED if any worker exited non-zero.
        """
        containers: dict[str, str] = json.loads(handle)
        any_running = False
        any_failed = False
        for container_id in containers:
            try:
                container = self.client.containers.get(container_id)
                container.reload()
            except docker.errors.NotFound:
                any_failed = True
                continue
            state = container.status
            if state == "running":
                any_running = True
            elif state == "exited":
                if container.attrs["State"]["ExitCode"] != 0:
                    any_failed = True
            else:
                any_failed = True
        if any_running:
            return "RUNNING"
        if any_failed:
            return "FAILED"
        return "COMPLETED"

    def worker_states(self, handle: str) -> dict[str, str]:
        """Return RUNNING, COMPLETED, or FAILED for each worker in a handle."""
        containers: dict[str, str] = json.loads(handle)
        states: dict[str, str] = {}
        for container_id, worker_id in containers.items():
            try:
                container = self.client.containers.get(container_id)
                container.reload()
            except docker.errors.NotFound:
                states[worker_id] = "FAILED"
                continue
            if container.status == "running":
                states[worker_id] = "RUNNING"
            elif container.status == "exited" and container.attrs["State"]["ExitCode"] == 0:
                states[worker_id] = "COMPLETED"
            else:
                states[worker_id] = "FAILED"
        return states

    def cleanup(self, handle: str) -> None:
        """Remove all containers for the job."""
        containers: dict[str, str] = json.loads(handle)
        for container_id in containers:
            try:
                container = self.client.containers.get(container_id)
                container.remove(force=True)
            except docker.errors.NotFound:
                pass
