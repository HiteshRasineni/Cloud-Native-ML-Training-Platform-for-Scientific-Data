"""Kubernetes Job executor for indexed, multi-worker training runs."""
import json
import os
import uuid
from typing import Any

from kubernetes import client, config
from kubernetes.client.rest import ApiException

from executors.base import Executor


class KubernetesExecutor(Executor):
    def __init__(self, namespace: str | None = None, image: str | None = None) -> None:
        try:
            config.load_incluster_config()
        except config.ConfigException:
            config.load_kube_config()
        self.namespace = namespace or os.getenv("K8S_NAMESPACE", "default")
        self.image = image or os.getenv("WORKER_IMAGE", "platform/training-worker:latest")
        self.batch = client.BatchV1Api()
        self.core = client.CoreV1Api()

    def launch(self, experiment_id: str, spec: dict[str, Any]) -> str:
        job_name = f"training-{experiment_id[:20]}-{uuid.uuid4().hex[:8]}"
        worker_ids = spec.get("_worker_ids") or [f"{job_name}-{i}" for i in range(spec.get("resources", {}).get("workers", 1))]
        config_name = f"{job_name}-config"
        config_body = client.V1ConfigMap(
            metadata=client.V1ObjectMeta(name=config_name, labels={"platform.experiment_id": experiment_id}),
            data={"experiment.json": json.dumps({**spec, "_worker_ids": worker_ids})},
        )
        self.core.create_namespaced_config_map(self.namespace, config_body)
        count = len(worker_ids)
        pod = client.V1PodTemplateSpec(
            metadata=client.V1ObjectMeta(labels={"platform.job": job_name, "platform.experiment_id": experiment_id}),
            spec=client.V1PodSpec(
                restart_policy="Never",
                containers=[client.V1Container(
                    name="training-worker", image=self.image,
                    env=[
                        client.V1EnvVar(name="EXPERIMENT_ID", value=experiment_id),
                        client.V1EnvVar(name="WORKER_INDEX", value_from=client.V1EnvVarSource(
                            field_ref=client.V1ObjectFieldSelector(field_path="metadata.labels['batch.kubernetes.io/job-completion-index']")
                        )),
                        client.V1EnvVar(name="BACKEND_URL", value=os.getenv("BACKEND_URL", "http://backend:8000")),
                        client.V1EnvVar(name="EXPERIMENT_CONFIG_PATH", value="/etc/platform/experiment.json"),
                    ],
                    env_from=[
                        client.V1EnvFromSource(config_map_ref=client.V1ConfigMapEnvSource(name="worker-config")),
                        client.V1EnvFromSource(secret_ref=client.V1SecretEnvSource(name="platform-secret")),
                    ],
                    volume_mounts=[client.V1VolumeMount(name="experiment-config", mount_path="/etc/platform")],
                )],
                volumes=[client.V1Volume(name="experiment-config", config_map=client.V1ConfigMapVolumeSource(name=config_name))],
            ),
        )
        body = client.V1Job(
            metadata=client.V1ObjectMeta(name=job_name, labels={"platform.experiment_id": experiment_id}),
            spec=client.V1JobSpec(
                completions=count, parallelism=count, completion_mode="Indexed", backoff_limit=0,
                template=pod,
            ),
        )
        self.batch.create_namespaced_job(self.namespace, body)
        return json.dumps({"job_name": job_name, "config_name": config_name, "worker_ids": worker_ids})

    def monitor(self, job_id: str) -> str:
        job = self.batch.read_namespaced_job_status(job_id, self.namespace)
        if job.status.failed:
            return "FAILED"
        if job.status.succeeded and job.status.succeeded >= (job.spec.completions or 1):
            return "COMPLETED"
        return "RUNNING"

    def poll(self, handle: str) -> str:
        return self.monitor(json.loads(handle)["job_name"])

    def worker_states(self, handle: str) -> dict[str, str]:
        details = json.loads(handle)
        pods = self.core.list_namespaced_pod(self.namespace, label_selector=f"platform.job={details['job_name']}").items
        states = {worker_id: "RUNNING" for worker_id in details["worker_ids"]}
        for pod in pods:
            index = pod.metadata.labels.get("batch.kubernetes.io/job-completion-index")
            if index is None or int(index) >= len(details["worker_ids"]):
                continue
            phase = pod.status.phase
            states[details["worker_ids"][int(index)]] = {
                "Succeeded": "COMPLETED", "Failed": "FAILED", "Pending": "RUNNING", "Running": "RUNNING",
            }.get(phase, "FAILED")
        return states

    def terminate(self, job_id: str) -> None:
        details = json.loads(job_id) if job_id.startswith("{") else {"job_name": job_id}
        try:
            self.batch.delete_namespaced_job(details["job_name"], self.namespace, propagation_policy="Background")
        except ApiException as exc:
            if exc.status != 404:
                raise
        if details.get("config_name"):
            try:
                self.core.delete_namespaced_config_map(details["config_name"], self.namespace)
            except ApiException as exc:
                if exc.status != 404:
                    raise

    def cleanup(self, handle: str) -> None:
        self.terminate(handle)
