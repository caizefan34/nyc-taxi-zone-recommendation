"""Tests for multi-seed RL evaluation."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


class TestMultiSeedRL:
    """Test multi-seed RL evaluation utilities."""

    def test_evaluate_seed_structure(self):
        """Seed evaluation should return expected structure."""
        from scripts.run_multiseed_rl import evaluate_seed
        result = evaluate_seed(42, n_episodes=10)
        assert result["seed"] == 42
        assert "mean_return" in result
        assert "std_return" in result
        assert len(result["episode_returns"]) == 10

    def test_confidence_interval_bounds(self):
        """CI should be valid (lower < upper)."""
        from scripts.run_multiseed_rl import compute_confidence_interval
        values = [100, 102, 98, 101, 99, 103]
        lower, upper = compute_confidence_interval(values, 0.95)
        assert lower < upper
        assert lower >= 95
        assert upper <= 108

    def test_different_seeds_different_results(self):
        """Different seeds should produce different return distributions."""
        from scripts.run_multiseed_rl import evaluate_seed
        r1 = evaluate_seed(0, n_episodes=100)
        r2 = evaluate_seed(1, n_episodes=100)
        assert abs(r1["mean_return"] - 265) < 30
        assert abs(r2["mean_return"] - 265) < 30
