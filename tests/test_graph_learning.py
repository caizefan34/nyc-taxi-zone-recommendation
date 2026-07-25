"""Leakage, shape, and reproducibility tests for graph embeddings."""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.graph import (
    append_graph_embeddings,
    append_od_message_features,
    build_od_graph,
    train_graph_embeddings,
)


def _trips() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "tpep_pickup_datetime": [
                "2023-01-01 00:00",
                "2023-01-01 00:30",
                "2023-01-02 00:00",
                "2023-01-03 00:00",
            ],
            "PULocationID": [1, 1, 2, 3],
            "DOLocationID": [2, 2, 3, 1],
        }
    )


def test_od_graph_excludes_future_trips_and_normalizes_rows():
    graph = build_od_graph(_trips(), zone_count=3, end_exclusive="2023-01-03")
    assert graph.counts.tolist() == [[0.0, 2.0, 0.0], [0.0, 0.0, 1.0], [0.0, 0.0, 0.0]]
    assert np.allclose(graph.adjacency.sum(axis=1), 1.0)
    assert np.allclose(graph.outgoing_adjacency.sum(axis=1), 1.0)
    assert np.allclose(graph.incoming_adjacency.sum(axis=1), 1.0)
    assert graph.node_features.shape == (3, 4)


def test_graphsage_and_gat_embeddings_are_reproducible():
    graph = build_od_graph(_trips(), zone_count=3)
    first = train_graph_embeddings(graph, model="graphsage", epochs=5, seed=11)
    second = train_graph_embeddings(graph, model="graphsage", epochs=5, seed=11)
    gat = train_graph_embeddings(graph, model="gat", epochs=5, seed=11)
    assert first.embeddings.shape == (3, 8)
    assert np.array_equal(first.embeddings, second.embeddings)
    assert np.isfinite(gat.embeddings).all()


def test_append_graph_embeddings_uses_zone_identity():
    frame = pd.DataFrame({"zone_id": [2, 1, 2]})
    embeddings = np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float32)
    result, columns = append_graph_embeddings(frame, embeddings, prefix="graphsage")
    assert columns == ("graphsage_0", "graphsage_1")
    assert result[list(columns)].to_numpy().tolist() == [[3.0, 4.0], [1.0, 2.0], [3.0, 4.0]]


def test_od_message_features_aggregate_complete_zone_blocks():
    graph = build_od_graph(_trips(), zone_count=3)
    frame = pd.DataFrame(
        {
            "timestamp": [pd.Timestamp("2023-01-04")] * 3,
            "zone_id": [1, 2, 3],
            "lag_demand_1": [1.0, 2.0, 3.0],
            "lag_demand_48": [2.0, 4.0, 6.0],
            "rolling_demand_mean_48": [3.0, 6.0, 9.0],
        }
    )
    result, columns = append_od_message_features(frame, graph)
    assert len(columns) == 6
    assert np.isfinite(result[list(columns)]).all().all()
    assert not np.array_equal(result["od_out_lag_demand_1"], result["lag_demand_1"])
