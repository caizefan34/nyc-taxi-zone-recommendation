# Dynamic Urban Mobility Decision System

## Research Release Report

**Version:** 1.0.0  
**Date:** 2026-07-26  
**Repository:** https://github.com/caizefan34/nyc-taxi-zone-recommendation

---

## 1. Problem Definition

### 1.1 Background

Urban taxi drivers face a fundamental decision problem: **where to go next** to find passengers. The NYC taxi market consists of 263 official taxi zones, each with time-varying demand, competition intensity, and earning potential. Drivers must decide which zone to relocate to after dropping off a passenger, balancing:

- **Expected fare revenue** at the destination
- **Relocation cost** (fuel, time) to reach that zone
- **Competition** from other drivers already in the zone
- **Uncertainty** about actual demand upon arrival

### 1.2 Research Questions

This project addresses four core research questions:

1. **Forecasting**: Can we predict zone-level demand 30 minutes ahead using multi-year NYC TLC data and external features?
2. **Simulation**: Can we build a realistic supply-demand simulator that captures multi-agent competition?
3. **Decision-making**: Can offline reinforcement learning improve driver zone-recommendation policies?
4. **Evaluation**: Can we rigorously evaluate policies without online deployment?

### 1.3 Key Challenges

- **Temporal dynamics**: Demand follows complex weekly, daily, and hourly patterns with seasonality.
- **Spatial structure**: Zones are connected via a directed travel-time graph with heterogeneous demand profiles.
- **Multi-agent competition**: Driver decisions affect each other's outcomes through finite trip inventory.
- **Evaluation without deployment**: Offline policy evaluation is necessary because online experimentation is impractical.

---

## 2. Dataset

### 2.1 Source

We use the **NYC TLC Yellow Taxi Trip Records** from January 2022 to December 2025. The dataset contains:

| Year | Rows (approx.) | Files |
|------|----------------|-------|
| 2022 | ~30M | 12 monthly parquet files |
| 2023 | ~32M | 12 monthly parquet files |
| 2024 | ~28M | 12 monthly parquet files |
| 2025 | ~25M | 12 monthly parquet files |

### 2.2 Preprocessing

Each trip record is cleaned using the following criteria:

- **Trip duration**: 1 - 240 minutes
- **Fare amount**: 0 - 200 USD
- **Trip distance**: 0.1 - 100 miles
- **Speed**: maximum 80 mph

### 2.3 Temporal Split

Data is split with **strict time isolation** to prevent leakage:

| Split | Period | Purpose |
|-------|--------|---------|
| **Train** | 2022-01-01 to 2023-12-31 | Model training, historical baselines |
| **Validation** | 2024-01-01 to 2024-12-31 | Hyperparameter tuning |
| **Test** | 2025-01-01 to 2025-12-31 | Final evaluation (held out) |

### 2.4 Feature Engineering

- **Zone-time demand**: Pickup counts aggregated by (zone, weekday, 30-min slot)
- **Mean fare**: Average fare amount per (zone, weekday, slot)
- **Travel time matrix**: 263x263 directed matrix computed via Dijkstra on historical traffic data
- **External features**: Weather, holidays, airport schedules, special events
- **Graph features**: Zone adjacency graph from shared boundary information

### 2.5 Data Pipeline

The src/data/pipeline.py module automates:
1. Download from TLC repository (src/data/download.py)
2. Parallel reading with Polars for large-scale columnar processing
3. Cleaning and schema validation
4. Temporal split with manifest generation
5. Zstandard-compressed parquet output

---

## 3. Forecasting

### 3.1 Models

We compared multiple forecasting approaches:

| Model | Description | Features |
|-------|-------------|----------|
| **Historical Average** | Training-only (zone, weekday, slot) mean | Zone, time |
| **LightGBM** | Gradient-boosted trees with time-series features | Demand lags, rolling stats, neighbor features |
| **XGBoost** | Alternative gradient boosting | Same feature set |
| **Temporal GNN** | Graph neural network over zone adjacency | Spatial-temporal graph |

### 3.2 Feature Set

The LightGBM model uses the following feature categories:

- **Temporal**: weekday, hour, half-hour bucket, time slot
- **Lag features**: demand at lags 1, 2, 48, 336 (30-min slots)
- **Rolling statistics**: mean over 3, 48, 336 previous slots
- **Spatial**: neighbor demand mean/std/max, mean travel time
- **External**: weather conditions, holiday indicator, airport activity

### 3.3 Performance

| Metric | Historical | LightGBM | Improvement |
|--------|-----------:|---------:|:-----------:|
| Demand MAE | Baseline | Reduced | 15-25% |
| Demand RMSE | Baseline | Reduced | 10-20% |
| Fare MAE | Baseline | Reduced | 5-10% |

Results are statistically validated using paired timestamp bootstrap with 95% confidence intervals (see outputs/forecasting_benchmark.json).

---

## 4. Dynamic Simulator

### 4.1 Architecture (v2)

The DynamicSimulator v2 is an event-driven, multi-agent simulation with:

`
┌─────────────────────────────────────────────────────────────┐
│                    DynamicSimulator v2                       │
├─────────────────────────────────────────────────────────────┤
│  SupplyDemandDynamics: pickup probability, demand response   │
│  RewardComponents: fare - fuel - time - competition - risk  │
│  EnvironmentState: zone state, driver state, time           │
│  Event loop: priority-queue driven, 30-min slots            │
└─────────────────────────────────────────────────────────────┘
`

### 4.2 Key Features

- **Supply-dependent pickup probability**: More taxis in a zone reduce each driver's chance of finding a fare
- **Dynamic demand**: Demand responds to traffic, weather, and holiday conditions
- **Competition**: Trip inventory is finite and depleted by successful pickups
- **Interpretable rewards**: Reward = fare - fuel_cost - time_cost - competition_penalty - risk_penalty
- **Configurable**: Driver count, demand ratio, traffic/weather variation, seed

### 4.3 vs v1 (Multi-Agent)

| Feature | v1 (Multi-Agent) | v2 (DynamicSimulator) |
|---------|------------------|----------------------|
| Demand | Fixed from TLC data | Synthetic, supply-responsive |
| Competition | Implicit via finite trips | Explicit via pickup probability |
| Rewards | Simple fare-based | Decomposed (5 components) |
| Speed | Slower (data-backed) | Faster (fully synthetic) |
| Realism | High (real trips) | Medium (calibrated) |

### 4.4 Calibration

The simulator is calibrated to real TLC data using src/simulator/calibration.py:

- **Demand calibration**: Scale synthetic demand to match real pickup distributions
- **Fare calibration**: Align simulated rewards with real fare distributions
- **Travel time calibration**: Match real traffic patterns
- **Reward calibration**: Scale v2 rewards to v1-equivalent values (factor ~0.80)

### 4.5 Reality Validation

We validate simulator outputs against real TLC data using:

- **KL/JS divergence** for zone demand distributions
- **Wasserstein distance** for distribution alignment
- **Hourly/weekday/weekend RMSE and correlation** for temporal patterns
- **KS test** for revenue distribution comparison

Results are documented in outputs/simulator_validation_report.md.

---

## 5. Offline RL

### 5.1 Why Offline RL?

Online RL in the taxi domain is impractical:
- Deploying suboptimal policies would reduce driver income
- Environment interaction is expensive (real drivers, real traffic)
- Offline RL leverages existing simulator-generated trajectories

### 5.2 IQL (Implicit Q-Learning)

We implement **IQL** (Kostrikov et al., 2022) which avoids querying out-of-distribution actions:

1. **Value function**: Trained via expectile regression (tau=0.7) to estimate V(s)
2. **Q-function**: Double-clipped ensemble (2 critics) to reduce overestimation
3. **Policy**: Extracted via advantage-weighted regression

**State space (7-dim)**:
- Normalized zone ID, time of day, supply density, effective demand, pickup probability, competition ratio, traffic factor

**Action space**: 263 discrete zones

**Reward**: Net driver profit per time slot

### 5.3 Data Collection

Trajectories are collected from the DynamicSimulator v2 with:

- Random exploration policy for diverse coverage
- Stay policy for baseline comparison
- Each trajectory corresponds to a 7-day simulation run

### 5.4 Training

IQL is trained on collected trajectories with:
- 10,000 gradient updates
- Batch size 256
- Hidden dimension 256
- Expectile tau=0.7 (optimistic)

---

## 6. Evaluation

### 6.1 Offline Policy Evaluation (OPE)

We use three complementary OPE methods:

| Method | Description | Advantages |
|--------|-------------|------------|
| **FQE** | Fitted Q-Evaluation via bootstrapped regression | Model-based, low variance |
| **WIS** | Weighted Importance Sampling | Unbiased asymptotically |
| **DR** | Doubly Robust (FQE + IS) | Lower bias and variance |

All estimates include 95% bootstrap confidence intervals.

### 6.2 Policy Comparison

We compare multiple policies across three dimensions:

**Forecasting**:
- MAE, RMSE for demand and fare prediction
- Paired timestamp bootstrap for statistical significance

**Decision-making**:
- NDCG@3, Hit@3 for recommendation quality
- Realized utility, relocation time

**RL**:
- Episode return (simulated revenue)
- Utilization rate, competition penalty
- OPE estimates with confidence intervals

### 6.3 Statistical Rigor

All comparisons use:
- **Paired bootstrap**: 2000 resamples for confidence intervals
- **Effect size**: Cohen's d for practical significance
- **Multiple OPE methods**: Cross-validation of evaluation estimates
- **Seed control**: All experiments reproducible with fixed seeds

---

## 7. Limitations

### 7.1 Simulation vs. Reality

> **Simulation performance does not guarantee real-world deployment performance.**

1. **Synthetic demand**: The DynamicSimulator v2 uses parameterized demand models, not real-time data.
2. **Simplified driver behavior**: Drivers do not learn or adapt during simulation episodes.
3. **No passenger model**: Passenger behavior is implicit in pickup probability, not explicitly modeled.
4. **Static policies**: Both collection and evaluation use stationary policies, unlike real adaptive drivers.

### 7.2 Offline RL Limitations

1. **Distribution shift**: OPE assumes the target policy's state-action distribution is covered by the training data.
2. **Simulator-generated data**: All offline RL trajectories come from the simulator, not real drivers.
3. **Partial observability**: The 7-dim state may miss relevant global market information.
4. **Reward specification**: The decomposed reward function may not reflect real driver preferences.

### 7.3 Evaluation Limitations

1. **OPE bias**: All OPE methods can be biased under severe distribution shift.
2. **Bootstrap assumptions**: Bootstrap CIs assume i.i.d. samples, which is optimistic for time-series data.
3. **No online validation**: We cannot test policies on real NYC taxi drivers in this research context.

---

## 8. Future Work

### 8.1 Model Improvements

- **Model-based RL**: Learn a world model from real data rather than using the analytical simulator.
- **Conservative Q-Learning (CQL)**: Alternative offline RL algorithm that explicitly penalizes OOD actions.
- **Decision Transformer**: Sequence modeling approach for trajectory-level optimization.

### 8.2 Evaluation

- **Real data OPE**: Evaluate on held-out real TLC data rather than simulator trajectories.
- **Human evaluation**: Compare simulator policies with real driver behavior patterns.
- **Multi-objective**: Extend the reward to include driver satisfaction, fuel efficiency, and fairness.

### 8.3 Deployment

- **API service**: Package the recommendation strategy as a microservice.
- **Real-time adaptation**: Incorporate streaming TLC data for dynamic demand updates.
- **A/B testing framework**: Design a safe online testing protocol for future deployment studies.

### 8.4 Reproducibility

- **MLflow tracking**: Integrate experiment tracking for all runs.
- **Model registry**: Version control for trained models.
- **Containerized deployment**: Docker-based reproducible execution environment.

---

## References

1. Kostrikov, I., Nair, A., & Levine, S. (2022). *Offline Reinforcement Learning with Implicit Q-Learning*. ICLR 2022.
2. Dudík, M., Langford, J., & Li, L. (2011). *Doubly Robust Policy Evaluation and Learning*. ICML 2011.
3. Voloshin, C., Le, H. M., Jiang, N., & Yue, Y. (2021). *Empirical Study of Offline Policy Evaluation*. ICML 2021.
4. NYC Taxi & Limousine Commission. *TLC Trip Record Data*. https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page

---

*This report accompanies the research release of the NYC Taxi Zone Recommendation project. All results are based on simulator experiments and may not transfer to real-world deployment.*
