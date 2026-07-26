# Phase 0 — Repository Upgrade Audit

> **Date:** 2026-07-26
> **Scope:** Full inventory of `src/`, `scripts/`, `data/`, `models/`, `simulator/`, `evaluation/`, `tests/`, `configs/`
> **Goal:** Baseline assessment before multi-year research-grade upgrade

---

## 1. Current System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                      NYC Taxi Zone Recommendation                    │
│              (January 2023 — Single-month experiment)                │
└─────────────────────────────────────────────────────────────────────┘

┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  Raw TLC │───>│  Clean   │───>│ Features │───>│  Model   │
│  Parquet │    │ Pipeline │    │ + Stats  │    │  Layer   │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
  Jan 2023       8 rules        zone-time         baselines
  only            filtering     stats (336×263)   forecasting
                                                    graph
┌──────────┐    ┌──────────┐    ┌──────────┐
│  Eval    │<───│Simulator │<───│  Policy  │
│  Layer   │    │  Layer   │    │  Layer   │
└──────────┘    └──────────┘    └──────────┘
 static diag    single-driver   two-step
 rollout        multi-agent     DQN/Double-DQN
 paired tests   finite demand   MDP value iter
```

---

## 2. Data Flow

### Current (January 2023 Only)

```
Step 1: Raw Download (manual)
  → data/raw/yellow_tripdata_2023-01.parquet

Step 2: Chronological Split (src/1_data_clean/clean.py::split_raw_data)
  → data/processed/train_uncleaned.parquet    (Jan 1 – Jan 24)
  → data/processed/validation_uncleaned.parquet (Jan 25 – Feb 1)

Step 3: Cleaning (src/1_data_clean/clean.py::clean)
  8 rules: date boundary, missing fields, invalid zones,
           fare range, duration range, distance range,
           speed cap, duplicate removal
  → data/processed/train_cleaned.parquet
  → data/processed/validation_cleaned.parquet

Step 4: Statistics (src/1_data_clean/clean.py::build_statistics)
  GroupBy [PULocationID, weekday, time_slot]
  → data/processed/zone_time_statistics.parquet

Step 5: Travel Time Matrix (scripts/build_travel_time_matrix.py)
  All-pairs shortest paths from OD graph
  → data/processed/travel_time_matrix_dijkstra.csv

Step 6: Validation Queries
  → data/processed/validation_input.parquet   (3360 queries)
  → data/processed/validation_answers.parquet  (reference utilities)
```

### Target (Multi-Year)

```
data/raw/
  YYYY/
    MM/  (auto-downloaded TLC parquet files)

data/processed/multi_year/
  train/        (2022–2023, cleaned)
  validation/   (2024, cleaned)
  test/         (2025, cleaned)
  zone_time_statistics/  (per-year)
  splits.json
```

---

## 3. Current Model Inventory

| Module | File | Type | Key Parameters |
|--------|------|------|----------------|
| Baseline 1 | `src/2_recommendation_algorithm/baseline_1.py` | Hot zone (historical demand) | Sort by pickup_count |
| Baseline 2.1 | `src/2_recommendation_algorithm/baseline_2_1.py` | Single-step best zone | demand × fare / travel_time |
| Baseline 2.2 | `src/2_recommendation_algorithm/baseline_2_2.py` | Single-step (public interface) | Same logic, simpler API |
| Improved Strategy | `src/2_recommendation_algorithm/improved_strategy.py` | Two-step finite-horizon | γ=0.5, λ=1.0, half_sat=240, pool=100 |
| Finite Horizon | `src/2_recommendation_algorithm/finite_horizon.py` | Multi-step lookahead | Configurable steps |
| Forecasting | `src/forecasting/model.py` | LightGBM + XGBoost | Poisson demand, MAE fare, 300 trees |
| Forecasting Strategy | `src/forecasting/strategy.py` | Forecast-enhanced ranking | predicted_demand × fare / (time+1) |
| Graph | `src/graph/builder.py` | OD graph construction | 4 node features, normalized adjacency |
| Graph Model | `src/graph/model.py` | GNN-enhanced LightGBM | Message-passing features |
| MDP | `src/mdp/model_based.py` | Value iteration | γ=0.5, ε=1e-4, 263 zones, 336 states |
| DQN | `src/rl/dqn.py` | DQN / Double DQN | 50 candidates, background 49 drivers |
| Q-Learning | `src/3_extension_task/extension_5_qlearning.py` | Tabular Q-learning | γ=0.9, α=0.1, ε=0.3, 5000 episodes |

---

## 4. Current Benchmark Process

### 4.1 Static Diagnostic
- **Queries:** 3360 (336 time slots × 10 zones), Jan 25 – Feb 1 2023
- **Metrics:** NDCG@3, Hit@3, reference utility@1
- **Reference:** Two-step → NDCG@3=0.9565, Hit@3=0.9714

### 4.2 Legacy Rollout
- **Window:** Jan 25–31, 2023 (7 days), 100 seeds, start zone 132
- **Metric:** Mean daily fare_amount
- **Hot Zone:** $431.21 | **Single-Step:** $548.77 | **Two-Step:** $570.61

### 4.3 Multi-Agent Simulator
- **Drivers:** 50, **Window:** Jan 25–31 2023, **Metric:** Revenue/driver
- **Sensitivity:** Demand/supply ratios 0.5, 1.0, 2.0

### 4.4 Forecasting Benchmark
- **Train:** Jan 8–20, **Validation:** Jan 21–24, 2023
- **Models:** LightGBM, XGBoost, ensemble
- **Best:** Ensemble demand MAE=1.4868

### 4.5 Graph Benchmark
- **Train:** Jan 1–24, **Validation:** Jan 25–31, 2023
- **Models:** LightGBM with OD messages, GraphSAGE, GAT
- **GraphSAGE MAE:** 1.4924 (CI crosses zero)

### 4.6 RL Benchmark
- **Train:** Jan 18–24, **Eval:** Jan 25–31, 2023
- **Drivers:** 50, **Runs:** 20 paired seeds
- **DQN:** $53.74/driver vs **Single-Step:** $46.96/driver

---

## 5. Reusable Modules

| Module | Reusability | Notes |
|--------|-------------|-------|
| `src/common/config.py` | High | Dot-notation config; trivial to extend |
| `src/common/data_loader.py` | Medium | Hardcoded 2023 paths; needs multi-year overload |
| `src/1_data_clean/clean.py` | High | Cleaning rules year-agnostic; date boundaries via config |
| `src/audit/statistics.py` | High | Paired comparison, bootstrap, effect size |
| `src/audit/temporal.py` | High | Temporal partition validation |
| `src/audit/fairness.py` | High | Exposure metrics |
| `src/eval/*` | Medium | Validation queries bound to Jan 2023 |
| `src/simulator/*` | High | Market cell model is date-agnostic |
| `src/graph/*` | High | Graph builder is year-agnostic |
| `scripts/*` | Medium | Most have hardcoded dates |

---

## 6. Technical Debt

### Critical
- [ ] **No automated data download** — Raw TLC parquet must be downloaded manually
- [ ] **Hardcoded January 2023 paths** throughout configs, scripts, and loaders
- [ ] **Single-month data** — No multi-year support
- [ ] **No versioned data splits** — Reproducibility risk

### Medium
- [ ] `configs/config.yaml` has flat path structure (no year/month patterns)
- [ ] Travel time matrix computed from single month (limited OD coverage)
- [ ] Validation queries specific to Jan 25–Feb 1 window
- [ ] Duplicate single-step implementations (baseline_2_1 vs baseline_2_2)
- [ ] `DataLoader.load_train_data()` returns `list[dict]` (inefficient for large data)
- [ ] No data integrity checks in pipeline
- [ ] `benchmark/run_ml_baselines.py` uses synthetic data, not real TLC data

### Low
- [ ] Global mutable `_CONFIG_CACHE` in `config.py` (thread-unsafe)
- [ ] Inconsistent config key naming (`domain.zone_count` vs `data.zone_count`)
- [ ] `requirements.txt` duplicates `pyproject.toml` dependencies

---

## 7. Upgrade Recommendations

### Phase 1 (Current)
- Multi-year dataset pipeline with automated TLC download
- Polars-based large-scale parquet processing
- Strict time-based split: Train (2022–2023), Validation (2024), Test (2025)
- Data protocol documentation
- Pipeline tests

### Phase 2 (Next)
- Extend statistics computation to multi-year
- Update config to support year/month pattern paths
- Add data versioning (split hash, manifest files)
- Parameterize evaluation scripts for date ranges
- Update travel time matrix from multi-year OD data

### Phase 3 (Future)
- Multi-year forecasting evaluation
- Year-stratified cross-validation
- Temporal drift analysis (2022–2025)
- Exogenous features (weather, events, holidays)
