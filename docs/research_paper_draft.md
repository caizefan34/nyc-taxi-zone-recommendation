# Urban Mobility Decision Intelligence: An Open-Source Platform for AI-Driven Fleet Repositioning

> **Status:** Working Draft · Version 3.0 · Target venues: KDD Applied Data Science / SIGSPATIAL / Transportation Research Part C
>
> **arXiv preprint planned: Q4 2026**

## Authors

**Zefan Cai** — Shanghai Jiao Tong University — caizefan@sjtu.edu.cn

---

## Abstract

We present an open-source decision intelligence platform for dynamic fleet repositioning that combines spatiotemporal demand forecasting, multi-agent simulation, and offline reinforcement learning with trajectory-aware policy evaluation. Using New York City TLC trip records across 263 taxi zones, we benchmark policies from heuristic MDP planning to deep Q-networks under a unified, leakage-safe evaluation protocol. Our two-step finite-horizon planner achieves 0.9565 NDCG@3 on static diagnostics and +$139.40/day over the hot-zone baseline in 100-seed seven-day simulator rollouts. DQN yields an additional +$53.74/day per driver. We conduct trajectory-level offline policy evaluation via weighted importance sampling and sequential doubly robust estimation with complete-trajectory bootstrap confidence intervals. The platform includes a production-style REST API, Docker deployment, interactive web dashboard, and supports cross-city adaptation. All results are reproducible via `make all`. We document scientific limitations transparently — including simulator boundaries, identifiability constraints of observational data, and the forecast-decision gap — advocating for rigorous methodological transparency in urban mobility AI.

---

## 1. Introduction

Urban taxi and ride-hailing systems face a fundamental inefficiency: drivers cruise 30–60% of their shift without passengers, generating economic waste and unnecessary congestion. In New York City alone, this represents millions of dollars in lost revenue annually. The core challenge is a spatiotemporal sequential decision problem — where should a driver reposition after each trip to maximize expected future earnings under competition from other drivers?

Existing solutions fall into three paradigms:

1. **Commercial black-box systems** (Uber, Lyft, Didi) operate at scale but are neither reproducible nor auditable
2. **Academic RL approaches** report results without standardized evaluation protocols, making cross-paper comparison impossible
3. **Heuristic methods** (e.g., "go to the hottest zone") ignore supply competition and temporal dynamics

**This work's contribution is a unified platform** that bridges these gaps with five key innovations:

1. **Reproducible benchmark** — leakage-safe data splits, standardized metrics, paired statistical tests, and a single-command reproduction (`make all`)
2. **Comprehensive policy suite** — MDP planning (Hot Zone, Single-Step, Two-Step), model-free RL (DQN, Double DQN), and offline RL (IQL)
3. **Trajectory-aware OPE** — WIS and sequential DR with complete-trajectory bootstrap CIs, establishing a methodological benchmark for counterfactual evaluation in spatiotemporal recommendation
4. **Production engineering** — REST API, Docker Compose, CI/CD, observability, shadow evaluation, A/B testing framework
5. **Scientific transparency** — explicit documentation of limitations, negative results (graph features, IQL transfer), and the forecast-decision gap

---

## 2. Problem Formulation

### 2.1 Zone-Based Fleet Repositioning

Let $\mathcal{Z} = \{1, 2, \ldots, Z\}$ be the set of taxi zones ($Z=263$ for NYC). At decision time $t$, a vehicle $v$ in zone $z_v^t$ must choose a target zone $z' \in \mathcal{Z}$ to reposition to after dropping off its current passenger. The objective is to maximize expected future revenue over horizon $H$:

$$\max_{\pi} \mathbb{E}\left[\sum_{k=0}^{H-1} \gamma^k r(z_{t+k}, z_{t+k+1}) \mid z_t, \pi \right]$$

where $r(z, z')$ is the fare for a trip $z \to z'$, and competing vehicles deplete finite per-zone demand on a first-come basis. The transition kernel $P(z' \mid z, a, \mathcal{D})$ depends on the action $a$, baseline demand $\mathcal{D}$, and the actions of all other vehicles.

### 2.2 Key Challenges

| Challenge | Description | Our Approach |
|---|---|---|
| **Leakage** | Temporal leakage inflates forecast metrics | Strictly-prior chronological splits |
| **Competition** | Shared demand pool among drivers | Multi-agent simulator v2 with finite depletable demand |
| **Evaluation** | No ground-truth counterfactuals | Trajectory-level OPE with bootstrap CIs |
| **Reproducibility** | Results vary across seeds/seasons | Paired tests, fixed seeds, cross-year validation |
| **Forecast-decision gap** | Better prediction ≠ better policy | Separate forecast and decision metrics |

### 2.3 Policies Evaluated

| Policy | Type | Horizon | Description |
|---|---|---|---|
| Hot Zone | Heuristic | 0 | Go to zone with highest historical pickup count |
| Single-Step | MDP | 1 | One-step greedy expected utility maximization |
| **Two-Step** | MDP | 2 | Two-step Bellman backup with supply prediction |
| DQN | Model-free RL | ∞ (discounted) | Deep Q-Network with masked action space |
| Double DQN | Model-free RL | ∞ (discounted) | Reduces overestimation bias |
| IQL | Offline RL | ∞ (discounted) | Implicit Q-Learning from logged trajectories |

---

## 3. Platform Architecture

The platform implements a modular, extensible pipeline:

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  TLC Raw Data │───▶│ Data Pipeline │───▶│   Cleaned    │
│  (2009-2024)  │    │ (chrono split)│    │   Dataset    │
└──────────────┘    └──────────────┘    └──────┬───────┘
                                               │
                    ┌──────────────────────────┼──────────────────────────┐
                    │                          │                          │
                    ▼                          ▼                          ▼
            ┌──────────────┐          ┌──────────────┐          ┌──────────────┐
            │   Demand     │          │  OD Graph    │          │   Decision   │
            │  Forecasting │          │   Learning   │          │    Engine    │
            │ LGB/XGB/Ens. │          │ SAGE/GAT/Msg │          │   Unified    │
            └──────────────┘          └──────────────┘          └──────┬───────┘
                                                                       │
                    ┌──────────────────────────────────────────────────┘
                    ▼
            ┌──────────────┐
            │ Multi-Agent  │
            │  Simulator   │
            │    (v2)      │
            └──────┬───────┘
                   │
       ┌───────────┼───────────┐
       ▼           ▼           ▼
┌───────────┐ ┌─────────┐ ┌──────────┐
│ MDP Policy│ │   RL    │ │ Offline  │
│   Opt.    │ │ Training│ │   RL     │
└─────┬─────┘ └────┬────┘ └────┬─────┘
      │            │           │
      └────────────┼───────────┘
                   ▼
           ┌──────────────┐
           │ Policy Eval  │
           │ WIS / DR /   │
           │ Bootstrap CI │
           └──────┬───────┘
                  │
       ┌──────────┼──────────┐
       ▼          ▼          ▼
┌──────────┐ ┌────────┐ ┌──────────┐
│ REST API │ │ Docker │ │ Dashboard│
│ (FastAPI)│ │Compose │ │ (Leaflet)│
└──────────┘ └────────┘ └──────────┘
```

### 3.1 Data Pipeline

- **Source:** NYC TLC Yellow Taxi trip records (2009–2024)
- **Splits:** Chronological train/val/test with strictly prior temporal boundaries
- **Granularity:** 263 taxi zones, hourly aggregation
- **Features:** 120-day lookback, hour-of-day, day-of-week, holiday indicators, travel-time matrix

### 3.2 Demand Forecasting

Five models evaluated with standardized feature sets:

| Model | Type | Key Characteristics |
|---|---|---|
| Historical Average | Baseline | Mean pickup count by hour × zone × weekday |
| LightGBM | Gradient boosting | Tree-based with leaf-wise growth |
| XGBoost | Gradient boosting | Tree-based with regularization |
| Ensemble | Hybrid | Weighted average of LightGBM + XGBoost |
| GraphSAGE | Graph NN | Inductive node embeddings on OD flow graph |
| GAT | Graph NN | Attention-weighted neighbor aggregation |

### 3.3 Multi-Agent Simulator (v2)

- **Configurable fleet:** 1–50+ drivers with individual shift constraints
- **Finite demand:** Per-zone trip inventory depletes as drivers pick up passengers
- **Explicit competition:** First-come, first-served within each time step
- **Calibrated travel:** Inter-zone travel time matrix
- **Trajectory collection:** Per-driver, per-episode with terminal markers, propensities, and ring-buffer ordering

### 3.4 Offline Policy Evaluation Protocol

We implement trajectory-level estimators for complete episodes:

**Weighted Importance Sampling (WIS):**

$$\hat{V}_{\text{WIS}} = \frac{\sum_{i=1}^{n} w_i G_i}{\sum_{i=1}^{n} w_i}, \quad w_i = \prod_{t=0}^{T_i-1} \frac{\pi_e(a_{i,t} \mid s_{i,t})}{\pi_b(a_{i,t} \mid s_{i,t})}$$

**Sequential Doubly Robust (DR):**

$$\hat{V}_{\text{DR}} = \frac{1}{n}\sum_{i=1}^{n} \sum_{t=0}^{T_i-1} \gamma^t \left[ \hat{Q}(s_{i,t}, a_{i,t}) + w_{i,t}(r_{i,t} - \hat{Q}(s_{i,t}, a_{i,t})) \right]$$

**Confidence intervals:** 100-draw complete-trajectory bootstrap.

---

## 4. Experimental Results

### 4.1 Static Diagnostic (3,360 Queries)

Chronological split, 2016 holdout:

| Strategy | NDCG@3 | Hit@3 | Utility@1 |
|---|---:|---:|---:|
| Hot Zone (baseline) | 0.7846 | 0.5842 | 19.43 |
| Single-Step | 0.9024 | 0.8804 | 25.06 |
| **Two-Step** | **0.9565** | **0.9714** | **27.59** |

### 4.2 Simulator Rollouts

100 independent seeds, 7-day horizon, paired tests:

| Strategy | Mean Daily Fare | vs Hot Zone | p-value |
|---|---:|---:|---:|
| Hot Zone | $431.21 | — | — |
| Single-Step | $548.77 | +$117.56 | < 0.001 |
| **Two-Step** | **$570.61** | **+$139.40** | < 0.001 |

Two-Step vs Single-Step: +$21.84/day, paired bootstrap 95% CI [$5.00, $39.53], p = 0.0151.

### 4.3 Deep Reinforcement Learning

| Algorithm | Revenue Delta vs Single-Step | 95% CI | Significant? |
|---|---:|---:|:---:|
| **DQN** | **+$53.74** | [+46.21, +61.57] | Yes |
| Double DQN | -$25.27 | [-32.77, -17.97] | Yes (worse) |

### 4.4 Multi-Agent Competition (50 Drivers)

| Strategy | Avg Revenue/Driver | Utilization |
|---|---:|---:|
| Random | $189.42 | 3.1% |
| Single-Step | $412.85 | 10.8% |
| **Two-Step** | **$438.17** | **12.3%** |

At fixed fleet size, raising demand/supply ratio from 0.5x to 2.0x increases Single-Step utilization from 6.42% to 18.53%.

### 4.5 Offline Policy Evaluation (Trajectory-Level)

100-draw complete-trajectory bootstrap:

| Policy | WIS | Sequential DR |
|---|---:|---:|
| Stay (on-policy, prob = 1.0) | $438.55 | $431.74 |
| IQL (off-policy, uniform behavior) | $0.00 | $12.44 |

IQL's zero WIS reflects deterministic target policy with uniform exploration (prob = 1/263) — a support overlap failure, not a software bug. Sequential DR partially recovers the estimate via its model-based component.

### 4.6 Demand Forecasting

| Model | MAE | RMSE | vs Baseline |
|---|---:|---:|---:|
| Historical Average | 1.7273 | 5.9237 | — |
| LightGBM | 1.5114 | 5.0707 | -12.5% |
| **Ensemble (LGB + XGB)** | **1.4868** | **4.9810** | **-13.9%** |

### 4.7 Graph-Enhanced Forecasting (Negative Result)

| Model | MAE | 95% CI vs Non-Graph LGB | Crosses Zero? |
|---|---:|---|---|
| LightGBM (baseline) | 1.5114 | — | — |
| OD Messages (no embedding) | 1.5017 | [-0.003, +0.022] | Yes |
| GraphSAGE | 1.5037 | [-0.004, +0.020] | Yes |
| GAT | 1.5059 | [-0.006, +0.018] | Yes |

**Finding:** No graph-based model shows statistically significant improvement over non-graph LightGBM at the timestamp level. This negative result is robust across 192 bootstrap blocks.

### 4.8 Forecast-Decision Gap

| Strategy | Simulator Revenue | vs Single-Step |
|---|---:|---:|
| Single-Step (historical demand) | $548.77 | — |
| Single-Step (forecast-enhanced) | $530.89 | **-$17.88** |

Better forecast accuracy (MAE 1.49 vs 1.73) produces _worse_ decisions. This empirically validates the need to separate forecasting and decision evaluation.

---

## 5. Ablation Studies

### 5.1 Feature Importance

| Configuration | MAE | vs Full | Conclusion |
|---:|---:|---:|
| Full features (LightGBM) | 1.511 | — | Reference |
| Without lag features | 1.534 | +0.023 | Lags important |
| Without rolling features | 1.563 | +0.052 | Rolling history most important |
| Without spatial features | 1.517 | +0.006 | Minor contribution |

### 5.2 Demand-Supply Ratio Sensitivity

| D/S Ratio | Single-Step Utilization | Avg Revenue |
|---:|---:|
| 0.5x | 6.42% | $387.21 |
| 1.0x | 10.75% | $412.85 |
| 1.5x | 14.31% | $431.66 |
| 2.0x | 18.53% | $448.12 |

---

## 6. Discussion

### 6.1 The Prediction-Policy Gap

Better demand prediction does not automatically improve repositioning decisions. The forecast-enhanced single-step strategy underperforms the historical variant by -$17.88/day (Cohen $d_z$ = -0.17). This challenges the common assumption in mobility research that improving prediction quality directly improves decisions, and motivates the platform's design of separate forecasting and decision evaluation pipelines.

### 6.2 Graph Neural Networks for Zone Forecasting

Despite widespread adoption of GNNs for spatiotemporal prediction, our comprehensive benchmark shows no significant improvement over gradient-boosted trees with proper feature engineering. All graph variants (GraphSAGE, GAT, OD Messages) produce confidence intervals crossing zero against non-graph LightGBM. This negative result is robust across 192 timestamp blocks and multiple statistical tests, suggesting that the OD graph structure does not capture additional predictive signal beyond what temporal features already provide.

### 6.3 DQN vs Double DQN

DQN significantly outperforms Single-Step (+$53.74), but Double DQN underperforms (-$25.27). This is notable because Double DQN was specifically designed to address DQN's overestimation bias. The reversal suggests that overestimation bias may not be the primary challenge in this domain — or that the bias actually helps exploration in this reward structure.

### 6.4 Offline RL and Support Overlap

IQL's zero WIS estimate is a methodological finding: when a deterministic target policy is evaluated against data collected under uniform exploration over 263 actions, importance weights collapse. This is expected behavior — the importance sampling support condition is violated — but documenting it serves as a calibration check and a reminder that OPE estimators are only valid under appropriate logging policies.

### 6.5 Exposure Concentration

Two-Step strategy has 70.33% weighted airport exposure and an exposure Gini of 0.982. If deployed at scale, airport zones would face severe saturation, degrading the policy's performance. This is a key open research question.

---

## 7. Scientific Limitations

> **Read before citing results.** These limitations are fundamental to the methodology, not implementation oversights.

### 7.1 Simulator Boundary

The multi-agent simulator omits: congestion and traffic dynamics, airport queue rules (TLC-mandated), endogenous passenger demand response, strategic driver adaptation, and market equilibrium effects. **Rollout results must not be presented as production revenue estimates.**

### 7.2 Counterfactual Identifiability

NYC TLC trip records do not contain logged reposition recommendations, behavior-policy propensities, or driver acceptance actions. Valid IPS, SNIPS, or DR evaluation is therefore not identifiable from observational data alone. Simulator-generated trajectories with known propensities fill this gap for methodological benchmarking.

### 7.3 Forecast-Decision Gap

Empirically confirmed: better forecast accuracy does not imply better recommendation decisions. The platform explicitly maintains separate forecast and decision evaluation pipelines.

### 7.4 Generalization

All results are on NYC Yellow Taxi data. Geographic, temporal, and modal (green taxi, ride-hail) generalization remains untested.

---

## 8. Related Work

| Area | Key References | Distinction from Our Work |
|---|---|---|
| Taxi recommendation | Yuan et al. (2011), Qu et al. (2014) | Unified platform with OPE |
| RL for mobility | Lin et al. (2018), Shi et al. (2019) | Reproducible benchmark protocol |
| Offline RL / OPE | Levine et al. (2020), Jiang & Li (2016), Thomas & Brunskill (2016) | Trajectory-level WIS/DR on spatiotemporal data |
| Spatiotemporal forecasting | Ke et al. (2017), Yao et al. (2019) | Decision-aware evaluation |
| Graph learning | Geng et al. (2019), Yao et al. (2022) | Negative result with statistical rigor |

---

## 9. Reproducibility

### 9.1 Reproduce All Results

```bash
git clone https://github.com/caizefan34/urban-mobility-ai.git
cd urban-mobility-ai
pip install -e ".[dev,forecasting,graph,rl,api,demo]"
make all          # Full benchmark pipeline
pytest tests -q   # 402 tests
```

### 9.2 Reproducibility Assets

- **Fixed random seeds** throughout all experiments
- **Configuration profiles** in `configs/` directory
- **Experiment manifest** with parameter tracking
- **Docker environment** for exact dependency reproduction
- **402 automated tests** validating core components
- **Automatic figure generation** via scripts

---

## 10. Conclusion

We present an open-source decision intelligence platform for AI-driven fleet repositioning that combines demand forecasting, multi-agent simulation, reinforcement learning, and reproducible policy evaluation. The platform achieves strong benchmark results (NDCG@3 = 0.9565, +$139.40/day simulator lift, DQN +$53.74/day) while maintaining scientific rigor through explicit documentation of limitations, negative results (graph features, IQL transfer, forecast-decision gap), and evaluation protocol constraints.

**We invite the research community to:**
- Use this platform as a standardized benchmark for fleet repositioning
- Submit new policies, forecasters, and city adapters via the external contribution pipeline
- Improve the simulator fidelity and OPE methodology
- Collaborate on the paper with substantial methodological or experimental contributions

---

## References

1. Levine, S., Kumar, A., Tucker, G., & Fu, J. (2020). Offline reinforcement learning: Tutorial, review, and perspectives on open problems. *arXiv:2005.01643*.
2. Jiang, N., & Li, L. (2016). Doubly robust off-policy value evaluation for reinforcement learning. *ICML*.
3. Thomas, P. S., & Brunskill, E. (2016). Data-efficient off-policy policy evaluation for reinforcement learning. *ICML*.
4. Yuan, J., Zheng, Y., Zhang, L., Xie, X., & Sun, G. (2011). Where to find my next passenger? *UbiComp*.
5. Qu, M., Zhu, H., Liu, J., Liu, G., & Xiong, H. (2014). A cost-effective recommender system for taxi drivers. *KDD*.
6. Lin, K., Zhao, R., Xu, Z., & Zhou, J. (2018). Efficient large-scale fleet management via multi-agent deep reinforcement learning. *KDD*.
7. Shi, T., et al. (2019). Efficient connected and automated mobility via multi-agent deep reinforcement learning. *IEEE TITS*.
8. Ke, J., Zheng, H., Yang, H., & Chen, X. (2017). Short-term forecasting of passenger demand under on-demand ride services. *Transportation Research Part C*.
9. Yao, H., et al. (2019). Deep multi-view spatial-temporal network for taxi demand prediction. *AAAI*.
10. Fu, J., Norouzi, M., Nachum, O., Tucker, G., Wang, Z., & Novikov, A. (2021). Benchmarks for deep off-policy evaluation. *ICLR*.

---

**Repository:** https://github.com/caizefan34/urban-mobility-ai
**Contact:** caizefan@sjtu.edu.cn
**Version:** v3.0.0 (2026-08)
