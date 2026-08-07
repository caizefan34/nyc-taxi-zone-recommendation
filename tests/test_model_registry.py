"""Tests for the model registry."""
from __future__ import annotations

from src.monitoring.registry import (
    ModelMetadata,
    ModelRegistry,
    compute_config_hash,
)


class TestModelMetadata:
    def test_creation(self):
        meta = ModelMetadata(
            model_name="lightgbm_demand",
            model_version="1.0.0",
            model_type="forecasting",
            training_dataset="train_cleaned.parquet",
            training_timestamp="2023-01-25",
            config_hash="abc123",
            metrics={"mae": 1.51},
        )
        assert meta.model_name == "lightgbm_demand"
        assert meta.metrics["mae"] == 1.51

    def test_to_dict(self):
        meta = ModelMetadata(
            model_name="test",
            model_version="0.1",
            model_type="policy",
            training_dataset="data.parquet",
            training_timestamp="2023-01-01",
        )
        d = meta.to_dict()
        assert d["model_name"] == "test"
        assert d["registered_at"]  # auto-generated


class TestModelRegistry:
    def test_register_and_get(self, tmp_path):
        registry = ModelRegistry(registry_dir=tmp_path)
        meta = ModelMetadata(
            model_name="test_model",
            model_version="1.0.0",
            model_type="forecasting",
            training_dataset="data.parquet",
            training_timestamp="2023-01-01",
            metrics={"mae": 1.5},
        )
        registry.register(meta)
        retrieved = registry.get("test_model", "1.0.0")
        assert retrieved is not None
        assert retrieved["model_name"] == "test_model"
        assert retrieved["metrics"]["mae"] == 1.5

    def test_list_models(self, tmp_path):
        registry = ModelRegistry(registry_dir=tmp_path)
        meta = ModelMetadata(
            model_name="m1",
            model_version="1.0",
            model_type="forecasting",
            training_dataset="d1",
            training_timestamp="t1",
        )
        registry.register(meta)
        models = registry.list_models()
        assert len(models) == 1
        assert models[0]["model_name"] == "m1"

    def test_list_by_type(self, tmp_path):
        registry = ModelRegistry(registry_dir=tmp_path)
        registry.register(ModelMetadata(
            model_name="forecast_1", model_version="1.0",
            model_type="forecasting", training_dataset="d", training_timestamp="t",
        ))
        registry.register(ModelMetadata(
            model_name="policy_1", model_version="1.0",
            model_type="policy", training_dataset="d", training_timestamp="t",
        ))
        assert len(registry.list_models("forecasting")) == 1
        assert len(registry.list_models("policy")) == 1
        assert len(registry.list_models()) == 2

    def test_get_nonexistent(self, tmp_path):
        registry = ModelRegistry(registry_dir=tmp_path)
        assert registry.get("nonexistent") is None


class TestConfigHash:
    def test_deterministic(self):
        config = {"a": 1, "b": [2, 3]}
        h1 = compute_config_hash(config)
        h2 = compute_config_hash(config)
        assert h1 == h2

    def test_different_configs(self):
        h1 = compute_config_hash({"a": 1})
        h2 = compute_config_hash({"a": 2})
        assert h1 != h2
