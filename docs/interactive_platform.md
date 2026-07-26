# Interactive Urban Mobility AI Platform

## Overview
An interactive web-based simulation platform demonstrating the NYC Taxi Zone Recommendation system. Deployed via GitHub Pages - no backend required.

## User Flow

```
1. Landing Page
   |-- Overview of system capabilities
       |-- "Run Interactive Simulation" button

2. NYC Zone Map
   |-- Interactive Leaflet.js map
       |-- Click on zones to view demand/supply data

3. Decision Simulation
   |-- Set time, weather, traffic conditions
       |-- "Run AI Decision"
           |-- Step 1: Demand Forecast visualization
           |-- Step 2: Policy Evaluation (candidate actions)
           |-- Step 3: AI Recommendation
               |-- "Apply Decision" -> Before/After comparison

4. Policy Comparison
   |-- Random vs AI Policy on key metrics

5. Forecast Visualization
   |-- Historical vs Forecast demand (Plotly.js)

6. Benchmark Dashboard
   |-- Key metrics from the research benchmark
```

## Architecture

```
+-------------------------------------------+
|              GitHub Pages                  |
|  +-------------------------------------+  |
|  |            index.html               |  |
|  |  +-------+ +-------+ +------+ +---+ |  |
|  |  | Map   | | Sim   | |Chart | |Bmk| |  |
|  |  |Module | |Module | |Module| |Mod| |  |
|  |  +-------+ +-------+ +------+ +---+ |  |
|  |  +-----------------------------+    |  |
|  |  |   zones.json (static)       |    |  |
|  |  +-----------------------------+    |  |
|  +-------------------------------------+  |
|  External CDNs: Leaflet.js, Plotly.js     |
+-------------------------------------------+
```

## Data Source
- Zone data: NYC TLC Taxi Zone Lookup Table (static sample)
- Demand/supply: Historical averages from the research benchmark
- Policy results: From benchmark_statistics.md and benchmark_report.md
- **All data is pre-computed, simulation-based - NOT real-time**

## Simulation Logic
1. User inputs time, weather, traffic
2. System looks up zone statistics from static JSON
3. Demand prediction: adjusts historical average based on time/weather factors
4. Policy evaluation: ranks zones by expected reward
5. Recommendation: selects top zones and computes expected impact
6. Before/After: compares current state with recommended state

## Limitations
- **Simulation-based experience only** - NOT real-time or production
- Uses pre-computed statistics, NOT live model inference
- Zone map shows sample zones (10 of 263), not full coverage
- Weather/traffic effects are simulated adjustments, not real data
- Does NOT replace the full research benchmark

## Modes
| Mode | Technology | Purpose |
|------|-----------|---------|
| Interactive Web | HTML/CSS/JS (GitHub Pages) | Quick public demo |
| Full Demo | Streamlit (app/app.py) | Full pipeline with code |
