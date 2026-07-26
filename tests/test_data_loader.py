from datetime import datetime

from src.common.data_loader import DataLoader


class TestDataLoader:
    """Tests for DataLoader utility."""

    def setup_method(self):
        self.loader = DataLoader()

    def test_next_half_hour_exact_boundary(self):
        dt = datetime(2023, 1, 15, 8, 0)
        result = self.loader.next_half_hour(dt)
        assert result.hour == 8
        assert result.minute == 30

    def test_next_half_hour_mid_slot(self):
        dt = datetime(2023, 1, 15, 8, 15)
        result = self.loader.next_half_hour(dt)
        assert result.hour == 8
        assert result.minute == 30

    def test_next_half_hour_exact_half(self):
        dt = datetime(2023, 1, 15, 8, 30)
        result = self.loader.next_half_hour(dt)
        assert result.hour == 9
        assert result.minute == 0

    def test_next_half_hour_end_of_day(self):
        dt = datetime(2023, 1, 15, 23, 45)
        result = self.loader.next_half_hour(dt)
        assert result.day == 16
        assert result.hour == 0
        assert result.minute == 0

    def test_datetime_to_state_monday_8am(self):
        dt = datetime(2023, 1, 16, 8, 15)
        state = self.loader.datetime_to_state(dt)
        expected_slot = 16 + 1
        expected_state = 0 * 48 + expected_slot
        assert state == expected_state

    def test_datetime_to_state_sunday(self):
        dt = datetime(2023, 1, 15, 12, 0)
        state = self.loader.datetime_to_state(dt)
        expected_slot = 25
        expected_state = 6 * 48 + expected_slot
        assert state == expected_state

    def test_project_root_exists(self):
        root = self.loader.project_root
        assert root.exists()
        assert (root / "src").exists()

    def test_slot_count_integrity(self):
        assert self.loader.slot_count == 48
        assert self.loader.zone_count == 263
        assert self.loader.week_slot_count == 336
