# Research-grade v2 Upgrade Audit

> **Date:** 2026-07-26
> **Repository:** caizefan34/urban-mobility-ai
> **Audit type:** Final acceptance — no code modified

---

## 总体评分

| Category | Score | Reasoning |
|---|---|---|
| **Data** | 7/10 | Multi-year pipeline exists (2022-2025) but download is untested on CI; no real data in repo |
| **Forecast** | 8/10 | LightGBM, XGBoost, Ensemble all work; GraphSAGE/GAT CI crosses zero (honest negative result) |
| **Simulator** | 9/10 | v2 dynamic simulator has full supply-demand feedback, competition, weather/traffic; genuine upgrade from v1 |
| **RL** | 6/10 | DQN/DDQN solid; IQL exists but trains on synthetic buffer data, not real trajectories |
| **Benchmark** | 8/10 | Comprehensive matrix with forecast, decision, robustness, deployment; Pareto analysis included |
| **Engineering** | 7/10 | Tests pass, lint clean, docs exist; no real data pipeline CI test; no CQL/Decision Transformer |

**Overall: 45/60 (75%)**

---

## 完成状态

| Phase | Status | Notes |
|---|---|---|
| **Phase 1 Data** | **PARTIAL** | Multi-year pipeline is coded and structured, but not executed with real data in CI. Data files not in repo (gitignored by design). `train/validation/test` split exists. Leakage prevention via chronological split is correct. |
| **Phase 2 Forecast** | **PASS** | LightGBM, XGBoost, Ensemble all have real training code. Temporal Graph Transformer has real model code. All enter benchmark. GraphSAGE/GAT documented as CI-crossing-zero (honest negative). |
| **Phase 3 Simulator** | **PASS** | v2 DynamicSimulator is a genuine upgrade: `DriverState` + `ZoneState` + `EnvironmentState`, supply-demand feedback, traffic/weather modulation, competition penalty, risk penalty, multi-component reward. |
| **Phase 4 RL** | **PARTIAL** | DQN/Double DQN: real training, replay buffer, epsilon-greedy, environment. IQL: real implementation (expectile regression, double-Q, OPE). **Critical defect**: training data is synthetic (np.random), not real historical trajectories. No CQL or Decision Transformer. |
| **Phase 5 Benchmark** | **PASS** | Forecast benchmark (MAE/RMSE), Decision benchmark (revenue/utilization/competition), RL benchmark (v1+v2), Robustness (ablation + CI), Deployment (latency/memory). Pareto analysis included. Endpoint separation clearly documented. |

---

## 最大剩余问题 (Top 10)

1. **IQL训练数据是模拟器生成的** — IQL trains on `np.random` data in the benchmark script, not real historical trajectories. This means the offline RL evaluation is a methodological demonstration, not a real policy evaluation. Real offline RL requires logged (state, action, reward, propensity) data from actual driver decisions.

2. **OPE置信区间不真实** — The Doubly Robust estimator in `ope_doubly_robust()` computes `mean_r + (fqe - mean_r) = fqe`, causing all bootstrap samples to be identical. The CI collapses to a point estimate.

3. **Multi-agent v1竞争检测是间接的** — Competition in v1 is through finite trip inventory rather than explicit driver payoff interaction. Drivers compete for limited trips but do not have strategic adaptation.

4. **没有端到端CI测试** — CI.yml runs lint and tests but does not execute the data pipeline or verify that `run_data_pipeline.py` actually produces correct splits.

5. **没有CQL或Decision Transformer** — Only IQL is implemented for offline RL. CQL's conservative Q-learning and Decision Transformer are not available.

6. **图形模型贡献不显著** — GraphSAGE, GAT, and OD Messages all have confidence intervals that cross zero vs non-graph LightGBM. This is honestly documented but limits the graph learning value.

7. **Mean Field低估收入** — Mean field approximation ($226/driver) significantly underestimates vs explicit multi-agent ($1,868/driver). The uniform flow assumption is too simplistic.

8. **数据管道在CI中未执行** — The `src/data/pipeline.py` has 410 lines of code but is never executed in CI. No test verifies real TLC data download.

9. **Benchmark指标不一致** — v1 and v2 simulators produce different revenue numbers for the same strategy. There is no calibration between the two simulator generations.

10. **无A/B测试框架** — All evaluation is in-simulator. No infrastructure for online A/B testing or deployment rollout exists.

---

## 是否达到目标

**NO — PARTIAL**

**原因：**
1. Offline RL (IQL) trains on synthetic data, not real trajectories. The core requirement of "real historical trajectory data" is not met.
2. OPE confidence intervals are degenerate (point estimates due to DR construction).
3. Data pipeline is coded but not verified end-to-end with real data.
4. No CQL or Decision Transformer implementation.
5. Multi-agent v1 competition is implicit (inventory-based) rather than explicit (strategic driver interaction).

**已达标的部分：**
- ✅ Multi-year data pipeline structure (2022-2025)
- ✅ Dynamic supply-demand simulator v2 (genuine upgrade)
- ✅ Demand forecasting (LightGBM, XGBoost, Ensemble)
- ✅ Temporal Graph Transformer
- ✅ DQN/Double DQN baselines preserved
- ✅ IQL implemented (methodological)
- ✅ Mean Field Game approximation
- ✅ Comprehensive benchmark matrix
- ✅ Pareto analysis
- ✅ Deployment profiling
- ✅ README with simulation!=deployment warning
- ✅ 230 passing tests, zero lint errors
