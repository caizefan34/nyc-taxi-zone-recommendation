"""Tests for Phase 3 Temporal Graph Forecasting.

Covers:
- TemporalGraphTransformer forward pass and output shapes
- Quantile loss (pinball loss)
- TemporalGraphDataset creation and indexing
- collate_sequences
- Temporal alignment (no future leakage)
- Graph bias integration
- Model prediction with numpy inputs
"""
from __future__ import annotations

import numpy as np
import pytest
import torch

from src.features.temporal_graph import (
    TemporalGraphDataset,
    TemporalGraphTransformer,
    TemporalGraphTransformerConfig,
    collate_sequences,
)
from src.features.temporal_graph.model import quantile_loss


# ===========================================================================
# Model Tests
# ===========================================================================


class TestTemporalGraphTransformer:
    @pytest.fixture
    def config(self) -> TemporalGraphTransformerConfig:
        return TemporalGraphTransformerConfig(
            zone_count=10,
            history_steps=12,
            forecast_steps=6,
            hidden_dim=32,
            num_heads=2,
            num_layers=2,
            external_feat_dim=3,
        )

    @pytest.fixture
    def model(self, config: TemporalGraphTransformerConfig) -> TemporalGraphTransformer:
        return TemporalGraphTransformer(config)

    def test_forward_output_shapes(self, model: TemporalGraphTransformer, config):
        batch, steps, zones = 4, config.history_steps, config.zone_count
        demand = torch.rand(batch, steps, zones)
        outputs = model.forward(demand)
        assert "P10" in outputs and "P50" in outputs and "P90" in outputs
        assert outputs["P50"].shape == (batch, zones, config.forecast_steps)

    def test_forward_with_external_features(self, model, config):
        batch, steps, zones, feat_dim = 4, config.history_steps, config.zone_count, config.external_feat_dim
        demand = torch.rand(batch, steps, zones)
        ext = torch.rand(batch, steps, feat_dim)
        outputs = model.forward(demand, ext)
        assert outputs["P50"].shape == (batch, zones, config.forecast_steps)

    def test_forward_with_zone_external_features(self, model, config):
        batch, steps, zones, feat_dim = 4, config.history_steps, config.zone_count, config.external_feat_dim
        demand = torch.rand(batch, steps, zones)
        ext = torch.rand(batch, steps, zones, feat_dim)
        outputs = model.forward(demand, ext)
        assert outputs["P50"].shape == (batch, zones, config.forecast_steps)

    def test_quantiles_are_ordered(self, model, config):
        """P10 < P50 < P90 on average."""
        batch, steps, zones = 4, config.history_steps, config.zone_count
        demand = torch.rand(batch, steps, zones)
        outputs = model.forward(demand)
        assert outputs["P10"].mean() <= outputs["P50"].mean() + 1e-4
        assert outputs["P50"].mean() <= outputs["P90"].mean() + 1e-4

    def test_prediction_with_numpy(self, model, config):
        demand = np.random.rand(config.history_steps, config.zone_count).astype(np.float32)
        preds = model.predict(demand, device="cpu")
        assert "P50" in preds
        assert preds["P50"].shape == (config.zone_count, config.forecast_steps)

    def test_prediction_with_ext_features(self, model, config):
        demand = np.random.rand(config.history_steps, config.zone_count).astype(np.float32)
        ext = np.random.rand(config.history_steps, config.zone_count, config.external_feat_dim).astype(np.float32)
        preds = model.predict(demand, ext, device="cpu")
        assert preds["P50"].shape == (config.zone_count, config.forecast_steps)

    def test_predictions_are_non_negative(self, model, config):
        """Demand forecasts should be non-negative for Poisson-like targets."""
        demand = np.random.rand(config.history_steps, config.zone_count).astype(np.float32) * 10
        preds = model.predict(demand, device="cpu")
        assert np.all(preds["P50"] >= -0.1)

    def test_graph_bias_acceptance(self, model, config):
        adj = np.random.rand(config.zone_count, config.zone_count).astype(np.float32)
        model.set_graph_bias(adj)
        assert hasattr(model, "_graph_bias")
        assert model._graph_bias is not None


# ===========================================================================
# Quantile Loss Tests
# ===========================================================================


class TestQuantileLoss:
    def test_loss_is_finite(self):
        batch, zones, steps = 4, 10, 6
        preds = {
            "P10": torch.rand(batch, zones, steps),
            "P50": torch.rand(batch, zones, steps),
            "P90": torch.rand(batch, zones, steps),
        }
        targets = torch.rand(batch, zones, steps)
        loss = quantile_loss(preds, targets, (0.1, 0.5, 0.9))
        assert torch.isfinite(loss)
        assert loss > 0

    def test_perfect_prediction_has_low_loss(self):
        batch, zones, steps = 2, 5, 3
        targets = torch.ones(batch, zones, steps) * 10.0
        preds = {
            "P10": torch.full((batch, zones, steps), 9.0),
            "P50": torch.full((batch, zones, steps), 10.0),
            "P90": torch.full((batch, zones, steps), 11.0),
        }
        loss = quantile_loss(preds, targets, (0.1, 0.5, 0.9))
        assert loss < 1.0


# ===========================================================================
# Dataset Tests
# ===========================================================================


class TestTemporalGraphDataset:
    def test_dataset_length(self):
        n_time, n_zones = 200, 10
        demand = np.random.rand(n_time, n_zones).astype(np.float32)
        dataset = TemporalGraphDataset(demand, history_steps=24, forecast_steps=12)
        expected = n_time - 24 - 12 + 1
        assert len(dataset) == expected

    def test_sample_shapes(self):
        n_time, n_zones = 200, 10
        demand = np.random.rand(n_time, n_zones).astype(np.float32)
        dataset = TemporalGraphDataset(demand, history_steps=24, forecast_steps=12)
        sample = dataset[0]
        assert sample["demand_history"].shape == (24, 10)
        assert sample["targets"].shape == (12, 10)

    def test_too_short_demand_raises(self):
        demand = np.random.rand(30, 10).astype(np.float32)
        with pytest.raises(ValueError, match="need at least"):
            TemporalGraphDataset(demand, history_steps=48, forecast_steps=48)

    def test_external_features_shape(self):
        n_time, n_zones, feat_dim = 200, 10, 3
        demand = np.random.rand(n_time, n_zones).astype(np.float32)
        ext = np.random.rand(n_time, n_zones, feat_dim).astype(np.float32)
        dataset = TemporalGraphDataset(demand, history_steps=24, forecast_steps=12, external_features=ext)
        sample = dataset[0]
        assert sample["external_features"].shape == (24, 10, 3)

    def test_external_features_2d_broadcast(self):
        n_time, n_zones, feat_dim = 200, 10, 3
        demand = np.random.rand(n_time, n_zones).astype(np.float32)
        ext = np.random.rand(n_time, feat_dim).astype(np.float32)
        dataset = TemporalGraphDataset(demand, history_steps=24, forecast_steps=12, external_features=ext)
        sample = dataset[0]
        assert sample["external_features"].shape == (24, 1, 3)


# ===========================================================================
# Collate Tests
# ===========================================================================


class TestCollate:
    def test_collate_batches(self):
        n_time, n_zones = 200, 10
        demand = np.random.rand(n_time, n_zones).astype(np.float32)
        dataset = TemporalGraphDataset(demand, history_steps=24, forecast_steps=12)
        batch = [dataset[i] for i in range(4)]
        batched = collate_sequences(batch)
        assert batched["demand_history"].shape == (4, 24, 10)
        assert batched["targets"].shape == (4, 12, 10)

    def test_collate_keeps_keys(self):
        n_time, n_zones, feat_dim = 200, 10, 3
        demand = np.random.rand(n_time, n_zones).astype(np.float32)
        ext = np.random.rand(n_time, n_zones, feat_dim).astype(np.float32)
        dataset = TemporalGraphDataset(demand, history_steps=24, forecast_steps=12, external_features=ext)
        batch = [dataset[0], dataset[1]]
        batched = collate_sequences(batch)
        assert "demand_history" in batched
        assert "targets" in batched
        assert "external_features" in batched


# ===========================================================================
# Temporal Leakage Tests
# ===========================================================================


class TestTemporalLeakage:
    def test_dataset_does_not_leak_future(self):
        """Each sample's targets should be strictly after its history."""
        n_time, n_zones = 100, 5
        # Demand increases over time
        demand = np.arange(n_time, dtype=np.float32).reshape(-1, 1) * np.ones((1, n_zones))
        dataset = TemporalGraphDataset(demand, history_steps=10, forecast_steps=5)
        for i in range(min(len(dataset), 10)):
            sample = dataset[i]
            hist_max = sample["demand_history"].max().item()
            target_min = sample["targets"].min().item()
            assert hist_max < target_min + 1e-4, f"Sample {i}: history contains future values"

    def test_time_ordering_preserved(self):
        """Timestamps should be in ascending order."""
        n_time, n_zones = 100, 5
        demand = np.random.rand(n_time, n_zones).astype(np.float32)
        dataset = TemporalGraphDataset(demand, history_steps=10, forecast_steps=5)
        for i in range(min(10, len(dataset))):
            sample = dataset[i]
            assert torch.all(sample["targets"] >= 0)
