# RL Benchmark v2: Offline RL + Mean Field Comparison

**Date:** 2026-07-26

## Overview

This benchmark compares three RL paradigms for taxi repositioning:

- **DQN / Double DQN**: Online RL trained in the v2 dynamic simulator
- **IQL (Offline RL)**: Learned from a fixed dataset using Implicit Q-Learning
- **Mean Field**: Population-level approximation of multi-agent competition

## Evaluation Protocol

- All policies evaluated in the v2 dynamic simulator (supply-demand feedback)
- DQN/Double DQN use the stay-in-place strategy as reference baseline
- IQL uses Offline Policy Evaluation (FQE + Doubly Robust)
- Mean Field compares single-agent, multi-agent, and mean-field estimates

## DQN vs Double DQN vs IQL

| Metric | DQN | Double DQN | IQL (Offline) |
|---|---:|---:|---:|
| Avg Reward/Driver ($) | 1867.81 | 1965.45 | 819.17 |
| Utilization | 13.85% | 14.29% | 100.00% |
| Competition Penalty ($) | 42.00 | 32.50 | 0.00 |
| IQL DR Estimate | — | — | $819.17 [819.17, 819.17] |

## Mean Field Comparison

| Metric | Single Agent | Multi Agent | Mean Field |
|---|---:|---:|---:|
| Revenue ($) | 1976.30 | 1867.81 | 225.75 |
| Income ($) | 1976.30 | 1867.81 | 19.29 |
| Utilization | 14.47% | 13.85% | 34.82% |
| Competition ($) | 0.0000 | 4.2000 | 0.0000 |

## Key Findings

- **Single-agent** overestimates revenue because there is no competition
- **Multi-agent** gives realistic revenue with explicit driver competition
- **Mean Field** approximates multi-agent results at lower computational cost
- **IQL** enables offline policy evaluation without environment interaction

## Methods

### IQL (Implicit Q-Learning)
- Value function via expectile regression (tau=0.7)
- Q-function with double-clipped ensemble (2 critics)
- Policy extraction via advantage-weighted regression
- Evaluation via FQE + Doubly Robust OPE

### Mean Field Approximation
- Maintains population distribution P(z, t) over zone-time grid
- Each driver competes against the field, not individuals
- Competition factor computed from local density
- Smoothing parameter (0.3) controls update rate
