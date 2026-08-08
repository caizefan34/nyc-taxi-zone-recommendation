# ROADMAP

## v1.0 — Research Foundation ✓
- [x] Data pipeline: chronological cleaning, statistics
- [x] Strategies: Hot Zone, Single-Step, Two-Step Horizon
- [x] Evaluation: NDCG@3, Hit@3, reference utility
- [x] Single-driver rollout simulator
- [x] Parameter selection grid search

## v2.0 — Research Benchmark ✓
- [x] Leakage-safe demand forecasting (LightGBM, XGBoost)
- [x] OD graph features (GraphSAGE, GAT)
- [x] Multi-agent finite-demand simulator
- [x] DQN and Double-DQN baselines (Gymnasium)
- [x] Corrected model-based MDP
- [x] Counterfactual estimators (IPS, SNIPS, DR)
- [x] Reproducible benchmark framework
- [x] Research-grade audit (fairness, exposure, temporal)
- [x] GitHub Pages documentation

## v2.1 — Community & Visibility ✓
- [x] Repository architecture cleanup
- [x] README redesign with badges
- [x] Project showcase landing page
- [x] Issue templates for external contributors
- [x] Enhanced CONTRIBUTING.md

## v3.0 — Decision Intelligence Platform ✓
- [x] Unified decision engine with rich metadata schema
- [x] REST API (FastAPI): /health, /ready, /v1/recommendations
- [x] Docker Compose one-click deployment (API + Demo) with health checks
- [x] Multi-stage Dockerfile (api, demo, test targets)
- [x] Enterprise config system (default, api, research, production)
- [x] Constraint-aware policy layer
- [x] Model registry / versioning
- [x] Structured observability (logging, metrics)
- [x] CI with Python 3.10/3.12 matrix + Docker build smoke
- [x] Trajectory-aware offline policy evaluation (WIS, sequential DR)
- [x] Implicit Q-Learning (IQL) offline RL baseline
- [x] Reproducible OPE benchmark with fixed-seed bootstrap
- [x] Per-driver/episode trajectory collection with behavior propensities
- [ ] Fleet operations dashboard enhancements
- [ ] Open benchmark leaderboard
- [ ] Cross-city data pipeline prototypes

## v3.5 — Real-world Evaluation 🔄
- [x] Historical replay framework
- [x] Shadow evaluation mode (record, don't execute)
- [x] A/B testing framework with bootstrap CIs
- [ ] Real-world shadow evaluation pilot
- [ ] Controlled A/B test deployment

## v4.0 — Multi-City
- [x] CityAdapter abstraction
- [x] NYC reference implementation
- [ ] Chicago taxi data integration
- [ ] London transport integration
- [ ] Singapore mobility data integration
- [ ] Transfer learning across cities

## v5.0 — Enterprise Pilot
- [ ] Fleet integration API
- [ ] Real-time data pipeline
- [ ] Production monitoring dashboard
- [ ] Online learning with bandit feedback
- [ ] Private deployment documentation
- [ ] Real-world A/B test results

## Research Directions

1. **Decision-aware forecasting**: Can we train forecasters that directly optimize decision quality?
2. **Policy adoption dynamics**: What happens when many drivers follow the same AI policy?
3. **Market equilibrium**: Can recommendation systems become self-defeating through market impact?
4. **Fairness-constrained optimization**: Balancing revenue, utilization, and service coverage across zones
5. **Multi-city transfer**: Can models trained on NYC generalize to other cities?
6. **Real logged propensities**: Deploy a stochastic logging policy to collect behavior probabilities for identifiable OPE

## How to contribute

See [CONTRIBUTING.md](CONTRIBUTING.md) and [good first issues](https://github.com/caizefan34/urban-mobility-ai/labels/good%20first%20issue).
