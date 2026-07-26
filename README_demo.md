# NYC Taxi Zone Recommendation — Interactive Demo

## Quick Start

### Option 1: Live Demo (No Installation)
Visit: https://caizefan34.github.io/nyc-taxi-zone-recommendation/web/

### Option 2: Run Locally

```bash
pip install -r requirements-demo.txt
python app/app.py
```

### Option 3: Streamlit App

```bash
pip install streamlit
streamlit run app/app.py
```

## What This Demo Shows

- **Demand Forecast**: Predict taxi demand for any NYC zone and time
- **Policy Recommendation**: Top-3 zone recommendations using Two-Step Horizon planner
- **Simulation Outcome**: Expected revenue, travel time, and zone comparison

## Data Used

This demo uses pre-computed sample statistics (5MB). No large dataset download required.

## Limitations

- Results are **simulator estimates** — not production revenue
- Uses static pre-computed data — not real-time TLC feed
- NYC-specific models only

## For Researchers

To run the full benchmark or contribute:
- See [CONTRIBUTING.md](CONTRIBUTING.md)
- Submit to the [leaderboard](docs/leaderboard.md)
- Read the [methodology](docs/methodology.md)
