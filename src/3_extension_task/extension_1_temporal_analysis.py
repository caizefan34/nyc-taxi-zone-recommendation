"""Extension 1: Temporal demand pattern analysis.

Analyzes how taxi demand varies by time of day, day of week, and location.
Generates statistical summaries of demand patterns across NYC zones.
"""
from __future__ import annotations
import json
import math
from pathlib import Path
import pyarrow.parquet as pq

PROJECT_ROOT = Path(__file__).resolve().parents[2]
STATISTICS_PATH = PROJECT_ROOT / "data/processed/zone_time_statistics.parquet"
OUTPUT_PATH = PROJECT_ROOT / "outputs/extension_temporal_analysis.json"

ZONE_COUNT = 263
SLOT_COUNT = 48


def main():
    table = pq.read_table(STATISTICS_PATH).to_pylist()
    
    # Aggregate by time slot across all zones and weekdays
    slot_demand = [0.0] * SLOT_COUNT
    slot_fare = [0.0] * SLOT_COUNT
    slot_count = [0] * SLOT_COUNT
    
    # Aggregate by weekday
    weekday_demand = [0.0] * 7
    weekday_fare = [0.0] * 7
    weekday_count = [0] * 7
    
    # Aggregate by zone
    zone_demand = [0.0] * ZONE_COUNT
    zone_fare = [0.0] * ZONE_COUNT
    zone_count = [0] * ZONE_COUNT
    
    # Top zones by total demand
    for row in table:
        loc = int(row["pickup_location_id"]) - 1
        wd = int(row["weekday"])
        ts = int(row["time_slot"])
        cnt = float(row["pickup_count"])
        fare = float(row["mean_fare_amount"]) if row["mean_fare_amount"] else 0.0
        
        slot_demand[ts] += cnt
        slot_fare[ts] += fare * cnt
        slot_count[ts] += cnt
        
        weekday_demand[wd] += cnt
        weekday_fare[wd] += fare * cnt
        weekday_count[wd] += cnt
        
        zone_demand[loc] += cnt
        zone_fare[loc] += fare * cnt
        zone_count[loc] += cnt
    
    # Average fare per slot
    slot_avg_fare = [slot_fare[i] / slot_count[i] if slot_count[i] > 0 else 0.0 for i in range(SLOT_COUNT)]
    weekday_avg_fare = [weekday_fare[i] / weekday_count[i] if weekday_count[i] > 0 else 0.0 for i in range(7)]
    zone_avg_fare = [zone_fare[i] / zone_count[i] if zone_count[i] > 0 else 0.0 for i in range(ZONE_COUNT)]
    
    # Peak hours: top 5 slots by demand
    peak_slots = sorted(range(SLOT_COUNT), key=lambda i: -slot_demand[i])[:5]
    
    # Top 10 zones by demand
    top_zones = sorted(range(ZONE_COUNT), key=lambda i: -zone_demand[i])[:10]
    
    # Rush hour analysis: morning (6-10) vs evening (16-20)
    morning_slots = list(range(12, 21))  # 6:00-10:30
    evening_slots = list(range(32, 41))  # 16:00-20:30
    morning_demand = sum(slot_demand[i] for i in morning_slots)
    evening_demand = sum(slot_demand[i] for i in evening_slots)
    total_demand = sum(slot_demand)
    
    result = {
        "total_training_records": sum(zone_count),
        "peak_hours_by_slot": [
            {"slot": s, "hour": f"{s // 2:02d}:{str((s % 2) * 30).zfill(2)}", "demand": slot_demand[s]}
            for s in peak_slots
        ],
        "rush_hour_analysis": {
            "morning_6_10_demand_pct": round(morning_demand / total_demand * 100, 2),
            "evening_16_20_demand_pct": round(evening_demand / total_demand * 100, 2),
            "morning_peak_hour": max(range(12, 21), key=lambda i: slot_demand[i]),
            "evening_peak_hour": max(range(32, 41), key=lambda i: slot_demand[i]),
        },
        "weekday_demand_distribution": [
            {"weekday": i, "name": ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"][i], "demand": weekday_demand[i], "avg_fare": round(weekday_avg_fare[i], 2)}
            for i in range(7)
        ],
        "top10_zones_by_demand": [
            {"zone": z + 1, "demand": zone_demand[z], "avg_fare": round(zone_avg_fare[z], 2)}
            for z in top_zones
        ],
        "demand_concentration": {
            "top3_zone_pct": round(sum(sorted(zone_demand, reverse=True)[:3]) / sum(zone_demand) * 100, 2),
            "top10_zone_pct": round(sum(sorted(zone_demand, reverse=True)[:10]) / sum(zone_demand) * 100, 2),
        },
        "fare_statistics": {
            "overall_mean_fare": round(sum(zone_fare) / sum(zone_count), 2),
            "max_mean_fare_zone": max(range(ZONE_COUNT), key=lambda i: zone_avg_fare[i]) + 1,
            "min_mean_fare_zone": min([i for i in range(ZONE_COUNT) if zone_count[i] > 0], key=lambda i: zone_avg_fare[i]) + 1,
        },
    }
    
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(f"\nResults written to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
