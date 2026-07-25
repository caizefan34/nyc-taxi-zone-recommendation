"""Generate evidence tables used by the repository research audit."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

from src.audit.fairness import exposure_metrics
from src.audit.temporal import exact_trip_overlap, validate_temporal_partition

TRIP_KEY = [
    "tpep_pickup_datetime",
    "tpep_dropoff_datetime",
    "PULocationID",
    "DOLocationID",
    "fare_amount",
    "trip_distance",
]


def _prediction_metrics(path: Path, lookup: pd.DataFrame, premium_zones: set[int]) -> dict[str, object]:
    frame = pq.read_table(path, columns=["rank_1", "rank_2", "rank_3"]).to_pandas()
    rankings = frame[["rank_1", "rank_2", "rank_3"]].to_numpy()
    result = exposure_metrics(rankings)
    exposure = np.asarray(result.pop("exposure"), dtype=float)
    borough = lookup.set_index("LocationID")["Borough"].to_dict()
    airport_zones = set(lookup.loc[lookup["Zone"].str.contains("Airport", case=False, na=False), "LocationID"])

    def share(zone_ids: set[int]) -> float:
        indices = [zone - 1 for zone in zone_ids if 1 <= zone <= len(exposure)]
        return float(exposure[indices].sum() / exposure.sum()) if indices else 0.0

    manhattan = {int(zone) for zone, name in borough.items() if name == "Manhattan"}
    result.update(
        {
            "manhattan_exposure_share": share(manhattan),
            "airport_exposure_share": share(airport_zones),
            "premium_fare_zone_exposure_share": share(premium_zones),
        }
    )
    return result


def generate(repo: Path) -> dict[str, object]:
    processed = repo / "data" / "processed"
    train = pq.read_table(processed / "train_cleaned.parquet").to_pandas()
    validation = pq.read_table(processed / "validation_cleaned.parquet").to_pandas()
    partition = validate_temporal_partition(
        train["tpep_pickup_datetime"],
        train["tpep_dropoff_datetime"],
        validation["tpep_pickup_datetime"],
        validation["tpep_dropoff_datetime"],
    )
    partition = {key: (value.isoformat() if hasattr(value, "isoformat") else value) for key, value in partition.items()}
    overlap_columns = [column for column in TRIP_KEY if column in train and column in validation]

    expected_stats = (
        train.groupby(["PULocationID", "weekday", "time_slot"], as_index=False)
        .agg(pickup_count=("fare_amount", "count"), mean_fare_amount=("fare_amount", "mean"))
        .rename(columns={"PULocationID": "pickup_location_id"})
        .sort_values(["pickup_location_id", "weekday", "time_slot"])
        .reset_index(drop=True)
    )
    actual_stats = (
        pq.read_table(processed / "zone_time_statistics.parquet").to_pandas()
        .sort_values(["pickup_location_id", "weekday", "time_slot"])
        .reset_index(drop=True)
    )
    stats_match = (
        len(expected_stats) == len(actual_stats)
        and np.array_equal(expected_stats["pickup_count"], actual_stats["pickup_count"])
        and np.allclose(expected_stats["mean_fare_amount"], actual_stats["mean_fare_amount"], atol=1e-6)
    )

    zone_fares = train.groupby("PULocationID")["fare_amount"].mean()
    premium_threshold = float(zone_fares.quantile(0.9))
    premium_zones = set(int(zone) for zone in zone_fares[zone_fares >= premium_threshold].index)
    lookup = pd.read_csv(repo / "data" / "meta" / "taxi_zone_lookup.csv")
    prediction_files = {
        "baseline_1": repo / "outputs" / "audit_b1_predictions.parquet",
        "baseline_2": repo / "outputs" / "audit_b2_predictions.parquet",
        "two_step": repo / "outputs" / "audit_improved_predictions.parquet",
    }

    return {
        "data": {
            "train_rows": len(train),
            "validation_rows": len(validation),
            "temporal_partition": partition,
            "exact_cross_split_trip_overlap": exact_trip_overlap(train, validation, overlap_columns),
            "statistics_exactly_reconstructed_from_train": bool(stats_match),
            "statistics_rows": len(actual_stats),
        },
        "counterfactual_identifiability": {
            "logged_recommendation_action": False,
            "logged_behavior_propensity": False,
            "logged_driver_acceptance": False,
            "ips_snips_dr_on_tlc_trips": "not identifiable",
            "reason": (
                "TLC trip records contain realized passenger trips, not recommendation actions "
                "sampled by a known logging policy."
            ),
        },
        "fairness": {
            name: _prediction_metrics(path, lookup, premium_zones)
            for name, path in prediction_files.items()
            if path.exists()
        },
        "premium_fare_definition": {
            "threshold": premium_threshold,
            "zone_count": len(premium_zones),
            "definition": "top decile of training-period zone mean fare_amount",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, default=Path("outputs/research_audit_evidence.json"))
    args = parser.parse_args()
    result = generate(args.repo.resolve())
    output = args.output if args.output.is_absolute() else args.repo / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
