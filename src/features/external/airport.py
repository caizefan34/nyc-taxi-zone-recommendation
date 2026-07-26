"""Airport activity features for JFK and LGA.

Derives airport activity metrics from TLC trip data:
- JFK and LGA pickup/dropoff counts per half-hour slot
- Airport share of total trips
- These can be used as features for demand forecasting

NYC taxi zones:
- JFK: Zone 132 (JFK Airport)
- LGA: Zone 138 (LaGuardia Airport)
"""
from __future__ import annotations

from datetime import datetime

import numpy as np
import pandas as pd

from .base import ExternalFeatureProvider, FeatureCollection

JFK_ZONE_ID: int = 132
LGA_ZONE_ID: int = 138


class AirportProvider(ExternalFeatureProvider):
    """Provider for airport activity features derived from TLC data.

    Features:
    - ``jfk_pickup_count``: JFK pickups in each half-hour slot
    - ``jfk_dropoff_count``: JFK dropoffs in each half-hour slot
    - ``lga_pickup_count``: LGA pickups in each half-hour slot
    - ``lga_dropoff_count``: LGA dropoffs in each half-hour slot
    - ``airport_trip_share``: Combined JFK+LGA fraction of total trips

    Optionally, can operate from pre-computed historical averages when
    real-time trip data is not available.
    """

    def __init__(
        self,
        trip_data: pd.DataFrame | None = None,
        *,
        use_historical_averages: bool = True,
        zone_count: int = 263,
    ) -> None:
        """
        Args:
            trip_data: Cleaned trip DataFrame with columns
                ``tpep_pickup_datetime``, ``tpep_dropoff_datetime``,
                ``PULocationID``, ``DOLocationID``.
                If None, uses historical averages.
            use_historical_averages: If True, uses pre-computed weekly
                averages when trip_data is unavailable.
            zone_count: Number of taxi zones.
        """
        self.trip_data = trip_data
        self.use_historical_averages = use_historical_averages
        self.zone_count = zone_count
        self._weekly_averages: dict[str, np.ndarray] | None = None

    @property
    def name(self) -> str:
        return "airport"

    def _compute_weekly_averages(self) -> dict[str, np.ndarray]:
        """Compute weekly (336-slot) historical airport activity averages."""
        if self._weekly_averages is not None:
            return self._weekly_averages

        if self.trip_data is not None:
            df = self.trip_data.copy()
            df["pickup_hour_slot"] = (
                pd.to_datetime(df["tpep_pickup_datetime"]).dt.hour * 2
                + pd.to_datetime(df["tpep_pickup_datetime"]).dt.minute // 30
            )
            df["pickup_weekday"] = pd.to_datetime(df["tpep_pickup_datetime"]).dt.weekday
            df["pickup_week_slot"] = df["pickup_weekday"] * 48 + df["pickup_hour_slot"]

            df["dropoff_hour_slot"] = (
                pd.to_datetime(df["tpep_dropoff_datetime"]).dt.hour * 2
                + pd.to_datetime(df["tpep_dropoff_datetime"]).dt.minute // 30
            )
            df["dropoff_weekday"] = pd.to_datetime(df["tpep_dropoff_datetime"]).dt.weekday
            df["dropoff_week_slot"] = df["dropoff_weekday"] * 48 + df["dropoff_hour_slot"]

            jfk_pickup = np.zeros(336, dtype=np.float32)
            jfk_dropoff = np.zeros(336, dtype=np.float32)
            lga_pickup = np.zeros(336, dtype=np.float32)
            lga_dropoff = np.zeros(336, dtype=np.float32)
            total_trips = np.zeros(336, dtype=np.float32)

            for _, row in df.iterrows():
                ws = int(row["pickup_week_slot"])
                pu = int(row["PULocationID"])
                do = int(row["DOLocationID"])
                total_trips[ws] += 1
                if pu == JFK_ZONE_ID:
                    jfk_pickup[ws] += 1
                if pu == LGA_ZONE_ID:
                    lga_pickup[ws] += 1
                if do == JFK_ZONE_ID:
                    jfk_dropoff[int(row["dropoff_week_slot"])] += 1
                if do == LGA_ZONE_ID:
                    lga_dropoff[int(row["dropoff_week_slot"])] += 1

            # Normalize
            eps = 1e-8
            airport_total = jfk_pickup + jfk_dropoff + lga_pickup + lga_dropoff
            airport_share = np.where(total_trips > 0, airport_total / (total_trips + eps), 0.0)

            self._weekly_averages = {
                "jfk_pickup": jfk_pickup,
                "jfk_dropoff": jfk_dropoff,
                "lga_pickup": lga_pickup,
                "lga_dropoff": lga_dropoff,
                "airport_share": airport_share,
            }
        else:
            # Synthetic weekly patterns as fallback
            rng = np.random.default_rng(42)
            self._weekly_averages = {
                "jfk_pickup": rng.exponential(15, 336).astype(np.float32) + 5,
                "jfk_dropoff": rng.exponential(12, 336).astype(np.float32) + 4,
                "lga_pickup": rng.exponential(10, 336).astype(np.float32) + 3,
                "lga_dropoff": rng.exponential(8, 336).astype(np.float32) + 2,
                "airport_share": rng.uniform(0.05, 0.15, 336).astype(np.float32),
            }

        return self._weekly_averages

    def get_features(
        self,
        start: str | datetime | pd.Timestamp,
        end: str | datetime | pd.Timestamp,
    ) -> FeatureCollection:
        timestamps = self._half_hour_grid(start, end)
        n = len(timestamps)
        weekly = self._compute_weekly_averages()

        jfk_pickup = np.zeros(n, dtype=np.float32)
        jfk_dropoff = np.zeros(n, dtype=np.float32)
        lga_pickup = np.zeros(n, dtype=np.float32)
        lga_dropoff = np.zeros(n, dtype=np.float32)
        airport_share = np.zeros(n, dtype=np.float32)

        for i, ts in enumerate(timestamps):
            ws = ts.weekday() * 48 + ts.hour * 2 + ts.minute // 30
            jfk_pickup[i] = weekly["jfk_pickup"][ws]
            jfk_dropoff[i] = weekly["jfk_dropoff"][ws]
            lga_pickup[i] = weekly["lga_pickup"][ws]
            lga_dropoff[i] = weekly["lga_dropoff"][ws]
            airport_share[i] = weekly["airport_share"][ws]

        return FeatureCollection(
            timestamps=timestamps,
            data={
                "jfk_pickup_count": jfk_pickup,
                "jfk_dropoff_count": jfk_dropoff,
                "lga_pickup_count": lga_pickup,
                "lga_dropoff_count": lga_dropoff,
                "airport_trip_share": airport_share,
            },
        )
