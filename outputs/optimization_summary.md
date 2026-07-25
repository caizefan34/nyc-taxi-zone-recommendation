# Post-Audit Optimization Summary

This document records remediation applied after the research-grade audit of commit `c1afcb6`.

## Resolved critical/high findings

- Removed unsupported headline values, fake regret, fake DOI/arXiv badges, and unbacked ablation tables from public documentation.
- Replaced hard-coded parameter-selection metrics with an executable 18-configuration grid.
- Added a checked-in machine-readable reference snapshot and generated Markdown report.
- Added official raw-parquet chronological splitting to the data pipeline.
- Replaced the invalid origin-independent MDP with synchronous Bellman backups over relocation, success/failure, OD destination, and elapsed time.
- Labeled Q-learning correctly as simulator-trained rather than offline RL and fixed its RNG seed.
- Replaced the Python-loop two-step query path with vectorized precomputation.
- Added paired bootstrap/t/Wilcoxon/effect-size statistics, horizon comparison, robustness analysis, and exposure concentration.
- Standardized evaluator imports and module-based experiment commands.
- Corrected Docker entrypoint behavior and CI lint scope.

## Current reproduced metrics

| Strategy | NDCG@3 | Hit@3 | Static latency | Mean daily simulator fare |
|---|---:|---:|---:|---:|
| Hot Zone | 0.7846 | 0.5842 | 0.108 ms | $431.21 |
| Single-Step | 0.9024 | 0.8804 | 0.317 ms | $548.77 |
| Two-Step | **0.9565** | **0.9714** | **0.113 ms** | **$570.61** |

The optimized main two-step query path is roughly 190 times faster than the earlier tracemalloc measurement while preserving NDCG and top-1 reference utility.

## Remaining scientific limitations

The optimization does not manufacture evidence that the source data cannot provide. The following remain explicit limitations:

- the static labels encode a reference heuristic rather than real counterfactual outcomes;
- the public validation set is not an untouched final test after parameter inspection;
- the rollout is single-driver and lacks demand depletion, competition, congestion, feedback, and equilibrium;
- TLC trips do not contain recommendation propensities needed for valid IPS/SNIPS/DR or offline RL;
- airport exposure remains highly concentrated and a production policy requires supply/capacity constraints;
- multi-month rolling evaluation is still required for publication-quality external validity.

## Authoritative artifacts

- `outputs/reference_metrics.json`
- `outputs/evaluation_report.md`
- `outputs/parameter_selection.json`
- `outputs/research_grade_audit.md`
- `outputs/audit_robustness.png`

## Final verification

- Raw January parquet rebuilt into a boundary-separated chronological split: 2,243,808 cleaned training rows and 688,256 cleaned validation rows.
- All schema, travel-time matrix, strategy-interface, and baseline-reference sanity checks passed.
- 78 tests passed; Ruff passed across `src`, `tests`, and `scripts`.
- Sphinx HTML documentation built successfully with warnings treated as errors.
- The public example script ran successfully on Windows.
- Docker image execution was not verified because the installed Docker Desktop daemon was not running; the Dockerfile changes were reviewed statically.
