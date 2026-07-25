"""Construct a leakage-safe weighted taxi-zone graph from OD trips."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class ODGraph:
    """Directed OD counts plus normalized undirected message-passing inputs."""

    counts: np.ndarray
    adjacency: np.ndarray
    outgoing_adjacency: np.ndarray
    incoming_adjacency: np.ndarray
    edge_mask: np.ndarray
    node_features: np.ndarray

    @property
    def zone_count(self) -> int:
        return int(self.counts.shape[0])


def _standardize(columns: np.ndarray) -> np.ndarray:
    mean = columns.mean(axis=0, keepdims=True)
    scale = columns.std(axis=0, keepdims=True)
    scale[scale == 0.0] = 1.0
    return ((columns - mean) / scale).astype(np.float32)


def _normalize_with_self_loops(weights: np.ndarray) -> np.ndarray:
    result = np.log1p(weights).astype(np.float32)
    diagonal = np.diag_indices(len(result))
    result[diagonal] = np.maximum(result[diagonal], 1.0)
    return result / result.sum(axis=1, keepdims=True)


def build_od_graph(
    trips: pd.DataFrame,
    *,
    zone_count: int = 263,
    end_exclusive: str | pd.Timestamp | None = None,
) -> ODGraph:
    """Aggregate only trips available before ``end_exclusive`` into an OD graph."""
    required = {"tpep_pickup_datetime", "PULocationID", "DOLocationID"}
    missing = sorted(required - set(trips))
    if missing:
        raise ValueError(f"missing trip columns: {missing}")
    if zone_count <= 1:
        raise ValueError("zone_count must be greater than one")

    frame = trips.loc[:, sorted(required)].copy()
    frame["timestamp"] = pd.to_datetime(frame["tpep_pickup_datetime"], errors="coerce")
    frame["pickup"] = pd.to_numeric(frame["PULocationID"], errors="coerce")
    frame["dropoff"] = pd.to_numeric(frame["DOLocationID"], errors="coerce")
    valid = (
        frame["timestamp"].notna()
        & frame["pickup"].between(1, zone_count)
        & frame["dropoff"].between(1, zone_count)
    )
    if end_exclusive is not None:
        valid &= frame["timestamp"] < pd.Timestamp(end_exclusive)
    frame = frame.loc[valid]
    if frame.empty:
        raise ValueError("at least one valid training-period OD trip is required")

    pickup = frame["pickup"].to_numpy(dtype=np.int64) - 1
    dropoff = frame["dropoff"].to_numpy(dtype=np.int64) - 1
    counts = np.zeros((zone_count, zone_count), dtype=np.float32)
    np.add.at(counts, (pickup, dropoff), 1.0)

    undirected = np.log1p(counts + counts.T)
    edge_mask = undirected > 0.0
    np.fill_diagonal(edge_mask, True)
    weighted = np.where(edge_mask, undirected, 0.0)
    diagonal = np.diag_indices(zone_count)
    weighted[diagonal] = np.maximum(weighted[diagonal], 1.0)
    adjacency = weighted / weighted.sum(axis=1, keepdims=True)
    outgoing_adjacency = _normalize_with_self_loops(counts)
    incoming_adjacency = _normalize_with_self_loops(counts.T)

    outgoing_degree = (counts > 0.0).sum(axis=1)
    incoming_degree = (counts > 0.0).sum(axis=0)
    node_features = _standardize(
        np.column_stack(
            [
                np.log1p(counts.sum(axis=1)),
                np.log1p(counts.sum(axis=0)),
                np.log1p(outgoing_degree),
                np.log1p(incoming_degree),
            ]
        )
    )
    return ODGraph(
        counts=counts,
        adjacency=adjacency.astype(np.float32),
        outgoing_adjacency=outgoing_adjacency.astype(np.float32),
        incoming_adjacency=incoming_adjacency.astype(np.float32),
        edge_mask=edge_mask,
        node_features=node_features,
    )
