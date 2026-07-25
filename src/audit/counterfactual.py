"""Logged-bandit off-policy estimators used by the research audit."""
from __future__ import annotations

import numpy as np


def _inputs(reward, target_probability, behavior_probability):
    reward = np.asarray(reward, dtype=float)
    target = np.asarray(target_probability, dtype=float)
    behavior = np.asarray(behavior_probability, dtype=float)
    if reward.shape != target.shape or reward.shape != behavior.shape or reward.ndim != 1:
        raise ValueError("reward and probabilities must be equal-length vectors")
    if len(reward) == 0 or np.any(behavior <= 0.0) or np.any(target < 0.0):
        raise ValueError("positive logged propensities and non-negative target probabilities are required")
    return reward, target / behavior


def ips(reward, target_probability, behavior_probability) -> float:
    """Inverse propensity score estimate E_mu[pi(a|x)/mu(a|x) r]."""
    reward, weight = _inputs(reward, target_probability, behavior_probability)
    return float(np.mean(weight * reward))


def snips(reward, target_probability, behavior_probability) -> float:
    """Self-normalized IPS estimate."""
    reward, weight = _inputs(reward, target_probability, behavior_probability)
    denominator = float(np.sum(weight))
    if denominator == 0.0:
        raise ValueError("target policy has zero support on all logged actions")
    return float(np.sum(weight * reward) / denominator)


def doubly_robust(
    reward,
    target_probability,
    behavior_probability,
    q_logged_action,
    q_target_policy,
) -> float:
    """Doubly robust contextual-bandit value estimate."""
    reward, weight = _inputs(reward, target_probability, behavior_probability)
    q_logged = np.asarray(q_logged_action, dtype=float)
    q_target = np.asarray(q_target_policy, dtype=float)
    if q_logged.shape != reward.shape or q_target.shape != reward.shape:
        raise ValueError("q estimates must match reward shape")
    return float(np.mean(q_target + weight * (reward - q_logged)))

