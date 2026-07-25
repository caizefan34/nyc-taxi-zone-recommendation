
import pytest

from src.common.config import get_config, load_config, reload_config


class TestConfig:
    """Tests for configuration system."""

    def test_load_config(self):
        config = load_config()
        assert config is not None
        assert "project" in config
        assert config["project"]["name"] == "NYC Taxi Zone Recommendation"

    def test_get_config_domain(self):
        assert get_config("domain.zone_count", 263) == 263
        assert get_config("domain.slot_count", 48) == 48
        assert get_config("domain.week_slot_count", 336) == 336

    def test_get_config_algorithm(self):
        gamma = get_config("algorithm.gamma", 0.5)
        assert gamma is not None
        assert isinstance(gamma, float)

    def test_get_config_default(self):
        assert get_config("nonexistent.key", "default") == "default"
        assert get_config("nonexistent.key") is None

    def test_get_config_qlearning(self):
        seed = get_config("qlearning.seed", 20230722)
        assert seed is not None

    def test_config_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            load_config("nonexistent.yaml")

    def test_reload_config(self):
        config = reload_config()
        assert config is not None
        assert "project" in config
