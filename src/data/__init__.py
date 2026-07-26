"""Multi-year NYC TLC data pipeline package.

Provides automated download, cleaning, and time-based splitting
for NYC TLC Yellow Taxi trip records (2022–2025).
"""
from __future__ import annotations

from .download import TLC_DOWNLOAD_URL, download_tlc_month, download_range
from .pipeline import (
    DataConfig,
    TLCDataPipeline,
    compute_splits,
    load_pipeline_config,
)

__all__ = [
    "TLC_DOWNLOAD_URL",
    "DataConfig",
    "TLCDataPipeline",
    "compute_splits",
    "download_tlc_month",
    "download_range",
    "load_pipeline_config",
]
