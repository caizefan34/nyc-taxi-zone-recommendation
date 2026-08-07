#!/usr/bin/env python3
"""Example: Get a zone recommendation via the Decision Engine.

Usage: python examples/recommendation.py
"""
from datetime import datetime

from src.decision.engine import build_recommendation, compute_confidence


def main():
    # Simulate importing a strategy
    try:
        from src.2_recommendation_algorithm.improved_strategy import recommend
        use_real = True
    except ImportError:
        use_real = False
        print("Real strategies not available (data not loaded). Using demo path.")

    now = datetime(2023, 1, 15, 18, 30)
    zone = 161  # Midtown Center

    if use_real:
        ranked = recommend(now, zone)
    else:
        ranked = [132, 236, 237]

    rec = build_recommendation(
        vehicle_id="demo_vehicle",
        current_time=now,
        current_zone=zone,
        ranked_zone_ids=list(ranked),
        model_name="two_step",
        model_version="v1",
    )
    rec.confidence = compute_confidence(rec.ranked_zones)
    rec.explanations.append("High predicted demand in recommended zone")
    rec.explanations.append("Low predicted supply competition")

    print(rec.to_dict())


if __name__ == "__main__":
    main()
