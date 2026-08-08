# Repository Audit — urban-mobility-ai

> **Date:** 2026-08-08
> **Version audited:** v3.0.0 (commit `499f918`)
> **Audit type:** Static code + test + config review. **No production/deployment data exists** — all quality claims below are about code maturity and simulated results, not real-world validation.

---

## 1. Executive Snapshot

| Dimension | Verdict | Notes |
|---|---|---|
| **Research capability** | Strong | Forecasting, RL, OPE, multi-agent sim, honest negative results |
| **Engineering maturity** | Strong | FastAPI, Docker, CI, configs, logging, registry, 402 tests |
| **Commercial readiness** | **Prototype platform** | NOT pilot-ready. No real data pipeline, no real fleet, no deployment |
| **Community readiness** | Strong | CONTRIBUTING, issue templates, benchmark submission flow |

**Bottom line:** The repository is a credible **research-grade prototype platform**. It should NOT be described as production-ready or validated on real-world deployments. The README already correctly labels results as simulator outcomes.

---

## 2. Architecture

### Current modules (`src/`)

| Module | Purpose | Maturity |
|---|---|---|
| `src/1_data_clean`, `2_recommendation_algorithm`, `3_extension_task` | Legacy sequential pipeline (clean → strategy → extension) | Legacy, kept for reproducibility |
| `src/data/` | Data download + pipeline | Functional |
| `src/forecasting/` | LightGBM/XGBoost ensemble demand forecasting | Functional |
| `src/graph/`, `src/features/temporal_graph/` | GraphSAGE/GAT, temporal graph | Functional, honest negative result |
| `src/mdp/` | Two-step MDP value iteration | Core strategy |
| `src/decision/` | **Unified decision engine** (Recommendation, RankedZone, constraints) | Core v3 asset |
| `src/simulator/` | Multi-agent v2 simulator + validation | Biggest research asset |
| `src/rl/` | DQN, Double DQN, IQL, mean-field | Functional |
| `src/evaluation/` | Shadow, historical replay, A/B, OPE | Core v3.5 asset |
| `src/cities/` | CityAdapter + NYC/Chicago/London/Singapore stubs | NYC real, others stubbed |
| `src/api/` | FastAPI app | Functional |
| `src/audit/`, `src/monitoring/`, `src/interfaces/`, `src/common/` | Audits, registry, interfaces, utils | Functional |

### Dependencies

- Core: numpy, pandas, pyarrow, scipy, matplotlib, pyyaml
- Optional extras: `api` (fastapi/pydantic/uvicorn), `demo` (streamlit), `forecasting` (lightgbm/xgboost/sklearn), `graph`/`rl` (torch, gymnasium), `dev` (pytest/ruff), `docs` (sphinx)
- Locked via `pyproject.toml` (setuptools, `pip install -e ".[dev,api,demo]"`)

### Data flow

```
NYC TLC raw trips → clean (chronological split, 263 zones) → processed
→ features (temporal, external: weather/events/airport) → forecast / graph / MDP
→ decision engine → multi-agent simulator → OPE (WIS / DR / bootstrap CI) → report
```

### Model flow

Forecasting (LGB/XGB) → OD graph (GraphSAGE/GAT) → MDP (two-step) → RL (DQN/DoubleDQN/IQL) → decision engine wraps all into unified `Recommendation`.

### Evaluation pipeline

Static diagnostics (NDCG@3/Hit@3/Utility) → simulator rollouts (daily fare) → multi-seed RL (bootstrap CI) → multi-agent competition → OPE (WIS/sequential DR) → shadow/historical replay → A/B.

---

## 3. Research Capability

### Strengths

1. **Decision-aware forecasting finding** — empirically shows better MAE → worse decisions (-$17.88/day). Genuine, non-obvious research contribution.
2. **Trajectory-level OPE** — WIS + sequential DR with complete-episode bootstrap in spatiotemporal recommendation.
3. **Honest negative results** — graph features don't help, IQL transfer fails, Double DQN underperforms. This is rare and credible.
4. **Multi-agent market effect experiment** — `outputs/experiments/adoption_sweep.json` already contains 1%–100% adoption sweep results.
5. **Mean-field RL** — population-level approximation exists.
6. **Exposure/fairness audit** — documents airport concentration (70.33%) and Gini 0.982.
7. **402 tests** covering math, leakage-safety, statistical correctness.

### Weaknesses

1. **`docs/research/multi_agent_market_effect.md` missing** — the experiment *data* exists but the research write-up does not. This is the single clearest gap.
2. **No LLM agent layer** — no tool-calling scaffold for explainable mobility queries.
3. **Cross-city adapters for Chicago/London/Singapore are stubs** — only NYC is real.
4. **No congestion proxy with vehicle-density → travel-time coupling** documented as a first-class research lever (v2 dynamics has a `traffic_multiplier` but no density-coupled experiment).
5. **No benchmark `run.py` CLI** — external submission requires `run_external_model.py`, which is functional but not a unified `--model/--city` entry point.

### Missing research opportunities

- Policy adoption dynamics (data exists, write-up missing)
- Congestion as a function of fleet density (levers exist, experiment missing)
- Cross-city transfer (adapter interface exists, data missing)
- Forecast-decision joint optimization (finding exists, method missing)

---

## 4. Engineering Maturity

| Area | Status |
|---|---|
| API | FastAPI, `/health` `/ready` `/version` `/v1/recommendations` `/v1/demand/forecast` `/v1/fleet/optimize` `/v1/models` |
| Docker | Multi-stage Dockerfile (api/demo/test), docker-compose.yml, `.env.example` |
| Configuration | YAML configs + hydra config + `.env.example` |
| Logging | Structured request logging with latency + `X-Source: simulation/historical_replay` header |
| Testing | 402 tests, pytest-cov, CI matrix (3.10/3.12) |
| Deployment | Docker Compose one-click; no K8s/Terraform |
| Monitoring | `src/monitoring/` metrics + registry; no Prometheus/Grafana wiring |

**Gap:** API lacks `/simulate` and `/evaluate` endpoints (Phase 6 in the target spec). Benchmark lacks a root-level `run.py`.

---

## 5. Commercial Readiness

**Verdict: Research prototype platform.** Not pilot-ready.

| Evidence for readiness | Evidence against |
|---|---|
| Deterministic inference mode (`deterministic=True`) | No real fleet API / real-time pipeline |
| Pydantic validation on all endpoints | No production A/B results |
| Registry/versioning for models | No real logged propensities for identifiable OPE |
| Docker one-click deploy | No K8s/Terraform, no auth/rate-limiting |
| Honest `X-Source` labeling | Simulator-only outcomes; no congestion/airport queues |

---

## 6. Gaps vs. the target spec (this upgrade)

1. `docs/repository_audit.md` — **this document** (Phase 0 deliverable)
2. `benchmark/run.py` CLI: `--model X --city Y` + leaderboard regeneration (Phase 5)
3. API `POST /simulate` + `POST /evaluate` (Phase 6)
4. `docs/research/multi_agent_market_effect.md` — write-up from existing `adoption_sweep.json` (Phase 3)
5. LLM Mobility Agent scaffold — tool-calling architecture, real tools only (Phase 11)
6. Unified `docs/{architecture,research,benchmark,deployment,enterprise}.md` entry points (Phase 12)

Everything else in the 14-phase spec is already present and functional.

---

## 7. Scientific Honesty Status

- ✅ Results labeled "simulator outcomes — not production revenue estimates"
- ✅ Counterfactual identifiability limitation documented
- ✅ Evaluation types distinguished (simulation / historical replay / shadow)
- ✅ No fabricated A/B or deployment claims
- ✅ Honest negative results published
