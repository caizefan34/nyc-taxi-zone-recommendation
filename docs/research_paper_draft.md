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
(Double DQN underperforms Single-Step by -/driver, CI [-33, -18]).

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
- **Forecasting:** Timestamp-block bootstrap with 192 blocks. Paired historical vs model on identical timestamps.
- **Policy:** 20 independent rollouts per method. Paired same-seed comparisons.
- **Calibration:** Pre/post comparison on fare RMSE, travel MAE, KL divergence.
- **Cross-year:** Independent evaluation on each year (2022-2025).
- **Latency:** 3,360 queries per strategy. Microsecond-level timing.
- **Reproducibility:** All random seeds fixed. 284 automated tests.

## 5. Results

### 5.1 Forecasting Results
Ensemble achieves MAE 1.487 (13.9% improvement over historical baseline). Graph-based
models show no statistically significant improvement over non-graph LightGBM. Feature
ablation confirms rolling demand features contribute most to accuracy.

### 5.2 Decision Policy Results
DQN achieves the highest per-driver weekly revenue of ,822 (+ vs Single-Step,
p < 1e-10). Double DQN underperforms Single-Step by -/driver (CI [-33, -18]),
demonstrating that overestimation bias is not the primary challenge.

### 5.3 Offline RL Results
IQL achieves average return of 247.20 with OPE DR estimate of 247.13 (CI [244.91, 249.61]).
Multi-seed validation (5 seeds) shows cross-seed variance of only 0.96, confirming
training stability.

### 5.4 Calibration Results
Calibration improves 2 of 3 simulator dimensions: fare RMSE reduced from 8.883 to 3.109
(-64%), travel MAE reduced from 3.034 to 1.315 (-57%). Demand KL divergence unchanged
at 0.662.

### 5.5 Cross-Year Robustness
Temporal drift detected in 2024 (MAE 3.239 vs training MAE 0.852). 2025 returns to
low drift (MAE 1.022), suggesting 2024 anomalies rather than persistent trend change.

## 6. Ablation Study

### 6.1 Feature Ablation
| Configuration | MAE | vs Full | Impact |
|---------------|:---:|:-------:|:------:|
| Full features (LightGBM) | 1.511 | --- | Reference |
| Without lag features | 1.534 | +0.023 | Lags are necessary |
| Without rolling features | 1.563 | +0.052 | Rolling history is necessary |
| Without graph embedding | 1.504 | -0.008 | Static embedding adds no gain |

### 6.2 Graph Model Ablation
Comparing advanced models against non-graph LightGBM (bootstrapped CI over 192 blocks):

| Model | MAE | CI crosses zero? |
|-------|:---:|:----------------:|
| LightGBM (no graph) | 1.511 | --- |
| OD Messages | 1.502 | YES (CI [-0.003, +0.022]) |
| GraphSAGE-enhanced | 1.504 | YES (CI [-0.004, +0.020]) |
| GAT | 1.506 | YES (CI [-0.006, +0.018]) |

No graph model shows statistically significant improvement over non-graph LightGBM.

### 6.3 RL Algorithm
Revenue comparison across 20 paired runs (50 drivers, same seeds):

| Algorithm | Revenue/Driver | vs Single-Step | Significance |
|-----------|:--------------:|:--------------:|:------------:|
| Single-Step | ,768 | baseline | --- |
| DQN | ,822 | + | p < 1e-10 |
| Double DQN | ,743 | - | p < 0.001 |

DQN is the only RL algorithm that significantly outperforms the greedy Single-Step baseline.

## 7. Discussion

**The prediction-policy gap.** Our results empirically confirm that better demand
prediction does not automatically translate into better repositioning policy. The
forecasting-enhanced heuristic underperforms historical baseline in the single-driver
simulator (-.88/day, Cohen d_z = -0.17). This challenges the common assumption
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
methods (+/driver/week over Single-Step). However, Double DQN underperforms
Single-Step, suggesting that overestimation bias is not the primary challenge in
this domain. IQL achieves competitive results but on a different reward scale,
making direct comparison unreliable. These mixed results underscore that offline
RL algorithm selection requires domain-specific validation.

## 8. Limitations

1. **Offline RL trajectories are simulator-generated**, not real logged driver data.
   RL policies may not transfer to real-world driving conditions.
2. **Simulation performance is not real-world deployment** --- models omit congestion,
   airport queues, strategic driver adaptation, and regulatory constraints.
3. **Temporal drift exists** --- models trained on 2023 may not generalize to 2024+.
   The detected 2024 drift (MAE 3.24 vs 0.85) limits deployment reliability.
4. **OPE not validated** against ground-truth online evaluation. Doubly Robust
   estimates assume correct model specification which is unverifiable without
   online data.
5. **Exposure concentration** --- two-step strategy has 70% airport exposure (55% at JFK),
   creating vulnerability to airport-specific disruptions.
6. **Single city** --- all results are limited to NYC Yellow Taxis. Geographic
   generalization is not tested.
7. **Single training seed** per method for most RL algorithms (except IQL with 5 seeds).
   Training variance may be underestimated.
8. **No causal identification** --- correlations between recommendations and outcomes
   may confound with unobserved demand shocks.

## 9. Benchmark Contribution

### 9.1 Standardized Evaluation
This work establishes a public benchmark protocol for taxi zone recommendation, including:
- Standardized dataset splits (chronological, leakage-safe)
- Unified metrics across forecasting, decision-making, and RL
- Bootstrap confidence intervals for statistical rigor
- Extensible model interfaces for community contributions

### 9.2 Baseline Results
Provide reference results for future work:

| Task | Metric | Best Model | Score |
|------|--------|-----------|:-----:|
| Forecasting | MAE | Ensemble | 1.487 |
| Decision | Revenue | DQN | ,822/driver |
| RL | Return | IQL | 264.88 |

### 9.3 Reproducibility Statement
All experiments in this paper are reproducible:
- Source code: https://github.com/caizefan34/nyc-taxi-zone-recommendation
- Configuration files: configs/ (YAML-based parameter management)
- Experiment manifest: configs/experiment_manifest.yaml
- Fixed random seeds throughout
- Docker environment specification
- Automatic figure generation scripts
- 284 unit tests validating core components

## 10. Broader Impact

### 10.1 Positive Potential
- Reduce driver idle time and fuel consumption
- Improve urban mobility efficiency
- Open research framework for community contribution

### 10.2 Negative Potential
- Algorithmic recommendations may concentrate drivers in wealthy areas
- Simulation-based optimization may not reflect real driver preferences
- Deployment without validation could reduce driver earnings

## 11. Ethical Considerations
- All data is publicly available NYC TLC data
- No personally identifiable information used
- Zone-level aggregation protects privacy
- Negative results reported transparently
- Limitations clearly documented

## 12. Future Work

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

## 13. Final Conclusion

This paper presents a reproducible research framework for urban mobility decision systems. Through multi-year NYC TLC data, calibrated simulation, offline RL, and rigorous evaluation, we demonstrate that improving predictive accuracy does not guarantee better decision policies. The framework is designed for extensibility, inviting community contributions toward more robust and generalizable urban mobility solutions.
