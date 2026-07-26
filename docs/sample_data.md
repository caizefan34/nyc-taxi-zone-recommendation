# Sample Dataset

## Source
- **Trip data:** Public NYC TLC trip records (via FiveThirtyEight Uber dataset) or synthetic generation as fallback.
- **Zone data:** NYC Taxi Zone lookup table.
- **Weather data:** Synthetic weather for testing external feature pipelines.

## Size
| File | Records | Size |
|------|:-------:|:----:|
| `sample_trip_data.csv` | 500 | ~50 KB |
| `sample_zone_data.csv` | 6 | ~300 B |
| `sample_weather_data.csv` | 56 | ~2 KB |

## Usage
```bash
python scripts/download_sample_data.py
```

## Difference from Full Dataset
| Dimension | Sample | Full Dataset |
|-----------|--------|:------------:|
| Time range | 1 day-1 week | 12+ months |
| Records | 500 | 10M+ |
| Zones | 6 (Manhattan focus) | 263 |
| File format | CSV (GitHub-friendly) | Parquet |
| Download | Instant | ~1 GB+ |

## Limitations
- Sample data is for testing pipeline mechanics only.
- Results from sample data do not represent full NYC taxi demand patterns.
- Synthetic weather data is randomly generated, not historical.
