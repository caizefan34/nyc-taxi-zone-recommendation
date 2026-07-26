# Simulator vs Real NYC TLC Data: Validation Report

**Generated:** 2026-07-26 15:50:27

## Overview

This report compares the DynamicSimulator v2 against real NYC TLC Yellow Taxi trip records. The goal is to quantify how well the simulator reproduces real-world demand, temporal, and revenue distributions.

---

## 1. Zone Demand Distribution

### Metrics

| Metric | Value | Interpretation |
|--------|-------|----------------|
| KL Divergence | 0.404585 | Lower is better (0 = identical) |
| JS Divergence | 0.027441 | Bounded [0, 1], lower is better |
| Wasserstein Distance | 1.0476 | Lower is better |
| Correlation | 0.9924 | Higher is better |
| Real Mean Demand | 28.42 | Average real pickup count |
| Sim Mean Demand | 28.19 | Average simulated demand |
| Real Std Dev | 32.46 | Real distribution spread |
| Sim Std Dev | 31.31 | Simulated distribution spread |
| Sample Size | 263 | Number of zones/observations |

### Interpretation

> Good match (KL=0.4046, JS=0.0274, Wasserstein=1.05, correlation=0.9924)

---

## 2. Temporal Pattern Validation

### Hourly Demand Curve

| Metric | Value |
|--------|------:|
| Hourly RMSE | 4.0190 |
| Hourly Correlation | 0.9926 |
| Peak Hour (Real) | 18:00 |
| Peak Hour (Sim) | 18:00 |
| Trough Hour (Real) | 2:00 |
| Trough Hour (Sim) | 2:00 |

### Weekday vs Weekend Pattern

| Metric | Weekday | Weekend |
|--------|--------:|--------:|
| RMSE | 4.8227 | 2.8133 |
| Correlation | 0.9926 | 0.9926 |

### Temporal Interpretation

> Hourly: Hourly correlation: 0.9926 (RMSE=4.02)

> Weekday: Weekday correlation: 0.9926 (RMSE=4.82)

> Weekend: Weekend correlation: 0.9926 (RMSE=2.81)

---

## 3. Revenue / Fare Validation

| Metric | Real TLC Data | Simulator |
|--------|--------------:|----------:|
| Mean Fare/Reward |  |  |
| Std Dev |  |  |
| Correlation | - | 0.0000 |
| Sample Count | 10 | 10 |

### Revenue Interpretation

> Poor revenue match (real=25.34, sim=1865.62, diff=7261.1%)

---

## 4. Summary

### Overall Assessment

> The simulator diverges from real data in some dimensions. Calibration improvements may be needed.


### Limitations

- **Simulated demand** uses synthetic patterns based on configurable base demand, not real-time TLC data.
- **Revenue comparison** is approximate: simulator rewards include penalties
- **Temporal patterns** depend on simulator traffic/weather parameters
- This validation compares distribution statistics, not per-trip correspondence.

### Experiment Configuration

`json
{'drivers': 10, 'seed': 42, 'zone_count': 263}
`
