"""Chicago taxi adapter — implements CityAdapter for Chicago TNP data.

Chicago Transportation Network Provider (TNP) trip data is available from:
https://data.cityofchicago.org/Transportation/Transportation-Network-Providers-Trips/m6dm-c72p

Community areas (77) serve as zones, analogous to NYC's 263 taxi zones.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from src.cities.base import CityAdapter, MobilityTrip, MobilityZone


class ChicagoAdapter(CityAdapter):
    """Chicago TNP (ride-hail) adapter.

    Uses 77 Chicago community areas as mobility zones.
    Data: Transportation Network Providers Trips dataset.
    """

    @property
    def city_name(self) -> str:
        return "chicago"

    @property
    def zone_count(self) -> int:
        return 77

    def __init__(self, data_dir: str | Path | None = None):
        if data_dir is None:
            self._data_dir = Path(__file__).resolve().parents[3] / "data" / "chicago"
        else:
            self._data_dir = Path(data_dir)
        self._zones: Optional[list[MobilityZone]] = None

    def load_zones(self) -> list[MobilityZone]:
        if self._zones is not None:
            return self._zones
        # Chicago community areas (subset for reference)
        area_names = {
            1: "Rogers Park", 2: "West Ridge", 3: "Uptown", 4: "Lincoln Square",
            5: "North Center", 6: "Lake View", 7: "Lincoln Park", 8: "Near North Side",
            9: "Edison Park", 10: "Norwood Park",
            28: "Near West Side", 29: "North Lawndale", 30: "South Lawndale",
            31: "Lower West Side", 32: "Loop", 33: "Near South Side",
            61: "Hyde Park", 68: "Englewood", 76: "O'Hare", 77: "Edgewater",
        }
        zones = []
        for zid in range(1, 78):
            zones.append(MobilityZone(
                zone_id=zid,
                name=area_names.get(zid, f"Community Area {zid}"),
                borough="Chicago",
                zone_type="community_area",
            ))
        self._zones = zones
        return zones

    def load_trips(self, start_date: str, end_date: str) -> list[MobilityTrip]:
        """Load trips from Chicago TNP dataset.

        Requires data at data/chicago/tnp_trips.parquet.
        Returns empty list if data not available.
        """
        trips_path = self._data_dir / "tnp_trips.parquet"
        if not trips_path.exists():
            return []
        import pyarrow.parquet as pq
        trips = []
        for row in pq.read_table(trips_path).to_pylist():
            trips.append(MobilityTrip(
                pickup_zone=int(row.get("pickup_community_area", 1)),
                dropoff_zone=int(row.get("dropoff_community_area", 1)),
                pickup_time=row.get("trip_start_timestamp"),
                fare=float(row.get("fare", 0)) if row.get("fare") else None,
                distance=float(row.get("trip_miles", 0)) if row.get("trip_miles") else None,
                duration_minutes=float(row.get("trip_seconds", 0)) / 60 if row.get("trip_seconds") else None,
            ))
        return trips

    def aggregate_demand(self, trips: list[MobilityTrip]) -> dict:
        demand = {}
        for t in trips:
            demand[t.pickup_zone] = demand.get(t.pickup_zone, 0) + 1
        return {"pickup_counts": demand, "total_trips": len(trips)}

    def travel_time(self, from_zone: int, to_zone: int) -> float:
        """Estimate based on ~2 min per zone distance for Chicago scale."""
        distance = abs(to_zone - from_zone)
        return 3.0 + distance * 1.5

    def zone_from_coordinates(self, lat: float, lon: float) -> Optional[int]:
        """Naive zone mapping. Chicago community area boundaries need shapefiles."""
        zones = self.load_zones()
        # Simple heuristic: zone_id by lat range
        if lat < 41.7:
            return 76  # South side (O'Hare area)
        elif lat < 41.85:
            return 32  # Loop
        elif lat < 41.95:
            return 8   # Near North Side
        else:
            return 1   # Far North
