# Codex Research and Engineering Audit

Audit date: 2026-07-25

Scope: repository state before the major simulator, RL, and graph-learning upgrades; the current PR adds only supervised demand forecasting.

## Executive assessment

The repository now has a reproducible chronological data path, explicit simulator-trained Q-learning labeling, paired statistical tests, and a leakage-safe supervised forecasting pipeline. Its strongest empirical result is limited to a fixed single-driver simulator. The evidence does not support claims of real-world revenue lift, causal policy value, offline-RL validity, equilibrium behavior, or novel Bellman planning.

The highest-impact remaining weakness is the simulator: it has one driver, immutable demand, no competition, and no supply-demand feedback. Until that is repaired, increasingly sophisticated policies can exploit simulator artifacts and cannot establish fleet-level value.

## Risk register

| Area | Finding | Risk | Evidence / consequence |
|---|---|---:|---|
| Modeling assumptions | Zone and half-hour aggregation erase within-zone position, queues, traffic state, and driver heterogeneity. | High | Transition and reward uncertainty are understated. |
| Simulator realism | Demand is not depleted and drivers do not compete. | Critical | The same attractive trip can effectively remain available to every hypothetical driver; saturation is unmeasured. |
| Demand estimation | Historical averages are stationary; recursive forecasts drift without online observations. | High | Supervised validation improves, but the week-long forecast strategy loses $17.88/day versus historical Single-Step in the fixed rollout. |
| Evaluation | Public NDCG/Hit compare against a supplied heuristic reference objective, not optimal or observed counterfactual actions. | Critical | NDCG 0.9565 cannot be interpreted as policy optimality or causal revenue gain. |
| Statistical validity | The 100-seed CI covers simulator randomness only. | High | It excludes training-sample uncertainty, temporal drift, model selection, and interference. |
| Reproducibility | Raw TLC data are externally downloaded and public validation artifacts are not regenerated from raw TLC data. | Medium | Core experiments are reproducible only when those inputs are available. |
| RL quality | Existing tabular Q-learning learns online inside an estimated simulator; logged behavior propensities are absent. | Critical | It is not offline RL, and IPS/SNIPS/DR/CQL claims are not identifiable from TLC trips alone. |
| Novelty | The Two-Step method is truncated lookahead with a fixed continuation heuristic, not full horizon-2 Bellman optimality. | High | A research reviewer can characterize it as task-specific approximate dynamic programming. |
| Market impact | Two-Step exposure is highly concentrated in airport zones. | High | The single-driver reward ignores queueing and recommendation-induced crowding. |

## Demand forecasting audit

The new panel contains every half-hour and every zone. The earliest supervised row is delayed by 336 slots, and same-slot targets do not enter lag, rolling, or neighbor features. Jan 21--24 is chronologically separated from Jan 8--20. LightGBM and XGBoost use the identical feature matrix and seed.

Forecast accuracy improves materially:

| Target | Historical | LightGBM | Selected ensemble |
|---|---:|---:|---:|
| Demand MAE | 1.7273 | 1.5114 | 1.4868 |
| Demand RMSE | 5.9237 | 5.0707 | 4.9810 |
| Fare MAE | 7.0103 | 5.9526 | 5.9188 |

The ensemble demand-MAE improvement is 0.2406 with timestamp-block bootstrap 95% CI [0.1960, 0.2820] and Cohen's dz 0.801. Because blend weights are selected on this same internal validation window, the ensemble metric is a model-selection estimate rather than an untouched test estimate. The unblended LightGBM improvement is the cleaner validation claim; the later public week provides the independent downstream strategy diagnostic.

All three tested feature groups contribute: removing lags, rolling statistics, or neighborhood features worsens LightGBM demand MAE from 1.5114 to 1.5344, 1.5632, or 1.5366. Nevertheless, improved point forecasts do not improve the current downstream score. This mismatch indicates objective and simulator limitations rather than permission to hide a negative benchmark.

## Prioritized roadmap

1. **Multi-agent simulator (next PR).** Add a configurable driver fleet, finite demand inventory, competition, utilization, idle time, fulfilled trips, and zone saturation. Calibrate demand/supply ratios and validate invariants before policy work.
2. **DQN and Double DQN (separate PR).** Wrap the multi-agent simulator in a Gymnasium-compatible environment, define observations/actions/rewards explicitly, fix seeds, and compare against Hot Zone, Single-Step, and Finite Horizon across paired scenarios.
3. **Graph learning (separate PR).** Build the OD graph from training trips only; evaluate GraphSAGE and, if feasible, GAT embeddings as forecasting features with temporal isolation and non-graph ablation.
4. **Combined evaluation.** Compare all policies with paired bootstrap intervals, effect sizes, ablations, multiple temporal windows, and sensitivity to fleet size, demand shocks, and compliance.
5. **Deployment evidence.** Collect recommendation logs, behavior propensities, accept/reject events, driver availability, and realized competing supply. Without these fields, credible counterfactual or offline-RL evaluation remains impossible.

## Expected impact

The multi-agent simulator should reduce optimistic revenue estimates and expose saturation failure modes; this may lower headline gains while increasing scientific validity. Reproducible DQN baselines will determine whether learned control improves the calibrated simulator rather than merely fitting historical aggregates. Graph features may improve sparse-zone demand estimates, but their value must be established by held-out temporal ablation. The combined benchmark should narrow claims to effects supported across seeds, temporal windows, and supply regimes.

## Acceptance boundary

A top-tier ML/RecSys submission would currently face rejection for non-causal evaluation, unrealistic market dynamics, missing multi-agent interference, and limited algorithmic novelty. A credible revision requires the simulator and policy baselines above, several chronological test periods, uncertainty that includes data/model variation, and either logged-policy propensities or a clearly bounded simulator-only claim. Forecast accuracy improvements alone are useful engineering evidence, not proof of recommendation or RL superiority.
