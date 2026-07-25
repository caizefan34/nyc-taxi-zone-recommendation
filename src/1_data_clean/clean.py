"""Data cleaning pipeline for NYC taxi trip data."""
from __future__ import annotations

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


def main():
    """Run the full data cleaning pipeline."""
    data_dir = Path(__file__).resolve().parents[2] / "data/processed"
    outputs_dir = Path(__file__).resolve().parents[2] / "outputs"
    outputs_dir.mkdir(parents=True, exist_ok=True)
    audit = []

    logger.info("=== Cleaning training data ===")
    train_df = clean(
        data_dir / "train_uncleaned.parquet",
        data_dir / "train_cleaned.parquet",
        TRAIN_BOUNDARY[0], TRAIN_BOUNDARY[1], audit, "train"
    )

    logger.info("=== Cleaning validation data ===")
    val_df = clean(
        data_dir / "validation_uncleaned.parquet",
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


if __name__ == "__main__":
    main()
