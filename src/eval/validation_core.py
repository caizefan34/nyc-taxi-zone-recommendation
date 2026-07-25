"""Read the fixed public validation labels shipped with the student release."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pyarrow.parquet as pq

from src.eval.offline_core import ZONE_COUNT


def read_validation_answers(path: Path) -> dict[int, np.ndarray]:
    """Load one 263-value public reference vector for each query ID."""
    table = pq.read_table(path)
    if table.schema.names != ["query_id", "reference_utility"]:
        raise ValueError("answer file columns must be query_id, reference_utility")
    answers: dict[int, np.ndarray] = {}
    for row in table.to_pylist():
        query_id = int(row["query_id"])
        values = np.asarray(row["reference_utility"], dtype=float)
        if query_id in answers:
            raise ValueError(f"duplicate answer for query ID {query_id}")
        if values.shape != (ZONE_COUNT,):
            raise ValueError("reference_utility must contain 263 values")
        answers[query_id] = values
    if not answers:
        raise ValueError("answer file must not be empty")
    return answers
