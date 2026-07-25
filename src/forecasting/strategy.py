"""Recommendation strategy backed by timestamped supervised forecasts."""
from __future__ import annotations

import math
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

from src.common.data_loader import DataLoader


class ForecastingRecommender:
    """Rank zones by predicted demand, expected fare, and relocation time."""

    def __init__(
        self,
        predictions_path: Path,
        *,
        project_root: Path | None = None,
        travel_times: np.ndarray | None = None,
    ) -> None:
        root = project_root or Path(__file__).resolve().parents[2]
        table = pq.read_table(
            predictions_path,
            columns=["timestamp", "zone_id", "predicted_demand_count", "predicted_expected_fare"],
        ).to_pandas()
        table["timestamp"] = pd.to_datetime(table["timestamp"])
        if table.duplicated(["timestamp", "zone_id"]).any():
            raise ValueError("forecast predictions must be unique by timestamp and zone")
        if travel_times is None:
            loader = DataLoader(root)
            self.zone_count = loader.zone_count
            self.travel_time = np.asarray(loader.load_travel_time_matrix(), dtype=float)
        else:
            self.travel_time = np.asarray(travel_times, dtype=float)
            if self.travel_time.ndim != 2 or self.travel_time.shape[0] != self.travel_time.shape[1]:
                raise ValueError("travel_times must be a square matrix")
            self.zone_count = self.travel_time.shape[0]
        self.forecasts: dict[pd.Timestamp, tuple[np.ndarray, np.ndarray]] = {}
        for timestamp, group in table.groupby("timestamp", sort=True):
            ordered = group.set_index("zone_id").reindex(range(1, self.zone_count + 1))
            if ordered[["predicted_demand_count", "predicted_expected_fare"]].isna().any().any():
                raise ValueError(f"forecast timestamp {timestamp} is missing zones")
            self.forecasts[pd.Timestamp(timestamp)] = (
                ordered["predicted_demand_count"].to_numpy(dtype=float),
                ordered["predicted_expected_fare"].to_numpy(dtype=float),
            )

    def recommend(self, current_datetime: datetime, current_location_id: int) -> list[int]:
        if not isinstance(current_datetime, datetime):
            raise TypeError("current_datetime must be a datetime")
        if not 1 <= current_location_id <= self.zone_count:
            raise ValueError(f"current_location_id must be in 1..{self.zone_count}")
        target = pd.Timestamp(DataLoader.next_half_hour(current_datetime))
        try:
            demand, fare = self.forecasts[target]
        except KeyError as error:
            raise KeyError(f"no forecast is available for {target}") from error
        times = self.travel_time[current_location_id - 1]
        scores = np.full(self.zone_count, -math.inf, dtype=float)
        reachable = np.isfinite(times) & (times >= 0.0)
        scores[reachable] = demand[reachable] * fare[reachable] / (times[reachable] + 1.0)
        ordered = np.lexsort((np.arange(self.zone_count), -scores))[:3]
        return (ordered + 1).tolist()
