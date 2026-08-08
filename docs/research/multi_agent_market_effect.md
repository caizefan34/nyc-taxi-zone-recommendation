# Multi-Agent Market Effect of AI Policy Adoption

> **Research question:** Does an AI repositioning recommendation degrade when an
> increasing share of drivers follows the *same* policy?
>
> **Answer (simulation):** Yes. Above ~50% adoption the AI-recommended cohort's
> revenue advantage disappears and turns negative, while market saturation rises
> toward 90%+ of pickup attempts.
>
> **Evaluation type:** SIMULATION (finite-demand multi-agent simulator). Not a
> real-world market, deployment, or A/B result.

---

## Experiment

- **Simulator:** `src/simulator/multi_agent/engine.py` — finite-demand, explicit
  competition, every trip assignable at most once.
- **Fleet:** 100 drivers, 7 simulated days, seed 42.
- **Policy:** `Two-Step Horizon` (`src/2_recommendation_algorithm/improved_strategy.py`)
  for the AI cohort; baseline drivers follow the `Hot Zone` heuristic.
- **Adoption rates:** 1%, 5%, 10%, 25%, 50%, 75%, 100%.
- **Artifact:** `outputs/experiments/adoption_sweep.json`
  (regenerate via `python scripts/run_adoption_sweep.py`).

---

## Results

| Adoption | AI revenue/driver | Baseline revenue/driver | Revenue gap | AI utilization | Zone concentration (top-3) | Saturation |
|---:|---:|---:|---:|---:|---:|---:|
| 1% | $24.98 | $21.09 | +$3.89 | 18.2% | 57.1% | 0.0% |
| 5% | $27.06 | $21.21 | +$5.85 | 17.9% | 31.4% | 0.0% |
| 10% | $24.64 | $21.17 | +$3.47 | 15.5% | 22.9% | 0.9% |
| 25% | $23.17 | $21.29 | +$1.88 | 15.3% | 24.0% | 43.0% |
| 50% | $21.24 | $21.90 | **−$0.65** | 14.8% | 19.4% | 74.5% |
| 75% | $19.20 | $20.93 | **−$1.73** | 14.2% | 19.8% | 83.6% |
| 100% | $17.24 | — | — | 13.1% | 18.6% | 92.1% |

At 100% adoption there is no non-AI cohort left to compare against, so the
baseline column is empty.

---

## Interpretation

1. **The advantage is fragile.** At low adoption (1–25%) the AI cohort earns
   more than the heuristic cohort. Above 50% the gap flips negative: the
   baseline cohort now earns *more* than the AI cohort.

2. **The mechanism is saturation.** `saturation_rate` — the fraction of pickup
   attempts in zone-slots where competing supply exceeded remaining trip
   inventory — rises monotonically from 0% to 92.1%. When many drivers follow
   the same recommendation, they converge on the same zones, compete for a
   finite pool of trips, and cannibalize each other.

3. **Concentration is not the whole story.** Zone top-3 concentration actually
   *falls* as adoption rises (57% → 19%). The AI fleet spreads out, but total
   demand is fixed, so spreading does not create new trips — it just dilutes
   the per-driver share of a fixed pool.

4. **Implication for deployment.** A single shared policy has a
   self-defeating equilibrium. Production systems need either stochastic
   policies (exploration), fleet-level coordination that internalizes
   competition, or heterogeneous policies — none of which are tested here.

---

## Limitations (read before citing)

- Single seed (42), single fleet size (100), 7-day horizon.
- No driver adaptation, learning, or abandonment.
- No congestion coupling (this experiment holds travel times fixed).
- Revenue figures are simulator proxies, not earnings.

---

## Follow-up directions

- Sweep fleet size and seed to confirm the crossover point (~50%).
- Vary policy diversity: how much heterogeneity restores the advantage?
- Add congestion coupling (`src/simulator/v2/dynamics.py` traffic multiplier)
  and test whether concentration now *increases* travel time.
- Compare a stochastic (epsilon-greedy) version of Two-Step vs the deterministic one.
