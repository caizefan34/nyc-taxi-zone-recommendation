# Evaluation Protocol

## For Research (Current)

All evaluation is **offline** using historical data:

1. **Static diagnostic**: NDCG@3, Hit@3 on validation queries
2. **Rollout simulation**: Single-agent and multi-agent simulators
3. **Historical replay**: Compare against actual trip outcomes
4. **Shadow evaluation**: Record recommendations without execution
5. **A/B testing**: Statistical comparison (simulation only)

All results are clearly labeled with their source:
- `SIMULATION` — Multi-agent simulator
- `HISTORICAL_REPLAY` — Historical data replay
- `SHADOW` — Shadow evaluation
- `REAL A/B` — Not yet available

## For Pilot Deployment (Future)

### Phase 1: Shadow Evaluation

1. Deploy recommendation API in shadow mode
2. Record vehicle positions and current zone from telemetry
3. Generate recommendations WITHOUT showing them to drivers
4. Compare AI recommendations against actual driver decisions
5. Evaluate after 2-4 weeks of data collection

### Phase 2: Controlled A/B Test

1. Randomly assign drivers to control (Hot Zone) and treatment (Two-Step) groups
2. Show recommendations only to treatment group
3. Track: revenue, utilization, empty distance, trip completion rate
4. Run for minimum 4 weeks (to capture day-of-week and weather effects)
5. Use bootstrap paired comparison for statistical analysis
6. Monitor for spillover effects between groups

### Phase 3: Full Rollout

1. Deploy to all consenting drivers
2. Continuous shadow evaluation against non-participating drivers
3. Monitor for policy degradation as adoption increases
4. A/B test policy variants (different models, different constraints)

## Metrics

### Primary

| Metric | Definition |
|---|---|
| Revenue per vehicle-hour | Total fare / total vehicle-hours |
| Utilization | Time with passenger / total time |
| Empty distance | Distance driven without passenger |

### Secondary

| Metric | Definition |
|---|---|
| Trip completion rate | Completed trips / trip opportunities |
| Recommendation acceptance | Times driver followed AI recommendation |
| Zone exposure | Distribution of recommended zones |
| Market saturation | % of time a zone has more drivers than demand |

## Statistical Rigor

- Bootstrap confidence intervals (2000 resamples, 95% CI)
- Paired comparison (same seeds, same demand realizations)
- Effect size (Cohen's d)
- Multiple comparison correction (Bonferroni for >2 metrics)

## Important Caveats

1. **No real-world validation exists** — All current metrics are simulation-based
2. **Simulator omits key dynamics** — No congestion, airport queues, driver adaptation
3. **Recommendation ≠ execution** — Drivers may ignore AI recommendations
4. **Market equilibrium unknown** — Mass adoption may degrade policy performance
