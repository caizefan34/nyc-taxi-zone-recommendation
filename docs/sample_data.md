# Sample Dataset

## Source
Synthetic data based on the public NYC TLC Yellow Taxi trip record format.
Does not contain any personally identifiable information.

## Files

| File | Size | Description |
|------|------|-------------|
| `data/sample/sample_trip_data.csv` | ~500 bytes | 5 sample trip records |
| `data/sample/sample_zone_data.csv` | ~200 bytes | 5 NYC taxi zones |
| `data/sample/sample_weather_data.csv` | ~150 bytes | 3 days of weather data |

## Usage
```bash
# Verify sample data is in place
python scripts/download_sample_data.py

# Run demo with sample data
python scripts/run_demo.py
```

## Difference from Full Dataset

| Aspect | Sample | Full Dataset |
|--------|--------|-------------|
| Records | 5 trips | ~1.1B trips |
| Zones | 5 zones | 263 zones |
| Years | 2024 only | 2022-2025 |
| Size | ~1 KB | ~10 GB |
| Purpose | Quick demo | Full research reproduction |

## Limitations
- Sample data is synthetic, not real trip records
- Too small for any meaningful model training
- For research reproduction, download the full dataset from NYC TLC
