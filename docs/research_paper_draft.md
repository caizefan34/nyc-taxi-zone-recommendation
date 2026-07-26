# Dynamic Urban Mobility Decision System

## Abstract

We present a reproducible research framework for urban mobility decision systems,
combining demand forecasting, calibrated multi-agent simulation, offline reinforcement
learning, and rigorous off-policy evaluation. Using 4 years of NYC Yellow Taxi data
across 263 zones, we demonstrate that better demand prediction does not automatically
translate into better repositioning policies.

## 1. Introduction

Taxi zone recommendation is a finite-horizon stochastic planning problem. Drivers
choose zones based on expected demand, competition, and travel costs. This paper
presents an end-to-end framework from data ingestion to benchmark evaluation. Our
key contribution is demonstrating that the gap between forecasting accuracy and
decision policy effectiveness requires careful experimental design and honest
reporting of negative results.

## 2. Related Work

Our work builds on three research threads: spatiotemporal demand forecasting,
simulation-based policy evaluation, and offline RL for sequential decision making.

**Demand Forecasting.** Traditional taxicab demand models (Moreira-Matias et al., 2013)
used time-series methods on aggregated data. Recent work has shifted to graph neural
networks for spatiotemporal prediction (Geng et al., 2019; Yao et al., 2022). However,
many graph contributions are evaluated without proper statistical testing. Our
benchmark shows that GraphSAGE (MAE 1.504) and GAT (MAE 1.506) do not significantly
outperform LightGBM (MAE 1.511) when bootstrap CIs are computed (GraphSAGE vs LightGBM:
CI [-0.004, +0.020], Cohen d_z = 0.09). This calls into question the practical value
of graph-based methods for zone-level demand prediction.

**Simulation for Policy Evaluation.** Urban mobility simulators (Lin et al., 2018;
Wen et al., 2020) enable offline policy comparison before real-world deployment.
Our calibrated multi-agent simulator v2 extends prior work with parameterized
demand-supply ratios (0.5x to 2.0x) and calibration validation that measures
improvement across fare RMSE (-64.9%), travel time MAE (-56.4%), and KL divergence
(unchanged at 0.662). To our knowledge, this is the first work to report both
successful and failed calibration dimensions.

**Offline RL for Mobility.** Qin et al. (2022) and Li et al. (2023) applied offline RL
to taxi dispatch. Unlike prior work that reports only aggregate metrics, our benchmark
includes paired statistical tests (t-test, Wilcoxon), multiple OPE estimators (FQE,
WIS, DR), bootstrap confidence intervals (2000 resamples), and honest negative results
(Double DQN underperforms Single-Step by -$25/driver, CI [-33, -18]).

## 3. Method

### 3.1 Data Pipeline
Processes NYC TLC Yellow Taxi data (2022-2025): trip-level cleaning, zone aggregation,
temporal feature engineering (lag, rolling, neighbor features). 164,112 training rows
and 50,496 validation rows with strict chronological split to prevent leakage.

### 3.2 Forecasting
Five models: Historical Average, LightGBM, XGBoost, GraphSAGE, and Ensemble.
The Ensemble achieves best MAE of 1.487 on 263 zones, a 13.9% improvement over
the Historical baseline (MAE 1.727). Feature ablation reveals that rolling demand
features contribute more (+0.052 MAE when removed) than lag features (+0.023).

### 3.3 Simulator
Multi-agent simulation with 50 drivers competing for finite trip inventory across
168,000 trip requests per evaluation week. Calibration reduces fare RMSE from 8.883
to 3.109 (-65%) and travel time MAE from 3.034 to 1.315 (-56.7%). The simulator
supports configurable demand-supply ratios (0.5x to 2.0x) for robustness testing.

### 3.4 Offline RL
Implicit Q-Learning (IQL) trained on 53,648 simulator-generated interaction steps.
Dueling DQN with experience replay capacity of 20,000, target network update
interval of 250 steps, and epsilon-greedy exploration decaying from 1.0 to 0.05.

### 3.5 OPE
Three estimators: Fitted Q-Evaluation, Weighted Importance Sampling, Doubly Robust.
Bootstrap confidence intervals with 2000 resamples. Paired tests with Cohen d_z
effect sizes.

## 4. Experiments

### 4.1 Setup
Benchmark across 100 seeds (forecast) and 20 seeds (policy), 7-day simulation episodes,
50 drivers. Cross-year validation: 2022-2025. Training: 2023-01-08 to 2023-01-20.
Validation: 2023-01-21 to 2023-01-24. Evaluation: 2023-01-25 to 2023-02-01.

### 4.2 Evaluation Protocol
- **Forecasting:** Timestamp-block bootstrap with 192 blocks. Paired historical vs
  model on identical timestamps.
- **Policy:** 20 independent rollouts per method. Paired same-seed comparisons.
- **Calibration:** Pre/post comparison on fare RMSE, travel MAE, KL divergence.
- **Cross-year:** Independent evaluation on each year (2022-2025).
- **Latency:** 3,360 queries per strategy. Microsecond-level timing.
- **Reproducibility:** All random seeds fixed. 274 automated tests.

## 5. Results

### 5.1 Forecasting Results

| Model | MAE | RMSE | vs Baseline | Significant? |
|-------|:---:|:----:|:-----------:|:------------:|
| Historical Average | 1.727 | 5.924 | Baseline | -- |
| LightGBM | 1.511 | 5.071 | -12.5% | YES (CI [0.16, 0.27]) |
| XGBoost | 1.496 | 5.002 | -13.4% | YES |
| Ensemble | 1.487 | 4.981 | -13.9% | YES (Cohen d = 0.80) |
| GraphSAGE | 1.504 | 5.072 | -12.9% | NO (CI crosses 0) |
| GAT | 1.506 | 5.073 | -12.8% | NO |
| OD Messages | 1.502 | 5.075 | -13.0% | NO |

**Key finding:** All tree-based models significantly improve over Historical.
Graph-based methods (GraphSAGE, GAT, OD Messages) do NOT significantly improve
over LightGBM. The Ensemble (weighted combination) achieves the best absolute MAE.

### 5.2 Policy Results

| Policy | Revenue/Driver | vs Single-Step | CI | Cohen d_z | Significant? |
|--------|:--------------:|:--------------:|:--:|:---------:|:------------:|
| Hot Zone | $1,689 | -- | -- | -- | -- |
| Two-Step | $1,508 | -- | -- | -- | -- |
| Single-Step | $1,768 | Baseline | -- | -- | -- |
| Double DQN | $1,743 | -$25 | [-33, -18] | -1.45 | YES (negative) |
| DQN | $1,822 | +$54 | [+46, +62] | 2.99 | YES (p < 1e-10) |
| IQL | $1,795 | -- | -- | -- | -- |

**Key finding:** DQN significantly outperforms all baselines (+$54/driver/week,
p < 1e-10). Double DQN underperforms Single-Step (-$25, p < 1e-6), showing that
the theoretical advantage of Double DQN does not translate to this domain.
IQL achieves competitive revenue ($1,795) but operates on a different reward scale
and is not directly comparable.

### 5.3 Calibration Results

| Metric | Before | After | Change |
|--------|:-----:|:-----:|:------:|
| Fare RMSE | 8.88 | 3.11 | -64.9% |
| Travel Time MAE | 3.03 | 1.32 | -56.4% |
| KL Divergence | 0.662 | 0.662 | No change |
| JS Divergence | 0.035 | 0.035 | No change |
| Wasserstein Dist | 3.15 | 4.41 | Worse |

**Key finding:** Calibration improves 2/3 dimensions. Fare and travel time metrics
improve substantially. Demand distribution matching remains unchanged, indicating
a need for additional demand-side calibration factors.

### 5.4 Ablation Study

**Feature ablation.** We removed feature groups from the LightGBM model and measured
MAE change:
- Without lags: MAE 1.534 (+0.023, -1.5% degradation)
- Without rolling: MAE 1.563 (+0.052, -3.4% degradation)
- Without neighborhood: MAE 1.537 (+0.026, -1.7% degradation)
Rolling demand features contribute most to model accuracy.

**Graph feature ablation.** We compared LightGBM against graph-enhanced variants:
- LightGBM no-graph: MAE 1.511
- OD Messages: MAE 1.502 (no significant improvement, CI crosses 0)
- GraphSAGE: MAE 1.504 (no significant improvement)
- GAT: MAE 1.506 (no significant improvement)
No graph method significantly improves over non-graph LightGBM.

**Policy ablation.** DQN consistently outperforms Double DQN across 20 runs (paired
test: -$79, CI [-89, -70], Cohen d_z = -3.62). The forecasting-enhanced heuristic
underperforms the simpler historical baseline (-$17.88/day, p = 0.087, Cohen
d_z = -0.17). This confirms the prediction-policy gap: better demand prediction
does not guarantee better repositioning decisions.

**Simulator calibration ablation.** Fare RMSE improves substantially (8.88 -> 3.11),
but demand distribution metrics remain unchanged. This suggests the calibration
primarily adjusts fare/timing parameters rather than demand patterns. The Wasserstein
distance actually increases (3.15 -> 4.41), indicating that demand distribution
matching may require structurally different calibration strategies.

**Demand ratio ablation.** We varied the demand-supply ratio from 0.5x to 2.0x:
- 0.5x (low demand): Single-Step $985, DQN $1,117
- 1.0x (baseline): Single-Step $1,768, DQN $1,822
- 2.0x (high demand): Single-Step $2,977, DQN $3,028
RL policies maintain their relative advantage across all demand regimes.

### 5.5 Cross-Year Robustness

| Year | MAE | Drift Detected |
|:----:|:---:|:--------------:|
| 2022 | 0.852 | no |
| 2023 | 1.492 | no |
| 2024 | 3.239 | yes |
| 2025 | 1.022 | no |

Drift detected in 1/4 years (2024). The 2024 anomaly may reflect post-pandemic
demand restructuring. Model retraining or calibration adjustment may be needed.

### 5.6 Latency Benchmark

| Strategy | Mean (us) | P95 (us) | P99 (us) |
|----------|:---------:|:--------:|:--------:|
| Stay | 0.07 | 0.10 | 0.20 |
| Random | 8.67 | 9.40 | 15.71 |

All strategies are well within real-time constraints.

## 6. Discussion

**The prediction-policy gap.** Our results empirically confirm that better demand
prediction does not automatically translate into better repositioning policy. The
forecasting-enhanced heuristic underperforms historical baseline in the single-driver
simulator (-$17.88/day, Cohen d_z = -0.17). This challenges the common assumption
in mobility research that improving prediction quality directly improves decisions.

**Graph networks for zone forecasting.** Despite widespread adoption of graph neural
networks for spatiotemporal prediction, our comprehensive benchmark shows no
significant improvement over gradient-boosted trees with proper feature engineering.
All graph variants (GraphSAGE, GAT, OD Messages) have confidence intervals crossing
zero when compared to non-graph LightGBM. This negative result is robust across
192 timestamp blocks and multiple statistical tests.

**Simulator calibration effectiveness.** Calibration improves fare and travel time
metrics substantially but fails to improve demand distribution matching. The
Wasserstein distance actually increases after calibration. This partial success
(2/3 dimensions) highlights the challenge of calibrating complex multi-agent systems
and the importance of reporting both successful and failed calibration dimensions.

**Offline RL in simulated environments.** DQN achieves the best revenue among all
methods (+$54/driver/week over Single-Step). However, Double DQN underperforms
Single-Step, suggesting that overestimation bias is not the primary challenge in
this domain. IQL achieves competitive results but on a different reward scale,
making direct comparison unreliable. These mixed results underscore that offline
RL algorithm selection requires domain-specific validation.

**Limitations.** Offline RL is trained on simulator data, not real trajectories.
OPE estimators are not validated against online deployment. Temporal drift (2024
MAE 3.24 vs training MAE 0.85) limits generalization. Single seed per method does
not capture training variability. All results are limited to NYC Yellow Taxis.
No causal identification is performed.

## 7. Future Work

Several directions follow from this work:

1. **Online validation.** Deploying policies in a real-world pilot to validate
simulator fidelity and OPE accuracy. The discrepancy between simulator and real-world
performance is the largest unknown in our framework.

2. **Multi-city generalization.** Extending the pipeline to Chicago, London,
and other cities to test geographic robustness. The 263-zone NYC topology may not
generalize to cities with different spatial structures.

3. **Multi-seed RL training.** Current results use a single training seed per method.
Multi-seed (10+) training with statistical aggregation would capture training
variability and improve confidence in policy rankings.

4. **Temporal adaptation.** Developing methods to handle temporal drift (detected
in 2024) without full retraining. Online calibration or adaptive forecasting could
mitigate the drift effects.

5. **Contextual bandit integration.** Using logged driver data with contextual
bandits to bridge the simulation-reality gap.

6. **Policy ensemble methods.** Combining multiple RL policies (DQN, IQL) with
weighted voting could improve robustness.

7. **Dynamic calibration.** Addressing the unchanged KL and JS divergences through
structurally different calibration objectives that directly optimize demand
distribution matching.

## 8. Conclusion

This work provides a reproducible benchmark for urban mobility decision systems,
demonstrating the gap between prediction accuracy and policy effectiveness.
Key findings include: (1) graph signals do not improve forecasting beyond
gradient-boosted trees, (2) DQN outperforms greedy baseline by $54/driver/week
(CI [+46, +62], Cohen d_z = 2.99), (3) calibration improves 2/3 simulator dimensions,
and (4) better prediction does not guarantee better policy (Cohen d_z = -0.17).
All code, data, and results are open-source for independent replication.
