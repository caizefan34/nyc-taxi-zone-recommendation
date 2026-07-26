from datetime import datetime

import pytest


@pytest.fixture
def sample_datetime():
    return datetime(2023, 1, 15, 8, 15)


@pytest.fixture
def sample_location_id():
    return 132


@pytest.fixture
def invalid_location_id():
    return 0


@pytest.fixture
def boundary_datetime():
    return datetime(2023, 1, 25, 0, 0)


@pytest.fixture
def weekend_datetime():
    return datetime(2023, 1, 28, 14, 30)
