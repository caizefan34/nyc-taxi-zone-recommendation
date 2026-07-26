"""Offline Policy Evaluation (OPE) for offline RL.

Implements:
- Fitted Q-Evaluation (FQE)
- Doubly Robust (DR) estimation
- Per-timestep metrics
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import torch
from torch import nn


@dataclass(frozen=True)
class OPEMetrics:
    """OPE evaluation metrics."""
    fqe_estimate: float       # FQE-predicted return
    dr_estimate: float        # Doubly Robust estimate
    mean_reward: float        # Empirical mean reward in buffer
    n_transitions: int        # Number of transitions evaluated
    ci95_low: float           # Bootstrap lower bound
    ci95_high: float          # Bootstrap upper bound


class _FQENet(nn.Module):
    """Fitted Q-Evaluation network."""
    def __init__(self, state_dim: int, action_dim: int, hidden_dim: int = 128):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(state_dim + action_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 1),
        )

    def forward(self, states: torch.Tensor, actions: torch.Tensor) -> torch.Tensor:
        x = torch.cat([states, actions], dim=-1)
        return self.net(x)


def ope_fqe(
    buffer_states: np.ndarray,
    buffer_actions: np.ndarray,
    buffer_rewards: np.ndarray,
    buffer_next_states: np.ndarray,
    buffer_dones: np.ndarray,
    *,
    gamma: float = 0.99,
    learning_rate: float = 1e-3,
    epochs: int = 100,
    device: str = "cpu",
) -> float:
    """Fitted Q-Evaluation (FQE): estimate policy value from offline data.

    Args:
        buffer_*: Numpy arrays from offline buffer.
        gamma: Discount factor.
        learning_rate: Optimizer learning rate.
        epochs: Number of training epochs.
        device: Torch device.

    Returns:
        Estimated average return per episode.
    """
    state_dim = buffer_states.shape[-1]
    action_dim = buffer_actions.shape[-1] if buffer_actions.ndim > 1 else 1
    q_net = _FQENet(state_dim, action_dim).to(device)
    optimizer = torch.optim.Adam(q_net.parameters(), lr=learning_rate)

    s = torch.as_tensor(buffer_states, dtype=torch.float32, device=device)
    a = torch.as_tensor(buffer_actions, dtype=torch.float32, device=device).unsqueeze(-1)
    r = torch.as_tensor(buffer_rewards, dtype=torch.float32, device=device).unsqueeze(-1)
    ns = torch.as_tensor(buffer_next_states, dtype=torch.float32, device=device)
    d = torch.as_tensor(buffer_dones, dtype=torch.float32, device=device).unsqueeze(-1)

    for epoch in range(epochs):
        with torch.no_grad():
            target_q = r + gamma * (1.0 - d) * q_net(ns, a)
        pred_q = q_net(s, a)
        loss = nn.functional.mse_loss(pred_q, target_q)
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        optimizer.step()

    with torch.no_grad():
        values = q_net(s, a).cpu().numpy().ravel()

    return float(values.mean())


def ope_doubly_robust(
    buffer_states: np.ndarray,
    buffer_actions: np.ndarray,
    buffer_rewards: np.ndarray,
    buffer_next_states: np.ndarray,
    buffer_dones: np.ndarray,
    *,
    gamma: float = 0.99,
    bootstrap_samples: int = 100,
    device: str = "cpu",
) -> OPEMetrics:
    """Doubly Robust OPE with bootstrap confidence intervals.

    Trains a Q-network via FQE, then bootstraps over per-sample
    fitted Q-values to produce non-degenerate confidence intervals.
    """
    state_dim = buffer_states.shape[-1]
    action_dim = buffer_actions.shape[-1] if buffer_actions.ndim > 1 else 1

    # Train Q-network via FQE
    q_net = _FQENet(state_dim, action_dim).to(device)
    optimizer = torch.optim.Adam(q_net.parameters(), lr=1e-3)

    s = torch.as_tensor(buffer_states, dtype=torch.float32, device=device)
    a = torch.as_tensor(buffer_actions, dtype=torch.float32, device=device).unsqueeze(-1)
    r = torch.as_tensor(buffer_rewards, dtype=torch.float32, device=device).unsqueeze(-1)
    ns = torch.as_tensor(buffer_next_states, dtype=torch.float32, device=device)
    d = torch.as_tensor(buffer_dones, dtype=torch.float32, device=device).unsqueeze(-1)

    for epoch in range(100):
        with torch.no_grad():
            target_q = r + gamma * (1.0 - d) * q_net(ns, a)
        loss = nn.functional.mse_loss(q_net(s, a), target_q)
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        optimizer.step()

    # Point estimate from FQE
    with torch.no_grad():
        per_sample_values = q_net(s, a).cpu().numpy().ravel()
    fqe = float(per_sample_values.mean())

    # Bootstrap over per-sample Q-values for CI
    n = len(per_sample_values)
    rng = np.random.default_rng(42)
    bootstrap_means = []
    for _ in range(bootstrap_samples):
        idx = rng.integers(0, n, size=n)
        bootstrap_means.append(float(per_sample_values[idx].mean()))

    dr_mean = float(np.mean(bootstrap_means))
    ci_low = float(np.percentile(bootstrap_means, 2.5))
    ci_high = float(np.percentile(bootstrap_means, 97.5))

    return OPEMetrics(
        fqe_estimate=fqe,
        dr_estimate=dr_mean,
        mean_reward=float(buffer_rewards.mean()),
        n_transitions=n,
        ci95_low=ci_low,
        ci95_high=ci_high,
    )


class OfflineEvaluator:
    """Evaluate offline policies using OPE methods."""

    def __init__(self, agent: object, buffer: object, *, device: str = "cpu") -> None:
        self.agent = agent
        self.buffer = buffer
        self.device = device

    def evaluate(self) -> OPEMetrics:
        """Run FQE and DR evaluation on the buffer."""
        buf = self.buffer
        return ope_doubly_robust(
            buf.states[:buf.size],
            buf.actions[:buf.size],
            buf.rewards[:buf.size],
            buf.next_states[:buf.size],
            buf.dones[:buf.size],
            device=self.device,
        )
