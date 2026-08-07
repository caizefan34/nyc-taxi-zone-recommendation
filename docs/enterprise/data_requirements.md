# Data Requirements

## For NYC TLC (Reference Implementation)

Download yellow taxi trip data from [NYC TLC](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page):

```
data/raw/yellow_tripdata_2023-01.parquet
```

Required columns:
- `tpep_pickup_datetime` — Pickup timestamp
- `tpep_dropoff_datetime` — Dropoff timestamp
- `PULocationID` — Pickup zone ID (1-263)
- `DOLocationID` — Dropoff zone ID (1-263)
- `fare_amount` — Fare in USD
- `trip_distance` — Trip distance in miles
- `passenger_count` — Number of passengers

## Zone Definitions

```
data/meta/taxi_zone_lookup.csv
```

Columns: `LocationID`, `Borough`, `Zone`, `service_zone`, `Latitude`, `Longitude`

## For Custom Cities

To adapt the platform to a new city, you need:

1. **Trip records** with:
   - Pickup time (timestamp)
   - Pickup location (zone ID or lat/lon)
   - Dropoff location
   - Fare or revenue
   - Trip duration or distance

2. **Zone definitions** with:
   - Zone ID
   - Zone name
   - Geographic boundaries or centroid (lat/lon)

3. **Optional but recommended**:
   - Weather data
   - Calendar/holiday data
   - Event data
   - Traffic/transit data

## Data Format

The platform expects Parquet files with PyArrow schema. The `CityAdapter` interface (see `src/cities/base.py`) defines the ingestion contract.

## Privacy Considerations

- NYC TLC data is publicly available and anonymized
- For proprietary fleet data, ensure PII is removed before ingestion
- The platform does NOT require driver identity or passenger information
- See [security.md](security.md) for data handling guidelines
