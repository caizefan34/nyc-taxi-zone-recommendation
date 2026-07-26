"""
generate_release_dashboard.py — Generate the release dashboard figure.
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "docs" / "results"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def load_json(path):
    p = Path(path)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def plot_forecast(ax, fore_data):
    demand = fore_data.get("demand", {})
    ensemble = fore_data.get("ensemble", {})
    models = ["Historical", "XGBoost", "LightGBM", "Ensemble", "GraphSAGE", "GAT"]
    maes = [
        demand.get("historical_mae", 1.727),
        fore_data.get("xgboost", {}).get("demand", {}).get("mae", 1.496),
        demand.get("lightgbm_mae", 1.511),
        ensemble.get("demand_mae", 1.487),
        1.504, 1.506,
    ]
    colors = ["#d3d3d3", "#87ceeb", "#87ceeb", "#3cb371", "#ffd700", "#ffd700"]
    bars = ax.bar(models, maes, color=colors, edgecolor="gray", linewidth=0.5)
    for bar, v in zip(bars, maes):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.02,
                f"{v:.3f}", ha="center", va="bottom", fontsize=7)
    ax.set_title("Forecast MAE (lower is better)", fontsize=10, fontweight="bold")
    ax.set_ylabel("MAE (pickups/slot)")
    ax.set_ylim(1.3, 1.9)
    ax.tick_params(axis="x", rotation=30, labelsize=7)


def plot_policy(ax, rl_data):
    agents = rl_data.get("multi_agent", {})
    def rev(key, default):
        return agents.get(key, {}).get("average_driver_revenue", default)
    policies = ["Hot Zone", "Two-Step", "Single-Step", "DQN", "Double DQN", "IQL"]
    revenues = [1689.0, 1508.0, rev("single_step", 1768.04), rev("dqn", 1821.77),
                rev("double_dqn", 1742.77), rev("iql", 1794.94)]
    colors = ["#ff9999", "#ff9999", "#87ceeb", "#3cb371", "#ffd700", "#9370db"]
    bars = ax.bar(policies, revenues, color=colors, edgecolor="gray", linewidth=0.5)
    for bar, v in zip(bars, revenues):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 10,
                f"${v:.0f}", ha="center", va="bottom", fontsize=7)
    ax.set_title("Policy Revenue per Driver/Week", fontsize=10, fontweight="bold")
    ax.set_ylabel("Revenue ($)")
    ax.tick_params(axis="x", rotation=30, labelsize=7)


def plot_calibration(ax):
    metrics = ["Fare RMSE", "Travel Time MAE"]
    before = [8.88, 3.03]
    after = [3.11, 1.32]
    x = np.arange(len(metrics))
    w = 0.3
    ax.bar(x - w / 2, before, w, label="Before", color="#ff9999", edgecolor="gray", linewidth=0.5)
    ax.bar(x + w / 2, after, w, label="After", color="#3cb371", edgecolor="gray", linewidth=0.5)
    for i, (b, a) in enumerate(zip(before, after)):
        ax.text(i - w / 2, b + 0.2, f"{b:.2f}", ha="center", va="bottom", fontsize=8)
        ax.text(i + w / 2, a + 0.2, f"{a:.2f}", ha="center", va="bottom", fontsize=8)
    ax.set_title("Calibration Improvement", fontsize=10, fontweight="bold")
    ax.set_ylabel("Error")
    ax.set_xticks(x)
    ax.set_xticklabels(metrics, fontsize=8)
    ax.legend(fontsize=7)


def plot_benchmark(ax):
    categories = ["Tests Passed", "Graph+OD Gain", "2024 Drift", "Lat (Stay)", "Lat (Random)"]
    values = [274, 0, 1, 0.07, 8.67]
    colors_bar = ["#3cb371", "#ffd700", "#ff9999", "#ff9999", "#87ceeb"]
    bars = ax.barh(categories, values, color=colors_bar, edgecolor="gray", linewidth=0.5)
    for bar, v in zip(bars, values):
        label = f"{v:.0f}" if v > 10 else f"{v:.2f}"
        ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height() / 2,
                label, va="center", fontsize=7)
    ax.set_title("System Benchmark Summary", fontsize=10, fontweight="bold")
    ax.set_xlabel("Value")
    ax.tick_params(axis="y", labelsize=7)


def main():
    fore_data = load_json(ROOT / "outputs" / "forecast_evaluation.json")
    rl_data = load_json(ROOT / "outputs" / "rl_benchmark.json")

    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    fig.suptitle("Dynamic Urban Mobility Decision System - v2.0 Release Dashboard",
                 fontsize=14, fontweight="bold", y=1.02)

    plot_forecast(axes[0, 0], fore_data)
    plot_policy(axes[0, 1], rl_data)
    plot_calibration(axes[1, 0])
    plot_benchmark(axes[1, 1])

    plt.tight_layout()
    out_path = OUT_DIR / "release_dashboard.png"
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    print(f"Dashboard saved to {out_path}")


if __name__ == "__main__":
    main()
