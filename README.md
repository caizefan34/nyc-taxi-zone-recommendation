<div align="center">
  <img src="assets/social-preview.svg" width="100%" alt="NYC Taxi Zone Recommendation">
  <p><strong>Finite-Horizon Taxi Zone Recommendation with Reproducible Evaluation</strong></p>
  <p>
    <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.10%2B-blue" alt="Python 3.10+"></a>
    <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green" alt="MIT License"></a>
    <a href="https://github.com/caizefan34/nyc-taxi-zone-recommendation/actions/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/caizefan34/nyc-taxi-zone-recommendation/ci.yml?branch=master&label=CI" alt="CI"></a>
  </p>
</div>

## Overview

This repository studies a taxi-driver repositioning problem: given a driver's current NYC taxi zone and time, return three zones in ranked order.

The project includes:

- chronological cleaning of January 2023 NYC TLC Yellow Taxi trips;
- weekday/half-hour/zone demand and fare statistics;
- leakage-safe LightGBM/XGBoost demand and fare forecasting;
- training-only OD graph features with GraphSAGE and GAT embeddings;
- a directed OD travel-time graph and all-pairs shortest paths;
- hot-zone, single-step, and finite-horizon planning strategies;
- static reference-objective diagnostics and a fixed stochastic rollout;
- paired statistical tests, horizon experiments, robustness checks, and exposure-concentration analysis;
- a corrected model-based MDP implementation;
- a reproducible simulator-trained Q-learning extension.

The repository deliberately distinguishes three different claims:

1. Static NDCG/Hit measure agreement with a supplied two-step reference objective.
2. Rollout fare measures performance only inside the supplied single-driver simulator.
3. Neither metric is a causal estimate of real-world deployment revenue.

## Reproduced results

These values come from [`outputs/reference_metrics.json`](outputs/reference_metrics.json) and are rendered into [`outputs/evaluation_report.md`](outputs/evaluation_report.md).

### Static diagnostic: 3,360 public validation queries

| Strategy | NDCG@3 | Hit@3 | Reference utility@1 |
|---|---:|---:|---:|
| Hot Zone | 0.7846 | 0.5842 | 19.4299 |
| Single-Step | 0.9024 | 0.8804 | 25.0589 |
| Two-Step | **0.9565** | **0.9714** | **27.5855** |

### Paired 100-seed, seven-day rollout

| Strategy | Mean daily `fare_amount` |
|---|---:|
| Hot Zone | $431.21 |
| Single-Step | $548.77 |
| Two-Step | **$570.61** |

Two-Step minus Single-Step is +$21.84/day in this simulator, with paired bootstrap 95% CI [$5.00, $39.53], paired t-test p=0.0151, and Cohen's dz=0.247.

This interval describes Monte Carlo seed variation in one fixed simulator. It does not capture market drift, estimation error, competing drivers, congestion, or deployment interference.

### Supervised demand forecasting

The forecasting upgrade uses a chronological Jan 8--20 training window and Jan 21--24 validation window. All lag, rolling, and travel-neighborhood demand features use only earlier half-hour slots.

| Target | Metric | Historical average | LightGBM | Selected ensemble |
|---|---:|---:|---:|---:|
| Demand count | MAE | 1.7273 | 1.5114 | **1.4868** |
| Demand count | RMSE | 5.9237 | 5.0707 | **4.9810** |
| Mean fare | MAE | 7.0103 | 5.9526 | **5.9188** |

The ensemble demand MAE improvement is 0.2406 per zone-slot with timestamp-block bootstrap 95% CI [0.1960, 0.2820] and Cohen's dz=0.801. XGBoost on the same split reaches demand MAE 1.4956. Removing lag, rolling, or neighborhood features increases LightGBM demand MAE to 1.5344, 1.5632, and 1.5366 respectively.

Better forecast accuracy does not automatically improve the current recommendation objective. The forecast-enhanced single-step strategy scores NDCG@3 0.8835 and $530.89/day in the fixed rollout, versus 0.9024 and $548.77/day for historical Single-Step. Its paired rollout difference is -$17.88/day, 95% CI [-$38.15, $3.03]. The production/default Two-Step strategy therefore remains unchanged.

### Graph-enhanced forecasting

The graph upgrade builds a 263-zone OD graph from 1,865,434 trips strictly before the Jan 21 internal validation boundary. OD-weighted lag messages and static GraphSAGE/GAT embeddings augment the same LightGBM matrix:

| Model | Demand MAE | Demand RMSE |
|---|---:|---:|
| Non-graph LightGBM | 1.5114 | **5.0707** |
| OD messages + LightGBM | **1.5024** | 5.0745 |
| GraphSAGE + LightGBM | 1.5037 | 5.0716 |
| GAT + LightGBM | 1.5058 | 5.0734 |

GraphSAGE reduces MAE by 0.0077 (0.51%), but its timestamp-level 95% CI [-0.0042, 0.0200] crosses zero. GAT is weaker, and both learned embeddings underperform OD messages without embeddings. These results do not establish a graph-neural improvement; see [`outputs/graph_benchmark.md`](outputs/graph_benchmark.md).

### Horizon comparison

| Horizon | NDCG@3 | Mean daily fare |
|---|---:|---:|
| 1 | **0.9582** | $569.78 |
| 2 | 0.9565 | $570.61 |
| 3 | 0.9549 | $573.47 |
| 5 | 0.9525 | **$575.97** |
| Adaptive | 0.9559 | $573.31 |

The result is intentionally reported because it shows that higher reference-objective NDCG does not imply higher simulated fare.

## Method

For candidate zone `z` at arrival state `s`, the two-step score uses

$$
p(s,z)=\frac{D(s,z)}{D(s,z)+240},
$$

$$
V_1(s,z)=p(s,z)\bar f(s,z),
$$

$$
Q_2(o,z,s)=\frac{p(s,z)\left[\bar f(s,z)+\gamma\sum_{z'}P(z'\mid z)V_1(s',z')\right]
 +(1-p(s,z))\gamma V_1(s+1,z)}{m(o,z)+1}.
$$

`m(o,z)` is rounded relocation time in half-hour slots. The continuation policy waits in the reached zone; therefore this is truncated lookahead with a terminal heuristic, not a full horizon-2 Bellman-optimal policy.

The generalized implementation in [`finite_horizon.py`](src/2_recommendation_algorithm/finite_horizon.py) supports horizons 1, 2, 3, and 5 plus an adaptive stopping rule.

## Architecture

```text
official monthly TLC parquet
        |
        v
chronological raw split -> cleaning -> train_cleaned / validation_cleaned
        |                                |
        +-> zone-time demand/fare         +-> fixed validation rollout market
        +-> OD travel graph
        +-> OD transition/duration model
                    |
                    v
       baseline and finite-horizon strategies
                    |
          +---------+----------+
          v                    v
 static reference diagnostic  stochastic rollout
          |                    |
          +-> statistics, robustness, horizon, and exposure reports
```

## Setup

```bash
git clone https://github.com/caizefan34/nyc-taxi-zone-recommendation.git
cd nyc-taxi-zone-recommendation
python -m pip install -e ".[dev]"
```

Download `yellow_tripdata_2023-01.parquet` from the [NYC TLC trip record page](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page) and place it at:

```text
data/raw/yellow_tripdata_2023-01.parquet
```

## End-to-end data pipeline

```bash
python -m scripts.run_data_pipeline --force-split
python -m scripts.build_travel_time_matrix
```

The cleaning entry point now creates the chronological uncleaned train/validation inputs directly from the official monthly parquet before applying cleaning rules.

The public `validation_input.parquet` and `validation_answers.parquet` are course evaluation artifacts; they are not generated from the TLC raw file by this repository.

## Validation

```bash
python -m src.eval.sanity_check \
  --train-cleaned data/processed/train_cleaned.parquet \
  --validation-cleaned data/processed/validation_cleaned.parquet \
  --statistics data/processed/zone_time_statistics.parquet \
  --travel-times data/processed/travel_time_matrix_dijkstra.csv \
  --baseline-1 src/2_recommendation_algorithm/baseline_1.py \
  --baseline-2 src/2_recommendation_algorithm/baseline_2_2.py \
  --strategy src/2_recommendation_algorithm/improved_strategy.py \
  --output outputs/sanity_report.json

python -m src.eval.public_validation \
  --strategy src/2_recommendation_algorithm/improved_strategy.py \
  --queries data/processed/validation_input.parquet \
  --answers data/processed/validation_answers.parquet \
  --predictions outputs/validation_predictions.parquet \
  --output outputs/validation_static_metrics.json

python -m src.eval.validation_rollout \
  --strategy src/2_recommendation_algorithm/improved_strategy.py \
  --output outputs/validation_rollout.json
```

## Research evaluation

```bash
python -m scripts.run_paired_rollout_audit --runs 100
python -m scripts.run_horizon_audit --runs 100
python -m scripts.run_research_audit
python -m scripts.run_robustness_audit
python -m scripts.generate_evaluation_report
```

## Forecast training and benchmark

Install the optional tree-model dependencies, train both baselines, generate recursive holdout forecasts, and run the paired recommendation benchmark:

```bash
python -m pip install -e ".[dev,forecasting,graph]"
python -m scripts.train_forecaster
python -m scripts.run_forecasting_benchmark --runs 100
python -m scripts.run_graph_benchmark
```

Generated model and row-level prediction artifacts remain under `data/processed/` and are ignored by Git. Reproducible aggregate results are checked in as [`outputs/forecast_evaluation.md`](outputs/forecast_evaluation.md), [`outputs/forecast_evaluation.json`](outputs/forecast_evaluation.json), and [`outputs/forecasting_benchmark.md`](outputs/forecasting_benchmark.md). See [`docs/forecasting.md`](docs/forecasting.md) for feature semantics and limitations.

Real parameter selection:

```bash
python -m scripts.run_parameter_selection
```

The parameter runner evaluates every configured combination. It does not contain pre-filled metric values.

## Testing

```bash
python -m pytest tests -q
ruff check src tests scripts
```

Tests with the full local dataset cover strategy integration. Small synthetic fixtures cover raw temporal splitting, leakage checks, counterfactual estimators, statistical metrics, MDP Bellman transitions, and Q-learning reproducibility.

## Simulator boundary

The rollout is useful for controlled strategy comparison, but it has material limitations:

- one driver;
- immutable historical demand cells;
- no demand depletion;
- no competing-driver supply;
- no congestion or airport queues;
- no supply-demand feedback or equilibrium;
- fixed 60%/30%/10% compliance over the ranked Top-3.

Consequently, rollout improvements must not be presented as production revenue lift.

## Counterfactual and offline-RL boundary

NYC TLC trips do not contain logged reposition recommendations, logging-policy propensities, or driver acceptance. Valid IPS, SNIPS, doubly robust, CQL, or BCQ evaluation of a reposition policy is therefore not identifiable from these records alone.

The repository provides tested IPS/SNIPS/DR formulas for future data that contain the required logging fields. The Q-learning extension is explicitly described as online Q-learning inside an estimated simulator, not offline RL.

## Exposure and market impact

On the public static queries, the two-step strategy has 70.33% weighted airport exposure, including about 55.0% at JFK. Its exposure Gini is 0.982 and effective exposure count is 5.51 zones. These values indicate substantial saturation risk that is absent from the single-driver simulator.

See the full [research-grade audit](outputs/research_grade_audit.md) and [robustness plot](outputs/audit_robustness.png).

## Repository structure

```text
src/
  1_data_clean/                 raw split, cleaning, statistics
  2_recommendation_algorithm/  baselines, two-step, finite horizons, parameter selection
  3_extension_task/            temporal analysis, sensitivity, simulator Q-learning
  eval/                         static diagnostic and rollout
  mdp/                          corrected model-based value iteration
  forecasting/                  causal features, tree models, evaluation, strategy adapter
  graph/                        leakage-safe OD graph, GraphSAGE, GAT, message features
  audit/                        leakage, OPE formulas, statistics, fairness
scripts/                        reproducible research experiment runners
tests/                          unit and data-backed integration tests
outputs/                        checked-in report and reference metric snapshot
```

## Citation and status

This is an educational/research prototype, not a production dispatch system. If citing it, cite the repository commit used and distinguish static diagnostic metrics from simulator outcomes.

## License

MIT License. See [LICENSE](LICENSE).
