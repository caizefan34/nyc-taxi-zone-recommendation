"""External urban feature providers for taxi demand forecasting.

Provides timestamp-aligned features:
- Weather (temperature, precipitation, snowfall)
- Calendar (weekday, holiday, month, season)
- Airport activity (JFK/LGA)
- Event interface for custom events
"""
from __future__ import annotations

from .airport import JFK_ZONE_ID, LGA_ZONE_ID, AirportProvider
from .base import ExternalFeatureProvider, FeatureCollection, align_features
from .calendar import US_HOLIDAYS_BY_YEAR, CalendarProvider
from .composite import CompositeFeatureProvider
from .events import Event, EventProvider
from .weather import WeatherProvider

__all__ = [
    "ExternalFeatureProvider",
    "FeatureCollection",
    "align_features",
    "CalendarProvider",
    "US_HOLIDAYS_BY_YEAR",
    "WeatherProvider",
    "AirportProvider",
    "JFK_ZONE_ID",
    "LGA_ZONE_ID",
    "Event",
    "EventProvider",
    "CompositeFeatureProvider",
]
