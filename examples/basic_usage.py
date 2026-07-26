#!/usr/bin/env python3
"""
NYC Taxi Zone Recommendation — Quick Demo

This script demonstrates the API without requiring the full NYC TLC dataset.
It works with the pre-computed statistics and zone metadata bundled with the repo.

Usage:
    python examples/basic_usage.py

Dependencies:
    pip install numpy pyyaml
"""
from __future__ import annotations

import csv
import sys
from datetime import datetime
from pathlib import Path


def load_zone_lookup(path: str) -> dict[int, str]:
    """Load taxi zone lookup table (LocationID -> Zone name)."""
    lookup = {}
    with open(path, "r", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            lid = int(row["LocationID"])
            zone = row["Zone"]
            borough = row.get("Borough", "")
            lookup[lid] = f"{zone} ({borough})" if borough else zone
    return lookup


def print_header(title: str) -> None:
    """Print a formatted section header."""
    print()
    print("=" * 68)
    print(f"  {title}")
    print("=" * 68)


def main() -> None:
    project_root = Path(__file__).resolve().parent.parent

    # ------------------------------------------------------------------ #
    # 1. Check environment
    # ------------------------------------------------------------------ #
    print_header("Environment Check")
    print(f"  Python:      {sys.version.split()[0]}")
    print(f"  Project:     {project_root}")

    # ------------------------------------------------------------------ #
    # 2. Load zone lookup
    # ------------------------------------------------------------------ #
    print_header("Zone Metadata")
    lookup_path = project_root / "data" / "meta" / "taxi_zone_lookup.csv"
    if lookup_path.exists():
        zones = load_zone_lookup(str(lookup_path))
        print(f"  Loaded {len(zones)} zone names")
        # Show a few sample zones
        for lid in [1, 132, 161, 236, 263]:
            if lid in zones:
                print(f"    Zone {lid:>3}: {zones[lid]}")
    else:
        print(f"  Zone lookup not found at {lookup_path}")
        print("  (Expected: only available with full data download)")
        zones = {}

    # ------------------------------------------------------------------ #
    # 3. Demonstrate the recommendation API concept
    # ------------------------------------------------------------------ #
    print_header("Recommendation API")
    print("  Interface:")
    print("    def recommend(current_datetime, current_location_id) -> list[int]")
    print()
    print("  Example calls (conceptual):")
    print()

    test_cases = [
        ("Weekday morning rush",   datetime(2023, 1, 30, 8, 15),   132),
        ("Weekday midday",         datetime(2023, 1, 30, 13, 0),    161),
        ("Weekday evening rush",    datetime(2023, 1, 30, 18, 30),   48),
        ("Weekend night",          datetime(2023, 1, 29, 23, 0),    236),
        ("Late night",             datetime(2023, 1, 30, 3, 0),     132),
    ]

    for label, dt, zone_id in test_cases:
        loc = zones.get(zone_id, f"Zone {zone_id}")
        print(f"  [{label}]")
        print(f"    Time: {dt.strftime('%Y-%m-%d %H:%M')} ({dt.strftime('%A')})")
        print(f"    Location: {loc}")
        print(f"    -> recommend({dt!r}, {zone_id})")
        print()

    # ------------------------------------------------------------------ #
    # 4. Show available strategy files
    # ------------------------------------------------------------------ #
    print_header("Available Strategies")
    strategies = [
        ("Baseline 1",    "Hot Zone Ranking",            "src/2_recommendation_algorithm/baseline_1.py"),
        ("Baseline 2",    "Single-Step Utility",         "src/2_recommendation_algorithm/baseline_2_2.py"),
        ("Two-Step",      "Truncated Lookahead",         "src/2_recommendation_algorithm/improved_strategy.py"),
        ("MDP",           "Model-Based Value Iteration", "src/mdp/model_based.py"),
    ]
    for name, desc, path in strategies:
        full_path = project_root / path
        exists = "OK" if full_path.exists() else "MISSING"
        print(f"  [{exists:7s}] {name:15s} - {desc:45s}  {path}")

    # ------------------------------------------------------------------ #
    # 5. Performance overview
    # ------------------------------------------------------------------ #
    print_header("Reproduced Performance")
    print(f"  {'Metric':<35s} {'Value':<12s} {'Context':<20s}")
    print(f"  {'-'*35} {'-'*12} {'-'*12}")
    print(f"  {'NDCG@3 (static)':<35s} {'0.9565':<12s} {'reference objective':<20s}")
    print(f"  {'Hit@3 (static)':<35s} {'0.9714':<12s} {'reference objective':<20s}")
    print(f"  {'Avg Daily Fare (rollout)':<35s} {'$570.61':<12s} {'single-driver simulator':<20s}")
    print(f"  {'Two-Step vs Single-Step':<35s} {'+$21.84':<12s} {'95% CI $5.00-$39.53':<20s}")
    print(f"  {'Airport Exposure':<35s} {'70.33%':<12s} {'saturation risk':<20s}")

    # ------------------------------------------------------------------ #
    # 6. Summary
    # ------------------------------------------------------------------ #
    print_header("How to Reproduce")
    print("  1. Download yellow_tripdata_2023-01.parquet from NYC TLC")
    print("     https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page")
    print("  2. Place in data/raw/")
    print("  3. Run:")
    print("     python -m scripts.run_data_pipeline --force-split")
    print("     python -m scripts.build_travel_time_matrix")
    print("     python -m pytest tests/ -v")
    print("  4. Evaluate:")
    print("     python -m src.eval.public_validation ...")
    print("     python -m src.eval.validation_rollout ...")
    print()
    print("  See README.md for detailed instructions.")
    print()


if __name__ == "__main__":
    main()

