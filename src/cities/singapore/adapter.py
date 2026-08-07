"""Singapore mobility adapter — implements CityAdapter for Singapore.

Uses Urban Redevelopment Authority (URA) planning areas (55).
Data sources: LTA (Land Transport Authority) open data, taxis, ride-hail.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional

from src.cities.base import CityAdapter, MobilityTrip, MobilityZone


class SingaporeAdapter(CityAdapter):
    """Singapore mobility adapter.

    Uses 55 URA planning areas as mobility zones.
    Data: LTA taxi/Grab/Gojek trip records.
    """

    @property
    def city_name(self) -> str:
        return "singapore"

    @property
    def zone_count(self) -> int:
        return 55

    def __init__(self, data_dir: str | Path | None = None):
        if data_dir is None:
            self._data_dir = Path(__file__).resolve().parents[3] / "data" / "singapore"
        else:
            self._data_dir = Path(data_dir)
        self._zones: Optional[list[MobilityZone]] = None

    def load_zones(self) -> list[MobilityZone]:
        if self._zones is not None:
            return self._zones
        planning_areas = {
            1: "Orchard", 2: "Downtown Core", 3: "Marina Bay",
            7: "Bukit Timah", 12: "Jurong East", 15: "Woodlands",
            20: "Tampines", 25: "Bedok", 28: "Changi",
            30: "Geylang", 35: "Kallang", 40: "Novena",
            45: "Queenstown", 50: "Hougang", 55: "Punggol",
        }
        zones = []
        for zid in range(1, 56):
            zones.append(MobilityZone(
                zone_id=zid,
                name=planning_areas.get(zid, f"Planning Area {zid}"),
                borough="Singapore",
                zone_type="planning_area",
                metadata={"country": "SG", "timezone": "Asia/Singapore"},
            ))
        self._zones = zones
        return zones

    def load_trips(self, start_date: str, end_date: str) -> list[MobilityTrip]:
        trips_path = self._data_dir / "taxi_trips.parquet"
        if not trips_path.exists():
            return []
        import pyarrow.parquet as pq
        trips = []
        for row in pq.read_table(trips_path).to_pylist():
            trips.append(MobilityTrip(
                pickup_zone=int(row.get("pickup_planning_area", 1)),
                dropoff_zone=int(row.get("dropoff_planning_area", 1)),
                pickup_time=row.get("pickup_datetime"),
                fare=float(row.get("total_fare_sgd", 0)) if row.get("total_fare_sgd") else None,
                distance=float(row.get("trip_distance_km", 0)) if row.get("trip_distance_km") else None,
                duration_minutes=float(row.get("trip_duration_min", 0)) if row.get("trip_duration_min") else None,
            ))
        return trips

    def aggregate_demand(self, trips: list[MobilityTrip]) -> dict:
        demand = {}
        for t in trips:
            demand[t.pickup_zone] = demand.get(t.pickup_zone, 0) + 1
        return {"pickup_counts": demand, "total_trips": len(trips)}

    def travel_time(self, from_zone: int, to_zone: int) -> float:
        """Singapore is compact — zones are ~5 min apart."""
        distance = abs(to_zone - from_zone)
        return 3.0 + distance * 1.2

    def zone_from_coordinates(self, lat: float, lon: float) -> Optional[int]:
        """Map lat/lon to planning area (approximate, Singapore is ~1.35N)."""
        if lat > 1.40:
            return 15  # North (Woodlands)
        elif lat > 1.35:
            return 30  # Central (Geylang/Kallang)
        elif lat > 1.30:
            return 1   # Downtown Core/Orchard
        else:
            return 45  # South (Queenstown)
