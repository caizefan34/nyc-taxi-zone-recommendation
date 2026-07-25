"""Tests for parameter selection module."""
from src.common.config import load_config


class TestParameterSelection:
    """Tests for parameter selection configuration."""
    def test_config_has_parameter_grid(self):
        config = load_config()
        grid = config.get("parameter_grid", {})
        assert "lambda_values" in grid
        assert "gamma_values" in grid
    def test_lambda_values_valid(self):
        config = load_config()
        lambdas = config["parameter_grid"]["lambda_values"]
        assert isinstance(lambdas, list)
        for v in lambdas:
            assert v > 0
    def test_gamma_values_valid(self):
        config = load_config()
        gammas = config["parameter_grid"]["gamma_values"]
        assert isinstance(gammas, list)
        for v in gammas:
            assert 0 < v < 1
