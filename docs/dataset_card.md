# Dataset Card: NYC TLC Yellow Taxi Trip Records

## Dataset Description

This dataset contains historical NYC Yellow Taxi trip records, used for zone-level demand forecasting, multi-agent simulation calibration, and offline RL policy evaluation. The project uses the “TLC Trip Record Data” published by the NYC Taxi and Limousine Commission (TLC).

**Tasks:**
- Zone-level demand forecasting (336 half-hour slots/week × 263 zones)
- Multi-agent supply-demand simulation
- Off-policy evaluation of repositioning strategies

## Source

- **Provider:** NYC Taxi and Limousine Commission (TLC)
- **URL:** https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page
- **License:** Public domain (government data). No personally identifiable information (PII) is included.
- **Citation:** NYC TLC Trip Record Data. https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page

> **Important:** This is aggregated zone-level data, not individual driver or passenger data. No PII, no driver IDs, no passenger information.

## Time Range

| Split | Years | Purpose |
|-------|-------|---------|
| Training | 2022, 2023 | Model training and validation |
| Holdout | 2024 | Cross-year drift detection |
| Test | 2025 | Final evaluation |

**Temporal structure:** Strict chronological split. Training uses Jan 2023, validation uses Jan 21–24, 2023, evaluation uses Jan 25–31, 2023.

## Features

### Raw trip-level fields (from TLC)
- pickup_datetime, dropoff_datetime
- PULocationID, DOLocationID (zone IDs, 1–263)
- trip_distance, fare_amount, total_amount
- passenger_count, RatecodeID, payment_type

### Engineered features
- **Calendar**: weekday, hour, half_hour_bucket, time_slot (1–336)
- **Lag features**: lag_demand_1, lag_demand_2, lag_demand_48, lag_demand_336
- **Rolling statistics**: rolling_demand_mean_3, rolling_demand_mean_48, rolling_demand_mean_336
- **Neighbor features**: neighbor_lag_demand_mean, neighbor_lag_demand_std, neighbor_lag_demand_max, neighbor_mean_travel_minutes
- **Graph embeddings**: Zone embeddings from GraphSAGE/GAT (8-dim)

### Target variables
- **Demand**: Number of pickups per zone per half-hour slot
- **Fare (secondary)**: Average fare per zone per slot

## Preprocessing

1. **Aggregation**: Raw trip records → zone-slot demand matrix (263 zones × 336 slots/week)
2. **Cleaning**: Filter invalid/outlier trips (negative fare, zero distance)
3. **Temporal encoding**: Time features (weekday, hour, half-hour bucket, slot number)
4. **Lag construction**: Demand at t-1, t-2, t-48, t-336 slots (1 hour, 1 day, 1 week ago)
5. **Neighbor computation**: Mean, std, max of neighbor zone demand using travel-time-weighted adjacency
6. **Graph construction**: Directed graph from trip OD pairs (18,259 edges across 263 zones)
7. **Normalization**: Min-max scaling for demand features

## Dataset Statistics

| Statistic | Value |
|-----------|-------|
| Zones | 263 |
| Time slots/week | 336 |
| Total training rows | 164,112 |
| Validation rows | 50,496 |
| Training trips (Jan 2023) | 1,865,434 |
| Edge count (directed graph) | 18,259 |
| Pass through zones | 13 (no pickup data) |

## Limitations

1. **Spatial coverage**: Only NYC Yellow Taxis (Manhattan-centric). Does not cover green cabs, ride-hail (Uber/Lyft), or other boroughs comprehensively.
2. **Temporal coverage**: Data starts from 2022. Pre-COVID patterns are not represented.
3. **External factors**: Weather, events, holidays are included as external features but their impact is limited.
4. **Pass-through zones**: 13 zones have no pickup data (airports, highways, parks).
5. **Aggregation loss**: Zone-slot aggregation loses intra-zone spatial detail and fine-grained temporal patterns.
6. **No driver behavior data**: The dataset captures trip demand, not driver supply-side behavior.

## Ethical Considerations

1. **Not personal data**: This is aggregated, de-identified trip volume data. No individual trips, driver identities, or passenger information are stored in the processed features.
2. **Public benefit**: Mobility optimization can reduce empty cruising, fuel consumption, and congestion.
3. **Bias awareness**: Yellow taxis disproportionately serve Manhattan and certain demographic groups. Models trained on this data may not generalize to other cities or transportation modes.
4. **No surveillance**: The system does not track individual vehicles or drivers. All analysis is at the zone level.
5. **Transparency**: All benchmark results are reported with honest limitations. No deployment recommendations are made without real-world validation.
