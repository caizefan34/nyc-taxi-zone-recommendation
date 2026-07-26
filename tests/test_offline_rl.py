"""Tests for Phase 5: Offline RL pipeline.

Covers:
- OfflineBuffer add/sample/collect
- IQLAgent initialization and update
- Expectile loss computation
- OPE (FQE, Doubly Robust)
- IQL training loop
"""
from __future__ import annotations

import numpy as np
import pytest
import torch

from src.rl.offline import IQLAgent, IQLConfig, OfflineBuffer
from src.rl.offline.evaluation import OPEMetrics, ope_doubly_robust, ope_fqe
from src.rl.offline.iql import _expectile_loss


# ===========================================================================
# Buffer Tests
# ===========================================================================


class TestOfflineBuffer:
    def test_add_and_sample(self):
        buf = OfflineBuffer(capacity=100, state_dim=4)
        for i in range(50):
            buf.add(
                np.random.rand(4), i % 10, float(np.random.rand()),
                np.random.rand(4), bool(i % 5 == 0),
            )
        assert buf.size == 50
        batch = buf.sample(10)
        assert batch["states"].shape == (10, 4)
        assert batch["actions"].shape == (10,)
        assert batch["rewards"].shape == (10,)

    def test_circular_overwrite(self):
        buf = OfflineBuffer(capacity=10, state_dim=2)
        for i in range(20):
            buf.add(np.zeros(2), 0, 1.0, np.zeros(2), False)
        assert buf.size == 10

    def test_sample_raises_when_empty(self):
        buf = OfflineBuffer(capacity=10, state_dim=2)
        with pytest.raises(ValueError, match="buffer has"):
            buf.sample(5)

    def test_fraction_filled(self):
        buf = OfflineBuffer(capacity=100, state_dim=2)
        for i in range(50):
            buf.add(np.zeros(2), 0, 1.0, np.zeros(2), False)
        assert abs(buf.fraction_filled - 0.5) < 0.01

    def test_clear_resets(self):
        buf = OfflineBuffer(capacity=10, state_dim=2)
        for i in range(5):
            buf.add(np.zeros(2), 0, 1.0, np.zeros(2), False)
        buf.clear()
        assert buf.size == 0


# ===========================================================================
# IQL Tests
# ===========================================================================


class TestIQLAgent:
    @pytest.fixture
    def agent(self) -> IQLAgent:
        return IQLAgent(state_dim=4, action_dim=5, device="cpu")

    @pytest.fixture
    def batch(self):
        return {
            "states": torch.rand(16, 4),
            "actions": torch.randint(0, 5, (16,)),
            "rewards": torch.rand(16),
            "next_states": torch.rand(16, 4),
            "dones": torch.zeros(16),
        }

    def test_initialization(self, agent):
        assert agent.state_dim == 4
        assert agent.action_dim == 5

    def test_update_returns_losses(self, agent, batch):
        info = agent.update(batch)
        assert "q_loss" in info
        assert "v_loss" in info
        assert np.isfinite(info["q_loss"])
        assert np.isfinite(info["v_loss"])

    def test_loss_decreases_over_time(self, agent, batch):
        losses = []
        for _ in range(20):
            info = agent.update(batch)
            losses.append(info["q_loss"])
        assert losses[-1] <= losses[0] + 0.1, "Loss should not increase"

    def test_get_q_values(self, agent):
        s = torch.rand(4, 4)
        a = torch.rand(4, 1)
        q = agent.get_q_values(s, a)
        assert q.shape == (4, 1)
        assert torch.isfinite(q).all()

    def test_get_value(self, agent):
        s = torch.rand(4, 4)
        v = agent.get_value(s)
        assert v.shape == (4, 1)

    def test_score_actions(self, agent):
        state = np.random.rand(4).astype(np.float32)
        candidates = np.array([0, 1, 2, 3])
        scores = agent.score_actions(state, candidates)
        assert scores.shape == (4,)
        assert np.all(np.isfinite(scores))

    def test_save_load(self, agent, tmp_path):
        p = tmp_path / "iql.pt"
        agent.save(str(p))
        assert p.exists()
        agent2 = IQLAgent(state_dim=4, action_dim=5, device="cpu")
        agent2.load(str(p))
        s = torch.rand(4, 4)
        assert torch.allclose(agent.get_value(s), agent2.get_value(s))


# ===========================================================================
# Expectile Loss Tests
# ===========================================================================


class TestExpectileLoss:
    def test_expectile_loss_is_finite(self):
        pred = torch.rand(10)
        target = torch.rand(10)
        loss = _expectile_loss(pred, target, 0.7)
        assert torch.isfinite(loss)

    def test_expectile_tau_05_equals_mse(self):
        pred = torch.randn(100)
        target = torch.randn(100)
        exp_loss = _expectile_loss(pred, target, 0.5)
        mse_loss = torch.nn.functional.mse_loss(pred, target)
        # tau=0.5 expectile loss = 0.5 * MSE (inherent weighting)
        assert abs(exp_loss.item() * 2 - mse_loss.item()) < 1e-4

    def test_perfect_prediction_zero_loss(self):
        target = torch.ones(10)
        loss = _expectile_loss(target, target, 0.7)
        assert loss.item() < 1e-6


# ===========================================================================
# OPE Tests
# ===========================================================================


class TestOPE:
    def test_fqe_returns_finite(self):
        n = 100
        states = np.random.rand(n, 4).astype(np.float32)
        actions = np.random.randint(0, 5, size=n).astype(np.float32)
        rewards = np.random.rand(n).astype(np.float32)
        next_states = np.random.rand(n, 4).astype(np.float32)
        dones = np.zeros(n, dtype=np.float32)

        val = ope_fqe(states, actions, rewards, next_states, dones, epochs=10)
        assert np.isfinite(val)

    def test_doubly_robust_returns_metrics(self):
        n = 200
        states = np.random.rand(n, 4).astype(np.float32)
        actions = np.random.randint(0, 5, size=n).astype(np.float32)
        rewards = np.random.rand(n).astype(np.float32)
        next_states = np.random.rand(n, 4).astype(np.float32)
        dones = np.zeros(n, dtype=np.float32)

        result = ope_doubly_robust(states, actions, rewards, next_states, dones, bootstrap_samples=10)
        assert isinstance(result, OPEMetrics)
        assert np.isfinite(result.fqe_estimate)
        assert np.isfinite(result.dr_estimate)
        assert np.isfinite(result.ci95_low)
        assert result.ci95_low <= result.ci95_high


# ===========================================================================
# Training Loop Test
# ===========================================================================


class TestIQLTraining:
    def test_train_iql_runs(self):
        agent = IQLAgent(state_dim=4, action_dim=5, device="cpu")
        buf = OfflineBuffer(capacity=500, state_dim=4)
        for i in range(300):
            buf.add(
                np.random.rand(4), i % 5, float(np.random.rand()),
                np.random.rand(4), bool(i % 10 == 0),
            )
        from src.rl.offline.iql import train_iql
        metrics = train_iql(agent, buf, steps=50, log_interval=25)
        assert "q_loss" in metrics
        assert "v_loss" in metrics
        assert len(metrics["q_loss"]) > 0
