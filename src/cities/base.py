"""Cross-city abstraction layer — generalize beyond NYC.

Defines:
- MobilityDataset: unified data ingestion interface
- MobilityZone: city-agnostic zone definition
- MobilityTrip: city-agnostic trip record
- CityAdapter: interface for city-specific implementations

NYC is the reference implementation. Future cities:
- Chicago, London, Singapore, etc.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class MobilityZone:
    """City-agnostic zone definition."""
    zone_id: int
    name: str
    borough: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    zone_type: Optional[str] = None
    metadata: dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class MobilityTrip:
    """City-agnostic trip record."""
    trip_id: Optional[str] = None
    pickup_zone: int = 0
    dropoff_zone: int = 0
    pickup_time: Optional[datetime] = None
    dropoff_time: Optional[datetime] = None
    fare: Optional[float] = None
    distance: Optional[float] = None
    duration_minutes: Optional[float] = None
    passenger_count: Optional[int] = None
    metadata: dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class CityAdapter(ABC):
    """Interface for city-specific data and configuration.

    Each city implements:
    - zone definitions
    - trip ingestion
    - demand aggregation
    - travel time estimation
    - geospatial mapping
    """

    @property
    @abstractmethod
    def city_name(self) -> str:
        """Unique city identifier (e.g., 'nyc', 'chicago', 'london')."""
        ...

    @property
    @abstractmethod
    def zone_count(self) -> int:
        """Total number of mobility zones."""
        ...

    @abstractmethod
    def load_zones(self) -> list[MobilityZone]:
        """Load zone definitions."""
        ...

    @abstractmethod
    def load_trips(self, start_date: str, end_date: str) -> list[MobilityTrip]:
        """Load trip records for a date range."""
        ...

    @abstractmethod
    def aggregate_demand(self, trips: list[MobilityTrip]) -> dict:
        """Aggregate demand by zone and time slot."""
        ...

    @abstractmethod
    def travel_time(self, from_zone: int, to_zone: int) -> float:
        """Estimate travel time between two zones (minutes)."""
        ...

    @abstractmethod
    def zone_from_coordinates(self, lat: float, lon: float) -> Optional[int]:
        """Map coordinates to zone ID."""
        ...
