# Cross-City Extension Framework

## Goal
Design a framework for extending the benchmark to new cities.

## Current Status
**Validated: NYC only.** All experiments use NYC TLC Yellow Taxi data (2022-2025).

## City Configuration
Each city is defined by a YAML config file (see configs/city_template.yaml):

```yaml
city_name: "nyc"
zones: 263
data_source: "NYC TLC Yellow Taxi"
```

## Required Data for New Cities
- Trip records with pickup time and location
- Zone definitions (lat/lon boundaries or zone IDs)
- (Optional) Weather, calendar, event data for external features

## Extension Steps
1. Create city config in configs/cities/{city_name}.yaml
2. Implement data adapter for city-specific format
3. Run feature engineering pipeline
4. Train forecasting models
5. Calibrate simulator if applicable
6. Run benchmark

## Limitations
- Feature engineering assumes NYC-style grid/time features
- Simulator calibration requires trip-level data with fare and travel time
- External features (airport, events) are NYC-specific
- Cross-city transfer learning is NOT yet implemented

## Future Work
- Chicago taxi data integration
- Ride-hail platform data (Uber/Lyft)
- International city formats
