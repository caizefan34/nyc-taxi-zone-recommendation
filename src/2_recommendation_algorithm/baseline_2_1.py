"""Build the 263 x 263 directed shortest-travel-time matrix for Baseline 2."""
from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra

from src.common.config import get_config
from src.common.logging_utils import get_logger

logger = get_logger(__name__)

ZONE_COUNT = get_config("domain.zone_count", 263)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_TRAIN_PATH = PROJECT_ROOT / "data/processed/train_cleaned.parquet"
DEFAULT_OUTPUT_PATH = PROJECT_ROOT / "data/processed/travel_time_matrix_dijkstra.csv"


def build_matrix(train_path: Path, output_path: Path) -> None:
    """Aggregate OD edges, run all-source Dijkstra, and write a CSV matrix."""
    logger.info("Building travel time matrix from %s", train_path)
    table = pq.read_table(train_path, columns=["PULocationID", "DOLocationID", "trip_duration"]).to_pylist()

    edge_sums = {}
    edge_counts = {}
    for row in table:
        origin = int(row["PULocationID"]) - 1
        dest = int(row["DOLocationID"]) - 1
        duration = float(row["trip_duration"])
        key = (origin, dest)
        edge_sums[key] = edge_sums.get(key, 0.0) + duration
        edge_counts[key] = edge_counts.get(key, 0) + 1

    rows, cols, data = [], [], []
    for (origin, dest), total in edge_sums.items():
        mean_duration = total / edge_counts[(origin, dest)]
        if origin == dest:
            continue
        if mean_duration > 0:
            rows.append(origin)
            cols.append(dest)
            data.append(mean_duration)

    adj_matrix = csr_matrix((data, (rows, cols)), shape=(ZONE_COUNT, ZONE_COUNT), dtype=float)
    dist_matrix = dijkstra(adj_matrix, directed=True, unweighted=False)

    diag_values = {}
    for (origin, dest), total in edge_sums.items():
        if origin == dest:
            diag_values[origin] = total / edge_counts[(origin, dest)]
    for i in range(ZONE_COUNT):
        if i in diag_values:
            dist_matrix[i, i] = diag_values[i]
        else:
            dist_matrix[i, i] = get_config("algorithm.default_same_zone_time", 10.0)

    _write_matrix(output_path, dist_matrix)
    logger.info("Wrote %d x %d matrix to %s", ZONE_COUNT, ZONE_COUNT, output_path)


def _write_matrix(output_path: Path, matrix: np.ndarray) -> None:
    """Write the distance matrix to a CSV file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["origin_location_id", *range(1, ZONE_COUNT + 1)])
        for origin, distances in enumerate(matrix, start=1):
            writer.writerow([origin, *(("inf" if math.isinf(float(v)) else f"{float(v):.6f}") for v in distances)])


def main() -> None:
    """Run the Dijkstra matrix builder."""
    parser = argparse.ArgumentParser(description="Build the directed Dijkstra travel-time matrix.")
    parser.add_argument("--train", type=Path, default=DEFAULT_TRAIN_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    args = parser.parse_args()
    build_matrix(args.train, args.output)


if __name__ == "__main__":
    main()
