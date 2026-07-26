"""Calendar-based features: weekday, holiday, month, season.

Holiday data is built-in for 2022–2025 US federal holidays.
No external download required.
"""
from __future__ import annotations

from datetime import datetime, timedelta

import numpy as np
import pandas as pd

from .base import ExternalFeatureProvider, FeatureCollection

# US Federal Holidays 2022-2025
US_HOLIDAYS_BY_YEAR: dict[int, list[tuple[str, int, int]]] = {
    2022: [
        ("New Year", 1, 1),
        ("Martin Luther King Jr. Day", 1, 17),
        ("Presidents Day", 2, 21),
        ("Memorial Day", 5, 30),
        ("Juneteenth", 6, 20),
        ("Independence Day", 7, 4),
        ("Labor Day", 9, 5),
        ("Columbus Day", 10, 10),
        ("Veterans Day", 11, 11),
        ("Thanksgiving", 11, 24),
        ("Christmas", 12, 25),
    ],
    2023: [
        ("New Year", 1, 1),
        ("Martin Luther King Jr. Day", 1, 16),
        ("Presidents Day", 2, 20),
        ("Memorial Day", 5, 29),
        ("Juneteenth", 6, 19),
        ("Independence Day", 7, 4),
        ("Labor Day", 9, 4),
        ("Columbus Day", 10, 9),
        ("Veterans Day", 11, 11),
        ("Thanksgiving", 11, 23),
        ("Christmas", 12, 25),
    ],
    2024: [
        ("New Year", 1, 1),
        ("Martin Luther King Jr. Day", 1, 15),
        ("Presidents Day", 2, 19),
        ("Memorial Day", 5, 27),
        ("Juneteenth", 6, 19),
        ("Independence Day", 7, 4),
        ("Labor Day", 9, 2),
        ("Columbus Day", 10, 14),
        ("Veterans Day", 11, 11),
        ("Thanksgiving", 11, 28),
        ("Christmas", 12, 25),
    ],
    2025: [
        ("New Year", 1, 1),
        ("Martin Luther King Jr. Day", 1, 20),
        ("Presidents Day", 2, 17),
        ("Memorial Day", 5, 26),
        ("Juneteenth", 6, 19),
        ("Independence Day", 7, 4),
        ("Labor Day", 9, 1),
        ("Columbus Day", 10, 13),
        ("Veterans Day", 11, 11),
        ("Thanksgiving", 11, 27),
        ("Christmas", 12, 25),
    ],
}

SEASON_MAP = {12: 0, 1: 0, 2: 0, 3: 1, 4: 1, 5: 1, 6: 2, 7: 2, 8: 2, 9: 3, 10: 3, 11: 3}
"""Month → season (0=Winter, 1=Spring, 2=Summer, 3=Fall)."""


class CalendarProvider(ExternalFeatureProvider):
    """Provider for calendar-based features.

    Features:
    - `weekday`: 0=Monday, 6=Sunday
    - `is_holiday`: 1 if US federal holiday, else 0
    - `is_weekend`: 1 if Saturday or Sunday
    - `month`: 1-12
    - `season`: 0=Winter, 1=Spring, 2=Summer, 3=Fall
    - `day_of_year`: 1-366
    - `days_since_holiday`: days since last US federal holiday
    - `days_until_holiday`: days until next US federal holiday
    """

    def __init__(self) -> None:
        super().__init__()
        self._holiday_dates: dict[datetime, str] = {}
        for year, holidays in US_HOLIDAYS_BY_YEAR.items():
            for name, month, day in holidays:
                dt = datetime(year, month, day)
                self._holiday_dates[dt] = name
                # Add observed day if holiday falls on weekend
                if dt.weekday() == 5:  # Saturday
                    self._holiday_dates[dt - timedelta(days=1)] = f"{name} (observed)"
                elif dt.weekday() == 6:  # Sunday
                    self._holiday_dates[dt + timedelta(days=1)] = f"{name} (observed)"

    @property
    def name(self) -> str:
        return "calendar"

    def get_features(
        self,
        start: str | datetime | pd.Timestamp,
        end: str | datetime | pd.Timestamp,
    ) -> FeatureCollection:
        timestamps = self._half_hour_grid(start, end)
        n = len(timestamps)

        weekday = np.zeros(n, dtype=np.int8)
        is_holiday = np.zeros(n, dtype=np.int8)
        is_weekend = np.zeros(n, dtype=np.int8)
        month = np.zeros(n, dtype=np.int8)
        season = np.zeros(n, dtype=np.int8)
        day_of_year = np.zeros(n, dtype=np.int16)
        days_since_holiday = np.full(n, 365, dtype=np.float32)
        days_until_holiday = np.full(n, 365, dtype=np.float32)

        sorted_holiday_dates = sorted(self._holiday_dates.keys())

        for i, ts in enumerate(timestamps):
            weekday[i] = ts.weekday()
            is_weekend[i] = 1 if ts.weekday() >= 5 else 0
            month[i] = ts.month
            season[i] = SEASON_MAP.get(ts.month, 0)
            day_of_year[i] = ts.timetuple().tm_yday

            ts_date = ts.date()
            ts_dt = datetime(ts_date.year, ts_date.month, ts_date.day)

            # Holiday check
            if ts_dt in self._holiday_dates:
                is_holiday[i] = 1

            # Distance to nearest holiday
            for hol_dt in sorted_holiday_dates:
                diff_days = (hol_dt - ts_dt).days
                if diff_days >= 0:
                    days_until_holiday[i] = float(diff_days)
                    break

            for hol_dt in reversed(sorted_holiday_dates):
                diff_days = (ts_dt - hol_dt).days
                if diff_days >= 0:
                    days_since_holiday[i] = float(diff_days)
                    break

        return FeatureCollection(
            timestamps=timestamps,
            data={
                "weekday": weekday,
                "is_holiday": is_holiday,
                "is_weekend": is_weekend,
                "month": month,
                "season": season,
                "day_of_year": day_of_year,
                "days_since_holiday": days_since_holiday,
                "days_until_holiday": days_until_holiday,
            },
        )
