"""Small dependency-light GraphSAGE and GAT zone encoders."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
import torch
from torch import nn

from .builder import ODGraph


class GraphSAGEEncoder(nn.Module):
    """Two-layer mean-aggregation GraphSAGE encoder."""

    def __init__(self, input_size: int, hidden_size: int, embedding_size: int) -> None:
        super().__init__()
        self.first = nn.Linear(2 * input_size, hidden_size)
        self.second = nn.Linear(2 * hidden_size, embedding_size)

    def forward(self, features: torch.Tensor, adjacency: torch.Tensor) -> torch.Tensor:
        aggregated = adjacency @ features
        hidden = torch.relu(self.first(torch.cat((features, aggregated), dim=1)))
        aggregated_hidden = adjacency @ hidden
        return self.second(torch.cat((hidden, aggregated_hidden), dim=1))


class GATEncoder(nn.Module):
    """Single-head graph attention followed by a weighted projection."""

    def __init__(self, input_size: int, hidden_size: int, embedding_size: int) -> None:
        super().__init__()
        self.projection = nn.Linear(input_size, hidden_size, bias=False)
        self.source_attention = nn.Linear(hidden_size, 1, bias=False)
        self.target_attention = nn.Linear(hidden_size, 1, bias=False)
        self.output = nn.Linear(2 * hidden_size, embedding_size)

    def forward(self, features: torch.Tensor, adjacency: torch.Tensor) -> torch.Tensor:
        projected = self.projection(features)
        scores = self.source_attention(projected) + self.target_attention(projected).T
        scores = nn.functional.leaky_relu(scores, negative_slope=0.2)
        scores = scores + torch.log(adjacency.clamp_min(1e-12))
        attention = torch.softmax(scores.masked_fill(adjacency <= 0.0, -torch.inf), dim=1)
        hidden = torch.nn.functional.elu(attention @ projected)
        aggregated = adjacency @ hidden
        return self.output(torch.cat((hidden, aggregated), dim=1))


@dataclass(frozen=True)
class GraphTrainingResult:
    """Learned zone embeddings and deterministic diagnostics."""

    embeddings: np.ndarray
    final_loss: float
    epochs: int
    model: str
    seed: int


def train_graph_embeddings(
    graph: ODGraph,
    *,
    model: str = "graphsage",
    embedding_size: int = 8,
    hidden_size: int = 32,
    epochs: int = 200,
    learning_rate: float = 0.01,
    seed: int = 20230722,
    device: str | torch.device = "cpu",
) -> GraphTrainingResult:
    """Train a graph autoencoder without using any demand-validation targets."""
    if model not in {"graphsage", "gat"}:
        raise ValueError("model must be 'graphsage' or 'gat'")
    if embedding_size <= 0 or hidden_size <= 0 or epochs <= 0 or learning_rate <= 0.0:
        raise ValueError("embedding_size, hidden_size, epochs, and learning_rate must be positive")

    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    target_device = torch.device(device)
    features = torch.as_tensor(graph.node_features, device=target_device)
    adjacency = torch.as_tensor(graph.adjacency, device=target_device)
    target = torch.as_tensor(graph.edge_mask, dtype=torch.float32, device=target_device)
    encoder_class = GraphSAGEEncoder if model == "graphsage" else GATEncoder
    encoder = encoder_class(features.shape[1], hidden_size, embedding_size).to(target_device)
    optimizer = torch.optim.Adam(encoder.parameters(), lr=learning_rate)
    off_diagonal = ~torch.eye(graph.zone_count, dtype=torch.bool, device=target_device)
    labels = target[off_diagonal]
    positives = labels.sum()
    negatives = labels.numel() - positives
    positive_weight = negatives / positives.clamp_min(1.0)

    loss = torch.tensor(torch.nan, device=target_device)
    for _ in range(epochs):
        embeddings = encoder(features, adjacency)
        logits = embeddings @ embeddings.T / np.sqrt(embedding_size)
        loss = nn.functional.binary_cross_entropy_with_logits(
            logits[off_diagonal],
            labels,
            pos_weight=positive_weight,
        )
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        optimizer.step()
    with torch.no_grad():
        embeddings = encoder(features, adjacency).cpu().numpy().astype(np.float32)
    return GraphTrainingResult(
        embeddings=embeddings,
        final_loss=float(loss.item()),
        epochs=epochs,
        model=model,
        seed=seed,
    )


def append_graph_embeddings(
    frame: pd.DataFrame,
    embeddings: np.ndarray,
    *,
    prefix: str,
) -> tuple[pd.DataFrame, tuple[str, ...]]:
    """Attach static zone embeddings to a supervised forecasting frame."""
    matrix = np.asarray(embeddings, dtype=np.float32)
    if matrix.ndim != 2 or matrix.shape[1] == 0:
        raise ValueError("embeddings must be a non-empty two-dimensional array")
    if "zone_id" not in frame:
        raise ValueError("frame must contain zone_id")
    indices = frame["zone_id"].to_numpy(dtype=np.int64) - 1
    if np.any(indices < 0) or np.any(indices >= matrix.shape[0]):
        raise ValueError("zone_id falls outside the embedding matrix")
    result = frame.copy()
    columns = tuple(f"{prefix}_{index}" for index in range(matrix.shape[1]))
    result.loc[:, list(columns)] = matrix[indices]
    return result, columns


def append_od_message_features(
    frame: pd.DataFrame,
    graph: ODGraph,
) -> tuple[pd.DataFrame, tuple[str, ...]]:
    """Append causal OD-weighted aggregates of lagged demand features."""
    sources = ("lag_demand_1", "lag_demand_48", "rolling_demand_mean_48")
    missing = sorted(set(("timestamp", "zone_id", *sources)) - set(frame))
    if missing:
        raise ValueError(f"frame is missing graph message columns: {missing}")
    if len(frame) % graph.zone_count != 0:
        raise ValueError("frame must contain complete timestamp-by-zone blocks")
    zone_blocks = frame["zone_id"].to_numpy(dtype=np.int64).reshape(-1, graph.zone_count)
    expected_zones = np.arange(1, graph.zone_count + 1)
    if not np.all(zone_blocks == expected_zones):
        raise ValueError("each timestamp block must be ordered by complete zone_id")

    result = frame.copy()
    columns = []
    for source in sources:
        values = frame[source].to_numpy(dtype=np.float32).reshape(-1, graph.zone_count)
        for direction, adjacency in (
            ("out", graph.outgoing_adjacency),
            ("in", graph.incoming_adjacency),
        ):
            column = f"od_{direction}_{source}"
            result[column] = (values @ adjacency.T).reshape(-1)
            columns.append(column)
    return result, tuple(columns)
