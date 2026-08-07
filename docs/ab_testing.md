# A/B Testing Framework

## Purpose

Statistically compare two policies (control vs treatment) with proper confidence intervals and effect size estimation.

## Current Status

**Framework implemented. Only simulation/historical replay data available.**

No real-world A/B test has been conducted. All results are from:
- Multi-agent simulator
- Historical replay
- Shadow evaluation

The framework is ready for real deployment but has not been validated with real-world traffic.

## Methods

### Bootstrap Confidence Intervals

Non-parametric bootstrap with 2000 resamples and 95% CI by default.

### Paired Comparison

Each metric is compared pair-wise (same seed, same demand realization) to control for variance in demand.

### Effect Size

Cohen's d: `(mean_treatment - mean_control) / pooled_std`

### Statistical Significance

Based on whether the 95% CI of the difference excludes zero.

## Usage

```python
from src.evaluation.ab.testing import (
    PolicyMetrics,
    compare_policies,
    ExperimentSource,
    generate_ab_report,
)

control = PolicyMetrics(
    policy_name="Hot Zone",
    revenue_per_vehicle=[...],
    utilization=[...],
)

treatment = PolicyMetrics(
    policy_name="Two-Step",
    revenue_per_vehicle=[...],
    utilization=[...],
)

result = compare_policies(
    control, treatment,
    source=ExperimentSource.SIMULATION,
)
```

## Source Labels

All results are automatically labeled with their data source:

| Label | Meaning |
|---|---|
| `simulation` | Multi-agent simulator results |
| `historical_replay` | Historical data replay |
| `shadow` | Shadow evaluation (recorded, not executed) |
| `real_ab` | Real-world A/B test (Not yet available) |

## Limitations

1. **No real-world A/B test data**: All comparisons are simulation-based
2. **No temporal drift**: Simulator uses static demand patterns
3. **No driver adaptation**: Drivers don't change behavior based on recommendation quality
4. **No network effects**: Recommendations to one driver don't affect others in the historical data

## Production Path

For real A/B testing in a pilot:

1. Randomly assign drivers to control/treatment groups
2. Run for sufficient duration (weeks, not hours)
3. Collect real revenue, utilization, empty distance data
4. Use the same statistical framework (bootstrap, paired comparison)
5. Monitor for spillover effects between groups

See [docs/enterprise/evaluation_protocol.md](enterprise/evaluation_protocol.md).
