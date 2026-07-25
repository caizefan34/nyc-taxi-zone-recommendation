"""Unified data loading utilities."""
from __future__ import annotations

import csv
import math
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq

from src.common.config import get_config


class DataLoader:
    """Centralized data loader for all project data.
    
    Eliminates duplicate loading code across modules.
    
    Attributes:
        project_root: Root directory of the project.
        zone_count: Number of taxi zones (default 263).
        slot_count: Number of time slots per day (default 48).
    """

    def __init__(self, project_root: str | Path | None = None) -> None:
        """Initialize DataLoader.
        
        Args:
            project_root: Project root directory. If None, auto-detected.
        """
        if project_root is None:
            self.project_root = Path(__file__).resolve().parents[2]
        else:
            self.project_root = Path(project_root)

        self.zone_count: int = get_config("data.zone_count", 263)
        self.slot_count: int = get_config("data.slot_count", 48)
        self.week_slot_count: int = 7 * self.slot_count

    def load_zone_statistics(
        self,
        statistics_path: str | Path | None = None,
    ) -> tuple[list[list[list[float]]], list[list[list[float]]]]:
        """Load zone-level demand and fare statistics.
        
        Args:
            statistics_path: Path to zone_time_statistics.parquet.
                If None, uses default location.
        
        Returns:
            Tuple of (demand, mean_fare) where each is indexed as
            [weekday][slot][zone_index].
        """
        if statistics_path is None:
            statistics_path = self.project_root / "data/processed/zone_time_statistics.parquet"

        demand = [[[0.0] * self.zone_count for _ in range(self.slot_count)] for _ in range(7)]
        mean_fare = [[[0.0] * self.zone_count for _ in range(self.slot_count)] for _ in range(7)]

        columns = [
            "pickup_location_id",
            "weekday",
            "time_slot",
            "pickup_count",
            "mean_fare_amount",
        ]

        for row in pq.read_table(statistics_path, columns=columns).to_pylist():
            location_id = int(row["pickup_location_id"])
            weekday = int(row["weekday"])
            time_slot = int(row["time_slot"])

            if not 1 <= location_id <= self.zone_count:
                continue

            index = location_id - 1
            demand[weekday][time_slot][index] = float(row["pickup_count"])

            raw_fare = row["mean_fare_amount"]
            if raw_fare is not None and math.isfinite(float(raw_fare)):
                mean_fare[weekday][time_slot][index] = max(0.0, float(raw_fare))

        return demand, mean_fare

    def load_travel_time_matrix(
        self,
        travel_time_path: str | Path | None = None,
    ) -> list[list[float]]:
        """Load Dijkstra travel time matrix.
        
        Args:
            travel_time_path: Path to travel_time_matrix_dijkstra.csv.
                If None, uses default location.
        
        Returns:
            263x263 matrix where matrix[i][j] is travel time from zone i+1 to zone j+1.
        
        Raises:
            ValueError: If matrix dimensions are invalid.
        """
        if travel_time_path is None:
            travel_time_path = self.project_root / "data/processed/travel_time_matrix_dijkstra.csv"

        with Path(travel_time_path).open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.reader(handle)
            header = next(reader)

            if len(header) != self.zone_count + 1:
                raise ValueError(
                    f"Travel-time matrix must have {self.zone_count} destination columns, "
                    f"got {len(header) - 1}"
                )

            matrix = []
            for expected_origin, row in enumerate(reader, start=1):
                if int(row[0]) != expected_origin or len(row) != self.zone_count + 1:
                    raise ValueError(f"Invalid travel-time matrix row {expected_origin}")
                matrix.append([float(value) for value in row[1:]])

        if len(matrix) != self.zone_count:
            raise ValueError(
                f"Travel-time matrix must have {self.zone_count} origin rows, "
                f"got {len(matrix)}"
            )

        return matrix

    def load_train_data(
        self,
        train_path: str | Path | None = None,
        columns: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Load cleaned training data.
        
        Args:
            train_path: Path to train_cleaned.parquet.
                If None, uses default location.
            columns: Columns to load. If None, loads all.
        
        Returns:
            List of row dictionaries.
        """
        if train_path is None:
            train_path = self.project_root / "data/processed/train_cleaned.parquet"

        return pq.read_table(train_path, columns=columns).to_pylist()

    @staticmethod
    def next_half_hour(value: datetime) -> datetime:
        """Round up to the next half-hour boundary.
        
        Args:
            value: Input datetime.
        
        Returns:
            Datetime rounded up to next :00 or :30.
        
        Examples:
            >>> DataLoader.next_half_hour(datetime(2023, 1, 15, 8, 15))
            datetime.datetime(2023, 1, 15, 8, 30)
            >>> DataLoader.next_half_hour(datetime(2023, 1, 15, 8, 30))
            datetime.datetime(2023, 1, 15, 9, 0)
        """
        slot_start = value.replace(
            minute=(value.minute // 30) * 30,
            second=0,
            microsecond=0,
        )
        return slot_start + timedelta(minutes=30)

    def datetime_to_state(self, dt: datetime) -> int:
        """Convert datetime to state index.
        
        Args:
            dt: Input datetime.
        
        Returns:
            State index in [0, 336) where state = weekday * 48 + slot.
        """
        target = self.next_half_hour(dt)
        slot = target.hour * 2 + target.minute // 30
        weekday = target.weekday()
        return weekday * self.slot_count + slot
