# Live Demo Guide

## Quick Start

### Option 1: Live Demo (No Installation)
Visit: https://caizefan34.github.io/urban-mobility-ai/web/

### Option 2: Run Locally
```bash
pip install -e ".[demo]"
streamlit run app/app.py
```

### Option 3: Docker
```bash
docker compose up
# Demo → http://localhost:8501
```

## What This Demo Shows

- **Interactive Map**: Explore NYC's 263 taxi zones with demand heatmaps
- **Demand Forecast**: Predict taxi demand for any zone and time
- **Policy Simulation**: Step-by-step AI decision walkthrough
- **Before/After Comparison**: Revenue, utilization, and wait time improvements

## Data Used

Uses pre-computed sample statistics (5MB). No large dataset download required.

## Limitations

- Results are **simulator estimates** — not production revenue
- Uses static pre-computed data — not real-time TLC feed
- NYC-specific models only

## For Researchers

To run the full benchmark or contribute:
- See [CONTRIBUTING.md](CONTRIBUTING.md)
- Submit to the [leaderboard](docs/leaderboard.md)
- Read the [methodology](docs/methodology.md)
