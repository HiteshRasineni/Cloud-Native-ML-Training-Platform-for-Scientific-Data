"""Tests for the checkpoint service path construction (pure logic, no MinIO)."""
from runtime.checkpoint import checkpoint_key, checkpoint_uri


def test_checkpoint_key_layout():
    assert checkpoint_key("exp-123", 7) == "experiments/exp-123/checkpoints/epoch_7.pt"


def test_checkpoint_uri_layout():
    uri = checkpoint_uri("exp-123", 1)
    assert uri.startswith("s3://")
    bucket, key = uri[5:].split("/", 1)
    assert key == "experiments/exp-123/checkpoints/epoch_1.pt"
    assert bucket  # bucket name comes from config/env


def test_experiment_subdirectory_isolation():
    a = checkpoint_key("aaa", 3)
    b = checkpoint_key("bbb", 3)
    assert a != b
    assert a.split("/")[1] == "aaa" and b.split("/")[1] == "bbb"
