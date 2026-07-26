"""Benchmark ML baselines (Random Forest, Gradient Boosting) for zone recommendation."""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

try:
    from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
    
    SKLEARN_AVAIL = True
except ImportError:
    SKLEARN_AVAIL = False

try:
    import xgboost as xgb
    XGB_AVAIL = True
except ImportError:
    XGB_AVAIL = False

ZONE_COUNT = 263

def generate_synthetic_data(n_samples=8000):
    """Generate synthetic training data."""
    np.random.seed(42)
    rows = []
    for _ in range(n_samples):
        w = np.random.randint(0, 7)
        s = np.random.randint(0, 48)
        z = np.random.randint(1, ZONE_COUNT + 1)
        h = s / 2
        manh = 1 if np.random.random() < 0.15 else 0
        d = max(0, int(100 * (1 + 0.5 * manh) * (0.3 + 0.7 * np.exp(-((h - 14)**2) / 50))
                       + 50 * np.random.exponential(0.2)))
        f = max(5, 15 + 20 * (1 - 0.5 * manh) + 10 * np.sin(np.pi * (h - 7) / 12) + np.random.normal(0, 5))
        rows.append({"weekday": w, "slot": s, "hour": h, "zone": z,
                      "in_manhattan": manh, "demand": d, "fare": f, "utility": d * f / 1000})
    return pd.DataFrame(rows)

def main():
    if not SKLEARN_AVAIL:
        print("ERROR: scikit-learn required. Run: pip install scikit-learn")
        sys.exit(1)

    print("=" * 60)
    print("ML Baseline Benchmark for NYC Taxi Zone Recommendation")
    print("=" * 60)

    df = generate_synthetic_data(8000)
    print(f"\nGenerated {len(df):,} synthetic samples")

    cols = ["weekday", "slot", "hour", "zone", "in_manhattan", "demand"]
    X, y = df[cols].values, df["utility"].values

    split = int(0.8 * len(X))
    X_train, X_test, y_train, y_test = X[:split], X[split:], y[:split], y[split:]
    print(f"Train: {len(X_train)}, Test: {len(X_test)}")

    models = {}
    results = {}

    # Random Forest
    t0 = time.time()
    rf = RandomForestRegressor(n_estimators=200, max_depth=15, random_state=42, n_jobs=-1)
    rf.fit(X_train, y_train)
    t = time.time() - t0
    pred = rf.predict(X_test)
    mse = np.mean((y_test - pred) ** 2)
    r2 = 1 - mse / np.var(y_test)
    models["Random Forest"] = rf
    results["Random Forest"] = {"mse": round(mse, 4), "r2": round(r2, 4), "train_time_s": round(t, 2)}
    print(f"  RandomForest: MSE={mse:.4f}, R2={r2:.4f}, {t:.2f}s")

    # Gradient Boosting
    t0 = time.time()
    gb = GradientBoostingRegressor(n_estimators=200, max_depth=8, learning_rate=0.1, random_state=42)
    gb.fit(X_train, y_train)
    t = time.time() - t0
    pred = gb.predict(X_test)
    mse = np.mean((y_test - pred) ** 2)
    r2 = 1 - mse / np.var(y_test)
    models["Gradient Boosting"] = gb
    results["Gradient Boosting"] = {"mse": round(mse, 4), "r2": round(r2, 4), "train_time_s": round(t, 2)}
    print(f"  GradBoost:     MSE={mse:.4f}, R2={r2:.4f}, {t:.2f}s")

    # XGBoost (optional)
    if XGB_AVAIL:
        t0 = time.time()
        xg = xgb.XGBRegressor(n_estimators=200, max_depth=8, learning_rate=0.1, random_state=42, n_jobs=-1)
        xg.fit(X_train, y_train)
        t = time.time() - t0
        pred = xg.predict(X_test)
        mse = np.mean((y_test - pred) ** 2)
        r2 = 1 - mse / np.var(y_test)
        models["XGBoost"] = xg
        results["XGBoost"] = {"mse": round(mse, 4), "r2": round(r2, 4), "train_time_s": round(t, 2)}
        print(f"  XGBoost:       MSE={mse:.4f}, R2={r2:.4f}, {t:.2f}s")
    else:
        print("  XGBoost: not installed (pip install xgboost)")

    # NDCG@3 comparison
    print(f"\n{'='*60}")
    print("Hit@3 Comparison (200 synthetic queries)")
    print(f"{'='*60}")

    np.random.seed(123)
    hits = {"HotZone(B1)": 0}
    for name in models: hits[name] = 0

    for _ in range(200):
        w = np.random.randint(0, 7)
        s = np.random.randint(0, 48)
        cz = np.random.randint(1, ZONE_COUNT + 1)

        true_utils = np.zeros(ZONE_COUNT)
        synth_demand = np.zeros((7, 48, ZONE_COUNT))
        for z in range(ZONE_COUNT):
            h = s / 2
            mh = 1 if np.random.random() < 0.15 else 0
            d = max(0, int(100 * (1 + 0.5 * mh)
                * (0.3 + 0.7 * np.exp(-((h - 14)**2) / 50))
                + 50 * np.random.exponential(0.2)))
            f = max(5, 15 + 20 * (1 - 0.5 * mh) + 10 * np.sin(np.pi * (h - 7) / 12) + np.random.normal(0, 5))
            true_utils[z] = d * f / 1000
            synth_demand[w, s, z] = d

        # B1: hot zone = use demand as proxy
        b1_pred = synth_demand[w, s, :]
        b1_top3 = np.argsort(-b1_pred)[:3]
        if np.any(true_utils[b1_top3] >= np.sort(true_utils)[-3]):
            hits["HotZone(B1)"] += 1

        # ML models: predict utility from features
        for name, model in models.items():
            X_val = np.zeros((ZONE_COUNT, 6))
            for z in range(ZONE_COUNT):
                mh_z = 1 if np.random.random() < 0.15 else 0
                d_z = max(0, int(100 * (1 + 0.5 * mh_z)
                    * (0.3 + 0.7 * np.exp(-((s/2 - 14)**2)/50))
                    + 50 * np.random.exponential(0.2)))
                X_val[z] = [w, s, s/2, z+1, mh_z, d_z]
            preds = model.predict(X_val)
            top3 = np.argsort(-preds)[:3]
            if np.any(true_utils[top3] >= np.sort(true_utils)[-3]):
                hits[name] += 1

    Q = 200
    for name, val in hits.items():
        print(f"  {name:<20} Hit@3: {val/Q:.4f}")

    out = Path("benchmark/ml_benchmark_results.json")
    out.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nMetrics saved to {out}")
    print(f"\n{'='*60}")
    print("ML models learn utility prediction, but the explicit")
    print("two-step planner captures OD transitions + future value.")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
