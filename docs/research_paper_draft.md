# Dynamic Urban Mobility Decision System

## A Reproducible Framework for Zone Recommendation in the NYC Taxi Market

**Draft Date:** 2026-07-26
**Repository:** https://github.com/caizefan34/nyc-taxi-zone-recommendation

---

## Abstract

Urban taxi drivers face a fundamental sequential decision problem: after dropping off a passenger,
which zone should they relocate to in order to minimize idle time and maximize expected revenue?
We present a reproducible research framework that combines multi-year NYC TLC Yellow Taxi data,
temporal demand forecasting, a calibrated multi-agent supply-demand simulator, and offline
reinforcement learning to produce zone-recommendation policies. Our forecasting ensemble achieves
a demand MAE of 1.487 (12.5% improvement over the historical baseline), and our calibrated simulator
matches real fare distributions with an RMSE of 3.11 (65% improvement). We implement Implicit
Q-Learning (IQL) for offline policy optimization and compare against DQN and Double DQN baselines
using three off-policy evaluation methods (FQE, WIS, Doubly Robust) with bootstrap confidence intervals.

We acknowledge fundamental limitations: all RL trajectories are simulator-generated rather than collected
from real driver behavior; policy comparisons use a single training seed; and drift is detected in 2024 data
(MAE 3.24), indicating that temporal generalization remains an open challenge. This work is intended as a
reproducible research artifact for the urban mobility community.

---

## 1. Introduction

The NYC taxi market comprises 263 official taxi zones with time-varying demand patterns. Drivers must
decide where to position themselves to maximize earning opportunities—a task complicated by competition,
relocation costs, and demand uncertainty. Existing approaches range from simple heuristic rules (stay in
the current hot zone) to single-step utility maximization, but few provide a reproducible end-to-end
framework spanning data processing, forecasting, simulation, offline RL, and rigorous evaluation.

We address four interconnected research questions: (1) Can we accurately forecast zone-level demand
30 minutes ahead using multi-year data? (2) Can we build a realistic yet computationally efficient
simulator that captures multi-agent competition effects? (3) Can offline RL improve recommendation
policies beyond heuristic baselines? (4) Can we rigorously evaluate policies without online deployment?

Our contributions are: (i) a cleaned, temporally-split multi-year NYC TLC dataset (2022-2025);
(ii) a LightGBM-based forecasting pipeline with ensemble blending; (iii) DynamicSimulator v2,
a calibrated event-driven multi-agent simulator; (iv) an IQL-based offline RL policy; (v) three OPE
methods with bootstrap intervals; and (vi) a comprehensive benchmark with statistical significance testing.

---

## 2. Related Work

**Taxi demand forecasting** has been extensively studied using time-series models (ARIMA, Prophet),
gradient boosting (LightGBM, XGBoost), and graph neural networks. Our work builds on established
feature engineering patterns (temporal lags, rolling statistics, neighborhood features) and provides
a reproducible benchmark with paired bootstrap confidence intervals.

**Multi-agent simulation** for urban mobility includes MATSim, SUMO, and custom discrete-event models.
Our DynamicSimulator v2 takes a simplified, analytically tractable approach with supply-dependent
pickup probability, explicit competition effects, and decomposed reward components. We validate against
real TLC distributions using KL divergence, Wasserstein distance, and temporal correlation metrics.

**Offline reinforcement learning** has seen rapid progress with algorithms such as IQL (Kostrikov et al., 2022),
CQL, and Decision Transformer. We apply IQL because it avoids querying out-of-distribution actions via
expectile regression, making it well-suited for the bounded action space of 263 zones.

**Off-policy evaluation** methods including FQE, importance sampling, and doubly robust estimation
(Dudik et al., 2011) provide statistical tools for evaluating policies without online deployment.
We follow best practices from Voloshin et al. (2021) and provide bootstrap confidence intervals.

---

## 3. Method

### 3.1 Data Pipeline

We use NYC TLC Yellow Taxi Trip Records (2022-2025), approximately 115M trips across 48 monthly files.
The pipeline performs: (1) schema validation and cleaning (filtering trip duration 1-240 min, fare $0-$200,
distance 0.1-100 miles, speed under 80 mph); (2) temporal split with strict time isolation:
train (2022-2023), validation (2024), test (2025); (3) feature engineering including zone-time demand
aggregation, mean fare computation, and travel time matrix construction via Dijkstra on historical data.

### 3.2 Forecasting

We compare three models: Historical Average (training-period mean by zone-weekday-slot),
LightGBM (500 estimators, max_depth=8, 64 leaves), and a blended ensemble (0.75 LightGBM + 0.25 historical
for demand; 0.85 LightGBM + 0.15 historical for fare). Features include temporal indicators,
demand lags (1, 2, 48, 336 slots), rolling statistics (3, 48, 336 slots), neighbor-zone features,
and external weather/holiday variables.

### 3.3 Dynamic Simulator

DynamicSimulator v2 is an event-driven multi-agent simulation with 50 drivers operating across 263 zones.
Key dynamics: (1) supply-dependent pickup probability using a half-saturation function (base=40, elasticity=0.3);
(2) finite trip inventory depleted by successful pickups; (3) decomposed rewards:
reward = fare - fuel_cost - time_cost - competition_penalty - risk_penalty;
(4) configurable traffic and weather variation. Simulation runs for 7 days with 30-minute time slots.

### 3.4 Simulator Calibration

Calibration aligns simulator outputs with TLC data across four dimensions: demand (scale factor 1.0),
fare (factor 0.80), travel time (factor 1.0), and reward scaling (factor 0.80). After calibration:
fare RMSE improves from 8.88 to 3.11 (65% reduction), travel MAE from 3.03 to 1.31 (57% reduction).
Zone demand distribution achieves 0.983 correlation with real data.

### 3.5 Offline RL (IQL)

Implicit Q-Learning uses expectile regression (tau=0.7, beta=3.0) with a double-clipped ensemble of 2 critics.
The state space is 7-dimensional (zone id, demand, fare, hour, weekday, competition, time since pickup).
Action space is 263 zones. Training uses 20 simulator episodes collected into a buffer of 100,000 transitions.
IQL update steps: 10,000 with batch size 256, hidden dimension 256, learning rate 3e-4.

### 3.6 Off-Policy Evaluation

We implement three OPE methods: (1) FQE - bootstrapped Q-function regression; (2) WIS - weighted importance
sampling with trajectory-wise weights; (3) DR - doubly robust combining FQE and IS. All estimates include
95% bootstrap confidence intervals (2000 resamples for benchmark statistics). Policies compared:
DQN, Double DQN, and IQL.

---

## 4. Experiments

### 4.1 Setup

All experiments use seed 42 for reproducibility. Forecasting is evaluated on held-out 2025 test data.
Simulator and RL experiments use 7-day simulation episodes with 50 drivers. Evaluation metrics include
demand MAE/RMSE, fare MAE, NDCG@3, Hit@3, revenue per driver, utilization rate, and episode return.
Statistical comparisons use paired bootstrap with 2000 resamples and Cohen's d effect sizes.

### 4.2 Forecasting Results

| Model | Demand MAE | Demand RMSE | Fare MAE | Fare RMSE |
|-------|-----------:|------------:|---------:|----------:|
| Historical Average | 1.7273 | 5.9237 | 7.0103 | 12.8339 |
| LightGBM | 1.5114 | 5.0707 | 5.9526 | 10.6708 |
| Selected Ensemble | 1.4868 | 4.9810 | 5.9188 | 10.6106 |

The ensemble achieves a statistically significant improvement over historical average: demand MAE
improvement 0.241, 95% CI [0.196, 0.282], Cohen's dz = 0.801. Feature ablation confirms that rolling
statistics are the most important feature category (loss of 0.052 MAE when removed).

### 4.3 Simulator Validation

Simulator zone demand distribution correlates with real TLC data at r = 0.983. KL divergence: 0.662,
JS divergence: 0.035. Temporal pattern validation shows hourly/weekday patterns are well-captured,
though 2024 exhibits drift (MAE 3.24, flagged as significant).

### 4.4 Calibration Effectiveness

| Metric | Before | After | Improvement |
|--------|-------:|------:|:-----------:|
| Fare RMSE | 8.8830 | 3.1091 | 65.0% |
| Travel MAE | 3.0340 | 1.3147 | 56.7% |
| KL Divergence | 0.6622 | 0.6622 | 0% |

Fare and travel time calibration show substantial improvement. Demand distribution KL divergence
did not change, indicating that the demand calibration factor may need further tuning.

### 4.5 Policy Evaluation

| Policy | Revenue/Driver | Utilization | DR OPE Estimate |
|--------|---------------:|:-----------:|----------------:|
| Hot Zone | $1,689 | N/A | N/A |
| Single-Step | $1,768 | N/A | N/A |
| DQN | $1,822 | 0.138 | 239.56 |
| Double DQN | $1,743 | 0.143 | N/A |
| IQL | $1,795 | 0.285 | 235.68 |

Note: IQL and DQN operate under different reward scales, so direct revenue comparisons between
online (DQN/Double DQN) and offline (IQL) methods should be interpreted cautiously. DQN achieves the
highest simulator revenue ($1,822/driver), while IQL achieves the highest utilization rate (28.5%).

---

## 5. Results Summary

**Forecasting:** Ensemble reduces demand MAE 12.5% over historical baseline (p < 0.001, dz = 0.801).
**Simulator:** Calibrated fare distribution within 3.11 RMSE of real data; zone correlation r = 0.983.
**RL policies:** DQN achieves highest revenue ($1,822/driver); IQL achieves highest utilization (28.5%).
**OPE:** FQE, WIS, and DR provide consistent policy rankings, though bootstrap CIs are wide.
**Cross-year:** 2024 drift detected (MAE 3.24), suggesting distribution shift challenges.
**Tests:** 274 tests pass, 15 skip (data-dependent tests).

---

## 6. Limitations

We explicitly identify the following limitations:

1. **Simulator-based trajectories**: All offline RL trajectories are generated by DynamicSimulator v2,
   not collected from real driver behavior. Simulated outcomes may not transfer to real-world deployment.

2. **Single training seed**: Policy comparisons use a single training seed (42).
   Confidence intervals reflect evaluation uncertainty, not training variability.

3. **Temporal drift**: Cross-year evaluation detects significant drift in 2024 (MAE 3.24 vs 0.85 in 2022).
   Models trained on 2022-2023 data may not generalize to future market conditions.

4. **No causal identification**: Correlations between policy actions and outcomes do not imply
   causal effects. OPE estimates are not substitutes for randomized controlled trials.

5. **Different reward scales IQL vs DQN**: IQL operates on a different reward scale than DQN/Double DQN,
   making direct revenue comparisons between online and offline methods unreliable.
   Cross-method comparisons should be interpreted with caution.

6. **Partial observability**: The 7-dimensional state space may miss relevant market information
   such as airport schedules, special events, or real-time traffic conditions.

7. **Simplified driver behavior**: Drivers in simulation do not learn, adapt, or exhibit strategic
   behavior changes in response to market conditions.

---

## 7. Conclusion

We present a reproducible end-to-end framework for urban mobility decision-making, combining multi-year
NYC TLC data, temporal forecasting, calibrated simulation, offline RL, and rigorous OPE. Our results
demonstrate that supervised forecasting materially improves demand prediction, calibrated simulation
can approximate real fare distributions, and offline RL policies achieve competitive utilization rates.
However, we emphasize that simulator-based results do not guarantee real-world deployment performance.
The primary contribution of this work is a reproducible research artifact with transparent methodology,
explicit limitations, and statistically rigorous comparisons that the community can build upon.

---

## References

1. Kostrikov, I., Nair, A., & Levine, S. (2022). Offline Reinforcement Learning with Implicit Q-Learning. ICLR 2022.
2. Dudik, M., Langford, J., & Li, L. (2011). Doubly Robust Policy Evaluation and Learning. ICML 2011.
3. Voloshin, C., Le, H. M., Jiang, N., & Yue, Y. (2021). Empirical Study of Offline Policy Evaluation. ICML 2021.
4. NYC Taxi & Limousine Commission. TLC Trip Record Data. https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page
5. Fujimoto, S., Meger, D., & Precup, D. (2019). Off-Policy Deep Reinforcement Learning without Exploration. ICML 2019.
