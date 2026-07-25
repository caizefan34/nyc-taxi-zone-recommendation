# Multi-Agent Simulator

## Purpose

The legacy rollout advances one driver through an immutable historical market. It cannot represent two drivers requesting the same trip or the loss of opportunity after another driver accepts it. The multi-agent simulator adds finite demand, simultaneous competition, and depletion while retaining the repository's existing Top-3 strategy interface.

## Event semantics

Drivers begin with a decision event. A recommendation is sampled with the existing 60%/30%/10% Top-3 compliance weights after unreachable zones are removed. Relocation advances the driver by rounded half-hour slots. All pickup attempts at the same timestamp are then grouped by zone before matching occurs.

Within each zone-slot:

1. available drivers are shuffled with the configured seed;
2. at most `min(driver_count, remaining_trip_count)` drivers are matched;
3. each matched trip is removed permanently from the inventory;
4. unmatched drivers wait one half-hour slot;
5. matched drivers receive the recorded fare and become available after the pickup slot plus recorded trip duration.

This ordering makes competition explicit and guarantees

$$
N_{\text{initial trips}} = N_{\text{fulfilled trips}} + N_{\text{remaining trips}}.
$$

## Demand/supply ratio

For a fleet of $D$ drivers and a horizon of $T$ half-hour slots, the configured ratio $\rho$ creates

$$
N_{\text{initial trips}}=\mathrm{round}(\rho D T).
$$

The inventory preserves the historical zone/time distribution through proportional allocation. When downsampling, trips are sampled without replacement. When the requested inventory exceeds the historical source count, records are resampled within their original zone-slot. The reported realized ratio verifies the exact scaled inventory.

This ratio uses nominal driver-slots as its supply denominator. Because passenger trips and relocations occupy multiple slots, it is a controlled load parameter rather than an equilibrium estimate.

## Metrics

- **fulfilled trips:** unique depleted trip records served by the fleet;
- **average driver revenue:** total recorded fare divided by driver count;
- **idle minutes:** horizon minutes not spent on passenger trips, including relocation and unmatched search;
- **utilization:** passenger-trip minutes divided by total driver-horizon minutes;
- **demand fulfillment:** fulfilled trips divided by initial finite inventory;
- **zone saturation:** fraction of pickup attempts occurring where competing drivers exceed remaining trips;
- **peak zone supply:** largest simultaneous driver count in one zone-slot.

## Benchmark

The checked-in benchmark uses 50 drivers, demand/supply ratio 1.0, 30 paired seeds, and seven days per seed.

| Strategy | Revenue/driver | Fulfilled trips | Utilization | Saturated attempts |
|---|---:|---:|---:|---:|
| Hot Zone | $1,233.41 | 2,965.8 | 7.31% | 95.83% |
| Single-Step | **$1,764.56** | **3,133.6** | **11.11%** | **88.39%** |
| Two-Step | $1,508.71 | 2,094.4 | 9.51% | 94.85% |

Single-Step exceeds Hot Zone by $531.16 per driver, 95% paired bootstrap CI [$525.64, $536.67]. Two-Step is $255.86 below Single-Step, 95% CI [$252.30, $259.50] in absolute loss. The concentrated Two-Step policy performs worse once many drivers compete for finite inventory.

Demand/supply sensitivity for Single-Step:

| Ratio | Revenue/driver | Utilization | Saturated attempts |
|---:|---:|---:|---:|
| 0.50 | $1,007.48 | 6.42% | 95.30% |
| 1.00 | $1,775.68 | 11.17% | 88.29% |
| 2.00 | $2,977.50 | 18.53% | 73.06% |

## Reproduction

```bash
python -m scripts.run_multi_agent_benchmark --drivers 50 --runs 30 --sensitivity-runs 10
```

## Remaining limitations

The simulator uses historical trips as an exogenous passenger market. It does not model congestion, airport queues, endogenous demand response, driver learning, strategic non-compliance, or equilibrium. Fares and durations are recorded outcomes rather than predictions under changed fleet behavior. Results support controlled simulator comparisons only.
