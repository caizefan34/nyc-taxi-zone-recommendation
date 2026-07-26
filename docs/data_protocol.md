# Data Protocol — Multi-Year TLC Dataset

> **Version:** 1.0
> **Status:** Phase 1
> **Last Updated:** 2026-07-26

---

## 1. Data Source

**Source:** NYC Taxi & Limousine Commission (TLC) Trip Record Data
**Dataset:** Yellow Taxi Trip Records
**URL:** https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page
**Download Pattern:**
```
https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_YYYY-MM.parquet
```

**Schema (relevant columns):**

| Column | Type | Description |
|--------|------|-------------|
| `tpep_pickup_datetime` | datetime | Pickup timestamp |
| `tpep_dropoff_datetime` | datetime | Dropoff timestamp |
| `PULocationID` | int32 | Pickup taxi zone ID (1–263) |
| `DOLocationID` | int32 | Dropoff taxi zone ID (1–263) |
| `fare_amount` | float64 | Fare amount (USD) |
| `trip_distance` | float64 | Trip distance (miles) |

---

## 2. Time Range

| Component | Coverage | Rationale |
|-----------|----------|-----------|
| **Full dataset** | January 2022 – December 2025 | 4 years of urban mobility data |
| **Train** | January 2022 – December 2023 | 2 years for model training |
| **Validation** | January 2024 – December 2024 | 1 year for hyperparameter tuning |
| **Test** | January 2025 – December 2025 | 1 year held-out for final evaluation |

---

## 3. Split Strategy

### 3.1 Principle: Strict Temporal Isolation

All splits are based **exclusively on `tpep_pickup_datetime`**. No random shuffling,
no cross-year mixing, and no future data visible during training.

```
     2022 ────────── 2023 ────────── 2024 ────────── 2025 ────
     ├──────────────────────────────┤
     │          TRAIN               │
     │   (2022-01-01 to 2023-12-31) │
     ├──────────────────────────────┼────────────────┤
                                   │  VALIDATION     │
                                   │  (2024 full yr) │
                                   ├────────────────┼────────────────┤
                                                   │     TEST       │
                                                   │  (2025 full yr) │
```

### 3.2 Split Configuration

```yaml
# data/config.yaml
train_end: "2024-01-01"    # exclusive
val_end:   "2025-01-01"    # exclusive
test_end:  "2026-01-01"    # exclusive (covers all of 2025)
```

### 3.3 What This Ensures

- Train sees **no trips** from 2024 or 2025
- Validation sees **no trips** from 2025
- All feature engineering (lag features, rolling windows, OD graphs) must use
  only data within the respective split
- The test set is never touched during model development or hyperparameter tuning

---

## 4. Leakage Prevention

### 4.1 What Is Blocked

| Leakage Type | Prevention |
|-------------|------------|
| **Future trip data** | Split by pickup timestamp; no random shuffle |
| **Future statistics** | Zone-time statistics computed only from training data |
| **OD graph leakage** | Graph built only from training-period trips |
| **Feature leakage** | Lag/rolling features use only preceding time slots |
| **Cross-split trip overlap** | Exact trip matching across train/validation/test reported |

### 4.2 What Must Be Enforced Downstream

- Forecasting models must use **chronological** train/val splits (no time-shuffled CV)
- OD graph must be built **only** from training trips
- Any feature that aggregates across time (e.g., rolling mean) must use
  only data points **strictly before** the target timestamp

---

## 5. Preprocessing Pipeline

### 5.1 Cleaning Rules (mirror `src/1_data_clean/clean.py`)

1. **Date boundary**: Keep only trips within the configured year range
2. **Temporal consistency**: `pickup < dropoff`
3. **Missing fields**: Drop rows missing required columns
4. **Valid zone IDs**: `PULocationID`, `DOLocationID` in [1, 263]
5. **Fare range**: `fare_amount` in [$0.00, $200.00]
6. **Duration range**: `trip_duration` in [1 min, 240 min]
7. **Distance range**: `trip_distance` in [0.1 mi, 100.0 mi]
8. **Speed cap**: Speed ≤ 80 mph
9. **Deduplication**: Unique on (pickup, dropoff, fare, distance)

### 5.2 Pipeline Steps

```
src/data/download.py
  ├── download_tlc_month(year, month) → single parquet file
  └── download_range(years) → all 12 months per year

src/data/pipeline.py
  ├── TLCDataPipeline.load_and_clean()
  │     ├── list_raw_files() → sorted by year/month
  │     ├── _read_parquet()  → polars.DataFrame
  │     ├── _clean_frame()   → 9 cleaning rules
  │     ├── compute_splits() → train/validation/test
  │     └── concat + dedup
  └── TLCDataPipeline.write_splits()
        ├── data.parquet per split
        └── splits.json manifest
```

### 5.3 Output Structure

```
data/processed/multi_year/
├── train/
│   └── data.parquet           # Cleaned 2022–2023 trips
├── validation/
│   └── data.parquet           # Cleaned 2024 trips
├── test/
│   └── data.parquet           # Cleaned 2025 trips
└── splits.json                # Row counts, time ranges, config
```

---

## 6. Directory Structure

```
data/
├── config.yaml                # Pipeline configuration (years, splits, thresholds)
├── raw/
│   ├── 2022/
│   │   ├── 01/
│   │   │   └── yellow_tripdata_2022-01.parquet
│   │   ├── 02/
│   │   │   └── yellow_tripdata_2022-02.parquet
│   │   └── ...
│   ├── 2023/
│   │   └── ...
│   ├── 2024/
│   │   └── ...
│   └── 2025/
│       └── ...
├── processed/
│   ├── multi_year/           # New multi-year pipeline outputs
│   │   ├── train/data.parquet
│   │   ├── validation/data.parquet
│   │   ├── test/data.parquet
│   │   └── splits.json
│   └── ...                   # Existing single-month processed files unchanged
└── meta/
    └── taxi_zone_lookup.csv   # Zone metadata
```

---

## 7. Usage

### Download

```python
from src.data import download_range

# Download all 2022–2025 months
paths = download_range([2022, 2023, 2024, 2025])
# Returns: {(2022, 1): Path("data/raw/2022/01/..."), ...}
```

### Build Dataset

```python
from src.data import TLCDataPipeline

pipeline = TLCDataPipeline()
outputs = pipeline.run()
# Returns: {"train": Path(".../train/data.parquet"), ...}
```

### Load for Analysis

```python
import polars as pl

train = pl.read_parquet("data/processed/multi_year/train/data.parquet")
validation = pl.read_parquet("data/processed/multi_year/validation/data.parquet")
test = pl.read_parquet("data/processed/multi_year/test/data.parquet")
```

---

## 8. Versioning

Each pipeline run generates a `splits.json` manifest with:
- Config parameters (boundaries, years)
- Per-split row counts and time ranges
- Column schema

This manifest serves as a lightweight version record. For full reproducibility,
pair with a git commit hash.
