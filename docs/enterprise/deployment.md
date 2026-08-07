# Deployment Guide

## Docker Deployment

```bash
# Build and start all services
docker compose up

# API available at http://localhost:8000
# API docs at http://localhost:8000/docs
# Demo at http://localhost:8501
```

## Manual Deployment

```bash
# Install
pip install -e ".[dev,forecasting]"

# Start API
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --workers 1

# Start demo
streamlit run app/app.py --server.address=0.0.0.0 --server.port=8501
```

## Configuration

1. Copy `.env.example` to `.env`
2. Copy `configs/production.example.yaml` to `configs/production.yaml`
3. Customize for your environment

## Requirements

- Python 3.10+
- 2GB RAM minimum (8GB recommended for full benchmark)
- NYC TLC data in `data/raw/` (for full functionality)
- Pre-computed statistics in `data/processed/` (for demo mode)

## Limitations

- Single-worker API (not horizontally scaled)
- No persistent database (in-memory only)
- No authentication (add auth proxy for production)
- Models must be pre-trained (no online learning)
- Uses pre-computed historical statistics (not real-time data)
