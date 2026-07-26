"""Feature engineering for half-hour taxi-zone forecasting."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Sequence

import numpy as np
import pandas as pd

LAG_SLOTS = (1, 2, 48, 336)
ROLLING_WINDOWS = (3, 48, 336)
MIN_HISTORY_SLOTS = max(LAG_SLOTS + ROLLING_WINDOWS)
FEATURE_COLUMNS = [
    "zone_id",
    "weekday",
    "hour",
    "half_hour_bucket",
    "time_slot",
    "lag_demand_1",
    "lag_demand_2",
    "lag_demand_48",
    "lag_demand_336",
    "rolling_demand_mean_3",
    "rolling_demand_mean_48",
    "rolling_demand_mean_336",
    "neighbor_lag_demand_mean",
    "neighbor_lag_demand_std",
    "neighbor_lag_demand_max",
    "neighbor_mean_travel_minutes",
]


@dataclass(frozen=True)
class DemandPanel:
    """Complete half-hour-by-zone observations without temporal gaps."""

    timestamps: pd.DatetimeIndex
    demand: np.ndarray
    mean_fare: np.ndarray
    zone_count: int

    def __post_init__(self) -> None:
        expected = (len(self.timestamps), self.zone_count)
        if self.demand.shape != expected or self.mean_fare.shape != expected:
            raise ValueError(f"panel arrays must have shape {expected}")


def build_demand_panel(trips: pd.DataFrame, *, zone_count: int = 263) -> DemandPanel:
    """Aggregate cleaned trips into a complete causal forecasting panel."""
    required = {"tpep_pickup_datetime", "PULocationID", "fare_amount"}
    missing = sorted(required - set(trips.columns))
    if missing:
        raise ValueError(f"missing trip columns: {missing}")
    if zone_count <= 0:
        raise ValueError("zone_count must be positive")

    frame = trips.loc[:, sorted(required)].copy()
    frame["timestamp"] = pd.to_datetime(frame["tpep_pickup_datetime"]).dt.floor("30min")
    frame["zone_id"] = pd.to_numeric(frame["PULocationID"], errors="coerce")
    frame["fare_amount"] = pd.to_numeric(frame["fare_amount"], errors="coerce")
    frame = frame[
        frame["timestamp"].notna()
        & frame["zone_id"].between(1, zone_count)
        & frame["fare_amount"].notna()
    ]
    if frame.empty:
        raise ValueError("at least one valid trip is required")
    frame["zone_id"] = frame["zone_id"].astype(int)

    timestamps = pd.date_range(frame["timestamp"].min(), frame["timestamp"].max(), freq="30min")
    zones = pd.Index(range(1, zone_count + 1), name="zone_id")
    counts = (
        frame.groupby(["timestamp", "zone_id"], observed=True)
        .size()
        .unstack("zone_id")
        .reindex(index=timestamps, columns=zones, fill_value=0)
        .fillna(0)
    )
    fares = (
        frame.groupby(["timestamp", "zone_id"], observed=True)["fare_amount"]
        .mean()
        .unstack("zone_id")
        .reindex(index=timestamps, columns=zones)
    )
    return DemandPanel(
        timestamps=timestamps,
        demand=counts.to_numpy(dtype=np.float32),
        mean_fare=fares.to_numpy(dtype=np.float32),
        zone_count=zone_count,
    )


def build_neighbor_index(
    travel_times: Sequence[Sequence[float]] | np.ndarray,
    *,
    neighbor_count: int = 5,
) -> tuple[np.ndarray, np.ndarray]:
    """Return each zone's nearest reachable outgoing neighbors and mean time."""
    matrix = np.asarray(travel_times, dtype=float)
    if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1]:
        raise ValueError("travel_times must be a square matrix")
    zone_count = matrix.shape[0]
    if not 1 <= neighbor_count < zone_count:
        raise ValueError("neighbor_count must be in 1..zone_count-1")
    valid = np.isfinite(matrix) & (matrix >= 0.0)
    costs = np.where(valid, matrix, np.inf).copy()
    np.fill_diagonal(costs, np.inf)
    order = np.argsort(costs, axis=1, kind="stable")[:, :neighbor_count]
    selected = np.take_along_axis(costs, order, axis=1)
    reachable = np.isfinite(selected)
    order = np.where(reachable, order, zone_count)
    counts = reachable.sum(axis=1)
    mean_times = np.divide(
        np.where(reachable, selected, 0.0).sum(axis=1),
        counts,
        out=np.zeros(zone_count, dtype=float),
        where=counts > 0,
    )
    return order.astype(np.int16), mean_times.astype(np.float32)


def feature_block(
    timestamp: datetime | pd.Timestamp,
    demand_history: np.ndarray,
    neighbor_indices: np.ndarray,
    neighbor_mean_travel: np.ndarray,
) -> pd.DataFrame:
    """Build one timestamp's zone features from strictly earlier demand."""
    history = np.asarray(demand_history, dtype=float)
    if history.ndim != 2:
        raise ValueError("demand_history must be two-dimensional")
    if len(history) < MIN_HISTORY_SLOTS:
        raise ValueError(f"at least {MIN_HISTORY_SLOTS} history slots are required")
    zone_count = history.shape[1]
    if neighbor_indices.shape[0] != zone_count or neighbor_mean_travel.shape != (zone_count,):
        raise ValueError("neighbor features must match the demand zone dimension")

    target = pd.Timestamp(timestamp)
    lag_1 = history[-1]
    valid_neighbors = neighbor_indices < zone_count
    extended_lag = np.append(lag_1, 0.0)
    neighbor_values = extended_lag[neighbor_indices]
    neighbor_counts = valid_neighbors.sum(axis=1)
    neighbor_means = np.divide(
        neighbor_values.sum(axis=1),
        neighbor_counts,
        out=np.zeros(zone_count, dtype=float),
        where=neighbor_counts > 0,
    )
    centered = np.where(valid_neighbors, neighbor_values - neighbor_means[:, None], 0.0)
    neighbor_stds = np.sqrt(
        np.divide(
            np.square(centered).sum(axis=1),
            neighbor_counts,
            out=np.zeros(zone_count, dtype=float),
            where=neighbor_counts > 0,
        )
    )
    neighbor_max = np.where(valid_neighbors, neighbor_values, -np.inf).max(axis=1)
    neighbor_max[~np.isfinite(neighbor_max)] = 0.0
    result = pd.DataFrame(
        {
            "zone_id": np.arange(1, zone_count + 1, dtype=np.int16),
            "weekday": np.full(zone_count, target.weekday(), dtype=np.int8),
            "hour": np.full(zone_count, target.hour, dtype=np.int8),
            "half_hour_bucket": np.full(zone_count, target.minute // 30, dtype=np.int8),
            "time_slot": np.full(zone_count, target.hour * 2 + target.minute // 30, dtype=np.int8),
            "lag_demand_1": lag_1,
            "lag_demand_2": history[-2],
            "lag_demand_48": history[-48],
            "lag_demand_336": history[-336],
            "rolling_demand_mean_3": history[-3:].mean(axis=0),
            "rolling_demand_mean_48": history[-48:].mean(axis=0),
            "rolling_demand_mean_336": history[-336:].mean(axis=0),
            "neighbor_lag_demand_mean": neighbor_means,
            "neighbor_lag_demand_std": neighbor_stds,
            "neighbor_lag_demand_max": neighbor_max,
            "neighbor_mean_travel_minutes": neighbor_mean_travel,
        }
    )
    return result.loc[:, FEATURE_COLUMNS]


def build_supervised_frame(
    panel: DemandPanel,
    travel_times: Sequence[Sequence[float]] | np.ndarray,
    *,
    neighbor_count: int = 5,
) -> tuple[pd.DataFrame, np.ndarray, np.ndarray]:
    """Build supervised rows whose features contain no current/future target data."""
    neighbors, neighbor_times = build_neighbor_index(travel_times, neighbor_count=neighbor_count)
    blocks: list[pd.DataFrame] = []
    for index in range(MIN_HISTORY_SLOTS, len(panel.timestamps)):
        block = feature_block(panel.timestamps[index], panel.demand[:index], neighbors, neighbor_times)
        block.insert(0, "timestamp", panel.timestamps[index])
        block["target_demand"] = panel.demand[index]
        block["target_mean_fare"] = panel.mean_fare[index]
        blocks.append(block)
    if not blocks:
        raise ValueError("panel is too short to construct supervised features")
    return pd.concat(blocks, ignore_index=True), neighbors, neighbor_times


def temporal_split(frame: pd.DataFrame, *, validation_days: int = 4) -> tuple[pd.DataFrame, pd.DataFrame, pd.Timestamp]:
    """Split by absolute timestamps, reserving the final full days."""
    if validation_days <= 0:
        raise ValueError("validation_days must be positive")
    if frame.empty or "timestamp" not in frame:
        raise ValueError("frame must contain timestamped rows")
    maximum = pd.Timestamp(frame["timestamp"].max())
    split_time = maximum.normalize() - pd.Timedelta(days=validation_days - 1)
    train = frame[frame["timestamp"] < split_time].copy()
    validation = frame[frame["timestamp"] >= split_time].copy()
    if train.empty or validation.empty:
        raise ValueError("temporal split produced an empty partition")
    return train, validation, split_time
