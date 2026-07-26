# Docker Setup Guide

> Reproducible environment for the NYC Taxi Zone Recommendation system.

## Prerequisites

- Docker Engine 24+
- Docker Compose v2+

## Quick Start

### Build the Docker image

```bash
docker build -t nyc-taxi-recommendation .
```

Builds a Python 3.12 environment with all dependencies. Uses multi-stage build for smaller image size.

### Run with Docker Compose

```bash
# Show available commands
docker compose run --rm nyc-taxi

# Run tests
docker compose run --rm test

# Train models
docker compose run --rm train
```

### Interactive shell

```bash
docker run -it --rm \
    -v .:/app \
    -e PYTHONPATH=/app \
    nyc-taxi-recommendation \
    /bin/bash
```

## Services

### `nyc-taxi` (default)
Entry point for general usage. Runs `make help` by default.

### `test`
Runs the test suite via `make test` (pytest).

### `train`
Runs full training pipeline via `make train` (data + forecasting + RL).

## Notes

- All random seeds are fixed in `configs/` for reproducibility
- Results are written to the mounted `outputs/` directory
- Container uses Python 3.12-slim for minimal size
- Volume mounts allow code changes without rebuilding
