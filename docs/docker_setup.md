# Docker Setup Guide

> Reproducible deployment for the Urban Mobility Decision Intelligence platform.

## Prerequisites

- Docker Engine 24+
- Docker Compose v2+

## Quick Start

### One-command deployment

```bash
docker compose up
# API  → http://localhost:8000/docs
# Demo → http://localhost:8501
```

`docker compose up` builds and runs both services with health checks.

### Build specific service images

```bash
docker build --target api -t nyc-taxi-api:latest .     # FastAPI service
docker build --target demo -t nyc-taxi-demo:latest .    # Streamlit dashboard
docker build --target test -t nyc-taxi-test:latest .    # Test harness
```

Multi-stage Dockerfile (`Dockerfile`):
- `source` — Python 3.12-slim base, copies the repo
- `api` — installs `.[api]`, serves FastAPI on `:8000`
- `demo` — installs `.[demo]`, serves Streamlit on `:8501`
- `test` — installs full stack (`.[dev,data,forecasting,graph,rl,api,demo]`), runs pytest

## Services

| Service | Image target | Port | Healthcheck | Purpose |
|---|---|---|---|---|
| `api` | `api` | 8000 | `/health` | REST API: recommendations, forecast, fleet, simulate, evaluate |
| `demo` | `demo` | 8501 | Streamlit `/_stcore/health` | Interactive dashboard (SIMULATION) |
| `test` | `test` | — | — | Runs the test suite |

## Data handling

- The `api` image **bakes in** `data/processed/` and `outputs/` so all endpoints
  (`/v1/recommendations`, `/simulate`, `/evaluate`) work out of the box.
- These directories are gitignored (large parquet files). Rebuild the image after
  re-running the data pipeline so the image reflects current artifacts:
  ```bash
  make all          # regenerate data/processed + outputs/
  docker compose build api
  docker compose up
  ```
- For BYO-data deployments, mount your own artifacts instead of rebuilding:
  ```bash
  docker run -p 8000:8000 \
    -v /host/data/processed:/app/data/processed \
    -v /host/outputs:/app/outputs \
    nyc-taxi-api:latest
  ```

## Notes

- All random seeds are fixed in `configs/` for reproducibility
- Results are written to `outputs/`
- Container uses Python 3.12-slim for minimal size
- The Streamlit dashboard is **simulation-only** and clearly labeled; it does not
  present production or A/B evidence
