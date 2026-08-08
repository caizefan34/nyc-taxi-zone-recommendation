# Offline Policy Evaluation Report

**Seed:** 42

## Scope

This is a reproducible **simulator-only methodological benchmark**. It is not real-world causal evidence: TLC trip records do not contain logged recommendations, driver acceptance, or behavior-policy propensities.

FQE below is a logged-action diagnostic. WIS and sequential DR use complete driver trajectories, explicit target/behavior probabilities, and trajectory bootstrap intervals.

## Results

| Policy | Method | Estimate | 95% CI Low | 95% CI High |
|--------|--------|---------:|-----------:|------------:|
| Stay (on-policy baseline) | FQE diagnostic | 294.5917 | - | - |
| Stay (on-policy baseline) | WIS | 438.5503 | 415.8975 | 458.8968 |
| Stay (on-policy baseline) | Sequential DR | 431.7397 | 408.6556 | 451.6729 |
| Stay (on-policy baseline) | Mean transition reward | 4.7734 | - | - |
| Stay (on-policy baseline) | Data volume | 12415 transitions / 50 trajectories | - | - |
| IQL (uniform-exploration behavior) | FQE diagnostic | 257.4508 | - | - |
| IQL (uniform-exploration behavior) | WIS | 0.0000 | 0.0000 | 0.0000 |
| IQL (uniform-exploration behavior) | Sequential DR | 12.4368 | 12.4366 | 12.4369 |
| IQL (uniform-exploration behavior) | Mean transition reward | 4.9846 | - | - |
| IQL (uniform-exploration behavior) | Data volume | 7144 transitions / 50 trajectories | - | - |

## Policy and estimator details

- Stay data use a deterministic stay behavior policy and evaluate that same policy with probability 1.
- IQL data use uniform random behavior over 263 zones with logged probability 1/263; the evaluated IQL policy is deterministic, so its logged-action probability is 0 or 1.
- IQL Q/V nuisance predictions come from the trained IQL networks. The stay DR benchmark uses zero nuisance predictions and therefore reduces to an importance-weighted return.
- Confidence intervals resample complete driver trajectories (100 bootstrap draws).
- Importance weighting can be unstable when the deterministic IQL policy has little overlap with uniform behavior data; intervals do not repair a lack of support.
