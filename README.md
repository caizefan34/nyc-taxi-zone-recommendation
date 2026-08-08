<div align="center">
  <a href="https://caizefan34.github.io/urban-mobility-ai/web/">
    <img src="assets/social-preview.svg" width="100%" alt="Urban Mobility Decision Intelligence">
  </a>

  <h1>Urban Mobility Decision Intelligence</h1>

  <p>
    <strong>
      Where should a taxi go next? We answer that question with AI —<br>
      combining demand forecasting, multi-agent simulation, and reinforcement learning<br>
      to help drivers earn <b>$139 more per day</b> on NYC's 263 taxi zones.
    </strong>
  </p>

  <p>
    <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.10%2B-blue?logo=python&logoColor=white" alt="Python"></a>
    <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green?logo=opensourceinitiative&logoColor=white" alt="MIT"></a>
    <a href="https://github.com/caizefan34/urban-mobility-ai/actions/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/caizefan34/urban-mobility-ai/ci.yml?branch=master&logo=githubactions&logoColor=white&label=tests" alt="CI"></a>
    <img src="https://img.shields.io/badge/benchmark-NDCG%400.9565-success?logo=googleanalytics&logoColor=white" alt="NDCG">
    <img src="https://img.shields.io/badge/lift-%2B%24139%2Fday-brightgreen?logo=uber&logoColor=white" alt="Lift">
    <a href="CONTRIBUTING.md"><img src="https://img.shields.io/badge/contributions-welcome-brightgreen?logo=github" alt="Contributions"></a>
  </p>
  <p>
    <a href="docs/badges/reproducibility.svg"><img src="docs/badges/reproducibility.svg" alt="Reproducible"></a>
    <a href="docs/badges/benchmark.svg"><img src="docs/badges/benchmark.svg" alt="Benchmark"></a>
    <a href="docs/badges/documentation.svg"><img src="docs/badges/documentation.svg" alt="Documentation"></a>
    <a href="#quick-start"><img src="https://img.shields.io/badge/docker-ready-blue?logo=docker&logoColor=white" alt="Docker"></a>
    <a href="https://github.com/caizefan34/urban-mobility-ai/stargazers"><img src="https://img.shields.io/github/stars/caizefan34/urban-mobility-ai?style=social" alt="Stars"></a>
    <a href="https://github.com/caizefan34/urban-mobility-ai/network/members"><img src="https://img.shields.io/github/forks/caizefan34/urban-mobility-ai?style=social" alt="Forks"></a>
  </p>

  <p>
    <a href="https://caizefan34.github.io/urban-mobility-ai/web/">&#127760; Live Demo</a>
    &nbsp;·&nbsp;
    <a href="https://caizefan34.github.io/urban-mobility-ai/docs/">&#128214; Documentation</a>
    &nbsp;·&nbsp;
    <a href="#-quick-start-">&#9889; Quick Start</a>
    &nbsp;·&nbsp;
    <a href="docs/research_paper_draft.md">&#128196; Paper Draft</a>
    &nbsp;·&nbsp;
    <a href="docs/leaderboard.md">&#127942; Leaderboard</a>
    &nbsp;·&nbsp;
    <a href="ROADMAP.md">&#128640; Roadmap</a>
    &nbsp;·&nbsp;
    <a href="https://github.com/caizefan34/urban-mobility-ai/discussions">&#128172; Discussions</a>
  </p>
</div>

---

## &#127775; Highlights

<table>
<tr>
<td width="25%" align="center">
  <b>0.9565</b><br>
  <sub>NDCG@3<br>(Two-Step MDP)</sub>
</td>
<td width="25%" align="center">
  <b>+$139.40</b><br>
  <sub>Daily Fare Lift<br>vs Hot Zone</sub>
</td>
<td width="25%" align="center">
  <b>+$53.74</b><br>
  <sub>DQN Advantage<br>per driver/day</sub>
</td>
<td width="25%" align="center">
  <b>402</b><br>
  <sub>Tests<br>CI Verified</sub>
</td>
</tr>
</table>

---

## &#128161; The Big Idea

> **In one sentence:** We built the most comprehensive open-source benchmark for AI-driven taxi repositioning — forecast demand, simulate competition, and let RL figure out where drivers should go next.

**The problem is simple, the math is deep:**

- NYC has 263 taxi zones. At any moment, each zone has some demand (people wanting rides) and some supply (empty taxis).
- A driver who just dropped off a passenger needs to decide: *cruise here, or reposition to another zone?*
- Competing drivers deplete the same pool of passengers. Every decision involves predicting demand AND anticipating what other drivers will do.
- This is a **finite-horizon stochastic game** with 263 actions, partial observability, and delayed rewards.

**What makes this project different:**

- &#9989; **Not just a paper** — runnable API, interactive map, Docker one-click deploy
- &#9989; **Not just a model** — 7 policies benchmarked: heuristic, MDP, DQN, Double DQN, IQL
- &#9989; **Not just results** — paired statistical tests, bootstrap CIs, exposure audits, honest negative findings
- &#9989; **Not just NYC** — CityAdapter interface; plug in Chicago, London, Singapore

---

## &#9889; Quick Start

### One command

```bash
docker compose up
# API → http://localhost:8000/docs    |    Demo → http://localhost:8501
```

### From source

```bash
git clone https://github.com/caizefan34/urban-mobility-ai.git && cd urban-mobility-ai
pip install -e ".[dev,api,demo]"

# Try it
curl -X POST http://localhost:8000/v1/recommendations \
  -H "Content-Type: application/json" \
  -d '{"vehicle_id": "v001", "zone_id": 161}'
```

---

## &#128202; Key Results

### Static Diagnostic (3,360 queries)

| Strategy | NDCG@3 | Hit@3 | Utility@1 |
|---|---:|---:|---:|
| Hot Zone (go where demand is highest) | 0.7846 | 0.5842 | 19.43 |
| Single-Step (one-step lookahead) | 0.9024 | 0.8804 | 25.06 |
| **Two-Step (two-step MDP planning)** | **0.9565** | **0.9714** | **27.59** |

### 100-Seed Simulator Rollout (7 days)

| Strategy | Mean Daily Fare | vs Hot Zone |
|---|---:|---:|
| Hot Zone | $431.21 | — |
| Single-Step | $548.77 | +$117.56 |
| **Two-Step** | **$570.61** | **+$139.40** |

Two-Step vs Single-Step: +$21.84/day, bootstrap 95% CI [$5.00, $39.53], p = 0.0151.

### Deep Reinforcement Learning

| Algorithm | Avg Revenue vs Single-Step | 95% CI |
|---|---:|---:|
| **DQN** | **+$53.74** | [+46.21, +61.57] |
| Double DQN | -$25.27 | [-32.77, -17.97] |

### Multi-Agent Competition (50 drivers)

| Strategy | Avg Revenue/Driver | Utilization |
|---|---:|---:|
| Random (no strategy) | $189.42 | 3.1% |
| Single-Step | $412.85 | 10.8% |
| **Two-Step** | **$438.17** | **12.3%** |

> At fixed fleet size, raising demand/supply ratio from 0.5x to 2.0x increases Single-Step utilization from 6.42% to 18.53%.

### Demand Forecasting

| Model | MAE | RMSE |
|---|---:|---:|
| Historical Average | 1.7273 | 5.9237 |
| LightGBM | 1.5114 | 5.0707 |
| **Ensemble (LGB + XGB)** | **1.4868** | **4.9810** |

> **Surprising finding:** Better forecast accuracy does NOT equal better decisions. The forecast-enhanced strategy scores -$17.88/day vs the simpler historical version. This "prediction-policy gap" is one of the platform's key research contributions. See [Decision-Aware Forecasting](docs/research/decision_aware_forecasting.md).

---

## &#127752; How It Works

```
NYC TLC Raw Trips (2009-2024)
          │
          ▼
   Data Pipeline (chronological split, 263 zones)
          │
          ├──────────────────┬──────────────────┐
          ▼                  ▼                  ▼
   Demand Forecast    OD Graph Learning    Decision Engine
   LightGBM/XGBoost   GraphSAGE/GAT        MDP / DQN / IQL
          │                  │                  │
          └──────────────────┴──────────────────┘
                             │
                             ▼
                  Multi-Agent Simulator v2
                  (finite demand, explicit competition)
                             │
                             ▼
                    Policy Evaluation
                    WIS / Doubly Robust / Bootstrap CI
                             │
                ┌────────────┼────────────┐
                ▼            ▼            ▼
            REST API      Docker       Live Demo
```

---

## &#127891; Why Researchers Love This

This platform isn't just a model — it's a **reproducible research instrument**:

- **Leakage-safe evaluation** — strictly-prior chronological splits prevent temporal data leakage
- **Paired statistical tests** — every comparison backed by bootstrap CIs, Cohen's d, and p-values
- **Honest negative results** — graph neural features (GraphSAGE, GAT) shown NOT to help; IQL transfer documented to fail; forecast-decision gap empirically validated
- **Trajectory-level OPE** — Weighted Importance Sampling and sequential Doubly Robust with complete-episode bootstrap for the first time in spatiotemporal recommendation
- **Single command reproduction** — `make all` runs the full pipeline

---

## &#127976; Repository Structure

```
src/
  decision/         Decision Engine        api/           FastAPI REST API
  forecasting/      LGB + XGB ensemble     graph/         GraphSAGE, GAT
  simulator/        Multi-agent v2         rl/            DQN, DoubleDQN, IQL
  mdp/              MDP value iteration    evaluation/    Shadow, A/B, OPE
  cities/           Cross-city adapter     monitoring/    Metrics, registry
scripts/            Benchmarks & runners   configs/       YAML configs
tests/              402 tests              docs/          Full documentation
web/                Live Leaflet demo      pages/         Landing page
notebooks/          Jupyter tutorials      examples/      Usage examples
```

---

## &#9888;&#65039; Scientific Limitations

> **Read before citing results.** These are fundamental, not implementation oversights.

- **Simulator outcomes only** — no congestion, no airport queues, no driver adaptation. Results are NOT production revenue estimates.
- **Counterfactual identifiability** — NYC TLC data lacks logged recommendations, propensities, and driver actions. Valid causal OPE requires a stochastic logging policy in deployment.
- **Forecast-decision gap** — empirically confirmed: better MAE → worse decisions (-$17.88/day).
- **Exposure concentration** — Two-Step strategy: 70.33% airport exposure, Gini 0.982. Saturation risk at scale.

---

## &#129309; Collaborate With Us

| Role | How to Contribute |
|---|---|
| **Researchers** | Benchmark your policy, extend the methods, co-author the paper |
| **Engineers** | Productionize API, add K8s/Terraform, improve CI/CD |
| **Domain Experts** | Review simulator assumptions, add city adapters, improve docs |
| **Students** | Good first issues, tutorial improvements, Jupyter notebooks |

&#128640; **Get started:** [Discussions](https://github.com/caizefan34/urban-mobility-ai/discussions) · [Issues](https://github.com/caizefan34/urban-mobility-ai/issues) · [CONTRIBUTING.md](CONTRIBUTING.md)

&#128231; **Contact:** Zefan Cai — caizefan@sjtu.edu.cn — [Shanghai Jiao Tong University](https://www.sjtu.edu.cn/)

---

## &#128214; Citation

```bibtex
@software{cai2026urban_mobility,
  author       = {Zefan Cai},
  title        = {Urban Mobility Decision Intelligence: An Open-Source Platform for AI-Driven Fleet Repositioning},
  year         = {2026},
  publisher    = {GitHub},
  url          = {https://github.com/caizefan34/urban-mobility-ai},
  note         = {v3.0.0. Cite the specific commit used. Simulator outcomes, not production estimates.}
}
```

---

## &#11088; Star History

<a href="https://star-history.com/#caizefan34/urban-mobility-ai&Date">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=caizefan34/urban-mobility-ai&type=Date&theme=dark" />
    <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=caizefan34/urban-mobility-ai&type=Date" />
    <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=caizefan34/urban-mobility-ai&type=Date" />
  </picture>
</a>

---

<p align="center">
  <sub>MIT License · Built at Shanghai Jiao Tong University · v3.0.0</sub>
</p>