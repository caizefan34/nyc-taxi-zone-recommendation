"""Stable module entry point for the directed travel-time matrix builder."""
from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _build_matrix():
    path = ROOT / "src/2_recommendation_algorithm/baseline_2_1.py"
    spec = importlib.util.spec_from_file_location("travel_matrix_entry", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module.build_matrix


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--train", type=Path, default=ROOT / "data/processed/train_cleaned.parquet")
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "data/processed/travel_time_matrix_dijkstra.csv",
    )
    args = parser.parse_args()
    _build_matrix()(args.train, args.output)


if __name__ == "__main__":
    main()

