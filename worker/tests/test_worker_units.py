"""Tests for checkpoint upload path construction and the normalizing flow shapes."""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from runtime.checkpoint import checkpoint_key, checkpoint_uri
from workloads.normalizing_flow.flow import NormalizingFlow


# ---------- Checkpoint path construction ----------


def test_checkpoint_key():
    key = checkpoint_key("exp-abc", 3)
    assert key == "experiments/exp-abc/checkpoints/epoch_3.pt"


def test_checkpoint_uri_uses_bucket_and_key(monkeypatch):
    monkeypatch.setenv("MINIO_BUCKET", "mlplatform")
    uri = checkpoint_uri("exp-abc", 3)
    assert uri == "s3://mlplatform/experiments/exp-abc/checkpoints/epoch_3.pt"


# ---------- Normalizing flow forward/inverse shapes ----------


@pytest.mark.parametrize("features", [4, 5])
@pytest.mark.parametrize("transforms", [1, 3])
@pytest.mark.parametrize("hidden_features", [8])
def test_flow_forward_inverse_shapes(features, transforms, hidden_features):
    flow = NormalizingFlow(features=features, transforms=transforms, hidden_features=hidden_features)
    x = torch_randn(8, features)
    z, log_prob = flow(x)
    assert z.shape == x.shape
    assert log_prob.shape == (8,)
    x_hat = flow.inverse(z)
    assert x_hat.shape == x.shape


@pytest.mark.parametrize("features", [4, 6])
def test_flow_sample_shape(features):
    flow = NormalizingFlow(features=features, transforms=2, hidden_features=16)
    samples = flow.sample(12)
    assert samples.shape == (12, features)


def torch_randn(rows, cols):
    import torch
    return torch.randn(rows, cols)
