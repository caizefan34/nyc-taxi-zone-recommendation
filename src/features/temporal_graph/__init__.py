"""Temporal Graph Forecasting for taxi zone demand.

Implements Temporal Graph Transformer for multi-step demand forecasting
with quantile output (P10, P50, P90).

Inputs:
- Zone graph (OD adjacency)
- Historical demand sequence
- Time embedding (sin/cos)
- External features (weather, calendar, airport)

Outputs:
- Future demand distribution per zone: P10, P50, P90
"""
from __future__ import annotations

from .dataset import TemporalGraphDataset, collate_sequences
from .model import TemporalGraphTransformer, TemporalGraphTransformerConfig

__all__ = [
    "TemporalGraphTransformer",
    "TemporalGraphTransformerConfig",
    "TemporalGraphDataset",
    "collate_sequences",
]
