"""Tests for historical replay evaluation."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


class TestHistoricalReplay:
    """Test historical replay evaluation."""

    def test_replay_policy_structure(self):
        """Replay should return expected metrics."""
        from src.evaluation.historical_replay import replay_policy
        demand = [{"zone_id": 237, "hour": 14, "pickups": 10, "zone_capacity": 20, "avg_fare": 15.0}]
        result = replay_policy("test_policy", demand)
        assert result["policy"] == "test_policy"
        assert result["total_revenue"] > 0
        assert 0 <= result["utilization"] <= 1
        assert 0 <= result["demand_coverage"] <= 1

    def test_empty_demand(self):
        """Empty demand should not crash."""
        from src.evaluation.historical_replay import replay_policy
        result = replay_policy("test_policy", [])
        assert result["n_steps"] == 1  # fallback

    def test_sample_demand_generation(self):
        """Sample demand should produce valid records."""
        from src.evaluation.historical_replay import generate_sample_demand
        demand = generate_sample_demand()
        assert len(demand) > 0
        for d in demand:
            assert "zone_id" in d
            assert "hour" in d
            assert "pickups" in d
