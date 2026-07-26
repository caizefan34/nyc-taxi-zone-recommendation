"""Tests for Phase 2 external urban features.

Covers:
- FeatureCollection validation and alignment
- CalendarProvider (holidays, weekday, season)
- WeatherProvider (temperature, precipitation, snowfall)
- AirportProvider (JFK/LGA activity)
- EventProvider (event count, impact)
- CompositeFeatureProvider (merging)
- align_features utility
"""

from __future__ import annotations

from datetime import datetime

import numpy as np
import pandas as pd
import pytest

from src.features.external import (
    AirportProvider,
    CalendarProvider,
    CompositeFeatureProvider,
    Event,
    EventProvider,
    FeatureCollection,
    WeatherProvider,
    align_features,
)

# ===========================================================================
# FeatureCollection Tests
# ===========================================================================


class TestFeatureCollection:
    def test_creation_and_access(self):
        timestamps = pd.date_range("2023-01-01", periods=4, freq="30min")
        data = {"feat_a": np.array([1.0, 2.0, 3.0, 4.0])}
        fc = FeatureCollection(timestamps=timestamps, data=data)
        assert fc.n_timestamps == 4
        assert "feat_a" in fc.feature_names

    def test_non_monotonic_timestamps_raises(self):
        timestamps = pd.DatetimeIndex([datetime(2023, 1, 3), datetime(2023, 1, 1)])
        with pytest.raises(ValueError, match="monotonically"):
            FeatureCollection(timestamps=timestamps, data={"a": np.array([1.0, 2.0])})

    def test_mismatched_length_raises(self):
        timestamps = pd.date_range("2023-01-01", periods=3, freq="30min")
        with pytest.raises(ValueError, match="rows"):
            FeatureCollection(timestamps=timestamps, data={"a": np.array([1.0, 2.0])})

    def test_to_dataframe_flat_features(self):
        timestamps = pd.date_range("2023-01-01", periods=2, freq="30min")
        fc = FeatureCollection(
            timestamps=timestamps,
            data={"temp": np.array([30.0, 35.0]), "humid": np.array([0.5, 0.6])},
        )
        df = fc.to_dataframe()
        assert list(df.columns) == ["timestamp", "temp", "humid"]
        assert len(df) == 2


# ===========================================================================
# CalendarProvider Tests
# ===========================================================================


class TestCalendarProvider:
    def test_provider_name(self):
        provider = CalendarProvider()
        assert provider.name == "calendar"

    def test_weekday_feature(self):
        provider = CalendarProvider()
        features = provider.get_features("2023-01-02", "2023-01-03")  # Monday
        assert features.data["weekday"][0] == 0  # Monday

    def test_weekend_feature(self):
        provider = CalendarProvider()
        features = provider.get_features("2023-01-07", "2023-01-08")  # Saturday
        assert features.data["is_weekend"][0] == 1

    def test_holiday_detection(self):
        provider = CalendarProvider()
        features = provider.get_features("2022-12-25", "2022-12-26")  # Christmas
        assert features.data["is_holiday"][0] == 1

    def test_season_feature(self):
        provider = CalendarProvider()
        features = provider.get_features("2023-06-01", "2023-06-02")  # Summer
        assert features.data["season"][0] == 2  # Summer

    def test_month_feature(self):
        provider = CalendarProvider()
        features = provider.get_features("2023-12-01", "2023-12-02")
        assert features.data["month"][0] == 12

    def test_timestamp_alignment(self):
        provider = CalendarProvider()
        features = provider.get_features("2023-01-01", "2023-01-02")
        assert len(features.timestamps) == 48  # 24 hours * 2 half-hours
        assert features.timestamps[0].hour == 0
        assert features.timestamps[0].minute == 0

    def test_non_overlapping_range_raises(self):
        provider = CalendarProvider()
        with pytest.raises(ValueError, match="before end"):
            provider.get_features("2023-01-02", "2023-01-01")


# ===========================================================================
# WeatherProvider Tests
# ===========================================================================


class TestWeatherProvider:
    def test_provider_name(self):
        provider = WeatherProvider(auto_download=False)
        assert provider.name == "weather"

    def test_weather_features_have_expected_keys(self, tmp_path):
        provider = WeatherProvider(cache_path=tmp_path / "weather.parquet", auto_download=True)
        features = provider.get_features("2023-01-01", "2023-01-02")
        expected_keys = {
            "temperature",
            "precipitation",
            "snowfall",
            "snow_depth",
            "is_extreme_heat",
            "is_extreme_cold",
            "is_heavy_precip",
        }
        assert expected_keys.issubset(set(features.data.keys()))

    def test_temperature_is_finite(self, tmp_path):
        provider = WeatherProvider(cache_path=tmp_path / "weather.parquet", auto_download=True)
        features = provider.get_features("2023-06-01", "2023-06-03")
        assert np.all(np.isfinite(features.data["temperature"]))

    def test_extreme_flags_are_binary(self, tmp_path):
        provider = WeatherProvider(cache_path=tmp_path / "weather.parquet", auto_download=True)
        features = provider.get_features("2023-01-01", "2023-01-08")
        for key in ["is_extreme_heat", "is_extreme_cold", "is_heavy_precip"]:
            assert set(np.unique(features.data[key])).issubset({0, 1})


# ===========================================================================
# AirportProvider Tests
# ===========================================================================


class TestAirportProvider:
    def test_provider_name(self):
        provider = AirportProvider()
        assert provider.name == "airport"

    def test_airport_features_have_expected_keys(self):
        provider = AirportProvider()
        features = provider.get_features("2023-01-01", "2023-01-02")
        expected_keys = {
            "jfk_pickup_count",
            "jfk_dropoff_count",
            "lga_pickup_count",
            "lga_dropoff_count",
            "airport_trip_share",
        }
        assert expected_keys.issubset(set(features.data.keys()))

    def test_values_are_non_negative(self):
        provider = AirportProvider()
        features = provider.get_features("2023-06-01", "2023-06-03")
        for key in features.data:
            assert np.all(features.data[key] >= 0), f"{key} has negative values"

    def test_airport_share_between_0_and_1(self):
        provider = AirportProvider()
        features = provider.get_features("2023-01-01", "2023-01-08")
        share = features.data["airport_trip_share"]
        assert np.all(share >= 0.0) and np.all(share <= 1.0)


# ===========================================================================
# EventProvider Tests
# ===========================================================================


class TestEventProvider:
    def test_provider_name(self):
        provider = EventProvider()
        assert provider.name == "events"

    def test_no_events_returns_zero(self):
        provider = EventProvider()
        features = provider.get_features("2023-01-01", "2023-01-02")
        assert np.all(features.data["event_count"] == 0)
        assert np.all(features.data["max_impact_multiplier"] == 1.0)

    def test_single_event_detected(self):
        event = Event(
            name="Test Concert",
            start_time=datetime(2023, 1, 14, 20, 0),
            end_time=datetime(2023, 1, 14, 23, 0),
        )
        provider = EventProvider([event])
        features = provider.get_features("2023-01-14", "2023-01-15")
        assert features.data["event_count"].sum() > 0
        assert np.any(features.data["max_impact_multiplier"] > 1.0)

    def test_add_event_dynamically(self):
        provider = EventProvider()
        provider.add_event(Event("Test", datetime(2023, 6, 1, 12, 0), datetime(2023, 6, 1, 14, 0)))
        features = provider.get_features("2023-06-01", "2023-06-02")
        assert features.data["event_count"].sum() > 0

    def test_clear_events(self):
        provider = EventProvider([Event("Test", datetime(2023, 1, 1, 0, 0), datetime(2023, 1, 1, 1, 0))])
        provider.clear_events()
        features = provider.get_features("2023-01-01", "2023-01-02")
        assert np.all(features.data["event_count"] == 0)


# ===========================================================================
# CompositeProvider Tests
# ===========================================================================


class TestCompositeProvider:
    def test_merges_multiple_providers(self, tmp_path):
        composite = CompositeFeatureProvider(
            [
                CalendarProvider(),
                WeatherProvider(cache_path=tmp_path / "weather.parquet", auto_download=True),
            ]
        )
        features = composite.get_features("2023-01-01", "2023-01-02")
        assert "calendar_weekday" in features.data
        assert "weather_temperature" in features.data

    def test_empty_providers_raises(self):
        with pytest.raises(ValueError, match="at least one"):
            CompositeFeatureProvider([])

    def test_provider_list_access(self):
        cal = CalendarProvider()
        composite = CompositeFeatureProvider([cal])
        assert composite.providers[0] is cal


# ===========================================================================
# align_features Tests
# ===========================================================================


class TestAlignFeatures:
    def test_align_single_provider(self):
        cal = CalendarProvider()
        timestamps = pd.date_range("2023-01-01", periods=48, freq="30min")
        df = align_features(timestamps, cal)
        assert "calendar_weekday" in df.columns
        assert len(df) == 48

    def test_align_multiple_providers(self, tmp_path):
        cal = CalendarProvider()
        weather = WeatherProvider(cache_path=tmp_path / "weather.parquet", auto_download=True)
        timestamps = pd.date_range("2023-06-01", periods=48, freq="30min")
        df = align_features(timestamps, cal, weather)
        assert "calendar_weekday" in df.columns
        assert "weather_temperature" in df.columns
