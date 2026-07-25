# 🚕 NYC Taxi Zone Recommendation

> **Two-step finite-horizon planning for taxi driver zone recommendations using NYC TLC Yellow Taxi trip data.**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![NDCG@3](https://img.shields.io/badge/NDCG%403-0.9978-success)](https://github.com/caizefan34/nyc-taxi-zone-recommendation)
[![Hit@3](https://img.shields.io/badge/Hit%403-0.9988-success)](https://github.com/caizefan34/nyc-taxi-zone-recommendation)

---

## 📖 Overview

This project tackles a **spatial-temporal recommendation problem**: given a taxi driver's current location and time, recommend the top 3 NYC taxi zones where they should go to find their next passenger. Using historical trip data from January 2023, we build and compare multiple recommendation strategies — from simple frequency-based heuristics to a **two-step finite-horizon planning** approach that models pickup probability, expected fare, and future transfer value.

**New York City** has **263 taxi zones**, and time is discretized into **48 half-hour slots per day** (336 slots per week), making this a large-scale state-space problem with real-world impact.

### Results Summary

| Strategy | Avg Daily Fare | Avg Pickups | Avg Idle Trips | Recommend Time |
|----------|:-------------:|:-----------:|:--------------:|:--------------:|
| Baseline 1 (Hot Zones) | $431.4 | 133.9 | 164.0 | 0.051 ms |
| Baseline 2 (Single-step Utility) | $549.0 | 107.0 | 130.7 | 0.072 ms |
| **Two-Step Planning (Ours)** | **$569.8** | 81.2 | 133.1 | ~0.24 ms |

**Static evaluation** on 3,360 public queries: **NDCG@3 = 0.9978**, **Hit@3 = 0.9988**, Top-1 Reference Utility = 27.75.

---

## 🧠 Methods

### Baseline 1 — Hot Zone Ranking
Ranks zones by historical pickup count for the same `(weekday, time_slot)`. Simple but ignores competition and travel cost.

### Baseline 2 — Single-Step Utility
Computes `pickup_count * mean_fare / (travel_time + 1)` for each zone. Accounts for both earning potential and relocation cost.

### Task C — Two-Step Finite Horizon Planning (Ours)
Balances immediate reward with expected future value:

$$U(z) = p_s \cdot (f + \gamma \cdot V_{success}) + (1 - p_s) \cdot \gamma \cdot V_{failure}$$

Where:
- **p_s**: Pickup probability at the target zone (sigmoid with half-saturation at 240 historical pickups)
- **f**: Expected fare amount
- **V_success**: Expected value after successful pickup (weighted by dropoff distribution from OD transition matrix)
- **V_failure**: Expected value after failing to find a passenger (stay in zone, advance one slot)
- **γ = 0.5**: Discount factor for future utility
- **λ = 1.0**: Relocation cost normalization parameter

### Extensions
- **Interactive Analysis System** — Data visualization (demand patterns, fare distribution, top zones) + CLI recommendation with human-readable zone names
- **Q-Learning Agent** — Tabular Q-learning on the full state space (~88,000 states). Fixed seed for reproducibility

---

## 🏗️ Project Structure

```
nyc-taxi-zone-recommendation/
├── src/
│   ├── 1_data_clean/
│   │   └── clean.py              # Data cleaning pipeline
│   ├── 2_recommendation_algorithm/
│   │   ├── baseline_1.py           # Hot zone ranking
│   │   ├── baseline_2_1.py         # Dijkstra travel time matrix builder
│   │   ├── baseline_2_2.py         # Single-step utility
│   │   ├── improved_strategy.py    # Two-step planning (main contribution)
│   │   └── parameter_selection.py  # Grid search for hyperparameters
│   ├── 3_extension_task/
│   │   ├── extension_1_temporal_analysis.py       # Temporal pattern analysis
│   │   ├── extension_2_interactive.py             # Interactive CLI + charts
│   │   ├── extension_2_parameter_sensitivity.py   # Parameter sensitivity study
│   │   └── extension_5_qlearning.py               # Q-learning RL agent
│   └── eval/
│       ├── public_validation.py    # Static evaluation (NDCG, Hit@3)
│       ├── validation_rollout.py   # Simulated market rollout
│       ├── sanity_check.py         # Sanity checks
│       └── offline_core.py         # Core evaluation primitives
├── configs/
│   └── parameters.json
├── tests/
│   └── test_improved_strategy.py
├── report/
│   └── report.tex                  # LaTeX report
├── requirements.txt
├── contribution.md
├── LICENSE
└── README.md
```

---

## ⚙️ Setup

### Prerequisites
- Python 3.10+
- NYC TLC Yellow Taxi trip data (January 2023) — download from [NYC TLC](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page)
- ~8 GB free disk space for raw + processed data

### Installation

```bash
# Clone the repository
git clone https://github.com/caizefan34/nyc-taxi-zone-recommendation.git
cd nyc-taxi-zone-recommendation

# Install dependencies
pip install -r requirements.txt

# Download and place raw data
# Place yellow_tripdata_2023-01.parquet in data/raw/
```

### Quick Start

```bash
# 1. Data cleaning
python src/1_data_clean/clean.py

# 2. Build travel time matrix (Dijkstra)
python src/2_recommendation_algorithm/baseline_2_1.py

# 3. Run unit tests
python -m unittest discover -s tests -v

# 4. Run sanity checks
PYTHONPATH=. python src/eval/sanity_check.py \
    --train-cleaned data/processed/train_cleaned.parquet \
    --validation-cleaned data/processed/validation_cleaned.parquet \
    --statistics data/processed/zone_time_statistics.parquet \
    --travel-times data/processed/travel_time_matrix_dijkstra.csv \
    --baseline-1 src/2_recommendation_algorithm/baseline_1.py \
    --baseline-2 src/2_recommendation_algorithm/baseline_2_2.py \
    --strategy src/2_recommendation_algorithm/improved_strategy.py \
    --output outputs/sanity_report.json
```

---

## 📊 Results

### Data Cleaning Audit

| Cleaning Rule | Training Set Removed | Validation Set Removed |
|---------------|:-------------------:|:----------------------:|
| Invalid date boundaries | 13 | 543 |
| Invalid zone IDs | 43,762 | 13,402 |
| Fare outliers (not in [0, 200]) | 18,710 | 5,509 |
| Trip duration outliers (not in [1, 240] min) | 21,412 | 6,069 |
| Distance outliers (not in [0.1, 100] mi) | 17,794 | 5,523 |
| Speed outliers (>80 mph) | 111 | 23 |
| Duplicate trips | 63 | 15 |
| **Clean rows remaining** | **2,243,804** | **688,250** |

### Simulation Rollout (100 runs, 7-day market)

| Strategy | Avg Daily Fare | Avg Pickups | Avg Idle Trips | Avg Idle Minutes |
|----------|:-------------:|:-----------:|:--------------:|:----------------:|
| Baseline 1 | $431.4 | 133.9 | 164.0 | 2,911 |
| Baseline 2 | $549.0 | 107.0 | 130.7 | 2,578 |
| **Two-Step Planning** | **$569.8** | **81.2** | **133.1** | **2,814** |

### Hyperparameter Selection

Grid search over λ ∈ {0.5, 1.0, 2.0} and γ ∈ {0.25, 0.5, 0.75}, selected by NDCG@3 → Hit@3 → latency.

**Final: λ = 1.0, γ = 0.5**

---

## 🔬 Extensions

### Extension 2 — Interactive CLI + Data Visualization
- Generates 4 analysis charts: demand by time, demand by weekday, fare distribution, top pickup zones
- Interactive CLI mode for real-time recommendations with human-readable zone names

### Extension 5 — Q-Learning for Zone Recommendation
- Tabular Q-learning agent with ε-greedy exploration
- 5,000 training episodes, γ = 0.9, α = 0.1
- Fixed seed (20230722) for full reproducibility
- Q-table size: 22,278 entries across ~88,000 states

---

## 📝 Citation

```bibtex
@software{cai2026nyctaxi,
  author = {Cai, Zefan},
  title = {NYC Taxi Zone Recommendation: Two-Step Planning for Driver Guidance},
  year = {2026},
  url = {https://github.com/caizefan34/nyc-taxi-zone-recommendation}
}
```

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

## 📚 Data Source

- NYC TLC Yellow Taxi Trip Record Data: https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page
- Taxi Zone Lookup Table: NYC TLC
