"""Tests for the new calibration framework.

Covers:
- CalibrationConfig loading
- Multi-dim calibration functions (demand, fare, travel time, reward)
- Backward compatibility
"""
from __future__ import annotations

from src.simulator.calibration import (
    CalibrationConfig,
    calibrate_demand,
    calibrate_fare,
    calibrate_reward,
    calibrate_travel_time,
    calibrate_v1_to_v2,
    calibrate_v2_to_v1,
)


class TestCalibrationConfig:
    def test_default_config(self):
        cfg = CalibrationConfig()
        assert cfg.demand_factor == 1.0
        assert cfg.fare_factor == 0.80
        assert cfg.reward_factor == 0.80

    def test_custom_config(self):
        cfg = CalibrationConfig(demand_factor=0.5, fare_factor=0.9, reward_factor=0.75)
        assert cfg.demand_factor == 0.5
        assert cfg.fare_factor == 0.9
        assert cfg.reward_factor == 0.75


class TestCalibrateDemand:
    def test_no_calibration(self):
        assert calibrate_demand(100.0) == 100.0

    def test_with_factor(self):
        cfg = CalibrationConfig(demand_factor=0.8)
        result = calibrate_demand(100.0, cfg)
        assert abs(result - 80.0) < 1e-6

    def test_with_offset(self):
        cfg = CalibrationConfig(demand_factor=1.0, demand_offset=10.0)
        result = calibrate_demand(100.0, cfg)
        assert abs(result - 110.0) < 1e-6

    def test_non_negative(self):
        cfg = CalibrationConfig(demand_factor=-1.0)
        result = calibrate_demand(100.0, cfg)
        assert result >= 0.0


class TestCalibrateFare:
    def test_default_factor(self):
        result = calibrate_fare(20.0)
        assert abs(result - 16.0) < 1e-6

    def test_custom_factor(self):
        cfg = CalibrationConfig(fare_factor=1.0)
        result = calibrate_fare(20.0, cfg)
        assert abs(result - 20.0) < 1e-6


class TestCalibrateTravelTime:
    def test_default(self):
        result = calibrate_travel_time(15.0)
        assert abs(result - 15.0) < 1e-6

    def test_with_factor(self):
        cfg = CalibrationConfig(travel_time_factor=1.2)
        result = calibrate_travel_time(15.0, cfg)
        assert abs(result - 18.0) < 1e-6

    def test_minimum_one(self):
        cfg = CalibrationConfig(travel_time_factor=0.1)
        result = calibrate_travel_time(5.0, cfg)
        assert result >= 1.0


class TestCalibrateReward:
    def test_backward_compat_v2_to_v1(self):
        result = calibrate_v2_to_v1(1000.0)
        assert result > 0

    def test_backward_compat_v1_to_v2(self):
        result = calibrate_v1_to_v2(800.0)
        assert result > 0

    def test_custom_reward_factor(self):
        cfg = CalibrationConfig(reward_factor=0.5)
        result = calibrate_reward(1000.0, cfg)
        assert abs(result - 500.0) < 1e-6

    def test_no_config_default(self):
        result = calibrate_reward(1000.0)
        assert result > 0

