"""Leakage and shape tests for supervised forecasting features."""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.forecasting.features import (
    FEATURE_COLUMNS,
    DemandPanel,
    build_demand_panel,
    build_neighbor_index,
    build_supervised_frame,
    feature_block,
    temporal_split,
)


def test_build_demand_panel_fills_missing_slots_and_zones():
    trips = pd.DataFrame(
        {
            "tpep_pickup_datetime": ["2023-01-01 00:05", "2023-01-01 01:05"],
            "PULocationID": [1, 2],
            "fare_amount": [10.0, 20.0],
        }
    )
    panel = build_demand_panel(trips, zone_count=3)
    assert panel.demand.shape == (3, 3)
    assert panel.demand.tolist() == [[1.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 1.0, 0.0]]
    assert np.isnan(panel.mean_fare[1, 0])


def test_feature_block_uses_strictly_prior_demand():
    history = np.arange(337 * 3, dtype=float).reshape(337, 3)
    travel = np.array([[0.0, 1.0, 2.0], [1.0, 0.0, 2.0], [2.0, 1.0, 0.0]])
    neighbors, neighbor_times = build_neighbor_index(travel, neighbor_count=2)
    features = feature_block(pd.Timestamp("2023-01-08 00:30"), history, neighbors, neighbor_times)
    assert list(features) == FEATURE_COLUMNS
    assert np.array_equal(features["lag_demand_1"], history[-1])
    assert np.array_equal(features["lag_demand_336"], history[-336])
    assert np.allclose(features["rolling_demand_mean_3"], history[-3:].mean(axis=0))


def test_supervised_targets_do_not_enter_same_slot_features():
    timestamps = pd.date_range("2023-01-01", periods=338, freq="30min")
    demand = np.zeros((338, 3), dtype=float)
    demand[-1] = 999.0
    panel = DemandPanel(timestamps, demand, np.full_like(demand, np.nan), 3)
    travel = np.array([[0.0, 1.0, 2.0], [1.0, 0.0, 2.0], [2.0, 1.0, 0.0]])
    frame, _, _ = build_supervised_frame(panel, travel, neighbor_count=2)
    final = frame[frame["timestamp"] == timestamps[-1]]
    assert (final["target_demand"] == 999.0).all()
    assert (final["lag_demand_1"] == 0.0).all()


def test_temporal_split_is_strict_and_absolute():
    timestamps = pd.date_range("2023-01-08", periods=10 * 48, freq="30min")
    frame = pd.DataFrame({"timestamp": np.repeat(timestamps, 2), "zone_id": [1, 2] * len(timestamps)})
    train, validation, split = temporal_split(frame, validation_days=3)
    assert train["timestamp"].max() < split
    assert validation["timestamp"].min() == split
    assert set(train["timestamp"]).isdisjoint(set(validation["timestamp"]))


def test_neighbor_index_masks_unreachable_rows():
    travel = np.array([[0.0, np.inf], [1.0, 0.0]])
    neighbors, mean_times = build_neighbor_index(travel, neighbor_count=1)
    assert neighbors.tolist() == [[2], [0]]
    assert mean_times.tolist() == [0.0, 1.0]
