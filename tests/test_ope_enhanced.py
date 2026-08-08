"""Tests for trajectory-aware offline policy evaluation."""
from __future__ import annotations

import numpy as np
import pytest

from src.rl.offline.evaluation import OPEMetrics, ope_doubly_robust, ope_weighted_importance_sampling


def _two_trajectories():
    rewards = np.array([1.0, 2.0, 3.0, 4.0])
    dones = np.array([0.0, 1.0, 0.0, 1.0])
    trajectory_ids = np.array([10, 10, 20, 20])
    return rewards, dones, trajectory_ids


class TestWeightedImportanceSampling:
    def test_on_policy_matches_mean_discounted_return(self):
        rewards, dones, trajectory_ids = _two_trajectories()
        probs = np.full(4, 0.5)
        estimate, low, high = ope_weighted_importance_sampling(
            rewards,
            dones,
            probs,
            target_probs=probs,
            trajectory_ids=trajectory_ids,
            gamma=0.5,
            bootstrap_samples=200,
        )
        assert estimate == pytest.approx(((1 + 0.5 * 2) + (3 + 0.5 * 4)) / 2)
        assert low <= estimate <= high

    def test_off_policy_uses_target_over_behavior_ratio(self):
        rewards = np.array([1.0, 9.0])
        dones = np.ones(2)
        ids = np.array([0, 1])
        behavior = np.array([0.5, 0.5])
        target = np.array([1.0, 0.0])
        estimate, _, _ = ope_weighted_importance_sampling(
            rewards,
            dones,
            behavior,
            target_probs=target,
            trajectory_ids=ids,
            bootstrap_samples=20,
        )
        assert estimate == pytest.approx(1.0)

    @pytest.mark.parametrize("missing", ["behavior", "target", "trajectory"])
    def test_requires_identifiable_propensities(self, missing):
        rewards, dones, ids = _two_trajectories()
        kwargs = {"behavior_probs": np.ones(4), "target_probs": np.ones(4), "trajectory_ids": ids}
        kwargs[{"behavior": "behavior_probs", "target": "target_probs", "trajectory": "trajectory_ids"}[missing]] = None
        with pytest.raises(ValueError, match="requires"):
            ope_weighted_importance_sampling(rewards, dones, **kwargs)

    def test_rejects_invalid_behavior_probability(self):
        rewards, dones, ids = _two_trajectories()
        with pytest.raises(ValueError, match="behavior probabilities"):
            ope_weighted_importance_sampling(
                rewards,
                dones,
                np.array([1.0, 0.0, 1.0, 1.0]),
                target_probs=np.ones(4),
                trajectory_ids=ids,
            )

    def test_requires_terminal_trajectory_boundaries(self):
        rewards, dones, ids = _two_trajectories()
        dones[1] = 0
        with pytest.raises(ValueError, match="done=True"):
            ope_weighted_importance_sampling(
                rewards, dones, np.ones(4), target_probs=np.ones(4), trajectory_ids=ids
            )

    def test_bootstrap_is_reproducible(self):
        rewards, dones, ids = _two_trajectories()
        args = (rewards, dones, np.ones(4))
        kwargs = {"target_probs": np.ones(4), "trajectory_ids": ids, "bootstrap_samples": 50, "seed": 7}
        assert ope_weighted_importance_sampling(*args, **kwargs) == ope_weighted_importance_sampling(*args, **kwargs)


class TestDoublyRobust:
    def test_hand_computable_on_policy_estimate(self):
        rewards, dones, ids = _two_trajectories()
        zeros = np.zeros(4)
        result = ope_doubly_robust(
            np.zeros((4, 1)),
            np.zeros(4),
            rewards,
            np.zeros((4, 1)),
            dones,
            trajectory_ids=ids,
            behavior_probs=np.ones(4),
            target_probs=np.ones(4),
            q_values=zeros,
            state_values=zeros,
            next_state_values=zeros,
            gamma=0.5,
            bootstrap_samples=100,
        )
        assert isinstance(result, OPEMetrics)
        assert result.dr_estimate == pytest.approx(3.5)
        assert result.wis_estimate == pytest.approx(3.5)
        assert result.n_trajectories == 2
        assert result.ci95_low <= result.dr_estimate <= result.ci95_high
        assert result.wis_ci95_low <= result.wis_estimate <= result.wis_ci95_high

    def test_perfect_nuisance_model_has_zero_correction(self):
        rewards = np.array([2.0, 4.0])
        dones = np.ones(2)
        result = ope_doubly_robust(
            np.zeros((2, 1)),
            np.zeros(2),
            rewards,
            np.zeros((2, 1)),
            dones,
            trajectory_ids=np.array([0, 1]),
            behavior_probs=np.ones(2),
            target_probs=np.ones(2),
            q_values=rewards,
            state_values=rewards,
            next_state_values=np.zeros(2),
            bootstrap_samples=20,
        )
        assert result.dr_estimate == pytest.approx(3.0)
        assert result.fqe_estimate == pytest.approx(3.0)

    def test_requires_target_policy_nuisance_predictions(self):
        rewards, dones, ids = _two_trajectories()
        with pytest.raises(ValueError, match="q_values"):
            ope_doubly_robust(
                np.zeros((4, 1)),
                np.zeros(4),
                rewards,
                np.zeros((4, 1)),
                dones,
                trajectory_ids=ids,
                behavior_probs=np.ones(4),
                target_probs=np.ones(4),
            )

    def test_single_trajectory_interval_degenerates_honestly(self):
        result = ope_doubly_robust(
            np.zeros((1, 1)),
            np.zeros(1),
            np.array([5.0]),
            np.zeros((1, 1)),
            np.ones(1),
            trajectory_ids=np.array([0]),
            behavior_probs=np.ones(1),
            target_probs=np.ones(1),
            q_values=np.zeros(1),
            state_values=np.zeros(1),
            next_state_values=np.zeros(1),
            bootstrap_samples=20,
        )
        assert result.ci95_low == result.ci95_high == 5.0
