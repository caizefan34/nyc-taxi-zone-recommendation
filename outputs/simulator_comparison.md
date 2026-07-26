# Simulator Comparison: v1 (Fixed Demand) vs v2 (Dynamic Supply-Demand)

**Date:** 2026-07-26

## Overview

| Property | v1 (Legacy) | v2 (Dynamic) |
|---|---|---|
| Demand model | Fixed, immutable | Dynamic, supply-responsive |
| Competition | Single driver only | N drivers simultaneously |
| Pickup probability | Fixed half-saturation | Supply-elastic logistic |
| Reward components | Fare only | Income - fuel - time - competition - risk |
| Traffic effects | None | Travel time multiplier + demand suppression |
| Weather effects | None | Demand factor (0.3-1.0) |
| Market feedback | None | Closed-loop (supply affects demand) |

## Quantitative Comparison

| Metric | v1 (Legacy) | v2 (Dynamic) |
|---|---:|---:|
| Driver count | 1 (per run) | N/A |
| Avg revenue/driver | N/A | $1867.81 |
| Total fulfilled trips | 0 | 776 |
| Driver utilization | N/A | 13.85% |
| Demand fulfillment | N/A | 14.75% |
| Zone saturation | N/A | 0.00% |

## V2 Reward Breakdown

| Component | Value | Description |
|---|---:|:---|
| Total Revenue | $18678.10 | Per-driver over 7 days |
| Total Fuel Cost | $-1989.63 | Per-driver over 7 days |
| Total Competition Penalty | $42.00 | Per-driver over 7 days |
| Total Risk Penalty | $-1070.56 | Per-driver over 7 days |

## Key Differences

### Supply-Demand Feedback (v2 only)

- When more drivers enter a zone, each driver's pickup probability drops
- Traffic congestion reduces effective demand (people travel less)
- Bad weather suppresses demand further
- Trip inventory depletes as trips are fulfilled

### Reward Decomposition (v2 only)

- **Income**: Actual fare from completed trip
- **Fuel Cost**: $0.65/mile (industry average)
- **Travel Time Cost**: $0.30/minute (opportunity cost)
- **Competition Penalty**: $0.50 per extra driver in same zone
- **Risk Penalty**: Higher for low-probability zones

### Competition (v2 only)

- Multiple drivers can compete for the same trip
- Zone saturation tracked as fraction of failed attempts due to oversupply
- Driver utilization measures productive vs idle time

## Limitations

- v2 uses synthetic demand when real data unavailable
- Traffic model is simplified (no dynamic congestion propagation)
- Weather uses daily normals rather than real-time observations
- No airport queue dynamics or driver learning
