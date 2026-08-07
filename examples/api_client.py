#!/usr/bin/env python3
"""Example: Call the Decision Intelligence API.

Start the API first:
    uvicorn src.api.main:app --host 0.0.0.0 --port 8000

Then run this script:
    python examples/api_client.py
"""
import json
import urllib.request


BASE = "http://localhost:8000"


def api_get(path):
    with urllib.request.urlopen(f"{BASE}{path}") as resp:
        return json.loads(resp.read())


def api_post(path, data):
    body = json.dumps(data).encode()
    req = urllib.request.Request(
        f"{BASE}{path}",
        data=body,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def main():
    # Check health
    health = api_get("/health")
    print(f"Health:  {health['status']} (v{health['version']})")

    # Check ready
    ready = api_get("/ready")
    print(f"Ready:   {ready['ready']}")

    # List models
    models = api_get("/v1/models")
    print(f"Models:  {json.dumps(models, indent=2)}")

    # Get recommendation
    rec = api_post("/v1/recommendations", {
        "vehicle_id": "example_001",
        "zone_id": 161,
        "model_name": "two_step",
    })
    print(f"\nRecommendation:")
    r = rec["recommendation"]
    print(f"  Vehicle: {r['vehicle_id']}")
    print(f"  Current zone: {r['current_zone']}")
    print(f"  Recommended zone: {r['recommended_zone']}")
    print(f"  Confidence: {r.get('confidence')}")
    print(f"  Top zones: {[z['zone_id'] for z in r['ranked_zones']]}")

    # Get demand forecast
    forecast = api_post("/v1/demand/forecast", {
        "zone_id": 132,
        "horizon_minutes": 60,
    })
    print(f"\nDemand Forecast (Zone 132):")
    print(f"  Predicted demand: {forecast['predicted_demand']}")
    print(f"  Model: {forecast['model_name']}")

    print(f"\nSource: {rec['metadata'].get('source', 'unknown')}")
    print("Note: Results are simulation/historical replay based. Not real-time data.")


if __name__ == "__main__":
    main()
