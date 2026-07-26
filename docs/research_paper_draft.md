
# Dynamic Urban Mobility Decision System

## Abstract

We present a reproducible research framework for urban mobility decision systems,
combining demand forecasting, calibrated multi-agent simulation, offline reinforcement
learning, and rigorous off-policy evaluation. Using 4 years of NYC Yellow Taxi data
across 263 zones, we demonstrate that better demand prediction does not automatically
translate into better repositioning policies.

## 1. Introduction

Taxi zone recommendation is a finite-horizon stochastic planning problem.
This paper presents an end-to-end framework from data ingestion to benchmark evaluation.

## 2. Related Work

Our work builds on three research threads: spatiotemporal demand forecasting,
simulation-based policy evaluation, and offline RL for sequential decision making.

## 3. Method

### 3.1 Data Pipeline
Processes NYC TLC Yellow Taxi data (2022-2025): trip-level cleaning, zone aggregation,
temporal feature engineering (lag, rolling, neighbor features).

### 3.2 Forecasting
Five models: Historical Average, LightGBM, XGBoost, GraphSAGE, and Temporal Graph
Transformer. The TGT achieves best MAE of 1.913 on 263 zones.

### 3.3 Simulator
Multi-agent simulation with 50 drivers competing for finite trip inventory.

### 3.4 Offline RL
Implicit Q-Learning (IQL) trained on simulator-generated trajectories.

### 3.5 OPE
Three estimators: Fitted Q-Evaluation, Weighted Importance Sampling, Doubly Robust.
Bootstrap confidence intervals with 2000 resamples.

## 4. Experiments

Full benchmark across 30 seeds, 7-day simulation episodes.

## 5. Results

Single-Step achieves $1764/driver, significantly outperforming Hot Zone ($1233) and
Two-Step ($1508). Calibration reduces fare RMSE by 64.9%.

## 6. Limitations

- Offline RL trained on simulator data, not real driver trajectories
- Single training seed does not capture RL training variability
- Limited to NYC Yellow Taxis; other cities and modes not tested

## 7. Conclusion

This work provides a reproducible benchmark for urban mobility decision systems,
demonstrating the gap between prediction accuracy and policy effectiveness.
