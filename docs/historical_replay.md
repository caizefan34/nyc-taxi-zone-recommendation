# Historical Replay Evaluation

## Goal
Evaluate zone recommendation policies against recorded historical demand patterns, reducing reliance on pure simulation.

## Methodology
1. Sample historical demand distribution (zone-level pickups by hour)
2. For each policy: simulate driver allocation matching demand
3. Measure: revenue, utilization, demand coverage
4. Compare across all policies

## Results

| Policy | Total Revenue | Utilization | Demand Coverage |
|--------|:------------:|:-----------:|:--------------:|
| (run script to fill) | | | |

## Comparison with Simulator

| Aspect | Historical Replay | Full Simulator |
|--------|:----------------:|:--------------:|
| Demand source | Recorded distribution | Generative model |
| Driver competition | Simplified | Full multi-agent |
| Computation | Fast (~seconds) | Slow (~minutes) |
| Realism | Medium | Medium-High |

## Limitations
- Replay != real deployment - no driver behavioral response
- Simplified competition model
- Historical demand may not reflect future patterns
