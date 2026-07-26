"""Generate documentation charts from the checked-in metrics snapshot."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
ASSETS_DIR = ROOT / "assets"


def _snapshot():
    return json.loads((ROOT / "outputs/reference_metrics.json").read_text(encoding="utf-8"))


def _bar(labels, values, *, ylabel, title, output, value_format):
    figure, axis = plt.subplots(figsize=(8, 5))
    bars = axis.bar(labels, values, color=["#ff9999", "#66b3ff", "#99ff99"], edgecolor="black")
    margin = max(values) * 0.03
    for bar, value in zip(bars, values):
        axis.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + margin,
            value_format.format(value),
            ha="center",
            fontweight="bold",
        )
    axis.set_ylabel(ylabel)
    axis.set_title(title)
    axis.set_ylim(0, max(values) * 1.15)
    axis.spines["top"].set_visible(False)
    axis.spines["right"].set_visible(False)
    figure.tight_layout()
    figure.savefig(ASSETS_DIR / output, dpi=150)
    plt.close(figure)


def main() -> None:
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    snapshot = _snapshot()
    labels = ["Hot Zone", "Single-Step", "Two-Step"]
    keys = ["baseline_1", "baseline_2", "two_step"]
    fares = [snapshot["rollout"]["mean_daily_fare"][key] for key in keys]
    ndcg = [snapshot["static"][key]["ndcg_at_3"] for key in keys]
    _bar(
        labels,
        fares,
        ylabel="Mean daily fare_amount ($)",
        title="Fixed Single-Driver Simulator",
        output="fare_comparison.png",
        value_format="${:.2f}",
    )
    _bar(
        labels,
        ndcg,
        ylabel="Reference-objective NDCG@3",
        title="Static Diagnostic",
        output="ndcg_comparison.png",
        value_format="{:.4f}",
    )


if __name__ == "__main__":
    main()
