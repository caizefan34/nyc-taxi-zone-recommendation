"""Tests for external model interfaces."""
from __future__ import annotations

import numpy as np
import pytest

from src.interfaces import ForecastModel, Policy, RLPolicy


class DummyForecastModel(ForecastModel):
    """Concrete ForecastModel for testing."""

    def predict(self, features: dict) -> dict:
        return {"prediction": 28.0, "model_name": "dummy_forecast"}

    def evaluate(self) -> tuple[np.ndarray, np.ndarray]:
        y_true = np.random.rand(100)
        y_pred = np.random.rand(100)
        return y_true, y_pred


class DummyPolicy(Policy):
    """Concrete Policy for testing."""

    def act(self, state: dict) -> list[dict]:
        return [
            {"zone_id": 237, "expected_reward": 45.2, "pickup_prob": 0.72},
        ]

    def evaluate(self) -> dict[str, float]:
        return {"revenue_per_driver": 1768.04, "utilization": 0.44}


class DummyRLPolicy(RLPolicy):
    """Concrete RLPolicy for testing."""

    def act(self, state: np.ndarray) -> int:
        return 0

    def evaluate(self, num_episodes: int = 10) -> list[float]:
        return [100.0 * (i + 1) for i in range(num_episodes)]


class TestForecastModelInterface:
    """Test ForecastModel interface."""

    def test_predict_returns_dict(self):
        model = DummyForecastModel()
        result = model.predict({"zone_id": 237, "hour": 14})
        assert isinstance(result, dict)
        assert "prediction" in result

    def test_evaluate_returns_tuple(self):
        model = DummyForecastModel()
        y_true, y_pred = model.evaluate()
        assert isinstance(y_true, np.ndarray)
        assert isinstance(y_pred, np.ndarray)
        assert y_true.shape == y_pred.shape


class TestPolicyInterface:
    """Test Policy interface."""

    def test_act_returns_list_of_dicts(self):
        policy = DummyPolicy()
        result = policy.act({"zone_id": 237, "hour": 14})
        assert isinstance(result, list)
        assert len(result) > 0
        assert "zone_id" in result[0]
        assert "expected_reward" in result[0]

    def test_evaluate_returns_metrics(self):
        policy = DummyPolicy()
        metrics = policy.evaluate()
        assert "revenue_per_driver" in metrics
        assert "utilization" in metrics


class TestRLPolicyInterface:
    """Test RLPolicy interface."""

    def test_act_returns_int(self):
        policy = DummyRLPolicy()
        action = policy.act(np.random.rand(10))
        assert isinstance(action, int)

    def test_evaluate_returns_returns(self):
        policy = DummyRLPolicy()
        returns = policy.evaluate(num_episodes=5)
        assert isinstance(returns, list)
        assert len(returns) == 5
        assert all(isinstance(r, float) for r in returns)


class TestAbstractEnforcement:
    """Test that abstract methods enforce implementation."""

    def test_forecast_model_abstract(self):
        with pytest.raises(TypeError):
            ForecastModel()

    def test_policy_abstract(self):
        with pytest.raises(TypeError):
            Policy()

    def test_rl_policy_abstract(self):
        with pytest.raises(TypeError):
            RLPolicy()
