"""Tests for city abstraction layer."""
from __future__ import annotations

from src.cities.base import CityAdapter, MobilityTrip, MobilityZone


class TestMobilityZone:
    def test_creation(self):
        zone = MobilityZone(zone_id=1, name="Test Zone", borough="Manhattan")
        assert zone.zone_id == 1
        assert zone.name == "Test Zone"
        assert zone.borough == "Manhattan"
        assert zone.metadata == {}

    def test_defaults(self):
        zone = MobilityZone(zone_id=1, name="Test")
        assert zone.latitude is None
        assert zone.metadata == {}


class TestMobilityTrip:
    def test_creation(self):
        trip = MobilityTrip(
            pickup_zone=161,
            dropoff_zone=132,
            fare=15.50,
            distance=2.3,
        )
        assert trip.pickup_zone == 161
        assert trip.dropoff_zone == 132
        assert trip.fare == 15.50
        assert trip.metadata == {}

    def test_defaults(self):
        trip = MobilityTrip(pickup_zone=1, dropoff_zone=2)
        assert trip.pickup_time is None
        assert trip.fare is None


class TestCityAdapter:
    def test_abstract(self):
        """Verify CityAdapter is abstract."""
        try:
            CityAdapter()
            assert False, "Should not be instantiable"
        except TypeError:
            pass  # Expected — ABC cannot be instantiated
