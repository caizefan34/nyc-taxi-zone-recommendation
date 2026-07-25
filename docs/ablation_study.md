# Reproducible Sensitivity and Ablation Results

This document reports only experiments backed by machine-readable artifacts. Static metrics use the public reference objective; rollout fare is simulator-specific.

## Planning horizon

| Horizon | NDCG@3 | Hit@3 | Coverage | Mean daily fare |
|---|---:|---:|---:|---:|
| 1 | **0.9582** | **0.9783** | 13.69% | $569.78 |
| 2 | 0.9565 | 0.9714 | 14.07% | $570.61 |
| 3 | 0.9549 | 0.9759 | **14.45%** | $573.47 |
| 5 | 0.9525 | 0.9741 | **14.45%** | **$575.97** |
| Adaptive | 0.9559 | 0.9735 | 14.07% | $573.31 |

The horizon experiment shows that static reference NDCG and simulated fare are not monotonic with each other.

## Executable parameter grid

The current runner evaluates half-saturation $\{120,240,360\}$, gamma $\{0.25,0.5,0.75\}$, and candidate pools $\{50,100\}$ against the public static reference objective.

The best static configuration is:

| Half-saturation | Gamma | K | NDCG@3 | Hit@3 |
|---:|---:|---:|---:|---:|
| 240 | 0.25 | 50 | **0.9577** | **0.9762** |

At half-saturation 240 and K=50:

| Gamma | NDCG@3 | Hit@3 |
|---:|---:|---:|
| 0.25 | **0.9577** | **0.9762** |
| 0.50 | 0.9565 | 0.9714 |
| 0.75 | 0.9557 | 0.9732 |

K=50 and K=100 produce the same rounded NDCG/Hit for these settings, so the smaller pool is preferred on computational grounds. The production-facing default remains gamma=0.5 because the static public reference is a diagnostic rather than the sole deployment objective.

## Stress tests

| Scenario | NDCG@3 | Hit@3 | Top-3 overlap |
|---|---:|---:|---:|
| Unperturbed | 0.9565 | 0.9714 | 100% |
| Manhattan demand +50% | 0.9451 | 0.9667 | 88.03% |
| Random 10% missing cells | 0.9042 | 0.7872 | 81.37% |
| Drop OD probabilities below 0.001 | 0.9565 | 0.9714 | 99.84% |
| Remove bottom-demand 10% zones | 0.9565 | 0.9714 | 100% |

Random missing zone-time cells are the most damaging tested perturbation. The rare-zone result also shows that bottom-demand zones have effectively no policy influence.

## Exposure concentration

| Strategy | Coverage | Gini | Effective zones | Airport exposure |
|---|---:|---:|---:|---:|
| Hot Zone | 7.98% | 0.974 | 9.22 | 27.74% |
| Single-Step | 14.07% | 0.970 | 9.21 | 50.62% |
| Two-Step | 14.07% | **0.982** | **5.51** | **70.33%** |

Nominal coverage increases, but effective exposure becomes more concentrated. A production-oriented objective should add supply, queue capacity, and concentration penalties.

## Unsupported ablations removed

Earlier versions listed precise contributions for cleaning, transition probabilities, duration modeling, K=150/263, and "regret versus optimal" without executable artifacts. Those tables have been removed. Future ablations must save configs, per-run outcomes, and paired uncertainty.
