"""Data cleaning pipeline for NYC taxi trip data."""
from __future__ import annotations

import argparse
import csv
from datetime import datetime
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

from src.common.config import get_config
from src.common.logging_utils import get_logger

logger = get_logger(__name__)

ZONE_COUNT = get_config("domain.zone_count", 263)
TRAIN_BOUNDARY = (
    datetime.fromisoformat(get_config("cleaning.train_boundary", ["2023-01-01", "2023-01-25"])[0]),
    datetime.fromisoformat(get_config("cleaning.train_boundary", ["2023-01-01", "2023-01-25"])[1]),
)
VAL_BOUNDARY = (
    datetime.fromisoformat(get_config("cleaning.validation_boundary", ["2023-01-25", "2023-02-01"])[0]),
    datetime.fromisoformat(get_config("cleaning.validation_boundary", ["2023-01-25", "2023-02-01"])[1]),
)
MAX_TRIP_DURATION_MINUTES = get_config("cleaning.max_trip_duration_minutes", 240.0)
MIN_TRIP_DURATION_MINUTES = get_config("cleaning.min_trip_duration_minutes", 1.0)
MAX_FARE = get_config("cleaning.max_fare", 200.0)
MIN_FARE = get_config("cleaning.min_fare", 0.0)
MAX_TRIP_DISTANCE = get_config("cleaning.max_trip_distance", 100.0)
MIN_TRIP_DISTANCE = get_config("cleaning.min_trip_distance", 0.1)
MAX_SPEED_MPH = get_config("cleaning.max_speed_mph", 80.0)


def _load(path: Path) -> pd.DataFrame:
    """Load a parquet file into a pandas DataFrame."""
    return pq.read_table(path).to_pandas()


def _save(df: pd.DataFrame, path: Path) -> None:
    """Save a DataFrame to a compressed parquet file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, compression="zstd", index=False)


def _add_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add derived features (trip_duration, weekday, time_slot)."""
    df = df.copy()
    df["tpep_pickup_datetime"] = pd.to_datetime(df["tpep_pickup_datetime"])
    df["tpep_dropoff_datetime"] = pd.to_datetime(df["tpep_dropoff_datetime"])
    df["trip_duration"] = (df["tpep_dropoff_datetime"] - df["tpep_pickup_datetime"]).dt.total_seconds() / 60.0
    df["weekday"] = df["tpep_pickup_datetime"].dt.weekday
    df["time_slot"] = df["tpep_pickup_datetime"].dt.hour * 2 + df["tpep_pickup_datetime"].dt.minute // 30
    return df


def clean(input_path, output_path, boundary_start, boundary_end, audit, label):
    """Clean uncleaned parquet file through 8 rules."""
    df = _load(input_path)
    before = len(df)
    audit.append({"rule": f"before_cleaning_{label}", "removed": 0, "remaining": before})

    df = _add_features(df)
    mask = (
        (df["tpep_pickup_datetime"] >= boundary_start)
        & (df["tpep_pickup_datetime"] < boundary_end)
        & (df["tpep_dropoff_datetime"] <= boundary_end)
        & (df["tpep_pickup_datetime"] < df["tpep_dropoff_datetime"])
    )
    removed = len(df) - mask.sum()
    df = df[mask].copy()
    audit.append({"rule": f"date_boundary_{label}", "removed": int(removed), "remaining": len(df)})

    required_cols = ["tpep_pickup_datetime", "tpep_dropoff_datetime", "PULocationID", "DOLocationID", "fare_amount"]
    before = len(df)
    df = df.dropna(subset=required_cols)
    audit.append({"rule": f"missing_required_fields_{label}", "removed": int(before - len(df)), "remaining": len(df)})

    before = len(df)
    df = df[df["PULocationID"].between(1, ZONE_COUNT) & df["DOLocationID"].between(1, ZONE_COUNT)]
    audit.append({"rule": f"invalid_zone_ids_{label}", "removed": int(before - len(df)), "remaining": len(df)})

    before = len(df)
    df = df[(df["fare_amount"] >= MIN_FARE) & (df["fare_amount"] <= MAX_FARE)]
    audit.append({"rule": f"fare_out_of_range_{label}", "removed": int(before - len(df)), "remaining": len(df)})

    before = len(df)
    df = df[(df["trip_duration"] >= MIN_TRIP_DURATION_MINUTES) & (df["trip_duration"] <= MAX_TRIP_DURATION_MINUTES)]
    audit.append({"rule": f"duration_out_of_range_{label}", "removed": int(before - len(df)), "remaining": len(df)})

    if "trip_distance" in df.columns:
        before = len(df)
        df = df[df["trip_distance"].between(MIN_TRIP_DISTANCE, MAX_TRIP_DISTANCE)]
        audit.append({"rule": f"distance_out_of_range_{label}", "removed": int(before - len(df)), "remaining": len(df)})

        before = len(df)
        speed = df["trip_distance"] / (df["trip_duration"] / 60.0)
        df = df[speed <= MAX_SPEED_MPH]
        audit.append({"rule": f"speed_exceeds_max_{label}", "removed": int(before - len(df)), "remaining": len(df)})

    before = len(df)
    dedup_cols = ["tpep_pickup_datetime", "tpep_dropoff_datetime", "PULocationID", "DOLocationID", "fare_amount"]
    if "trip_distance" in df.columns:
        dedup_cols.append("trip_distance")
    df = df.drop_duplicates(subset=[x for x in dedup_cols if x in df.columns])
    audit.append({"rule": f"duplicate_orders_{label}", "removed": int(before - len(df)), "remaining": len(df)})

    _save(df, output_path)
    return df


def build_statistics(train_df, output_path):
    """Build zone-time statistics from cleaned training data."""
    stats = (
        train_df.groupby(["PULocationID", "weekday", "time_slot"])
        .agg(pickup_count=("fare_amount", "count"),
             mean_fare_amount=("fare_amount", "mean"))
        .reset_index()
        .rename(columns={"PULocationID": "pickup_location_id"})
    )
    stats["pickup_count"] = stats["pickup_count"].astype(int)
    stats["mean_fare_amount"] = stats["mean_fare_amount"].round(6)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    stats.to_parquet(output_path, compression="zstd", index=False)
    logger.info("Statistics: %d rows written", len(stats))


def split_raw_data(raw_path: Path, train_path: Path, validation_path: Path) -> tuple[int, int]:
    """Create chronological uncleaned inputs from the official monthly parquet."""
    logger.info("Splitting raw data from %s", raw_path)
    frame = _load(raw_path)
    pickup = pd.to_datetime(frame["tpep_pickup_datetime"], errors="coerce")
    train_mask = (pickup >= TRAIN_BOUNDARY[0]) & (pickup < TRAIN_BOUNDARY[1])
    validation_mask = (pickup >= VAL_BOUNDARY[0]) & (pickup < VAL_BOUNDARY[1])
    train = frame.loc[train_mask].copy()
    validation = frame.loc[validation_mask].copy()
    _save(train, train_path)
    _save(validation, validation_path)
    logger.info("Raw split: train=%d validation=%d", len(train), len(validation))
    return len(train), len(validation)


def run_pipeline(
    *,
    raw_path: Path | None = None,
    processed_dir: Path | None = None,
    force_split: bool = False,
) -> None:
    """Run raw splitting, cleaning, and training-statistic generation."""
    project_root = Path(__file__).resolve().parents[2]
    data_dir = processed_dir or project_root / "data/processed"
    raw_path = raw_path or project_root / get_config(
        "paths.raw_data",
        "data/raw/yellow_tripdata_2023-01.parquet",
    )
    train_uncleaned = data_dir / "train_uncleaned.parquet"
    validation_uncleaned = data_dir / "validation_uncleaned.parquet"
    if force_split or not train_uncleaned.exists() or not validation_uncleaned.exists():
        split_raw_data(raw_path, train_uncleaned, validation_uncleaned)

    outputs_dir = project_root / "outputs"
    outputs_dir.mkdir(parents=True, exist_ok=True)
    audit = []

    logger.info("=== Cleaning training data ===")
    train_df = clean(
        train_uncleaned,
        data_dir / "train_cleaned.parquet",
        TRAIN_BOUNDARY[0], TRAIN_BOUNDARY[1], audit, "train"
    )

    logger.info("=== Cleaning validation data ===")
    val_df = clean(
        validation_uncleaned,
        data_dir / "validation_cleaned.parquet",
        VAL_BOUNDARY[0], VAL_BOUNDARY[1], audit, "validation"
    )

    logger.info("=== Building zone-time statistics ===")
    build_statistics(train_df, data_dir / "zone_time_statistics.parquet")

    audit_path = outputs_dir / "cleaning_audit.csv"
    with audit_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["rule", "removed", "remaining"])
        writer.writeheader()
        writer.writerows(audit)
    logger.info("Train: %d rows after cleaning", len(train_df))
    logger.info("Validation: %d rows after cleaning", len(val_df))


def main() -> None:
    """Run the full data pipeline from an official monthly parquet."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path)
    parser.add_argument("--processed-dir", type=Path)
    parser.add_argument("--force-split", action="store_true")
    args = parser.parse_args()
    run_pipeline(
        raw_path=args.raw,
        processed_dir=args.processed_dir,
        force_split=args.force_split,
    )


if __name__ == "__main__":
    main()
