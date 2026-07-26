"""Automated download of NYC TLC Yellow Taxi trip records.

Downloads parquet files from the NYC TLC data portal for a given
year/month range. Files are stored in a year/month directory structure.

TLC URL pattern:
  https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_YYYY-MM.parquet
"""
from __future__ import annotations

import shutil
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Sequence

TLC_DOWNLOAD_URL: str = "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_{year}-{month:02d}.parquet"
"""URL template for TLC Yellow Taxi parquet files."""

USER_AGENT: str = "NYC-Taxi-Research/1.0"
RETRY_COUNT: int = 3
RETRY_DELAY_SEC: float = 2.0
DOWNLOAD_TIMEOUT_SEC: int = 300


def _url(year: int, month: int) -> str:
    """Build the download URL for a given year and month."""
    return TLC_DOWNLOAD_URL.format(year=year, month=month)


def _output_path(root: Path, year: int, month: int) -> Path:
    """Build the local filesystem path for a given year and month."""
    return root / str(year) / f"{month:02d}" / f"yellow_tripdata_{year}-{month:02d}.parquet"


def download_tlc_month(
    year: int,
    month: int,
    *,
    root: Path = Path("data/raw"),
    force: bool = False,
) -> Path:
    """Download one month of TLC Yellow Taxi data.

    Args:
        year: Calendar year (e.g. 2022).
        month: Calendar month (1–12).
        root: Root directory for raw data storage.
            Files are stored at ``root/{year}/{month:02d}/``.
        force: If True, re-download even if the file exists.

    Returns:
        Path to the downloaded parquet file.

    Raises:
        urllib.error.HTTPError: If the file is not available at the TLC portal
            (e.g. future months, or months before 2009).
    """
    if not 1 <= month <= 12:
        raise ValueError(f"month must be in 1..12, got {month}")

    output = _output_path(root, year, month)
    if output.exists() and not force:
        return output

    url = _url(year, month)
    output.parent.mkdir(parents=True, exist_ok=True)

    last_error: Exception | None = None
    for attempt in range(RETRY_COUNT):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=DOWNLOAD_TIMEOUT_SEC) as response:
                with open(output, "wb") as f:
                    shutil.copyfileobj(response, f)
            return output
        except (urllib.error.HTTPError, urllib.error.URLError, OSError, TimeoutError) as exc:
            last_error = exc
            if attempt < RETRY_COUNT - 1:
                time.sleep(RETRY_DELAY_SEC * (attempt + 1))

    msg = (
        f"Failed to download {url} after {RETRY_COUNT} attempts: {last_error}"
    )
    raise RuntimeError(msg) from last_error


def download_range(
    years: Sequence[int],
    *,
    root: Path = Path("data/raw"),
    force: bool = False,
) -> dict[tuple[int, int], Path]:
    """Download TLC data for a range of years (all months).

    Args:
        years: Sequence of years to download.
        root: Root directory for raw data storage.
        force: If True, re-download existing files.

    Returns:
        Dictionary mapping ``(year, month)`` to the downloaded file path.
    """
    results: dict[tuple[int, int], Path] = {}
    for year in sorted(years):
        for month in range(1, 13):
            path = download_tlc_month(year, month, root=root, force=force)
            results[(year, month)] = path
    return results
