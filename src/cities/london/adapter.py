"""London transport adapter — implements CityAdapter for London.

London uses Boroughs (33) as primary zones.
Data sources: TfL (Transport for London) open data, Uber Movement.

Trip data from TfL taxi/PHV (Private Hire Vehicle) records.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from src.cities.base import CityAdapter, MobilityTrip, MobilityZone

LONDON_BOROUGHS = {
    1: "City of London", 2: "Westminster", 3: "Camden", 4: "Islington",
    5: "Hackney", 6: "Tower Hamlets", 7: "Greenwich", 8: "Lewisham",
    9: "Southwark", 10: "Lambeth", 11: "Wandsworth", 12: "Hammersmith and Fulham",
    13: "Kensington and Chelsea", 14: "Brent", 15: "Ealing", 16: "Hounslow",
    17: "Richmond upon Thames", 18: "Kingston upon Thames", 19: "Merton",
    20: "Sutton", 21: "Croydon", 22: "Bromley", 23: "Bexley",
    24: "Havering", 25: "Barking and Dagenham", 26: "Redbridge",
    27: "Newham", 28: "Waltham Forest", 29: "Haringey", 30: "Enfield",
    31: "Barnet", 32: "Harrow", 33: "Hillingdon",
}


class LondonAdapter(CityAdapter):
    """London TfL PHV/taxi adapter.

    Uses 33 London boroughs as mobility zones.
    Data: TfL PHV trip records, Uber Movement data.
    """

    @property
    def city_name(self) -> str:
        return "london"

    @property
    def zone_count(self) -> int:
        return 33

    def __init__(self, data_dir: str | Path | None = None):
        if data_dir is None:
            self._data_dir = Path(__file__).resolve().parents[3] / "data" / "london"
        else:
            self._data_dir = Path(data_dir)
        self._zones: Optional[list[MobilityZone]] = None

    def load_zones(self) -> list[MobilityZone]:
        if self._zones is not None:
            return self._zones
        zones = []
        for zid in range(1, 34):
            zones.append(MobilityZone(
                zone_id=zid,
                name=LONDON_BOROUGHS.get(zid, f"Borough {zid}"),
                borough=LONDON_BOROUGHS.get(zid, "Unknown"),
                zone_type="borough",
            ))
        self._zones = zones
        return zones

    def load_trips(self, start_date: str, end_date: str) -> list[MobilityTrip]:
        """Load trips from TfL/PHV dataset.

        Requires data at data/london/phv_trips.parquet.
        Returns empty list if data not available.
        """
        trips_path = self._data_dir / "phv_trips.parquet"
        if not trips_path.exists():
            return []
        import pyarrow.parquet as pq
        trips = []
        for row in pq.read_table(trips_path).to_pylist():
            trips.append(MobilityTrip(
                pickup_zone=int(row.get("pickup_borough", 1)),
                dropoff_zone=int(row.get("dropoff_borough", 1)),
                pickup_time=row.get("pickup_datetime"),
                fare=float(row.get("total_fare_gbp", 0)) if row.get("total_fare_gbp") else None,
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
        """Estimate based on Euclidean borough adjacency distance."""
        distance = abs(to_zone - from_zone)
        return 5.0 + distance * 2.0

    def zone_from_coordinates(self, lat: float, lon: float) -> Optional[int]:
        """Map lat/lon to borough (approximate)."""
        # Central London: 51.507, -0.128
        if lat > 51.56:
            return 31  # North London (Barnet/Enfield)
        elif lat > 51.52:
            return 1   # Central (City/Westminster)
        elif lat > 51.47:
            return 9   # South (Southwark)
        else:
            return 21  # Far South (Croydon)
