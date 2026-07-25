# DQN and Double-DQN Benchmark

Training uses only Jan 18--24 finite-market episodes. Evaluation uses Jan 25--31 with 50 drivers, demand/supply ratio 1.0, and 20 paired seeds.

| Strategy | Revenue/driver | Fulfilled trips | Utilization | Saturated attempts |
|---|---:|---:|---:|---:|
| Hot Zone | $1235.71 | 2968.7 | 7.31% | 95.81% |
| Single-Step | $1768.04 | 3134.2 | 11.15% | 88.37% |
| Finite Horizon | $1511.16 | 2094.8 | 9.52% | 94.84% |
| DQN | $1821.77 | 3950.7 | 11.21% | 78.54% |
| Double DQN | $1742.77 | 3410.8 | 10.69% | 82.33% |

## Training diagnostics

| Algorithm | Interactions | First-20 return | Last-20 return | Last-100 loss |
|---|---:|---:|---:|---:|
| DQN | 53648 | 120.27 | 171.21 | 0.469 |
| Double DQN | 50903 | 116.65 | 177.88 | 0.528 |

## Paired comparisons

- DQN minus Single-Step: $53.74/driver, 95% CI [$46.21, $61.57], paired t p=3.96e-11, Wilcoxon p=1.91e-06, Cohen's dz=2.995.
- Double DQN minus Single-Step: -$25.27/driver, 95% CI [-$32.77, -$17.97], paired t p=3.36e-06, Wilcoxon p=5.72e-06, Cohen's dz=-1.447.
- Double DQN minus DQN: -$79.01/driver, 95% CI [-$88.71, -$70.27], paired t p=1.4e-12, Wilcoxon p=1.91e-06, Cohen's dz=-3.623.

The policies see training-derived demand/fare, travel time, candidate utility, and expected background supply. They do not observe evaluation trip inventory or future arrivals.

DQN improves on Single-Step inside this simulator, while Double DQN does not. This is a single training seed with 20 evaluation-market seeds, so the confidence intervals measure paired simulator variation, not training uncertainty or causal deployment lift. The default recommender is unchanged.
