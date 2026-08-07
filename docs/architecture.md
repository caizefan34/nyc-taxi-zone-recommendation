# Platform Architecture

**Version:** 3.0 — Decision Intelligence Platform

## Design Principle

> Research-first, Commercial-ready Urban Mobility Decision Intelligence Platform

NYC Taxi is the reference implementation. The architecture generalizes to any city with zone-based trip data.

## Target Architecture

```
src/
├── data/                    # Data ingestion, validation, preprocessing (EXISTING, enhanced)
│   ├── download.py          # Multi-year TLC download
│   ├── pipeline.py          # Data pipeline with leakage-safe splits
│   └── __init__.py
│
├── forecasting/             # Demand/fare forecasting (EXISTING)
│   ├── model.py             # LightGBM, XGBoost, ensemble
│   ├── features.py          # Feature engineering
│   ├── strategy.py          # Forecast-enhanced recommendation adapter
│   ├── evaluation.py        # Forecast metrics
│   └── __init__.py
│
├── graph/                   # Graph neural features (EXISTING)
│   ├── builder.py           # OD graph construction
│   ├── model.py             # GraphSAGE, GAT
│   └── __init__.py
│
├── simulation/              # Multi-agent simulation (EXISTING)
│   ├── multi_agent/         # v1: finite demand, competition
│   ├── v2/                  # v2: dynamic supply-demand
│   ├── calibration.py       # Simulator calibration
│   └── validation/          # Simulator validation
│
├── decision/                # Decision Engine (NEW)
│   ├── engine.py            # Unified recommendation pipeline
│   ├── schemas.py           # Recommendation dataclass, Pydantic models
│   ├── policies/            # Policy wrappers
│   │   ├── base.py          # Base policy interface
│   │   ├── hot_zone.py      # Hot Zone wrapper
│   │   ├── single_step.py   # Single-Step wrapper
│   │   ├── two_step.py      # Two-Step wrapper
│   │   └── constraints.py   # Constraint-aware policy decorator
│   └── __init__.py
│
├── evaluation/              # Multi-modal evaluation (ENHANCED)
│   ├── offline/             # Static diagnostics (from eval/)
│   ├── simulation/          # Rollout evaluation
│   ├── shadow/              # Shadow mode (NEW)
│   ├── ab/                  # A/B testing (NEW)
│   ├── statistical/         # Bootstrap, CIs, tests
│   ├── counterfactual/      # IPS, SNIPS, DR
│   ├── historical_replay.py # Historical replay
│   └── __init__.py
│
├── api/                     # REST API (NEW)
│   ├── main.py              # FastAPI app
│   ├── routes/              # Route handlers
│   ├── schemas/             # Pydantic models
│   ├── services/            # Business logic
│   └── __init__.py
│
├── monitoring/              # Observability (NEW)
│   ├── metrics.py           # Metrics abstraction
│   ├── logging.py           # Structured logging
│   └── __init__.py
│
├── cities/                  # Multi-city abstraction (NEW)
│   ├── base.py              # CityAdapter interface
│   ├── nyc/                 # NYC reference implementation
│   └── __init__.py
│
├── common/                  # Shared utilities (EXISTING)
│   ├── config.py            # Configuration management
│   ├── data_loader.py       # Data loading
│   ├── logging_utils.py     # Logging setup
│   └── mlflow_tracking.py   # MLflow wrapper
│
├── 1_data_clean/            # Original data pipeline (PRESERVED)
├── 2_recommendation_algorithm/  # Original strategies (PRESERVED)
├── 3_extension_task/        # Original extensions (PRESERVED)
├── rl/                      # RL components (PRESERVED)
└── mdp/                     # MDP solver (PRESERVED)
```

## Key New Modules

### Decision Engine (`src/decision/`)

The unified abstraction layer. Wraps existing strategy functions with rich metadata.

```
Prediction → Candidate Generation → Optimization → Constraint Filter → Recommendation
```

### API (`src/api/`)

FastAPI application with:
- `/health`, `/ready`, `/version` — Health checks
- `/v1/recommendations` — Zone recommendations
- `/v1/demand/forecast` — Demand forecasting
- `/v1/fleet/optimize` — Fleet-wide optimization
- `/v1/models` — Model registry listing

### Shadow Evaluation (`src/evaluation/shadow/`)

```
Input vehicle state → AI Recommendation → DO NOT EXECUTE → Record
→ Observe actual outcome → Compare AI vs actual
```

### A/B Testing (`src/evaluation/ab/`)

Statistical framework for comparing policies:
- Bootstrap confidence intervals
- Paired comparison
- Effect size calculations
- Automatic source labeling (SIMULATION / SHADOW / REAL A/B)

### City Abstraction (`src/cities/`)

```
CityAdapter (interface)
  ├── zone definitions
  ├── trip ingestion
  ├── demand aggregation
  ├── travel time
  └── geospatial mapping

cities/nyc/  — NYC implementation
```

## Backward Compatibility

All existing code paths preserved:
- `src/1_data_clean/` → unchanged
- `src/2_recommendation_algorithm/` → unchanged (wrapped by decision engine)
- `src/3_extension_task/` → unchanged
- `src/eval/` → preserved (legacy evaluation)
- `scripts/` → unchanged
- `tests/` → existing tests unchanged; new tests added

## Migration Notes

1. New `Recommendation` dataclass wraps existing zone lists
2. Decision Engine adapters for old strategy functions
3. API serves new schemas; old functions still importable
4. No imports broken; no function signatures changed
