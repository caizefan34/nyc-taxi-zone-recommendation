# API Documentation

## Decision Intelligence Platform API

**Base URL:** `http://localhost:8000`

### Source Label

All API responses include metadata indicating the data source:
```json
{"metadata": {"source": "simulation/historical_replay"}}
```

This platform uses historical data and simulation. No real-time NYC taxi data is connected.

### Endpoints

#### GET /health

Health check.

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "ok",
  "version": "3.0.0",
  "models_loaded": ["hot_zone", "single_step", "two_step"]
}
```

#### GET /ready

Readiness check — verifies models can be loaded.

#### GET /version

Version and build info.

#### GET /v1/models

List available models.

#### POST /v1/recommendations

Generate zone recommendation.

Request:
```json
{
  "vehicle_id": "vehicle_001",
  "latitude": 40.758,
  "longitude": -73.985,
  "zone_id": 161,
  "model_name": "two_step",
  "deterministic": true
}
```

Response:
```json
{
  "recommendation": {
    "vehicle_id": "vehicle_001",
    "timestamp": "2026-08-07T18:30:00Z",
    "current_zone": 161,
    "recommended_zone": 132,
    "ranked_zones": [
      {
        "zone_id": 132,
        "score": 0.91,
        "expected_demand": 41.7,
        "expected_supply": null,
        "expected_revenue": null,
        "travel_time_minutes": null
      }
    ],
    "confidence": 0.87,
    "model_name": "two_step",
    "model_version": "two-step-v1",
    "explanations": ["Deterministic recommendation"]
  },
  "alternatives": [],
  "metadata": {
    "model_version": "two-step-v1",
    "source": "simulation/historical_replay"
  }
}
```

#### POST /v1/demand/forecast

Get demand forecast for a zone.

#### POST /v1/fleet/optimize

Optimize recommendations for an entire fleet.

### Error Handling

Errors return:
```json
{
  "error": "description",
  "detail": "optional detail message",
  "timestamp": "2026-08-07T18:30:00Z"
}
```

### Model Names

| Name | Description |
|---|---|
| `hot_zone` | Ranks zones by historical pickup demand |
| `single_step` | Greedy single-step utility maximization |
| `two_step` | Truncated two-step horizon planning (default) |

### Interactive Docs

Start the API and visit:
- Swagger: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
