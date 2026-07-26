# Demo Workflow

## Goal

The demo provides a **lightweight end-to-end preview** of the Dynamic Urban Mobility Decision System pipeline without requiring the full NYC TLC dataset (~10 GB) or running model training. It uses pre-computed benchmark results to demonstrate the system's capabilities.

## Input

The demo reads from pre-computed benchmark snapshots in `outputs/`:

- `outputs/forecast_evaluation.json` — Forecasting performance data
- `outputs/multi_agent_benchmark.json` — Multi-agent simulation results
- `outputs/benchmark_report.json` — Combined benchmark report

## Pipeline

```
Pre-computed benchmark data -> Demand prediction -> Simulator step -> Policy recommendation -> JSON output
```

## Output

The demo writes to `outputs/demo/demo_result.json` with keys:
- `demand_prediction` — MAE values and improvement percentages
- `simulator` — Calibration metrics and strategy revenues
- `recommendation` — Best policy, expected revenue, significance

## Limitations

- **Demo is simulation-based.** It uses pre-computed results, not live computation.
- **Full pipeline requires data download.** See [reproduction.md](reproduction.md).
- **Single seed only.** RL training was run with one seed; multi-seed would improve robustness.
- **No real-world validation.** All results are from calibrated simulation, not deployed.
