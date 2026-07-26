# ruff: noqa: E501
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "docs" / "results"
OUT.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "font.size": 11,
    "axes.titlesize": 13,
    "axes.labelsize": 11,
})

def _load_json(name):
    p = REPO / "outputs" / name
    if p.exists():
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    return {}

br = _load_json("benchmark_report.json")
fe = _load_json("forecast_evaluation.json")
rl = _load_json("rl_benchmark.json")
bs = _load_json("benchmark_statistics.json")
cr = _load_json("cross_year_benchmark.json")
cv = _load_json("calibration_validation_report.json")
print("Data loaded OK")

def draw_architecture():
    fig, ax = plt.subplots(figsize=(10, 7))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 8)
    ax.axis("off")
    ax.set_title("System Architecture", fontsize=14, fontweight="bold", pad=15)

    boxes = {
        "Data Pipeline": (0.5, 6.5, 2.5, 1.0),
        "Forecasting": (4.0, 6.5, 2.5, 1.0),
        "Dynamic Simulator": (7.5, 5.0, 2.5, 1.0),
        "Offline RL (IQL)": (4.0, 3.5, 2.5, 1.0),
        "OPE (FQE/WIS/DR)": (7.5, 2.0, 2.5, 1.0),
        "Evaluation Benchmark": (4.0, 0.5, 2.5, 1.0),
        "NYC TLC Data": (0.5, 3.5, 2.5, 1.0),
    }

    colors = ["#4472C4", "#ED7D31", "#70AD47", "#FFC000", "#5B9BD5", "#A5A5A5", "#264478"]
    for i, (label, (x, y, w, h)) in enumerate(boxes.items()):
        rect = plt.Rectangle((x, y), w, h, facecolor=colors[i], edgecolor="black", alpha=0.85)
        ax.add_patch(rect)
        ax.text(x + w / 2, y + h / 2, label, ha="center", va="center", color="white", fontsize=10, fontweight="bold")

    arrows = [
        (2.0, 7.0, 4.0, 7.0),
        (6.5, 6.5, 7.5, 5.5),
        (5.5, 5.0, 7.5, 5.0),
        (5.5, 4.5, 5.5, 4.5),
        (6.5, 3.5, 7.5, 2.5),
        (6.5, 2.0, 6.5, 1.0),
        (3.0, 4.0, 4.0, 4.0),
        (2.0, 5.5, 4.0, 6.5),
        (3.0, 2.0, 4.0, 1.0),
    ]

    for x1, y1, x2, y2 in arrows:
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="->", color="gray", lw=1.5))

    fig.savefig(OUT / "architecture.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("Saved architecture.png")

def draw_forecast():
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.5))
    models = ["Historical", "LightGBM", "Ensemble"]
    demand_mae = [1.7273, 1.5114, 1.4868]
    fare_mae = [7.0103, 5.9526, 5.9188]
    colors_bar = ["#4472C4", "#ED7D31", "#70AD47"]

    ax = axes[0]
    x = np.arange(len(models))
    bars = ax.bar(x, demand_mae, color=colors_bar, width=0.5, edgecolor="black")
    ax.set_xticks(x)
    ax.set_xticklabels(models)
    ax.set_ylabel("Demand MAE")
    ax.set_title("Demand Prediction Error")
    for bar, val in zip(bars, demand_mae):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.03, f"{val:.4f}", ha="center", va="bottom", fontsize=9)

    ax = axes[1]
    bars = ax.bar(x, fare_mae, color=colors_bar, width=0.5, edgecolor="black")
    ax.set_xticks(x)
    ax.set_xticklabels(models)
    ax.set_ylabel("Fare MAE")
    ax.set_title("Fare Prediction Error")
    for bar, val in zip(bars, fare_mae):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.05, f"{val:.4f}", ha="center", va="bottom", fontsize=9)

    fig.suptitle("Forecasting Performance Comparison", fontsize=13, fontweight="bold", y=1.02)
    fig.tight_layout()
    fig.savefig(OUT / "forecast_comparison.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("Saved forecast_comparison.png")

def draw_policy():
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.5))
    policies = ["Hot Zone", "Single-Step", "DQN", "Double DQN", "IQL"]
    revenues = [1689, 1768, 1822, 1743, 1795]

    ax = axes[0]
    colors_pol = ["#4472C4", "#ED7D31", "#70AD47", "#FFC000", "#5B9BD5"]
    x = np.arange(len(policies))
    bars = ax.bar(x, revenues, color=colors_pol, width=0.5, edgecolor="black")
    ax.set_xticks(x)
    ax.set_xticklabels(policies, fontsize=9)
    ax.set_ylabel("Revenue / Driver ($)")
    ax.set_title("Policy Revenue Comparison")
    for bar, val in zip(bars, revenues):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 5, f"${val}", ha="center", va="bottom", fontsize=9)

    ax = axes[1]
    rl_policies = ["DQN", "Double DQN", "IQL"]
    rl_utils = [0.138, 0.143, 0.285]
    x2 = np.arange(len(rl_policies))
    bars = ax.bar(x2, rl_utils, color=["#70AD47", "#FFC000", "#5B9BD5"], width=0.5, edgecolor="black")
    ax.set_xticks(x2)
    ax.set_xticklabels(rl_policies, fontsize=9)
    ax.set_ylabel("Utilization Rate")
    ax.set_title("RL Policy Utilization")
    for bar, val in zip(bars, rl_utils):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.003, f"{val:.3f}", ha="center", va="bottom", fontsize=9)

    fig.suptitle("Policy Comparison Results", fontsize=13, fontweight="bold", y=1.02)
    fig.tight_layout()
    fig.savefig(OUT / "policy_comparison.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("Saved policy_comparison.png")

def draw_calibration():
    fig, axes = plt.subplots(1, 3, figsize=(12, 4))
    metrics = ["Fare RMSE", "Travel MAE", "KL Div"]
    before = [8.8830, 3.0340, 0.6622]
    after = [3.1091, 1.3147, 0.6622]
    x = np.arange(len(metrics))
    w = 0.35

    for i, (ax, metric, b, a) in enumerate(zip(axes, metrics, before, after)):
        bars_b = ax.bar(x[i] - w / 2, b, w, color="#ED7D31", edgecolor="black", label="Before" if i == 0 else "")
        bars_a = ax.bar(x[i] + w / 2, a, w, color="#70AD47", edgecolor="black", label="After" if i == 0 else "")
        ax.set_xticks([x[i]])
        ax.set_xticklabels([metric])
        ax.set_ylabel("Error")
        for bar, val in zip([bars_b, bars_a], [b, a]):
            ax.text(bar[0].get_x() + bar[0].get_width() / 2, bar[0].get_height() + 0.1, f"{val:.4f}", ha="center", va="bottom", fontsize=8)

    axes[0].legend()
    fig.suptitle("Calibration Effectiveness", fontsize=13, fontweight="bold", y=1.02)
    fig.tight_layout()
    fig.savefig(OUT / "calibration_effect.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("Saved calibration_effect.png")

def draw_benchmark():
    fig, ax = plt.subplots(figsize=(8, 5))
    comparisons = ["Forecast MAE", "DQN Revenue", "Double DQN Revenue", "IQL Utilization", "Calib Fare RMSE", "Calib Travel MAE"]
    values = [1.4868, 1821.77, 1742.77, 0.2847, 3.1091, 1.3147]
    refs = [1.7273, 1768.00, 1768.00, 0.1379, 8.8830, 3.0340]
    colors_comp = ["#70AD47" if v < r else "#ED7D31" for v, r in zip(values, refs)]
    x = np.arange(len(comparisons))
    w = 0.35
    bars_v = ax.bar(x - w / 2, values, w, color=colors_comp, edgecolor="black", label="Achieved")
    bars_r = ax.bar(x + w / 2, refs, w, color="#A5A5A5", edgecolor="black", alpha=0.6, label="Baseline")
    ax.set_xticks(x)
    ax.set_xticklabels(comparisons, fontsize=9)
    ax.set_ylabel("Value")
    ax.set_title("Benchmark Summary: Achieved vs Baseline", fontsize=13, fontweight="bold")
    ax.legend()
    for bar, val in zip(bars_v, values):
        label = f"{val:.4f}" if val < 100 else f"${val:.0f}"
        yoff = 0.02 if val < 100 else 5
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + yoff, label, ha="center", va="bottom", fontsize=8)
    fig.tight_layout()
    fig.savefig(OUT / "benchmark_summary.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("Saved benchmark_summary.png")

if __name__ == "__main__":
    draw_architecture()
    draw_forecast()
    draw_policy()
    draw_calibration()
    draw_benchmark()
    print("All figures generated successfully.")

