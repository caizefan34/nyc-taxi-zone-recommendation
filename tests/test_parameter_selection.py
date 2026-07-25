"""Tests for executable parameter selection."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from src.common.config import load_config
from src.eval.offline_core import Query


def _load_module():
    path = Path(__file__).resolve().parents[1] / "src/2_recommendation_algorithm/parameter_selection.py"
    spec = importlib.util.spec_from_file_location("tested_parameter_selection", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_config_has_valid_parameter_grid():
    grid = load_config()["parameter_grid"]
    assert all(value > 0 for value in grid["pickup_half_saturation_values"])
    assert all(0 <= value < 1 for value in grid["gamma_values"])
    assert all(3 <= value <= 263 for value in grid["candidate_pool_sizes"])


def test_parameter_selection_uses_evaluator_results(tmp_path, monkeypatch):
    module = _load_module()
    queries_path = tmp_path / "queries.parquet"
    answers_path = tmp_path / "answers.parquet"
    output_path = tmp_path / "results.json"
    pq.write_table(pa.table({"placeholder": [1]}), queries_path)
    pq.write_table(pa.table({"placeholder": [1]}), answers_path)
    query = Query(1, 1, __import__("datetime").datetime(2023, 1, 25))
    monkeypatch.setattr(module, "read_public_queries", lambda _: [query])
    monkeypatch.setattr(module, "read_validation_answers", lambda _: {1: np.ones(263)})

    class Planner:
        def __init__(self, **_):
            self.pickup_half_saturation = 0.0
            self.gamma = 0.0
            self.candidate_pool_size = 0

        def _precompute_values(self):
            return {1: None, 2: None}

        def recommend(self, *_args, **_kwargs):
            return [1, 2, 3]

    monkeypatch.setattr(module, "_load_planner_class", lambda: Planner)
    monkeypatch.setattr(
        module,
        "evaluate_validation",
        lambda *_args, **_kwargs: {
            "ndcg_at_3": 0.5,
            "hit_at_3": 0.25,
            "reference_two_step_utility_at_1": 7.0,
            "average_recommend_time_ms": 1.0,
        },
    )
    results = module.run_parameter_selection(
        queries_path,
        answers_path,
        output_path,
        [120.0],
        [0.5],
        [50],
    )
    assert results[0]["ndcg_at_3"] == 0.5
    assert output_path.exists()
