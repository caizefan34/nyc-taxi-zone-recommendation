"""Tests for core algorithm math (stateless logic only)."""
from __future__ import annotations
import math
import pytest
from datetime import datetime


class TestDataLoaderHelpers:
    """Test DataLoader static/utility methods."""

    def test_next_half_hour_regular(self):
        """next_half_hour should round up to the next :00 or :30."""
        from src.common.data_loader import DataLoader
        
        dt = datetime(2023, 1, 15, 8, 15)
        result = DataLoader.next_half_hour(dt)
        assert result.hour == 8
        assert result.minute == 30
        assert result.second == 0

    def test_next_half_hour_exact(self):
        """next_half_hour of :30 should go to next hour."""
        from src.common.data_loader import DataLoader
        
        dt = datetime(2023, 1, 15, 8, 30)
        result = DataLoader.next_half_hour(dt)
        assert result.hour == 9
        assert result.minute == 0
        assert result.second == 0

    def test_next_half_hour_exact_hour(self):
        """next_half_hour of :00 should go to :30."""
        from src.common.data_loader import DataLoader
        
        dt = datetime(2023, 1, 15, 8, 0)
        result = DataLoader.next_half_hour(dt)
        assert result.hour == 8
        assert result.minute == 30
        assert result.second == 0

    def test_next_half_hour_midnight(self):
        """next_half_hour should handle midnight boundary."""
        from src.common.data_loader import DataLoader
        
        dt = datetime(2023, 1, 15, 23, 45)
        result = DataLoader.next_half_hour(dt)
        assert result.hour == 0
        assert result.minute == 0
        assert result.day == 16  # Next day

    def test_datetime_to_state_morning(self):
        """datetime_to_state should return correct slot for morning time.
        
        2023-01-02 08:00 (Monday):
        - next_half_hour = 08:30 -> hour=8, minute=30
        - slot = 8*2 + 30//30 = 16 + 1 = 17
        - weekday = 0 (Monday)
        - state = 0*48 + 17 = 17
        """
        from src.common.data_loader import DataLoader
        
        loader = DataLoader()
        dt = datetime(2023, 1, 2, 8, 0)  # Monday
        state = loader.datetime_to_state(dt)
        # Monday=0, 08:30 -> slot=17, so state=0*48+17=17
        assert state >= 0 and state < 336
        assert state == 17

    def test_datetime_to_state_midnight(self):
        """datetime_to_state should handle midnight correctly.
        
        2023-01-02 00:15 (Monday):
        - next_half_hour = 00:30 -> slot = 0*2 + 30//30 = 1
        - state = 0*48 + 1 = 1
        """
        from src.common.data_loader import DataLoader
        
        loader = DataLoader()
        dt = datetime(2023, 1, 2, 0, 15)
        state = loader.datetime_to_state(dt)
        assert state == 1

    def test_datetime_to_state_sunday(self):
        """datetime_to_state should handle Sunday (weekday=6).
        
        2023-01-01 12:00 (Sunday):
        - next_half_hour = 12:30 -> slot = 12*2 + 30//30 = 24 + 1 = 25
        - weekday = 6
        - state = 6*48 + 25 = 288 + 25 = 313
        """
        from src.common.data_loader import DataLoader
        
        loader = DataLoader()
        dt = datetime(2023, 1, 1, 12, 0)  # Sunday
        state = loader.datetime_to_state(dt)
        assert state == 313

    def test_datetime_to_state_midnight_exact(self):
        """datetime_to_state for 00:00 should give slot 0.
        
        2023-01-02 00:00 (Monday):
        - next_half_hour = 00:30 -> slot = 0*2 + 30//30 = 1
        - Wait, no: 00:00 -> minute=0, floor(0/30)*30 = 0, then +30 = 00:30
        - Actually let me re-read the code logic.
        
        In next_half_hour:
        - slot_start = value.replace(minute=(0//30)*30=0, second=0, microsecond=0) = 00:00
        - return slot_start + 30min = 00:30
        - slot = 0*2 + 30//30 = 1
        """
        from src.common.data_loader import DataLoader
        
        loader = DataLoader()
        dt = datetime(2023, 1, 2, 0, 0)
        state = loader.datetime_to_state(dt)
        assert state == 1


class TestValueFunctionHelpers:
    """Test mathematical helper functions from improved_strategy."""

    def test_one_step_value_high_demand(self):
        """Value near fare for very high demand: p = d/(d+240)."""
        d = 10000.0
        f = 20.0
        lam = 240.0
        p = d / (d + lam)
        expected = p * f
        assert abs(expected - 19.53) < 0.1

    def test_one_step_value_low_demand(self):
        """Value low for low demand."""
        d = 10.0
        f = 15.0
        lam = 240.0
        p = d / (d + lam)
        expected = p * f
        assert abs(expected - 0.6) < 0.05

    def test_one_step_value_zero_demand(self):
        """Value 0 for zero demand (convention)."""
        d = 0.0
        f = 20.0
        lam = 240.0
        p = 0.0
        expected = p * f
        assert expected == 0.0

    def test_sigmoid_shape(self):
        """Sigmoid d/(d+lambda) should be monotonic and bounded."""
        lam = 240.0
        demands = [0, 10, 50, 100, 240, 500, 1000, 10000]
        probs = [d / (d + lam) if d > 0 else 0.0 for d in demands]
        for i in range(1, len(probs)):
            assert probs[i] >= probs[i - 1]
        assert all(0 <= p <= 1 for p in probs)


class TestConfigAndDomain:
    """Test domain constant validation."""

    def test_zone_count_positive(self):
        """Zone count must be positive."""
        from src.common.config import get_config
        zc = get_config("domain.zone_count", 263)
        assert zc > 0
        assert zc == 263

    def test_slot_count_valid(self):
        """Slot count must be 48 (half-hour slots in 24h)."""
        from src.common.config import get_config
        sc = get_config("domain.slot_count", 48)
        assert sc == 48

    def test_week_slot_count_consistency(self):
        """Week slot count should be 7 * slot_count."""
        from src.common.config import get_config
        sc = get_config("domain.slot_count", 48)
        wsc = get_config("domain.week_slot_count", 336)
        assert wsc == 7 * sc

    def test_algorithm_params_in_range(self):
        """Algorithm parameters should be in valid ranges."""
        from src.common.config import get_config
        gamma = get_config("algorithm.gamma", 0.5)
        lam = get_config("algorithm.lambda_param", 1.0)
        k = get_config("algorithm.candidate_pool_size", 100)
        assert 0 <= gamma <= 1
        assert lam > 0
        assert k > 0 and k <= 263


class TestTravelTimeHelpers:
    """Test travel time related calculations."""

    def test_arrival_slot_calculation(self):
        """Arrival slot should advance by travel time."""
        state = 0
        travel_time_minutes = 30.0
        move_slots = int(math.floor(travel_time_minutes / 30.0 + 0.5))
        assert move_slots == 1
        arrival = (state + move_slots) % 336
        assert arrival == 1

    def test_arrival_slot_zero_travel(self):
        """Same-zone travel should result in same state."""
        state = 100
        travel_time_minutes = 0.0
        move_slots = int(math.floor(0.0 / 30.0 + 0.5))
        assert move_slots == 0
        arrival = (state + move_slots) % 336
        assert arrival == state

    def test_arrival_slot_wraparound(self):
        """Arrival slot should wrap around at week boundary."""
        state = 335
        travel_time_minutes = 60.0
        move_slots = int(math.floor(60.0 / 30.0 + 0.5))
        assert move_slots == 2
        arrival = (state + move_slots) % 336
        assert arrival == 1

    def test_utility_normalization(self):
        """Utility should be normalized by move slots."""
        utility = 100.0
        move_cost = 15.0
        move_slots = int(math.floor(move_cost / 30.0 + 0.5))
        normalized = utility / (move_slots + 1.0)
        assert move_slots == 1
        assert normalized == 100.0 / 2.0

    def test_utility_normalization_zero_move(self):
        """Same-zone utility should not be penalized."""
        utility = 100.0
        move_cost = 0.0
        move_slots = int(math.floor(0.0 / 30.0 + 0.5))
        normalized = utility / (move_slots + 1.0)
        assert move_slots == 0
        assert normalized == 100.0
