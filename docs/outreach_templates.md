# Community Outreach Templates

> **Status**: Templates prepared. Not yet sent.
> **Purpose**: Standardized messages for promoting the project to research communities.

---

## 1. GitHub Repository Announcement

**For**: GitHub Discussions, project README, release notes

```
**Dynamic Urban Mobility Decision System v3.0.0**

We're excited to share our open-source decision intelligence platform for AI-driven
urban mobility.

What it does:
- Combines demand forecasting, multi-agent simulation, and offline RL
- Trajectory-aware OPE with WIS and sequential Doubly Robust estimation
- Reproducible benchmark with 402 tests and checked-in metrics
- Interactive web demo (no installation required)
- REST API + Docker Compose one-command deployment
- External submission system for community benchmarks

Key results: Two-Step Horizon planner achieves NDCG@3 of 0.9565
with $139 daily revenue lift per driver over baseline. DQN adds +$53.74/driver
over Single-Step with 95% CI [+46.21, +61.57].

Try it: [Live Demo URL]
GitHub: [Repo URL]
Docs: [Docs URL]

We welcome contributions, benchmark submissions, and feedback!
```

---

## 2. Research Community Post

**For**: Reddit r/MachineLearning, r/urbanplanning, ML Discord servers

**Title**: "An Open Benchmark for AI-driven Taxi Repositioning — Reproducible, Leakage-Safe, with Multi-Agent Simulation"

**Body**:
```
I built an open-source decision intelligence platform for urban mobility AI and wanted
to share it with the community.

The problem: Taxi drivers waste 30-50% of their shift cruising. Where should
they go next? This is fundamentally a sequential decision problem.

What the project does:
- Leakage-safe demand forecasting (LightGBM + XGBoost + GraphSAGE/GAT)
- Multi-agent simulator with finite demand and explicit competition
- MDP-based planning + DQN/Double DQN + Implicit Q-Learning (IQL) policies
- Trajectory-aware offline policy evaluation (WIS, sequential DR, bootstrap CI)
- Fully reproducible benchmark with all metrics checked into the repo
- REST API + Docker Compose deployment with health checks

Key design decisions:
- Strict chronological splits (no future leakage — random splits inflate
  accuracy by 15-25% in our tests)
- Simulator-based evaluation with counterfactual analysis
- OPE requires explicit behavior/target probabilities — no silent defaults
- Fixed-seed reproducibility for all scripts and benchmarks
- 402 tests, paired statistical validation, multi-seed RL runs

Try the interactive demo (no install): [URL]
GitHub: [URL]

I'd love feedback from anyone working on urban computing, RL for
recommendations, or reproducible ML. Also happy to help if anyone
wants to submit a benchmark entry!
```

---

## 3. Email Introduction

**For**: Contacting researchers, potential collaborators, advisors

**Subject**: "Open-source urban mobility benchmark — seeking feedback/collaboration"

```
Dear [Name],

I came across your work on [their topic] and thought you might be
interested in an open-source project I've been developing.

The Dynamic Urban Mobility Decision System is a decision intelligence platform for
AI-driven taxi repositioning, combining demand forecasting, multi-agent
simulation, offline RL, and trajectory-aware policy evaluation. All results
are reproducible with checked-in metrics and 402 automated tests.

Key highlights:
- Leakage-safe evaluation with strict chronological data splits
- Multi-agent simulator with finite demand, explicit competition, and recorded propensities
- Two-Step Horizon planner achieves NDCG@3 of 0.9565
- Trajectory-level WIS and sequential Doubly Robust OPE with bootstrap CIs
- Interactive web demo + REST API + Docker Compose deployment

The project is fully open-source (MIT license) with documentation,
a public leaderboard, and an external submission workflow.

I would value your perspective on [specific aspect relevant to them].
If you have time for a brief chat or feedback on the repository,
I would greatly appreciate it.

Repository: https://github.com/caizefan34/nyc-taxi-zone-recommendation
Live Demo: https://caizefan34.github.io/nyc-taxi-zone-recommendation/web/

Best regards,
Zefan Cai
```

---

## 4. Conference Submission Summary

**For**: Workshop submissions, poster abstracts, demo track

**Title**: "Dynamic Urban Mobility Decision System: An Open Decision Intelligence Platform for Reproducible Taxi Repositioning Research"

**One-paragraph summary**:
We present an open-source decision intelligence platform for AI-driven taxi repositioning that integrates leakage-safe demand forecasting, multi-agent simulation, offline reinforcement learning, and trajectory-aware policy evaluation into a reproducible pipeline. The platform processes over 100 million NYC taxi trips, generates demand predictions with MAE of 1.49, simulates competitive multi-driver scenarios, evaluates policies including a Two-Step Horizon planner (NDCG@3: 0.9565, +\$139/driver daily vs baseline) and DQN (+$53.74/driver, 95% CI [+46.21, +61.57]), and provides trajectory-level WIS and sequential Doubly Robust OPE with bootstrap confidence intervals. All 402 tests pass, metrics are checked into the repository, and the platform ships with REST API, Docker Compose deployment, and a public leaderboard for external submissions.

**Keywords**: urban mobility, benchmark, reinforcement learning, offline policy evaluation, doubly robust estimation, simulation

---

## Usage Notes

- Customize [bracketed] fields before sending
- Do not mass-email; personalize each outreach
- Wait until deployment is stable before broad outreach
- Track responses in impact_tracking.md
