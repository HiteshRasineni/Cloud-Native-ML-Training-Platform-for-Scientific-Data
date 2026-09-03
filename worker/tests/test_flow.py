"""Tests for the normalizing flow forward/inverse pass shapes and invertibility."""
import torch

from workloads.normalizing_flow.flow import NormalizingFlow


def make_flow(features=4, transforms=3, hidden=16):
    torch.manual_seed(42)
    return NormalizingFlow(features=features, transforms=transforms, hidden_features=hidden)


def test_forward_output_shapes():
    flow = make_flow()
    x = torch.randn(32, 4)
    z, log_prob = flow(x)
    assert z.shape == x.shape
    assert log_prob.shape == (32,)


def test_inverse_maps_latent_to_data_space():
    flow = make_flow()
    z = torch.randn(16, 4)
    x = flow.inverse(z)
    assert x.shape == z.shape


def test_forward_inverse_roundtrip_recovers_input():
    # RealNVP coupling layers are exactly invertible: inverse(forward(x)) == x
    flow = make_flow(features=6, transforms=4)
    flow.eval()
    x = torch.randn(8, 6)
    with torch.no_grad():
        z, _ = flow(x)
        x_rec = flow.inverse(z)
    assert torch.allclose(x, x_rec, atol=1e-4)


def test_training_reduces_loss_on_two_gaussians():
    flow = make_flow(features=4, transforms=3, hidden=16)
    opt = torch.optim.Adam(flow.parameters(), lr=1e-2)
    data = torch.cat([torch.randn(256, 4) - 2.0, torch.randn(256, 4) + 2.0])

    def loss_value():
        _, log_prob = flow(data)
        return -log_prob.mean().item()

    first = loss_value()
    for _ in range(60):
        opt.zero_grad()
        _, log_prob = flow(data)
        loss = -log_prob.mean()
        loss.backward()
        opt.step()
    assert loss_value() < first  # density fitting actually learns
