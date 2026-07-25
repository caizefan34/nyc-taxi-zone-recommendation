# Reproducible Evaluation Report

> Generated from machine-readable artifacts at `2026-07-25T13:42:26.041351+00:00`.
> Static metrics measure agreement with the public two-step reference objective; they are not counterfactual revenue estimates.

## Static diagnostic

| Strategy | NDCG@3 | Hit@3 | Reference utility@1 | Mean latency (ms) |
|---|---:|---:|---:|---:|
| Baseline 1 | 0.7846 | 0.5842 | 19.4299 | 0.108 |
| Baseline 2 | 0.9024 | 0.8804 | 25.0589 | 0.317 |
| Two-step | 0.9565 | 0.9714 | 27.5855 | 0.113 |

## Paired 100-seed rollout

| Strategy | Mean daily fare |
|---|---:|
| Baseline 1 | $431.21 |
| Baseline 2 | $548.77 |
| Two-step | $570.61 |

| Comparison | Mean difference | Bootstrap 95% CI | Paired t p | Cohen dz |
|---|---:|---:|---:|---:|
| Two-step - Baseline 1 | $139.40 | [$123.31, $153.96] | 1.07e-32 | 1.784 |
| Two-step - Baseline 2 | $21.84 | [$5.00, $39.53] | 0.0151 | 0.247 |
| Baseline 2 - Baseline 1 | $117.57 | [$100.29, $133.08] | 1.02e-24 | 1.376 |

## Horizon comparison

| Horizon | NDCG@3 | Hit@3 | Coverage | Mean daily fare | Query latency (ms) |
|---|---:|---:|---:|---:|---:|
| 1 | 0.9582 | 0.9783 | 13.69% | $569.78 | 0.031 |
| 2 | 0.9565 | 0.9714 | 14.07% | $570.61 | 0.032 |
| 3 | 0.9549 | 0.9759 | 14.45% | $573.47 | 0.031 |
| 5 | 0.9525 | 0.9741 | 14.45% | $575.97 | 0.032 |
| adaptive | 0.9559 | 0.9735 | 14.07% | $573.31 | 0.068 |

## Static parameter grid

The best public-reference configuration is shown for diagnostics only; the same public labels must not be treated as an untouched test set.

| Half-saturation | Gamma | Candidate pool | NDCG@3 | Hit@3 |
|---:|---:|---:|---:|---:|
| 240 | 0.25 | 50 | 0.9577 | 0.9762 |

## Exposure concentration

| Strategy | Coverage | Gini | Effective zones | Airport exposure | Premium-fare exposure |
|---|---:|---:|---:|---:|---:|
| Baseline 1 | 7.98% | 0.974 | 9.22 | 27.74% | 24.94% |
| Baseline 2 | 14.07% | 0.970 | 9.21 | 50.62% | 43.65% |
| Two-step | 14.07% | 0.982 | 5.51 | 70.33% | 54.97% |

## Interpretation boundary

The rollout is a fixed single-driver historical-market simulator. It does not model competing drivers, demand depletion, congestion, supply-demand feedback, or equilibrium. Its confidence intervals quantify Monte Carlo seed variation only.

IPS, SNIPS, and doubly robust evaluation are not identifiable from the TLC trip table because logged recommendation actions and behavior propensities are absent.
