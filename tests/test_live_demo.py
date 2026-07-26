"""Tests for live demo pipeline."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


class TestLiveDemo:
    """Test live demo pipeline components."""

    def test_build_features(self):
        """Feature construction should produce expected keys."""
        from scripts.run_live_demo import build_features
        features = build_features(237, 14, 2, 7)
        assert features["zone_id"] == 237
        assert features["hour"] == 14
        assert "half_hour_bucket" in features
        assert "lag_demand_1" in features

    def test_forecast_fallback(self):
        """Forecast should provide fallback values."""
        from scripts.run_live_demo import forecast_demand
        result = forecast_demand({"zone_id": 237, "lag_demand_1": 10, "lag_demand_2": 8})
        assert "predicted_pickups" in result
        assert result["predicted_pickups"] > 0

    def test_recommendation_structure(self):
        """Recommendation should produce valid output structure."""
        from scripts.run_live_demo import recommend_policy
        state = {
            "utilization": 0.8, "competition_level": "high",
            "zone_id": 237, "forecasted_demand": 15,
            "zone_capacity": 20, "n_available_drivers": 10,
        }
        result = recommend_policy(237, state)
        assert "recommendations" in result
        assert len(result["recommendations"]) == 3
        assert "expected_reward" in result
        assert "overall_utilization" in result

    def test_end_to_end(self):
        """Full pipeline should produce valid output."""
        from scripts.run_live_demo import run_inference
        result = run_inference(zone_id=237, hour=14, day_of_week=2, month=7)
        assert result["recommendation"]["strategy"] is not None
        assert len(result["recommendation"]["recommendations"]) == 3


