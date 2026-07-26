# Offline Policy Evaluation Report

**Generated:** 2026-07-26 15:50:58

## Overview

This report compares three OPE methods (FQE, WIS, DR) across different policies. The evaluation uses trajectories collected from the DynamicSimulator v2.

## Methods

| Method | Description |
|--------|-------------|
| **FQE** (Fitted Q-Evaluation) | Learns a Q-function from offline data via bootstrapped regression |
| **WIS** (Weighted Importance Sampling) | Corrects distribution shift via importance weights |
| **DR** (Doubly Robust) | Combines FQE and IS for lower bias and variance |

## Results

| Policy | Method | Estimate | 95% CI Low | 95% CI High |
|--------|--------|---------:|-----------:|------------:|
| DQN (stay) | FQE | 262.5309 | - | - |
| DQN (stay) | WIS | 449.4401 | 445.0510 | 452.8159 |
| DQN (stay) | DR | 239.5595 | 236.8958 | 452.8159 |
| DQN (stay) | Mean Return | 4.8143 | - | - |
| DQN (stay) | Transitions | 5000 | - | - |
| IQL (offline RL) | FQE | 264.4870 | - | - |
| IQL (offline RL) | WIS | 463.4393 | 459.1917 | 467.2356 |
| IQL (offline RL) | DR | 235.6796 | 232.0487 | 467.2356 |
| IQL (offline RL) | Mean Return | 5.2205 | - | - |
| IQL (offline RL) | Transitions | 5000 | - | - |

## Policy Ranking

| Rank | Policy | DR Estimate |
|-----:|--------|------------:|
| 1 | DQN (stay) | 239.5595 |
| 2 | IQL (offline RL) | 235.6796 |

## Bootstrap Distribution

Confidence intervals are computed via bootstrap resampling (n=100) of per-sample Q-values and importance-weighted returns. Wider intervals indicate higher uncertainty in the estimate.

- **DQN (stay)**: DR 95% CI width = 215.9200
- **IQL (offline RL)**: DR 95% CI width = 235.1869

## Interpretation

- **FQE** provides a model-based estimate but may be biased by function approximation error.
- **WIS** is unbiased in the limit but can have high variance with long trajectories.
- **DR** combines both approaches for the most reliable estimate.
- Bootstrap CIs > 0.5 indicate high variance in the underlying data distribution.

### Caveats

- All evaluations are on **simulator-generated data**, not real driver trajectories.
- OPE estimates assume no distribution shift beyond what's captured in the buffer.
- The behavior policy probability is approximated (uniform prior for random exploration).
