"""Tests for the raw-to-temporal-split ingestion stage."""

from __future__ import annotations

import importlib.util
from datetime import datetime
from pathlib import Path

import pandas as pd


def _load_clean_module():
    path = Path(__file__).resolve().parents[1] / "src/1_data_clean/clean.py"
    spec = importlib.util.spec_from_file_location("tested_clean_pipeline", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_split_raw_data_is_chronological(tmp_path):
    module = _load_clean_module()
    raw = tmp_path / "raw.parquet"
    train = tmp_path / "train.parquet"
    validation = tmp_path / "validation.parquet"
    pd.DataFrame(
        {
            "tpep_pickup_datetime": [
                datetime(2023, 1, 24, 23, 59),
                datetime(2023, 1, 25, 0, 0),
                datetime(2023, 2, 1, 0, 0),
            ],
            "value": [1, 2, 3],
        }
    ).to_parquet(raw, index=False)
    counts = module.split_raw_data(raw, train, validation)
    assert counts == (1, 1)
    assert pd.read_parquet(train)["value"].tolist() == [1]
    assert pd.read_parquet(validation)["value"].tolist() == [2]
