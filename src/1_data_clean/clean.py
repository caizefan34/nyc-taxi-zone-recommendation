"""Data cleaning pipeline for NYC taxi trip data."""
from __future__ import annotations
import csv
from datetime import datetime
from pathlib import Path
import pandas as pd
import pyarrow.parquet as pq

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ZONE_COUNT = 263
TRAIN_BOUNDARY = (datetime(2023, 1, 1, 0, 0), datetime(2023, 1, 25, 0, 0))
VAL_BOUNDARY = (datetime(2023, 1, 25, 0, 0), datetime(2023, 2, 1, 0, 0))
MAX_TRIP_DURATION_MINUTES = 240.0
MIN_TRIP_DURATION_MINUTES = 1.0
MAX_FARE = 200.0
MIN_FARE = 0.0
MAX_TRIP_DISTANCE = 100.0
MIN_TRIP_DISTANCE = 0.1
MAX_SPEED_MPH = 80.0


def _load(path: Path) -> pd.DataFrame:
    return pq.read_table(path).to_pandas()


def _save(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, compression="zstd", index=False)


def _add_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["tpep_pickup_datetime"] = pd.to_datetime(df["tpep_pickup_datetime"])
    df["tpep_dropoff_datetime"] = pd.to_datetime(df["tpep_dropoff_datetime"])
    df["trip_duration"] = (
        df["tpep_dropoff_datetime"] - df["tpep_pickup_datetime"]
    ).dt.total_seconds() / 60.0
    df["weekday"] = df["tpep_pickup_datetime"].dt.weekday
    df["time_slot"] = (
        df["tpep_pickup_datetime"].dt.hour * 2
        + df["tpep_pickup_datetime"].dt.minute // 30
    )
    return df


def clean(
    input_path, output_path, boundary_start, boundary_end, audit, label
):
    """Clean uncleaned parquet file and return cleaned DataFrame."""
    df = _load(input_path)
    before = len(df)
    audit.append(
        {"rule": f"before_cleaning_{label}", "removed": 0, "remaining": before}
    )

    # Rule 1: Fixed date boundaries
    df = _add_features(df)
    mask = (
        (df["tpep_pickup_datetime"] >= boundary_start)
        & (df["tpep_pickup_datetime"] < boundary_end)
        & (df["tpep_dropoff_datetime"] <= boundary_end)
        & (df["tpep_pickup_datetime"] < df["tpep_dropoff_datetime"])
    )
    removed = len(df) - mask.sum()
    df = df[mask].copy()
    audit.append(
        {
            "rule": f"date_boundary_{label}",
            "removed": int(removed),
            "remaining": len(df),
        }
    )

    # Rule 2: Missing required fields
    required_cols = [
        "tpep_pickup_datetime",
        "tpep_dropoff_datetime",
        "PULocationID",
        "DOLocationID",
        "fare_amount",
    ]
    before = len(df)
    df = df.dropna(subset=required_cols)
    removed = before - len(df)
    audit.append(
        {
            "rule": f"missing_required_fields_{label}",
            "removed": int(removed),
            "remaining": len(df),
        }
    )

    # Rule 3: Invalid zone IDs
    before = len(df)
    df = df[
        df["PULocationID"].between(1, ZONE_COUNT)
        & df["DOLocationID"].between(1, ZONE_COUNT)
    ]
    removed = before - len(df)
    audit.append(
        {
            "rule": f"invalid_zone_ids_{label}",
            "removed": int(removed),
            "remaining": len(df),
        }
    )

    # Rule 4: Fare out of range
    before = len(df)
    df = df[(df["fare_amount"] >= MIN_FARE) & (df["fare_amount"] <= MAX_FARE)]
    removed = before - len(df)
    audit.append(
        {
            "rule": f"fare_out_of_range_{label}",
            "removed": int(removed),
            "remaining": len(df),
        }
    )

    # Rule 5: Trip duration out of range
    before = len(df)
    df = df[
        (df["trip_duration"] >= MIN_TRIP_DURATION_MINUTES)
        & (df["trip_duration"] <= MAX_TRIP_DURATION_MINUTES)
    ]
    removed = before - len(df)
    audit.append(
        {
            "rule": f"duration_out_of_range_{label}",
            "removed": int(removed),
            "remaining": len(df),
        }
    )

    # Rule 6: Trip distance out of range
    if "trip_distance" in df.columns:
        before = len(df)
        df = df[df["trip_distance"].between(MIN_TRIP_DISTANCE, MAX_TRIP_DISTANCE)]
        removed = before - len(df)
        audit.append(
            {
                "rule": f"distance_out_of_range_{label}",
                "removed": int(removed),
                "remaining": len(df),
            }
        )

    # Rule 7: Speed check (distance / duration hours > MAX_SPEED_MPH)
    if "trip_distance" in df.columns:
        before = len(df)
        speed = df["trip_distance"] / (df["trip_duration"] / 60.0)
        df = df[speed <= MAX_SPEED_MPH]
        removed = before - len(df)
        audit.append(
            {
                "rule": f"speed_exceeds_max_{label}",
                "removed": int(removed),
                "remaining": len(df),
            }
        )

    # Rule 8: Duplicate orders
    before = len(df)
    dedup_cols = [
        "tpep_pickup_datetime",
        "tpep_dropoff_datetime",
        "PULocationID",
        "DOLocationID",
        "fare_amount",
    ]
    if "trip_distance" in df.columns:
        dedup_cols.append("trip_distance")
    existing = [c for c in dedup_cols if c in df.columns]
    df = df.drop_duplicates(subset=existing)
    removed = before - len(df)
    audit.append(
        {
            "rule": f"duplicate_orders_{label}",
            "removed": int(removed),
            "remaining": len(df),
        }
    )

    _save(df, output_path)
    return df


def build_statistics(train_df, output_path):
    """Build zone-time statistics from cleaned training data."""
    stats = (
        train_df.groupby(["PULocationID", "weekday", "time_slot"])
        .agg(
            pickup_count=("fare_amount", "count"),
            mean_fare_amount=("fare_amount", "mean"),
        )
        .reset_index()
        .rename(columns={"PULocationID": "pickup_location_id"})
    )
    stats["pickup_count"] = stats["pickup_count"].astype(int)
    stats["mean_fare_amount"] = stats["mean_fare_amount"].round(6)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    stats.to_parquet(output_path, compression="zstd", index=False)
    print(f"Statistics: {len(stats)} rows written")


def main():
    data_dir = PROJECT_ROOT / "data/processed"
    outputs_dir = PROJECT_ROOT / "outputs"
    outputs_dir.mkdir(parents=True, exist_ok=True)

    audit = []

    print("=== Cleaning training data ===")
    train_df = clean(
        data_dir / "train_uncleaned.parquet",
        data_dir / "train_cleaned.parquet",
        TRAIN_BOUNDARY[0],
        TRAIN_BOUNDARY[1],
        audit,
        "train",
    )

    print("=== Cleaning validation data ===")
    val_df = clean(
        data_dir / "validation_uncleaned.parquet",
        data_dir / "validation_cleaned.parquet",
        VAL_BOUNDARY[0],
        VAL_BOUNDARY[1],
        audit,
        "validation",
    )

    print("=== Building zone-time statistics ===")
    build_statistics(train_df, data_dir / "zone_time_statistics.parquet")

    audit_path = outputs_dir / "cleaning_audit.csv"
    with audit_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["rule", "removed", "remaining"])
        writer.writeheader()
        writer.writerows(audit)
    print(f"\nTrain: {len(train_df)} rows after cleaning")
    print(f"Validation: {len(val_df)} rows after cleaning")


if __name__ == "__main__":
    main()
