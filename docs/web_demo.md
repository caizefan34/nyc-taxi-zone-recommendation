# Web Demo

## Overview
Streamlit-based interactive web demo for the NYC Taxi Zone Recommendation system.

## Prerequisites
```bash
pip install streamlit
```

## Usage
```bash
streamlit run app/app.py
```

## Features
- Interactive zone and time input
- Real-time demand forecast display
- Simulator state visualization
- Top-3 zone recommendations with expected rewards
- Expandable pipeline JSON view

## Architecture
```
User Input (zone, time)
    ↓
Feature Construction (build_features)
    ↓
Forecast Inference (forecast_demand)
    ↓
Simulator State Update (simulate_state)
    ↓
Policy Recommendation (recommend_policy)
    ↓
Streamlit UI Display
```

## Limitations
- Uses pre-computed historical averages (not trained models)
- Only 10 zones available in the dropdown (full set: 263)
- Simulation-based — no real deployment
- Single strategy (Historical Single-Step)
- Requires streamlit package installation
