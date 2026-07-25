# Technical Paper Summary

## Finite-Horizon Taxi Zone Recommendation with Reproducible Evaluation

This project studies ranked zone recommendations for NYC taxi drivers using January 2023 TLC Yellow Taxi records. It combines training-period demand and fare statistics, a directed OD travel-time graph, and empirical passenger destination transitions.

The central strategy is a truncated lookahead model. It evaluates the initial relocation action and then assumes the driver waits in the reached or passenger-dropoff zone. It should be interpreted as fixed-continuation finite-horizon planning, not a novel Bellman-optimal or offline-RL algorithm.

## Reproduced evidence

| Strategy | Reference NDCG@3 | Reference Hit@3 | Simulator mean daily fare |
|---|---:|---:|---:|
| Hot Zone | 0.7846 | 0.5842 | $431.21 |
| Single-Step | 0.9024 | 0.8804 | $548.77 |
| Two-Step | **0.9565** | **0.9714** | **$570.61** |

In a paired 100-seed simulator comparison, Two-Step exceeds Single-Step by $21.84/day, with bootstrap 95% CI [$5.00, $39.53] and Cohen's dz=0.247.

The static metric and simulator objective are not equivalent. Horizon 1 obtains higher NDCG than horizon 2, while horizon 5 obtains lower NDCG but higher simulator fare.

## Validity boundary

The rollout contains one driver and an immutable historical market. It omits competing supply, passenger depletion, congestion, airport queues, feedback, and equilibrium. Results therefore support only within-simulator comparison.

The TLC trip table does not include logged reposition recommendations or logging propensities. Valid IPS/SNIPS/DR or offline-RL evaluation of a recommendation policy is not identifiable from these records alone.

## Market concentration

Two-Step assigns 70.33% of weighted recommendation exposure to airport zones, including about 55.0% to JFK. Its exposure Gini is 0.982. A realistic deployment study must model saturation and supply-aware pickup probability.

## Reproducibility

- Machine-readable snapshot: [`outputs/reference_metrics.json`](../outputs/reference_metrics.json)
- Generated report: [`outputs/evaluation_report.md`](../outputs/evaluation_report.md)
- Full validity audit: [`outputs/research_grade_audit.md`](../outputs/research_grade_audit.md)
- Method: [`docs/methodology.md`](../docs/methodology.md)
- Sensitivity results: [`docs/ablation_study.md`](../docs/ablation_study.md)

This repository is an educational research prototype rather than a production dispatch system or a top-tier novelty claim.
