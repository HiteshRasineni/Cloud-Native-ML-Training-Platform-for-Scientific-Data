"""Lightweight RealNVP-style normalizing flow, implemented from scratch in PyTorch.

A RealNVP flow stacks coupling layers; each layer splits the input features into
two halves x = [x_a, x_b] and applies an affine transform to one half conditioned
on the other through a small MLP (the "scale/translate network"). Forward maps
data -> latent (log-density computable); inverse maps latent -> data.
"""
import torch
import torch.nn as nn


class AffineCoupling(nn.Module):
    def __init__(self, features: int, hidden_features: int) -> None:
        super().__init__()
        self.features = features
        # True => "conditioning" half (passed through and fed to the net).
        self.register_buffer("mask", torch.arange(features) % 2 == 0)
        self.n_condition = int((self.mask).sum())
        self.n_move = features - self.n_condition
        self.net = nn.Sequential(
            nn.Linear(self.n_condition, hidden_features),
            nn.ReLU(),
            nn.Linear(hidden_features, hidden_features),
            nn.ReLU(),
            nn.Linear(hidden_features, 2 * self.n_move),
        )

    def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        """x -> y, plus log-determinant of the Jacobian."""
        m = self.mask
        x_a = x[:, m]
        x_b = x[:, ~m]
        st = self.net(x_a)
        s, t = torch.split(st, self.n_move, dim=1)
        s = torch.tanh(s)  # bounded scale for stability
        y_b = x_b * torch.exp(s) + t
        y = torch.empty_like(x)
        y[:, m] = x_a
        y[:, ~m] = y_b
        log_det = s.sum(dim=1)
        return y, log_det

    def inverse(self, y: torch.Tensor) -> torch.Tensor:
        m = self.mask
        y_a = y[:, m]
        y_b = y[:, ~m]
        st = self.net(y_a)
        s, t = torch.split(st, self.n_move, dim=1)
        s = torch.tanh(s)
        x_b = (y_b - t) * torch.exp(-s)
        x = torch.empty_like(y)
        x[:, m] = y_a
        x[:, ~m] = x_b
        return x


class NormalizingFlow(nn.Module):
    """Stack of coupling layers with an isotropic standard-normal base."""

    def __init__(self, features: int, transforms: int = 4, hidden_features: int = 32) -> None:
        super().__init__()
        self.features = features
        self.layers = nn.ModuleList(
            [AffineCoupling(features, hidden_features) for _ in range(transforms)]
        )

    def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        """data -> latent, returns (z, log_prob) where log_prob = N(z) log-density
        summed with the total log-determinant."""
        log_det = torch.zeros(x.shape[0], device=x.device)
        z = x
        for layer in self.layers:
            z, ld = layer(z)
            log_det = log_det + ld
        log_prob = self._base_log_prob(z) + log_det
        return z, log_prob

    def inverse(self, z: torch.Tensor) -> torch.Tensor:
        """latent -> data (sampling path)."""
        x = z
        for layer in reversed(self.layers):
            x = layer.inverse(x)
        return x

    def _base_log_prob(self, z: torch.Tensor) -> torch.Tensor:
        const = 0.5 * torch.log(torch.tensor(2 * torch.pi, device=z.device))
        return (-0.5 * z**2 - const).sum(dim=1)

    def sample(self, n: int) -> torch.Tensor:
        z = torch.randn(n, self.features)
        with torch.no_grad():
            return self.inverse(z)
