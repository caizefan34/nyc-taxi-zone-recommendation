"""NYC taxi zone adapter — implements CityAdapter for NYC TLC data."""
from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from typing import Optional

import numpy as np

from src.cities.base import CityAdapter, MobilityTrip, MobilityZone
from src.common.data_loader import DataLoader


class NYCAdapter(CityAdapter):
    """NYC Yellow Taxi adapter using TLC data."""

    @property
    def city_name(self) -> str:
        return "nyc"

    @property
    def zone_count(self) -> int:
        return 263

    def __init__(self, data_dir: str | Path | None = None):
        if data_dir is None:
            self._data_dir = Path(__file__).resolve().parents[3] / "data"
        else:
            self._data_dir = Path(data_dir)
        self._loader = DataLoader()
        self._zones: Optional[list[MobilityZone]] = None

    def load_zones(self) -> list[MobilityZone]:
        if self._zones is not None:
            return self._zones

        lookup_path = self._data_dir / "meta" / "taxi_zone_lookup.csv"
        zones = []
        if lookup_path.exists():
            with open(lookup_path, "r", encoding="utf-8-sig") as f:
                for row in csv.DictReader(f):
                    zones.append(MobilityZone(
                        zone_id=int(row["LocationID"]),
                        name=row["Zone"],
                        borough=row.get("Borough"),
                        latitude=float(row["Latitude"]) if row.get("Latitude") else None,
                        longitude=float(row["Longitude"]) if row.get("Longitude") else None,
                        zone_type=row.get("service_zone"),
                    ))
        self._zones = zones
        return zones

    def load_trips(self, start_date: str, end_date: str) -> list[MobilityTrip]:
        """Load trips from processed training data."""
        trips = []
        try:
            train_path = self._data_dir / "processed" / "train_cleaned.parquet"
            if not train_path.exists():
                return trips
            import pyarrow.parquet as pq
            for row in pq.read_table(
                train_path,
                columns=["pickup_datetime", "PULocationID", "DOLocationID",
                         "fare_amount", "trip_distance", "trip_duration", "passenger_count"],
            ).to_pylist():
                pickup = row.get("pickup_datetime")
                if isinstance(pickup, (int, float)):
                    pickup = datetime.fromtimestamp(pickup / 1000.0)
                trips.append(MobilityTrip(
                    pickup_zone=int(row["PULocationID"]),
                    dropoff_zone=int(row["DOLocationID"]),
                    pickup_time=pickup if isinstance(pickup, datetime) else None,
                    fare=float(row.get("fare_amount", 0)),
                    distance=float(row.get("trip_distance", 0)),
                    duration_minutes=float(row.get("trip_duration", 0)),
                    passenger_count=int(row.get("passenger_count", 0)) if row.get("passenger_count") else None,
                ))
        except Exception:
            pass
        return trips

    def aggregate_demand(self, trips: list[MobilityTrip]) -> dict:
        """Aggregate demand by zone (count of pickups)."""
        demand = {}
        for t in trips:
            demand[t.pickup_zone] = demand.get(t.pickup_zone, 0) + 1
        return {"pickup_counts": demand, "total_trips": len(trips)}

    def travel_time(self, from_zone: int, to_zone: int) -> float:
        """Travel time from Dijkstra matrix."""
        try:
            matrix = self._loader.load_travel_time_matrix()
            return float(matrix[from_zone - 1][to_zone - 1])
        except Exception:
            return float("inf")

    def zone_from_coordinates(self, lat: float, lon: float) -> Optional[int]:
        """Naive nearest-zone mapping by centroid distance."""
        zones = self.load_zones()
        best_zone = None
        best_dist = float("inf")
        for z in zones:
            if z.latitude and z.longitude:
                d = np.sqrt((lat - z.latitude) ** 2 + (lon - z.longitude) ** 2)
                if d < best_dist:
                    best_dist = d
                    best_zone = z.zone_id
        return best_zone
