# Reproduction Guide

**Version:** 1.0.0
**Date:** 2026-07-26
**Repository:** https://github.com/caizefan34/nyc-taxi-zone-recommendation

This guide provides step-by-step instructions to reproduce all experiments and benchmarks.

---

## Prerequisites

- Python 3.10+
- Git
- 8GB+ RAM (16GB recommended for full data processing)
- 10GB+ disk space for raw NYC TLC data

---

## Step 1: Environment Setup

**Purpose:** Create a reproducible Python environment with all dependencies.

```bash
# Clone the repository
git clone https://github.com/caizefan34/nyc-taxi-zone-recommendation.git
cd nyc-taxi-zone-recommendation

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

**Expected output:** All dependencies installed successfully.

---

## Step 2: Data Preparation

**Purpose:** Download and process NYC TLC Yellow Taxi data (2022-2025).

```bash
# Run the complete data pipeline
python scripts/run_data_pipeline.py
```

This script:
- Downloads monthly parquet files from the NYC TLC repository
- Cleans and validates trip records (duration, fare, distance filters)
- Generates temporal split manifests (train: 2022-2023, validation: 2024, test: 2025)
- Computes travel time matrix using Dijkstra on historical traffic data
- Saves processed data as Zstandard-compressed parquet files

**Expected output:** Processed data in `data/processed/multi_year/` with split manifests.
**Approximate runtime:** 15-30 minutes (download speed dependent).

---

## Step 3: Train Forecasting Model

**Purpose:** Train the LightGBM demand forecasting model.

```bash
python scripts/train_forecaster.py
```

This script:
- Loads processed training data
- Engineers features (temporal lags, rolling statistics, neighbor features)
- Trains LightGBM with 500 estimators (max_depth=8, 64 leaves)
- Evaluates on validation and test splits
- Saves model to `models/forecaster.pkl`

**Expected output:**
- Demand MAE ~1.51 on validation, ~1.49 on test
- Feature importance report
- Saved model file
**Approximate runtime:** 5-10 minutes.

---

## Step 4: Run Simulator

**Purpose:** Run the DynamicSimulator v2 with calibration.

```bash
# Run simulator comparison (v1 vs v2)
python scripts/run_simulator_comparison.py

# Run calibration validation
python scripts/run_calibration_validation.py

# Run simulator reality validation
python scripts/run_simulator_validation.py
```

These scripts:
- Run 50-driver, 7-day simulations
- Compare v1 (data-backed) and v2 (synthetic) simulators
- Validate simulator outputs against real TLC distributions
- Generate validation plots and reports in `outputs/`

**Expected output:**
- `outputs/simulator_comparison.md`
- `outputs/calibration_validation_report.md`
- `outputs/simulator_validation_report.md`
**Approximate runtime:** 10-20 minutes.

---

## Step 5: Train Offline RL

**Purpose:** Train IQL policy on simulator-generated trajectories.

```bash
# Train RL baselines (DQN, Double DQN)
python scripts/train_rl_baselines.py

# Run RL benchmark v2
python scripts/run_rl_benchmark_v2.py
```

These scripts:
- Collect simulator trajectories into replay buffer
- Train IQL with expectile regression (tau=0.7, beta=3.0)
- Train DQN and Double DQN for comparison
- Evaluate policies on held-out simulation episodes

**Expected output:**
- Trained policy checkpoints in `models/`
- RL benchmark reports in `outputs/rl_benchmark_v2.md`
**Approximate runtime:** 20-40 minutes.

---

## Step 6: Run Evaluation

**Purpose:** Evaluate policies using OPE and statistical benchmarks.

```bash
# Off-policy evaluation comparison
python scripts/run_ope_comparison.py

# Statistical benchmark
python scripts/run_forecasting_benchmark.py
python scripts/run_multi_agent_benchmark.py
python scripts/run_cross_year_benchmark.py
python scripts/run_benchmark_statistics.py
```

These scripts:
- Run FQE, WIS, and Doubly Robust OPE with bootstrap CIs
- Compare policies across forecast accuracy, decision quality, and RL metrics
- Compute cross-year robustness analysis
- Generate statistical significance tests with Cohen's d effect sizes

**Expected output:**
- `outputs/policy_evaluation_report.md`
- `outputs/forecasting_benchmark.md`
- `outputs/multi_agent_benchmark.md`
- `outputs/cross_year_benchmark.md`
- `outputs/benchmark_statistics.md`
**Approximate runtime:** 10-20 minutes.

---

## Step 7: Generate Full Benchmark

**Purpose:** Generate combined benchmark report and visualizations.

```bash
# Generate combined benchmark report
python scripts/generate_combined_benchmark.py

# Generate paper figures
python scripts/generate_paper_figures.py

# Run all tests
pytest tests/ -v --tb=short
```

**Expected output:**
- `outputs/benchmark_report.md`
- `docs/results/architecture.png` (system diagram)
- `docs/results/forecast_comparison.png`
- `docs/results/policy_comparison.png`
- `docs/results/calibration_effect.png`
- `docs/results/benchmark_summary.png`
- 274 passed, 15 skipped tests
**Approximate runtime:** 5-10 minutes.

---

## Reproducibility Notes

1. **Seeds**: All experiments use seed 42 by default. Results may vary slightly across
   hardware platforms and library versions.
2. **Data dependency**: 15 tests require downloaded TLC data and skip gracefully if absent.
3. **Hardware**: CPU-only training is supported. GPU CUDA support is optional for RL training.
4. **Version pinning**: See `requirements.txt` for exact dependency versions.
