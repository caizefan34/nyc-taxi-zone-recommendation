"""Tests for enhanced OPE methods (WIS).
"""
from __future__ import annotations

import numpy as np

from src.rl.offline.evaluation import (
    OPEMetrics,
    ope_doubly_robust,
    ope_weighted_importance_sampling,
)


class TestWeightedImportanceSampling:
    def test_wis_with_uniform_probs(self):
        n = 500
        rewards = np.random.rand(n).astype(np.float32)
        dones = np.zeros(n, dtype=np.float32)
        dones[-1] = 1.0
        probs = np.ones(n, dtype=np.float32)
        est, lo, hi = ope_weighted_importance_sampling(rewards, dones, probs, bootstrap_samples=20)
        assert np.isfinite(est)
        assert lo <= est <= hi

    def test_wis_with_nonuniform_probs(self):
        n = 500
        rewards = np.random.rand(n).astype(np.float32)
        dones = np.zeros(n, dtype=np.float32)
        dones[-1] = 1.0
        probs = np.random.uniform(0.1, 1.0, n).astype(np.float32)
        est, lo, hi = ope_weighted_importance_sampling(rewards, dones, probs, bootstrap_samples=20)
        assert np.isfinite(est)

    def test_wis_no_probs_fallback(self):
        n = 500
        rewards = np.random.rand(n).astype(np.float32)
        dones = np.zeros(n, dtype=np.float32)
        est, lo, hi = ope_weighted_importance_sampling(rewards, dones, None, bootstrap_samples=20)
        assert np.isfinite(est)
        assert lo <= est <= hi

    def test_wis_identical_rewards(self):
        n = 100
        rewards = np.ones(n, dtype=np.float32) * 5.0
        dones = np.zeros(n, dtype=np.float32)
        dones[-1] = 1.0
        probs = np.ones(n, dtype=np.float32)
        est, lo, hi = ope_weighted_importance_sampling(rewards, dones, probs, gamma=0.99, bootstrap_samples=10)
        assert np.isfinite(est)


class TestOPEMetricsStruct:
    def test_ope_metrics_has_wis_field(self):
        n = 200
        states = np.random.rand(n, 4).astype(np.float32)
        actions = np.random.randint(0, 5, size=n).astype(np.float32)
        rewards = np.random.rand(n).astype(np.float32)
        next_states = np.random.rand(n, 4).astype(np.float32)
        dones = np.zeros(n, dtype=np.float32)

        result = ope_doubly_robust(states, actions, rewards, next_states, dones, bootstrap_samples=10)
        assert isinstance(result, OPEMetrics)
        assert hasattr(result, "wis_estimate")
        assert np.isfinite(result.wis_estimate)
        assert np.isfinite(result.dr_estimate)
        assert np.isfinite(result.fqe_estimate)

