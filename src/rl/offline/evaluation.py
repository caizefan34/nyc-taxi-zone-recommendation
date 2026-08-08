"""Trajectory-aware offline policy evaluation.

WIS and doubly robust estimates require probabilities for the logged action
under both the behavior and target policies.  They are computed per trajectory;
transition-level resampling is not a valid substitute for episode bootstrap.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import torch
from torch import nn


@dataclass(frozen=True)
class OPEMetrics:
    """Offline policy evaluation metrics and method-specific intervals."""

    fqe_estimate: float
    dr_estimate: float
    wis_estimate: float
    mean_reward: float
    n_transitions: int
    ci95_low: float
    ci95_high: float
    wis_ci95_low: float
    wis_ci95_high: float
    n_trajectories: int


class _FQENet(nn.Module):
    """Small fitted-Q network used as a nuisance model."""

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
        return self.net(torch.cat([states, actions], dim=-1))


def _action_matrix(actions: np.ndarray) -> np.ndarray:
    actions = np.asarray(actions)
    return actions[:, None] if actions.ndim == 1 else actions


def _validate_transitions(
    rewards: np.ndarray,
    dones: np.ndarray,
    trajectory_ids: np.ndarray,
    behavior_probs: np.ndarray,
    target_probs: np.ndarray,
) -> tuple[np.ndarray, ...]:
    arrays = tuple(np.asarray(x).reshape(-1) for x in (rewards, dones, trajectory_ids, behavior_probs, target_probs))
    n = len(arrays[0])
    if n == 0:
        raise ValueError("OPE requires at least one transition")
    if any(len(x) != n for x in arrays[1:]):
        raise ValueError("all OPE arrays must have the same length")
    if not np.all(np.isfinite(arrays[0])):
        raise ValueError("rewards must be finite")
    if np.any(arrays[3] <= 0) or np.any(arrays[3] > 1):
        raise ValueError("behavior probabilities must be in (0, 1]")
    if np.any(arrays[4] < 0) or np.any(arrays[4] > 1):
        raise ValueError("target probabilities must be in [0, 1]")
    return arrays


def _trajectory_indices(trajectory_ids: np.ndarray) -> list[np.ndarray]:
    """Return trajectory indices in first-seen order and reject interleaving."""
    ordered_ids = list(dict.fromkeys(trajectory_ids.tolist()))
    trajectories = [np.flatnonzero(trajectory_ids == trajectory_id) for trajectory_id in ordered_ids]
    for indices in trajectories:
        if len(indices) > 1 and np.any(np.diff(indices) != 1):
            raise ValueError("trajectory transitions must be contiguous and time ordered")
    return trajectories


def _bootstrap_interval(values: np.ndarray, samples: int, seed: int) -> tuple[float, float]:
    if samples <= 0:
        raise ValueError("bootstrap_samples must be positive")
    if len(values) == 1:
        value = float(values[0])
        return value, value
    rng = np.random.default_rng(seed)
    draws = np.empty(samples, dtype=np.float64)
    for draw in range(samples):
        indices = rng.integers(0, len(values), size=len(values))
        draws[draw] = values[indices].mean()
    return float(np.percentile(draws, 2.5)), float(np.percentile(draws, 97.5))


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
    seed: int = 42,
) -> float:
    """Fit a diagnostic Q model on logged transitions.

    This function alone is not a target-policy value estimate: without target
    next actions it uses the logged action at the next state.  The explicit
    limitation prevents the model diagnostic from being confused with OPE.
    """
    states = np.asarray(buffer_states)
    actions = _action_matrix(buffer_actions)
    next_states = np.asarray(buffer_next_states)
    rewards = np.asarray(buffer_rewards).reshape(-1)
    dones = np.asarray(buffer_dones).reshape(-1)
    if len(states) == 0 or not (len(states) == len(actions) == len(rewards) == len(next_states) == len(dones)):
        raise ValueError("FQE arrays must be non-empty and have the same length")

    torch.manual_seed(seed)
    q_net = _FQENet(states.shape[-1], actions.shape[-1]).to(device)
    optimizer = torch.optim.Adam(q_net.parameters(), lr=learning_rate)
    s = torch.as_tensor(states, dtype=torch.float32, device=device)
    a = torch.as_tensor(actions, dtype=torch.float32, device=device)
    r = torch.as_tensor(rewards[:, None], dtype=torch.float32, device=device)
    ns = torch.as_tensor(next_states, dtype=torch.float32, device=device)
    d = torch.as_tensor(dones[:, None], dtype=torch.float32, device=device)

    for _ in range(epochs):
        with torch.no_grad():
            target_q = r + gamma * (1.0 - d) * q_net(ns, a)
        loss = nn.functional.mse_loss(q_net(s, a), target_q)
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        optimizer.step()

    with torch.no_grad():
        return float(q_net(s, a).mean().cpu())


def _per_decision_wis(
    rewards: np.ndarray,
    trajectory_ids: np.ndarray,
    ratios: np.ndarray,
    gamma: float,
) -> float:
    trajectories = _trajectory_indices(trajectory_ids)
    estimate = 0.0
    max_length = max(len(indices) for indices in trajectories)
    cumulative = [np.cumprod(ratios[indices], dtype=np.float64) for indices in trajectories]
    for step in range(max_length):
        active = [(indices, weights) for indices, weights in zip(trajectories, cumulative) if step < len(indices)]
        denominator = sum(weights[step] for _, weights in active)
        if denominator > 0:
            numerator = sum(weights[step] * rewards[indices[step]] for indices, weights in active)
            estimate += gamma**step * numerator / denominator
    return float(estimate)


def ope_weighted_importance_sampling(
    buffer_rewards: np.ndarray,
    buffer_dones: np.ndarray,
    behavior_probs: np.ndarray | None = None,
    *,
    target_probs: np.ndarray | None = None,
    trajectory_ids: np.ndarray | None = None,
    gamma: float = 0.99,
    bootstrap_samples: int = 100,
    seed: int = 42,
) -> tuple[float, float, float]:
    """Compute per-decision self-normalized WIS and a trajectory bootstrap CI."""
    if behavior_probs is None or target_probs is None or trajectory_ids is None:
        raise ValueError("WIS requires behavior_probs, target_probs, and trajectory_ids")
    rewards, dones, trajectory_ids, behavior_probs, target_probs = _validate_transitions(
        buffer_rewards, buffer_dones, trajectory_ids, behavior_probs, target_probs
    )
    trajectories = _trajectory_indices(trajectory_ids)
    for indices in trajectories:
        if not bool(dones[indices[-1]]):
            raise ValueError("every trajectory must end with done=True")

    ratios = target_probs / behavior_probs
    estimate = _per_decision_wis(rewards, trajectory_ids, ratios, gamma)
    rng = np.random.default_rng(seed)
    bootstrap = np.empty(bootstrap_samples, dtype=np.float64)
    for draw in range(bootstrap_samples):
        sampled = rng.integers(0, len(trajectories), size=len(trajectories))
        bs_rewards: list[np.ndarray] = []
        bs_ratios: list[np.ndarray] = []
        bs_ids: list[np.ndarray] = []
        for new_id, source in enumerate(sampled):
            indices = trajectories[source]
            bs_rewards.append(rewards[indices])
            bs_ratios.append(ratios[indices])
            bs_ids.append(np.full(len(indices), new_id))
        bootstrap[draw] = _per_decision_wis(
            np.concatenate(bs_rewards), np.concatenate(bs_ids), np.concatenate(bs_ratios), gamma
        )
    return estimate, float(np.percentile(bootstrap, 2.5)), float(np.percentile(bootstrap, 97.5))


def ope_doubly_robust(
    buffer_states: np.ndarray,
    buffer_actions: np.ndarray,
    buffer_rewards: np.ndarray,
    buffer_next_states: np.ndarray,
    buffer_dones: np.ndarray,
    *,
    trajectory_ids: np.ndarray | None = None,
    behavior_probs: np.ndarray | None = None,
    target_probs: np.ndarray | None = None,
    q_values: np.ndarray | None = None,
    state_values: np.ndarray | None = None,
    next_state_values: np.ndarray | None = None,
    gamma: float = 0.99,
    bootstrap_samples: int = 100,
    seed: int = 42,
    device: str = "cpu",
) -> OPEMetrics:
    """Compute sequential doubly robust OPE with episode bootstrap.

    ``q_values`` must estimate Q(s_t, a_t) for the logged action, while
    ``state_values`` and ``next_state_values`` estimate V(s_t) and V(s_{t+1})
    under the target policy.  Supplying these nuisance predictions explicitly
    avoids silently pretending logged actions came from the target policy.
    """
    del device  # Retained for API compatibility; nuisance models are supplied explicitly.
    if trajectory_ids is None or behavior_probs is None or target_probs is None:
        raise ValueError("DR requires trajectory_ids, behavior_probs, and target_probs")
    if q_values is None or state_values is None or next_state_values is None:
        raise ValueError("DR requires target-policy q_values, state_values, and next_state_values")

    rewards, dones, trajectory_ids, behavior_probs, target_probs = _validate_transitions(
        buffer_rewards, buffer_dones, trajectory_ids, behavior_probs, target_probs
    )
    n = len(rewards)
    for name, values in {
        "q_values": q_values,
        "state_values": state_values,
        "next_state_values": next_state_values,
    }.items():
        array = np.asarray(values).reshape(-1)
        if len(array) != n or not np.all(np.isfinite(array)):
            raise ValueError(f"{name} must be finite and match transition count")
    q_values = np.asarray(q_values).reshape(-1)
    state_values = np.asarray(state_values).reshape(-1)
    next_state_values = np.asarray(next_state_values).reshape(-1)

    trajectories = _trajectory_indices(trajectory_ids)
    ratios = target_probs / behavior_probs
    contributions = np.empty(len(trajectories), dtype=np.float64)
    fqe_values = np.empty(len(trajectories), dtype=np.float64)
    for trajectory_number, indices in enumerate(trajectories):
        if not bool(dones[indices[-1]]):
            raise ValueError("every trajectory must end with done=True")
        rho = 1.0
        contribution = float(state_values[indices[0]])
        for step, index in enumerate(indices):
            rho *= ratios[index]
            td_residual = rewards[index] + gamma * (1.0 - dones[index]) * next_state_values[index] - q_values[index]
            contribution += gamma**step * rho * td_residual
        contributions[trajectory_number] = contribution
        fqe_values[trajectory_number] = state_values[indices[0]]

    dr_estimate = float(contributions.mean())
    dr_low, dr_high = _bootstrap_interval(contributions, bootstrap_samples, seed)
    wis_estimate, wis_low, wis_high = ope_weighted_importance_sampling(
        rewards,
        dones,
        behavior_probs,
        target_probs=target_probs,
        trajectory_ids=trajectory_ids,
        gamma=gamma,
        bootstrap_samples=bootstrap_samples,
        seed=seed,
    )
    return OPEMetrics(
        fqe_estimate=float(fqe_values.mean()),
        dr_estimate=dr_estimate,
        wis_estimate=wis_estimate,
        mean_reward=float(rewards.mean()),
        n_transitions=n,
        ci95_low=dr_low,
        ci95_high=dr_high,
        wis_ci95_low=wis_low,
        wis_ci95_high=wis_high,
        n_trajectories=len(trajectories),
    )


class OfflineEvaluator:
    """Evaluate a target policy using explicitly supplied nuisance predictions."""

    def __init__(self, agent: object, buffer: object, *, device: str = "cpu") -> None:
        self.agent = agent
        self.buffer = buffer
        self.device = device

    def evaluate(
        self,
        *,
        target_probs: np.ndarray,
        q_values: np.ndarray,
        state_values: np.ndarray,
        next_state_values: np.ndarray,
    ) -> OPEMetrics:
        """Run trajectory-aware WIS and DR on the buffer in logical order."""
        del self.agent
        data = self.buffer.as_ordered_dict()
        return ope_doubly_robust(
            data["states"],
            data["actions"],
            data["rewards"],
            data["next_states"],
            data["dones"],
            trajectory_ids=data["trajectory_ids"],
            behavior_probs=data["behavior_probs"],
            target_probs=target_probs,
            q_values=q_values,
            state_values=state_values,
            next_state_values=next_state_values,
            device=self.device,
        )
