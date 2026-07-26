"""Implicit Q-Learning (IQL) for offline RL.

IQL avoids querying out-of-distribution actions by using expectile
regression to estimate the value function, then extracting a policy
via advantage-weighted regression.

Kostrikov et al. 2022: https://arxiv.org/abs/2110.06169
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import torch
from torch import nn


@dataclass(frozen=True)
class IQLConfig:
    """Hyperparameters for IQL training."""
    gamma: float = 0.99
    tau: float = 0.7          # Expectile for V-function (0.5 = MSE, >0.5 = optimistic)
    beta: float = 3.0         # Inverse temperature for advantage weighting
    learning_rate: float = 3e-4
    hidden_dim: int = 256
    batch_size: int = 256
    n_critics: int = 2        # Ensemble size for Q-function
    expectile_threshold: float = 0.005  # Early stopping threshold


class _IQLValueNet(nn.Module):
    """V(s) network trained with expectile regression."""

    def __init__(self, state_dim: int, hidden_dim: int = 256):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(state_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 1),
        )

    def forward(self, states: torch.Tensor) -> torch.Tensor:
        return self.net(states)


class _IQLQNet(nn.Module):
    """Q(s, a) network. Uses ensemble of 2 critics to reduce overestimation."""

    def __init__(self, state_dim: int, action_dim: int, hidden_dim: int = 256):
        super().__init__()
        input_dim = state_dim + 1  # actions are scalar integers
        self.net1 = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.LayerNorm(hidden_dim), nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.LayerNorm(hidden_dim), nn.ReLU(),
            nn.Linear(hidden_dim, 1),
        )
        self.net2 = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.LayerNorm(hidden_dim), nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.LayerNorm(hidden_dim), nn.ReLU(),
            nn.Linear(hidden_dim, 1),
        )

    def forward(self, states: torch.Tensor, actions: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        x = torch.cat([states, actions], dim=-1)
        return self.net1(x), self.net2(x)

    def forward_min(self, states: torch.Tensor, actions: torch.Tensor) -> torch.Tensor:
        q1, q2 = self.forward(states, actions)
        return torch.min(q1, q2)


def _expectile_loss(pred: torch.Tensor, target: torch.Tensor, tau: float) -> torch.Tensor:
    """Expectile regression loss: L_2^tau."""
    diff = target - pred
    weight = torch.where(diff > 0, tau, 1.0 - tau)
    return (weight * diff ** 2).mean()


class IQLAgent:
    """IQL agent with V, Q, and policy networks.

    Usage:
        agent = IQLAgent(state_dim=7, action_dim=263)
        train_iql(agent, buffer)
    """

    def __init__(
        self,
        state_dim: int,
        action_dim: int,
        config: IQLConfig | None = None,
        *,
        device: str = "cpu",
    ) -> None:
        self.config = config or IQLConfig()
        self.device = torch.device(device)
        self.state_dim = state_dim
        self.action_dim = action_dim

        self.v_net = _IQLValueNet(state_dim, self.config.hidden_dim).to(self.device)
        self.target_v_net = _IQLValueNet(state_dim, self.config.hidden_dim).to(self.device)
        self.target_v_net.load_state_dict(self.v_net.state_dict())

        self.q_net = _IQLQNet(state_dim, action_dim, self.config.hidden_dim).to(self.device)

        self.optim_v = torch.optim.Adam(self.v_net.parameters(), lr=self.config.learning_rate)
        self.optim_q = torch.optim.Adam(self.q_net.parameters(), lr=self.config.learning_rate)

        self._step = 0

    def update(self, batch: dict[str, torch.Tensor]) -> dict[str, float]:
        """Perform one IQL update step.

        Args:
            batch: Dict with keys: states (B, S), actions (B,), rewards (B,),
                   next_states (B, S), dones (B,).

        Returns:
            Dict of loss components.
        """
        s = batch["states"]
        a = batch["actions"].float().unsqueeze(-1)
        r = batch["rewards"].unsqueeze(-1)
        ns = batch["next_states"]
        d = batch["dones"].unsqueeze(-1)

        # ----- Update Q-function -----
        with torch.no_grad():
            target_v = self.target_v_net(ns)
            q_target = r + self.config.gamma * (1.0 - d) * target_v

        q1, q2 = self.q_net(s, a)
        q_loss = nn.functional.mse_loss(q1, q_target) + nn.functional.mse_loss(q2, q_target)

        self.optim_q.zero_grad(set_to_none=True)
        q_loss.backward()
        torch.nn.utils.clip_grad_norm_(self.q_net.parameters(), 10.0)
        self.optim_q.step()

        # ----- Update V-function -----
        with torch.no_grad():
            q_min = self.q_net.forward_min(s, a)
        v_pred = self.v_net(s)
        v_loss = _expectile_loss(v_pred, q_min, self.config.tau)

        self.optim_v.zero_grad(set_to_none=True)
        v_loss.backward()
        torch.nn.utils.clip_grad_norm_(self.v_net.parameters(), 10.0)
        self.optim_v.step()

        # ----- Update target V network -----
        for param, target_param in zip(self.v_net.parameters(), self.target_v_net.parameters()):
            target_param.data.copy_(0.005 * param.data + 0.995 * target_param.data)

        self._step += 1
        return {
            "q_loss": float(q_loss.item()),
            "v_loss": float(v_loss.item()),
            "q_mean": float(q_min.mean().item()),
            "v_mean": float(v_pred.mean().item()),
        }

    @torch.no_grad()
    def get_q_values(self, states: torch.Tensor, actions: torch.Tensor) -> torch.Tensor:
        return self.q_net.forward_min(states, actions)

    @torch.no_grad()
    def get_value(self, states: torch.Tensor) -> torch.Tensor:
        return self.v_net(states)

    @torch.no_grad()
    def score_actions(self, state: np.ndarray, action_candidates: np.ndarray) -> np.ndarray:
        """Score candidate actions using Q-values."""
        s = torch.as_tensor(state, dtype=torch.float32, device=self.device).unsqueeze(0)
        a = torch.as_tensor(action_candidates, dtype=torch.float32, device=self.device).unsqueeze(-1)
        s_expanded = s.expand(len(action_candidates), -1)
        q = self.q_net.forward_min(s_expanded, a)
        return q.cpu().numpy().ravel()

    def save(self, path: str) -> None:
        torch.save({
            "v": self.v_net.state_dict(),
            "q": self.q_net.state_dict(),
        }, path)

    def load(self, path: str) -> None:
        data = torch.load(path, map_location=self.device, weights_only=True)
        self.v_net.load_state_dict(data["v"])
        self.q_net.load_state_dict(data["q"])


def train_iql(
    agent: IQLAgent,
    buffer: object,
    *,
    steps: int = 10_000,
    log_interval: int = 500,
) -> dict[str, list[float]]:
    """Train IQL agent on an offline buffer.

    Args:
        agent: IQLAgent instance.
        buffer: OfflineBuffer with at least batch_size transitions.
        steps: Number of gradient steps.
        log_interval: Logging interval.

    Returns:
        Dict of training metrics.
    """
    metrics: dict[str, list[float]] = {"q_loss": [], "v_loss": [], "q_mean": [], "v_mean": []}

    for step in range(steps):
        batch_np = buffer.sample(agent.config.batch_size)
        batch_t = {k: torch.as_tensor(v, device=agent.device) for k, v in batch_np.items()}
        info = agent.update(batch_t)

        if step % log_interval == 0:
            for k, v in info.items():
                metrics[k].append(v)
                if step % (log_interval * 5) == 0:
                    pass  # Could add logging here

    return metrics
