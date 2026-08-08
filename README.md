<div align="center">
  <img src="assets/social-preview.svg" width="100%" alt="Urban Mobility Decision Intelligence">

  <h1>Urban Mobility Decision Intelligence</h1>

  <p>
    <strong>
      An open-source decision intelligence platform for dynamic fleet repositioning —<br>
      demand forecasting, multi-agent simulation, offline reinforcement learning, and reproducible evaluation.
    </strong>
  </p>

  <!-- Badges -->
  <p>
    <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.10%2B-blue?logo=python&logoColor=white" alt="Python"></a>
    <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green?logo=opensourceinitiative&logoColor=white" alt="License"></a>
    <a href="https://github.com/caizefan34/nyc-taxi-zone-recommendation/actions/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/caizefan34/nyc-taxi-zone-recommendation/ci.yml?branch=master&logo=githubactions&logoColor=white&label=tests" alt="CI"></a>
    <a href="https://github.com/caizefan34/nyc-taxi-zone-recommendation"><img src="https://img.shields.io/github/stars/caizefan34/nyc-taxi-zone-recommendation?style=social" alt="Stars"></a>
    <a href="https://github.com/caizefan34/nyc-taxi-zone-recommendation"><img src="https://img.shields.io/github/forks/caizefan34/nyc-taxi-zone-recommendation?style=social" alt="Forks"></a>
  </p>
  <p>
    <a href="docs/badges/reproducibility.svg"><img src="docs/badges/reproducibility.svg" alt="Reproducible"></a>
    <a href="docs/badges/benchmark.svg"><img src="docs/badges/benchmark.svg" alt="Benchmark"></a>
    <a href="docs/badges/documentation.svg"><img src="docs/badges/documentation.svg" alt="Documentation"></a>
    <a href="#quick-start"><img src="https://img.shields.io/badge/docker-ready-blue?logo=docker&logoColor=white" alt="Docker"></a>
    <a href="CONTRIBUTING.md"><img src="https://img.shields.io/badge/contributions-welcome-brightgreen?logo=github" alt="Contributions"></a>
    <a href="https://doi.org/10.5281/zenodo.XXXXXXX"><img src="https://img.shields.io/badge/DOI-10.5281%2Fzenodo.XXXXXXX-blue?logo=doi" alt="DOI"></a>
  </p>

  <!-- Quick Links -->
  <p>
    <a href="https://caizefan34.github.io/nyc-taxi-zone-recommendation/web/"><strong>Live Demo</strong></a>
    &nbsp;·&nbsp;
    <a href="https://caizefan34.github.io/nyc-taxi-zone-recommendation/docs/"><strong>Documentation</strong></a>
    &nbsp;·&nbsp;
    <a href="#quick-start"><strong>Quick Start</strong></a>
    &nbsp;·&nbsp;
    <a href="docs/research_paper_draft.md"><strong>Paper Draft</strong></a>
    &nbsp;·&nbsp;
    <a href="ROADMAP.md"><strong>Roadmap</strong></a>
    &nbsp;·&nbsp;
    <a href="https://github.com/caizefan34/nyc-taxi-zone-recommendation/discussions"><strong>Discussions</strong></a>
  </p>
</div>

---

## Platform Overview

```
Historical/Real-time Mobility Data
          ↓
   Demand Forecasting
          ↓
 Supply-Demand Modeling
          ↓
  Mobility Simulation
          ↓
 Decision / Policy Engine
          ↓
   Fleet Optimization
          ↓
Recommendation / API / Dashboard
          ↓
Shadow Evaluation / A-B Testing
```

**NYC Taxi** is the reference implementation. The architecture generalizes to any city with zone-based trip data: Chicago, London, Singapore, ride-hailing, delivery, autonomous fleets.

---

## Why this project?

**The problem:** Taxi drivers waste 30-60% of their shift cruising for passengers. In NYC alone, this represents millions of dollars in lost revenue and unnecessary congestion annually.

**The approach:** We treat fleet repositioning as a sequential decision problem combining forecasting, simulation, and optimization:

```
Historical trips  →  Demand Forecasting  →  Simulator  →  Policy Optimization  →  Recommendation
                       ↓                      ↓               ↓
                    LightGBM/XGBoost      Multi-agent     DQN / MDP / Planning
                       ↓                      ↓               ↓
                    GraphSAGE + GAT        Competition      Reproducible benchmark
```

**The contribution:** A reproducible, research-grade platform where forecasting models, simulators, and policies can be evaluated under consistent, leakage-safe conditions — plus production-style API and Docker deployment for pilot readiness.

---

## Quick Start

### Docker (one command)

```bash
docker compose up
# API → http://localhost:8000/docs
# Demo → http://localhost:8501
```

### Local

```bash
git clone https://github.com/caizefan34/nyc-taxi-zone-recommendation.git
cd nyc-taxi-zone-recommendation
pip install -e ".[dev,api,demo]"

# API
uvicorn src.api.main:app --host 0.0.0.0 --port 8000

# Demo
streamlit run app/app.py
```

### Quick API Example

```bash
curl -X POST http://localhost:8000/v1/recommendations \
  -H "Content-Type: application/json" \
  -d '{"vehicle_id": "v001", "zone_id": 161}'
```

```json
{
  "recommendation": {
    "vehicle_id": "v001",
    "current_zone": 161,
    "recommended_zone": 132,
    "confidence": 0.87,
    "ranked_zones": [
      {"zone_id": 132, "score": 0.91, "expected_demand": 41.7},
      {"zone_id": 236, "score": 0.85, "expected_demand": 38.2}
    ],
    "model_version": "two-step-v1"
  },
  "metadata": {
    "source": "simulation/historical_replay"
  }
}
```

---

## Key Results

### Static diagnostic: 3,360 public validation queries

| Strategy | NDCG@3 | Hit@3 | Reference utility@1 |
|---|---:|---:|---:|
| Hot Zone | 0.7846 | 0.5842 | 19.43 |
| Single-Step | 0.9024 | 0.8804 | 25.06 |
| Two-Step | **0.9565** | **0.9714** | **27.59** |

### Paired 100-seed, seven-day simulator rollout

| Strategy | Mean daily fare | vs Hot Zone |
|---|---:|---:|
| Hot Zone | $431.21 | — |
| Single-Step | $548.77 | +$117.56 |
| Two-Step | **$570.61** | **+$139.40** |

Two-Step vs Single-Step: +$21.84/day, paired bootstrap 95% CI [$5.00, $39.53], p=0.0151.

### Supervised demand forecasting

| Model | Demand MAE | Demand RMSE |
|---|---:|---:|
| Historical average | 1.7273 | 5.9237 |
| LightGBM | 1.5114 | 5.0707 |
| Ensemble (LightGBM + XGBoost) | **1.4868** | **4.9810** |

> Better forecast accuracy does not automatically improve recommendation. The forecast-enhanced single-step strategy scores -$17.88/day vs the historical Single-Step. See [Decision-Aware Forecasting](docs/research/decision_aware_forecasting.md).

### Graph-enhanced forecasting

GraphSAGE achieves demand MAE 1.5037 (0.51% improvement over non-graph LightGBM), but its timestamp-level 95% CI [-0.0042, 0.0200] crosses zero. GAT is weaker. OD messages without embeddings outperform both learned embeddings. See [outputs/graph_benchmark.md](outputs/graph_benchmark.md). The graph-neural contribution is not statistically supported at this sample size.

### Multi-agent competition (50 drivers)

| Strategy | Avg revenue | Utilization |
|---|---:|---:|
| Random | $189.42 | 3.1% |
| Single-Step | $412.85 | 10.8% |
| Two-Step | **$438.17** | **12.3%** |

Single-Step vs Hot Zone in 50-driver benchmark: +531.16/driver.

At fixed fleet size, raising the demand/supply ratio from 0.5 to 2.0 increases Single-Step utilization from 6.42% to 18.53%. See [outputs/multi_agent_benchmark.md](outputs/multi_agent_benchmark.md).

### Deep RL baselines

| Algorithm | Avg revenue vs Single-Step | 95% CI |
|---|---|---|
| DQN | +53.74 | [46.21, 61.57] |
| Double DQN | -25.27 | [-32.77, -17.97] |

DQN minus Single-Step is +53.74 per driver. These intervals cover evaluation-market seeds for one trained network per algorithm, not training uncertainty or real deployment effects. The default recommender remains unchanged. See [outputs/rl_benchmark.md](outputs/rl_benchmark.md).

### Offline RL / OPE (trajectory-level)

| Policy | WIS | Sequential DR |
|---|---|---|
| Stay (on-policy, prob=1.0) | $438.55 | $431.74 |
| IQL (off-policy, uniform behavior) | $0.00 | $12.44 |

Trajectory-level Weighted Importance Sampling and sequential Doubly Robust with 100-draw complete-trajectory bootstrap. IQL uses uniform exploration behavior (prob=1/263) with a deterministic greedy target — the zero WIS estimate reflects support overlap failure, not a bug. FQE is labeled as a diagnostic. See [docs/offline_rl_protocol.md](docs/offline_rl_protocol.md) and [outputs/policy_evaluation_report.md](outputs/policy_evaluation_report.md).

> **Important:** These are simulator outcomes, not production revenue estimates. OPE is a methodological benchmark, not evidence of real-world causal lift. See [Scientific Limitations](#scientific-limitations) below.

---

## System Architecture

```mermaid
graph TD
    A[NYC TLC Raw Trips] --> B[Data Pipeline]
    B --> C[Cleaned Dataset]
    C --> D[Demand Forecasting]
    C --> E[OD Graph Learning]
    D --> F[Decision Engine]
    E --> F
    F --> G[Multi-Agent Simulator]
    G --> H[Policy Evaluation]
    H --> I[API / Dashboard]
    
    subgraph Policies
        P1[Hot Zone]
        P2[Single-Step]
        P3[Two-Step Horizon]
        P4[DQN / Double DQN]
    end
    
    F --> P1 & P2 & P3 & P4
    P1 & P2 & P3 & P4 --> H
```

---

## Platform Capabilities

### Research
- Leakage-safe demand forecasting with LightGBM/XGBoost and strictly-prior temporal splits
- Graph neural features via OD-weighted GraphSAGE and GAT
- Multiple policies: Hot Zone, Single-Step, Two-Step Horizon, DQN, Double DQN
- Multi-agent simulator with configurable fleet, finite demand, competition
- Paired statistical tests, robustness checks, exposure analysis
- Counterfactual estimators (IPS, SNIPS, DR)

### Engineering
- **REST API** (FastAPI) — `/health`, `/ready`, `/v1/recommendations`, `/v1/demand/forecast`
- **Docker** — `docker compose up` for API + Demo
- **Decision Engine** — Unified recommendation schema with rich metadata
- **Shadow Evaluation** — Compare AI vs actual without execution
- **A/B Testing Framework** — Bootstrap CIs, effect size, statistical significance
- **Model Registry** — File-based versioning with training metadata
- **Cross-city abstraction** — CityAdapter interface; NYC reference implementation
- **Observability** — Structured logging, request latency tracking, metrics snapshot

---

## Repository Structure

```text
src/
  decision/              Decision Engine (unified recommendation)
  api/                   FastAPI REST API
  evaluation/            Shadow, A/B, historical replay
  cities/                Cross-city abstraction (NYC adapter)
  monitoring/            Metrics, model registry
  forecasting/           LightGBM, XGBoost, feature pipeline
  graph/                 GraphSAGE, GAT, OD graph
  simulator/             Multi-agent v1 + v2, calibration
  rl/                    Gymnasium env, DQN/DoubleDQN, offline RL (IQL, OPE)
  mdp/                   Model-based value iteration
  common/                Config, data loader, logging
  interfaces/            ABCs, adapters, model registry
  1_data_clean/          Original data pipeline (preserved)
  2_recommendation_algorithm/  Original strategies (preserved)
  3_extension_task/      Original extensions (preserved)
scripts/                 Experiment runners and benchmarks
tests/                   Method and regression test suite (see CI for current status)
configs/                 Configuration profiles
docs/                    Documentation, audit reports, blog post draft
pages/                   Landing page (deployed to GitHub Pages)
web/                     Interactive Leaflet map demo
```

---

## Scientific Limitations

> **Read before citing results.**

### Simulator boundary

The multi-agent simulator improves on single-driver rollouts with a configurable fleet, finite trip inventory, and explicit competition. However, it still omits:
- Congestion and traffic dynamics
- Airport queue rules
- Endogenous passenger demand
- Strategic driver adaptation
- Market equilibrium effects

**Rollout improvements must not be presented as production revenue lift.**

### Counterfactual boundary

NYC TLC trips do not contain logged reposition recommendations, logging-policy propensities, or driver acceptance. Valid IPS, SNIPS, or doubly robust evaluation is therefore not identifiable from these records alone. Simulator-generated OPE benchmarks are a methodological check, not evidence of real-world causal lift. Real-world OPE requires a deployed stochastic logging policy that records recommendations, accepted actions, propensities, timestamps, outcomes, and episode boundaries.

### Forecast-decision gap

Better forecast accuracy (lower MAE/RMSE) has been shown NOT to improve recommendation decisions in this domain. The platform explicitly separates forecast and decision metrics.

### Exposure and market impact

Two-Step strategy airport exposure: 70.33% weighted. Exposure Gini: 0.982. These indicate substantial saturation risk at scale — a key research question for the platform.

---

## Docker

```bash
# Start API + Demo
docker compose up

# API documentation
open http://localhost:8000/docs

# Demo dashboard
open http://localhost:8501
```

See [.env.example](.env.example) for configuration.

---

## Reproduce Research Results

```bash
# Data pipeline
python -m scripts.run_data_pipeline --force-split
python -m scripts.build_travel_time_matrix

# Static evaluation
make static

# Full benchmark
make all

# Tests
pytest tests -q

# Simulator-only trajectory-aware OPE benchmark
python -m scripts.run_ope_comparison --seed 42
```

See [docs/reproduction.md](docs/reproduction.md) for detailed instructions.

---

## Research Platform Capabilities

### Implemented and verified

| Capability | Status |
|---|---|
| Leakage-safe demand forecasting (LightGBM, XGBoost, ensemble) | Verified: MAE 1.49 |
| OD graph features (GraphSAGE, GAT) | Verified: CI crosses zero |
| Multi-agent finite-demand simulator (v2) | Verified: 50-driver benchmarks |
| MDP policies (Hot Zone, Single-Step, Two-Step) | Verified: 100-seed paired tests |
| DQN / Double DQN (Gymnasium env) | Verified: +$53.74 DQN lift |
| Implicit Q-Learning (IQL) offline RL | Verified: trained, OPE-tested |
| Trajectory-level WIS and sequential DR OPE | Verified: seed-42 reproducible |
| Trajectory bootstrap CIs (complete episodes) | Verified: separate WIS/DR intervals |
| Per-driver trajectory collection with propensities | Verified: terminal markers, ring order |
| Counterfactual / fairness / exposure audit | Verified: exposure Gini 0.982 |
| Shadow evaluation mode | Verified: record, don't execute |
| REST API (FastAPI) | Verified: /health, /ready, /v1/recommendations |
| Docker Compose (API + Demo) | Verified: health checks, multi-stage build |
| CI (Python 3.10/3.12 + Docker smoke) | Verified: 402 tests, coverage upload |

---

## Citation

```bibtex
@software{cai2025nyc_taxi_recommendation,
  author       = {Zefan Cai},
  title        = {Urban Mobility Decision Intelligence: An Open-Source Platform for AI-Driven Fleet Repositioning},
  year         = {2025},
  publisher    = {GitHub},
  url          = {https://github.com/caizefan34/nyc-taxi-zone-recommendation},
  note         = {Cite the specific commit used. Distinguish static diagnostic metrics from simulator outcomes.}
}
```

---

## How to Collaborate

This platform is designed for multi-disciplinary collaboration. Whether you're a researcher, engineer, or domain expert, there are concrete ways to contribute and collaborate.

### For Researchers

- **Use as a benchmark** — Standardized evaluation protocol with leakage-safe splits, paired statistical tests, and reproducible baselines. Submit your policy or forecaster via [external contribution guide](docs/external_contribution.md).
- **Extend the methods** — Add new policies (RL, planning, bandit), forecasting models (transformers, diffusion), or graph learning approaches. The modular `src/` layout supports drop-in replacements.
- **Publish together** — See [docs/research_paper_draft.md](docs/research_paper_draft.md) for a manuscript draft. Co-authorship opportunities for substantial methodological or experimental contributions.
- **Cross-city adaptation** — Implement a city adapter for your city (Chicago, London, Singapore, etc.). See [docs/cross_city_extension.md](docs/cross_city_extension.md).

### For Engineers

- **Productionize** — REST API, Docker, CI/CD, and observability are already in place. Help with load testing, Kubernetes configs, monitoring dashboards, or cloud deployment.
- **New features** — Streaming data pipeline, real-time inference, Redis caching, WebSocket-based live updates. Check [ROADMAP.md](ROADMAP.md).
- **Infrastructure** — Multi-cloud deployment, Terraform, Helm charts, GitHub Actions improvements.

### For Domain Experts

- **Review assumptions** — Feedback on simulator realism, market modeling, driver behavior, and NYC-specific constraints is invaluable.
- **Documentation & tutorials** — Improve onboarding, write Jupyter notebook tutorials, create video walkthroughs.
- **Industry partnerships** — Fleet operators, ride-hailing companies, or transit agencies interested in pilot studies. See [docs/enterprise/pilot.md](docs/enterprise/pilot.md).

### Start Collaborating

1. **Open a Discussion** — [GitHub Discussions](https://github.com/caizefan34/nyc-taxi-zone-recommendation/discussions) for questions, ideas, and coordination
2. **Pick an Issue** — Look for `good first issue` or `help wanted` tags
3. **Propose an Experiment** — Use the [experiment proposal template](.github/ISSUE_TEMPLATE/experiment_proposal.md)
4. **Submit a PR** — See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines

**Contact:** Zefan Cai — caizefan@sjtu.edu.cn — [Shanghai Jiao Tong University](https://www.sjtu.edu.cn/)

---

## License

MIT License. See [LICENSE](LICENSE).

---

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines. Good first issues are tagged in the [issue tracker](https://github.com/caizefan34/nyc-taxi-zone-recommendation/issues).

### Contributors

<a href="https://github.com/caizefan34/nyc-taxi-zone-recommendation/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=caizefan34/nyc-taxi-zone-recommendation" />
</a>

---

## Acknowledgments

This work is conducted at [Shanghai Jiao Tong University](https://www.sjtu.edu.cn/). The platform builds on NYC TLC open data, and we gratefully acknowledge the TLC for maintaining this valuable public resource.

Research methodology draws from:
- Offline reinforcement learning (Levine et al., 2020)
- Doubly robust policy evaluation (Jiang & Li, 2016; Thomas & Brunskill, 2016)
- Spatiotemporal demand forecasting for urban mobility

---

## Star History

<a href="https://star-history.com/#caizefan34/nyc-taxi-zone-recommendation&Date">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=caizefan34/nyc-taxi-zone-recommendation&type=Date&theme=dark" />
    <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=caizefan34/nyc-taxi-zone-recommendation&type=Date" />
    <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=caizefan34/nyc-taxi-zone-recommendation&type=Date" />
  </picture>
</a>

