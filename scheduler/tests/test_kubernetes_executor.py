import pytest
from unittest.mock import Mock, patch

kubernetes = pytest.importorskip("kubernetes")
from executors.kubernetes.executor import KubernetesExecutor


def test_launch_creates_indexed_multi_worker_job():
    with patch("executors.kubernetes.executor.config.load_incluster_config"), patch(
        "executors.kubernetes.executor.config.load_kube_config"
    ):
        executor = KubernetesExecutor(namespace="test")
    executor.core = Mock()
    executor.batch = Mock()

    handle = executor.launch(
        "experiment-123",
        {"resources": {"workers": 2}, "_worker_ids": ["worker-a", "worker-b"]},
    )

    body = executor.batch.create_namespaced_job.call_args.args[1]
    assert body.spec.parallelism == 2
    assert body.spec.completions == 2
    assert body.spec.completion_mode == "Indexed"
    assert body.spec.template.spec.restart_policy == "Never"
    assert body.spec.template.spec.containers[0].env[-1].value == "/etc/platform/experiment.json"
    config = executor.core.create_namespaced_config_map.call_args.args[1]
    assert "worker-a" in config.data["experiment.json"]
    assert "worker-b" in config.data["experiment.json"]
    assert len(handle) > 0
