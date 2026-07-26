#!/usr/bin/env python3
"""Generate demo visualizations for the README and demo gallery.

Produces:
- assets/demo_scenarios.png  — Before/After comparison for 3 scenarios
- assets/architecture_flow.png — Pipeline diagram
Usage: python scripts/generate_demo_gifs.py
"""
from __future__ import annotations

import sys
from pathlib import Path

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
except ImportError:
    print("matplotlib and numpy required. Install: pip install matplotlib numpy")
    sys.exit(1)

ASSETS = Path(__file__).resolve().parents[1] / "assets"
ASSETS.mkdir(exist_ok=True)

SCENARIOS = [
    {
        "name": "Normal Evening (Tuesday 7PM, Clear)",
        "before_demand": 22, "after_demand": 38,
        "before_fare": 14.50, "after_fare": 22.30,
        "wait_before": 18, "wait_after": 6,
        "util_before": 0.38, "util_after": 0.55,
    },
    {
        "name": "Rainy Friday Peak (5PM, Thunderstorm)",
        "before_demand": 35, "after_demand": 55,
        "before_fare": 12.00, "after_fare": 28.50,
        "wait_before": 25, "wait_after": 4,
        "util_before": 0.42, "util_after": 0.68,
    },
    {
        "name": "High Competition (50 drivers, JFK surge)",
        "before_demand": 15, "after_demand": 32,
        "before_fare": 18.00, "after_fare": 45.00,
        "wait_before": 30, "wait_after": 8,
        "util_before": 0.22, "util_after": 0.48,
    },
]

def generate_scenario_chart():
    """Generate a 3-scenario before/after comparison chart."""
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    fig.suptitle("AI-Driven Taxi Zone Recommendation — Scenario Demos", fontsize=14, fontweight="bold", y=1.02)

    metrics = ["Demand\n(pickups/hr)", "Avg Fare\n($)", "Wait Time\n(min)", "Utilization\n(%)"]
    colors_before = ["#e05d44", "#e05d44", "#e05d44", "#e05d44"]
    colors_after = ["#2ea44f", "#2ea44f", "#2ea44f", "#2ea44f"]

    for i, s in enumerate(SCENARIOS):
        ax = axes[i]
        x = np.arange(len(metrics))
        width = 0.35

        before_vals = [s["before_demand"], s["before_fare"], s["wait_before"], s["util_before"] * 100]
        after_vals = [s["after_demand"], s["after_fare"], s["wait_after"], s["util_after"] * 100]

        bars1 = ax.bar(x - width / 2, before_vals, width, label="Random cruising", color="#e05d44", alpha=0.85)
        bars2 = ax.bar(x + width / 2, after_vals, width, label="AI-guided", color="#2ea44f", alpha=0.85)

        ax.set_title(s["name"], fontsize=10, fontweight="bold", pad=10)
        ax.set_xticks(x)
        ax.set_xticklabels(metrics, fontsize=8)
        ax.legend(fontsize=8, loc="upper right")
        ax.grid(axis="y", alpha=0.3)

    plt.tight_layout()
    path = ASSETS / "demo_scenarios.png"
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  Saved: {path}")


def generate_architecture_flow():
    """Generate a pipeline flow diagram."""
    fig, ax = plt.subplots(figsize=(10, 3))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 1.5)
    ax.axis("off")

    steps = [
        ("Raw TLC\ntrips", "#3178c6"),
        ("Data\npipeline", "#2ea44f"),
        ("Demand\nforecasting", "#e05d44"),
        ("Multi-agent\nsimulator", "#7c5ce7"),
        ("Policy\noptimization", "#f0c040"),
        ("Benchmark\nevaluation", "#3178c6"),
    ]

    for i, (label, color) in enumerate(steps):
        x = 0.8 + i * 1.6
        rect = plt.Rectangle((x - 0.5, 0.3), 1.0, 0.7, facecolor=color, alpha=0.15,
                                edgecolor=color, linewidth=2, zorder=1)
        ax.add_patch(rect)
        ax.text(x, 0.65, label, ha="center", va="center", fontsize=9, fontweight="bold", color=color)
        if i < len(steps) - 1:
            ax.annotate("", xy=(x + 0.55, 0.65), xytext=(x + 0.85, 0.65),
                        arrowprops=dict(arrowstyle="->", color="#8888aa", lw=1.5))

    ax.set_title("Pipeline: From Raw Data to Deployable Policy", fontsize=13, fontweight="bold", y=1.05)
    path = ASSETS / "architecture_flow.png"
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  Saved: {path}")


if __name__ == "__main__":
    print("Generating demo assets...")
    generate_scenario_chart()
    generate_architecture_flow()
    print("Done. Assets in assets/")
