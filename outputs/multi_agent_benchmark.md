# Multi-Agent Simulator Benchmark

Configuration: 50 drivers, configured demand/supply ratio 1.00, 30 paired seeds, seven days per seed.
Demand is finite and every trip can be assigned at most once.

| Strategy | Revenue/driver | Fulfilled trips | Utilization | Idle min/driver | Saturated attempts |
|---|---:|---:|---:|---:|---:|
| Hot Zone | $1233.41 | 2965.8 | 7.31% | 9343.3 | 95.83% |
| Single-Step | $1764.56 | 3133.6 | 11.11% | 8959.6 | 88.39% |
| Two-Step | $1508.71 | 2094.4 | 9.51% | 9121.4 | 94.85% |

Paired Two-Step minus Single-Step revenue per driver: -$255.86, 95% bootstrap CI [-$259.50, -$252.30], paired t-test p=3.6e-42, Wilcoxon p=1.86e-09, Cohen's dz=-24.700.

Single-Step minus Hot Zone is $531.16 per driver, 95% CI [$525.64, $536.67], Cohen's dz=33.885.

`zone_saturation_rate` is the fraction of pickup attempts made in zone-slots where competing supply exceeded the remaining trip inventory. Utilization is passenger-trip minutes divided by total driver-horizon minutes; relocation and unmatched search are idle time.

## Demand/supply sensitivity

Single-Step with the same fleet size; higher ratios add finite trip inventory while preserving the historical zone/time distribution.

| Demand/supply ratio | Revenue/driver | Utilization | Fulfillment | Saturated attempts |
|---:|---:|---:|---:|---:|
| 0.50 | $1007.48 | 6.42% | 22.41% | 95.30% |
| 1.00 | $1775.68 | 11.17% | 18.72% | 88.29% |
| 2.00 | $2977.50 | 18.53% | 14.17% | 73.06% |
