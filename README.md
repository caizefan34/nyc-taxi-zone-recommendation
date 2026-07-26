# Dynamic Urban Mobility Decision System

> **NYC taxi zone-level mobility optimization**: demand forecasting, calibrated multi-agent simulation, offline RL, and robust evaluation of repositioning policies.

[![docs](https://img.shields.io/badge/docs-live_site-00d2ff)](https://caizefan34.github.io/nyc-taxi-zone-recommendation/) [![python](https://img.shields.io/badge/python-3.10+-blue)](https://www.python.org/downloads/) [![license](https://img.shields.io/badge/license-MIT-green)](LICENSE) [![CI](https://img.shields.io/github/actions/workflow/status/caizefan34/nyc-taxi-zone-recommendation/ci.yml?branch=master&label=CI)](https://github.com/caizefan34/nyc-taxi-zone-recommendation/actions/workflows/ci.yml)

---

## Interactive Demo

[![Open in GitHub Pages](https://img.shields.io/badge/demo-interactive-00d2ff)](https://caizefan34.github.io/nyc-taxi-zone-recommendation/web/)

Experience the system without installing anything:
- **Interactive NYC Map** - Click zones to see demand/supply data
- **AI Decision Simulation** - Set conditions, run the pipeline, see recommendations
- **Policy Comparison** - Compare AI vs baseline policies
- **Forecast Visualization** - Historical vs forecast demand charts

**[Launch Interactive Demo](https://caizefan34.github.io/nyc-taxi-zone-recommendation/web/)**

*Simulation-based experience. See `docs/interactive_platform.md` for details.*

---

## Overview

Given a taxi driver current NYC zone and time of day, return top-3 zone recommendations to maximize expected revenue. This is a **finite-horizon stochastic planning problem** with 263 discrete zones, 336 half-hour slots/week, and multi-year NYC TLC data (2022-2025) with strict chronological splits.

**Core question:** *Can better demand prediction translate into better repositioning policy?*

---

## System Architecture

```
NYC TLC Data (2022-2025)
  -> Feature Engineering (calendar, weather, airport, traffic)
    -> Forecasting Models (LightGBM, XGBoost, Ensemble)
      -> Calibrated Dynamic Simulator (multi-agent v2)
        -> Offline RL Policies (DQN, Double DQN, IQL)
          -> OPE Evaluation (FQE, DR)
            -> Benchmark and Analysis
```

Pipeline diagram: `docs/results/architecture.png` | Benchmark figures: `docs/results/`

---

## Key Contributions

1. **Multi-year mobility data pipeline** - Polars-based ETL for 2022-2025 NYC TLC data with strict chronological splits and automated external features.
2. **Dynamic supply-demand simulator** - Multi-agent v2 with configurable demand-supply ratios, zone saturation, and driver competition. Calibration improves fare RMSE 8.88 -> 3.11 and travel MAE 3.03 -> 1.32.
3. **Simulator-calibrated offline RL** - DQN, Double DQN, and IQL pipelines with paired statistical tests. DQN achieves **$1,822/driver** (+$54 vs. greedy baseline, p < 1e-10).
4. **Research-grade evaluation** - Leakage-safe evaluation, honest negative results, cross-year robustness, latency/memory benchmarks, 274 passing tests.

---

## Key Results

### Forecasting (Demand MAE)

| Model | MAE | vs. Baseline |
|-------|:---:|:------------:|
| Historical Average | 1.727 | Baseline |
| LightGBM | 1.511 | -12.5% |
| GraphSAGE | 1.504 | CI crosses zero |
| **Ensemble** | **1.487** | **-13.9%** |

### Policy Revenue (50 drivers, 20 runs)

| Policy | Revenue/Driver | vs. Greedy | Significance |
|--------|:--------------:|:----------:|:------------:|
| Hot Zone | $1,237 | -$531 | -- |
| Single-Step | $1,768 | Baseline | -- |
| Double DQN | $1,743 | -$25 | p < 0.001 |
| **DQN** | **$1,822** | **+$54** | **p < 1e-10** |

### Calibration Validation

| Dimension | Before | After | Improved? |
|-----------|:------:|:-----:|:---------:|
| Fare RMSE | 8.883 | 3.109 | YES |
| Travel MAE | 3.034 | 1.315 | YES |
| Demand KL | 0.662 | 0.662 | NO |

### Honest Negative Results

- Graph signals do not improve forecasting (CI crosses zero vs. non-graph LightGBM)
- Better forecast does not mean better policy (-$17.88/day, p = 0.087)
- Double DQN underperforms DQN (-$25/driver despite theoretical advantage)
- Temporal drift detected (2024 MAE = 3.24, drift = yes)

---

## Honest Limitations

1. Offline RL trajectories are simulator-generated, not real logged driver data.
2. Simulation performance is not real-world deployment - models omit congestion, airport queues, strategic adaptation.
3. Temporal drift exists - models trained on 2023 may not generalize to 2024+.
4. OPE not validated against ground-truth online evaluation.
5. Exposure concentration - two-step strategy has 70% airport exposure (55% at JFK).

---

## Quick Start

```bash
git clone https://github.com/caizefan34/nyc-taxi-zone-recommendation.git
cd nyc-taxi-zone-recommendation
pip install -e ".[dev]"
python -m pytest tests -q

# Web demo (no install)
open web/index.html

# Streamlit demo
pip install streamlit && streamlit run app/app.py

# Data pipeline
python -m scripts.run_data_pipeline

# Forecasting benchmark
pip install -e ".[dev,forecasting,graph]"
python -m scripts.train_forecaster

# RL benchmarks
python -m scripts.train_rl_baselines --episodes 300 --drivers 50 --runs 20
python -m scripts.run_rl_benchmark_v2 --drivers 10 --seed 42

# Generate paper figures
python scripts/generate_paper_figures.py
```

---

## Repository Structure

```
src/             Core source (data, models, rl, simulator, eval, audit)
scripts/         Reproducible experiment runners
tests/           274 unit + integration tests
benchmark/       Standardized evaluation framework
app/             Streamlit web demo
web/             Interactive web demo (GitHub Pages)
docs/            Documentation, figures, research paper
configs/         Unified YAML configs
outputs/         Checked-in report and metric snapshots
```

---

## Validated Metrics

These precise values are validated against `outputs/*.json` snapshots to ensure documentation accuracy.

| Category | Metric | Value |
|----------|--------|:-----:|
| Recommendation | NDCG@3 | 0.9565 |
| Recommendation | Hit@3 | 0.9714 |
| Benchmark | Single-Step vs Hot Zone | +$531.16 |
| Offline RL | DQN vs Single-Step | +$53.74 |
| Forecasting | Ensemble Demand MAE | 1.4868 |
| Forecasting | Forecast-vs-Historical Rollout | -$17.88/day |
| Graph NN | GraphSAGE Demand MAE | 1.5037 |

> **Note**: Graph neural contribution is not statistically supported (CI crosses zero vs non-graph LightGBM).

---

## External Model Interface

Add new models via `src/interfaces/`:

```python
from src.interfaces import ForecastModel, Policy, RLPolicy
```
... implement the interface, then pass to benchmark runners.

```python
from benchmark.runners import run_forecast_benchmark
results = run_forecast_benchmark({"my_model": model})
```

See `docs/adding_new_models.md` for step-by-step guide.

---

## Cross-City Extension

Multi-city extension via `configs/city_template.yaml`. See `docs/cross_city_extension.md`.

> **Note**: Current experiments validated only for NYC. Cross-city results are future work.

---

## Citation

Cite the specific commit used and distinguish static diagnostic metrics from simulator outcomes.

## License

MIT. See [LICENSE](LICENSE).
