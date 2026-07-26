# Demo Guide

## Goal

This demo demonstrates the end-to-end zone recommendation pipeline of the Dynamic Urban Mobility Decision System:
1. **Demand prediction** — estimate pickup demand for a given zone and time
2. **Simulator step** — simulate driver competition and reward
3. **Policy recommendation** — recommend top-3 zones to maximize expected revenue

The demo uses pre-computed benchmark results (not real-time model inference) to provide a fast, reproducible illustration of the system.

## Input

| Parameter | Default | Description |
|-----------|---------|-------------|
| --zone | 237 | NYC TLC zone ID (1-263) |
| --time-slot | 18 | Half-hour slot (0-47, 0=00:00) |
| --weekday | 2 | Day of week (0=Mon, 6=Sun) |
| --strategy | dqn | Policy: single_step, dqn, or iql |

## Pipeline

`
Input (zone, time, day)
  -> Load benchmark results (forecast, RL)
    -> Predict demand using LightGBM reference MAE
      -> Recommend zones using policy benchmark data
        -> Output top-3 zones with expected rewards
`

## Output

Results are saved to outputs/demo/demo_result.json and printed to stdout.

## Running

`ash
# Default demo
python scripts/run_demo.py

# Custom scenario with DQN policy
python scripts/run_demo.py --zone 158 --time-slot 32 --weekday 5 --strategy dqn

# Single-step policy
python scripts/run_demo.py --strategy single_step
`

## Limitations

- **Demo is simulation-based.** Results reflect benchmark performance, not real-world deployment.
- **No live model inference.** Demand predictions use pre-computed reference MAE values.
- **Zone recommendations are illustrative.** They use benchmark data patterns, not trained model outputs.
- **No real driver data.** The simulator uses synthetic competition dynamics.

## Source

scripts/run_demo.py