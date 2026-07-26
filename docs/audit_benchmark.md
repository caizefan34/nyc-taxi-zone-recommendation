# Benchmark Audit

## Metrics Coverage

| Domain | Metric | Status | Evidence |
|--------|--------|--------|----------|
| Forecast | MAE | ✅ | forecasting_benchmark.json |
| Forecast | RMSE | ✅ | forecasting_benchmark.json |
| Forecast | MAPE | ❌ | Not implemented (MAE + RMSE only) |
| Decision | Revenue | ✅ | rl_benchmark_v2.json (avg_reward_per_driver) |
| Decision | Utilization | ✅ | rl_benchmark_v2.json |
| Decision | Competition | ✅ | rl_benchmark_v2.json (competition_penalty) |
| RL | Episode Return | ✅ | rl_benchmark_v2.json (FQE estimate, DR estimate) |
| RL | OPE CI | ✅ | rl_benchmark_v2.json (ci95_low, ci95_high) |
| Robustness | Cross-year | ⚠️ | Only audit_robustness.png exists |
| Deployment | Latency | ⚠️ | sanity_check.py uses tracemalloc, no dedicated script |
| Deployment | Memory | ⚠️ | Peak tracemalloc in sanity_check.py |

## Statistical Rigor

| Feature | Status | Evidence |
|---------|--------|----------|
| Paired bootstrap | ✅ | scripts/run_benchmark_statistics.py + run_ope_comparison.py |
| Confidence intervals | ✅ | All benchmark JSONs include CI fields |
| Effect size (Cohen d) | ✅ | benchmark_statistics.md includes cohens_d |
| Multiple OPE methods | ✅ | FQE + WIS + DR compared in policy_evaluation_report.md |

**Score: 7/10** (no MAPE, deployment robustness scripts are minimal)
