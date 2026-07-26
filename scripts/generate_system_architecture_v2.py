#!/usr/bin/env python3
"""Generate v2 system architecture diagram."""
import matplotlib

matplotlib.use("Agg")
from pathlib import Path

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt


def create_architecture():
    fig, ax = plt.subplots(1, 1, figsize=(14, 10))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 10)
    ax.axis("off")

    components = [
        (1, 8.5, "NYC TLC Data\n(2022-2025)", "#3498db"),
        (1, 6.5, "Feature Engineering\nCalendar, Weather, Events", "#2ecc71"),
        (1, 4.5, "Forecasting\nLightGBM, XGBoost, GNN", "#9b59b6"),
        (1, 2.5, "Calibrated Simulator\nMulti-agent, 50 drivers", "#e67e22"),
        (1, 0.5, "Offline RL / Policy\nIQL, DQN, Double DQN", "#e74c3c"),
        (7.5, 8.5, "External Models\nCustom ForecastModel/Policy", "#1abc9c"),
        (7.5, 6.5, "Public Benchmark\nStandardized metrics & protocol", "#34495e"),
        (7.5, 4.5, "Web Demo\nStreamlit UI", "#f39c12"),
        (7.5, 2.5, "Historical Replay\nRecorded demand evaluation", "#8e44ad"),
        (7.5, 0.5, "Multi-seed Validation\nStatistical robustness", "#c0392b"),
    ]

    for x, y, label, color in components:
        rect = mpatches.FancyBboxPatch(
            (x, y), 4, 1.2, boxstyle="round,pad=0.1",
            facecolor=color, edgecolor="white", linewidth=2, alpha=0.9
        )
        ax.add_patch(rect)
        ax.text(x + 2, y + 0.6, label, ha="center", va="center",
                color="white", fontsize=10, fontweight="bold")

    # Arrows between left column
    for y_start in [7.5, 5.5, 3.5, 1.5]:
        ax.annotate("", xy=(3, y_start), xytext=(3, y_start + 0.8),
                    arrowprops=dict(arrowstyle="->", color="#7f8c8d", lw=2))

    # Arrow connecting left to right
    ax.annotate("", xy=(7, 9.1), xytext=(5.5, 9.1),
                arrowprops=dict(arrowstyle="->", color="#7f8c8d", lw=2))

    # Labels
    ax.text(3, 9.8, "Core Pipeline", ha="center", fontsize=14, fontweight="bold")
    ax.text(9.5, 9.8, "Extension Points", ha="center", fontsize=14, fontweight="bold")

    plt.tight_layout()
    output_dir = Path("docs")
    output_path = output_dir / "system_architecture_v2.png"
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Architecture diagram saved to {output_path}")

if __name__ == "__main__":
    create_architecture()
