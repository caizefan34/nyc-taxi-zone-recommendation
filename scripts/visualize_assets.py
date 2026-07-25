"""Generate comparison charts for README documentation."""
from __future__ import annotations
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ASSETS_DIR = Path(__file__).resolve().parents[1] / "assets"

def plot_fare_comparison():
    strategies = ["Baseline 1", "Baseline 2", "Two-Step (Ours)"]
    fares = [431.4, 549.0, 569.8]
    colors = ["#ff9999", "#66b3ff", "#99ff99"]
    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(strategies, fares, color=colors, edgecolor="black", linewidth=1.2)
    for b, f in zip(bars, fares):
        ax.text(b.get_x() + b.get_width()/2, b.get_height() + 5, f"${f:.1f}", ha="center", fontsize=12, fontweight="bold")
    ax.set_ylabel("Avg Daily Fare ($)", fontsize=12)
    ax.set_title("Strategy Comparison: Average Daily Fare", fontsize=14, fontweight="bold")
    ax.set_ylim(0, 650)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    plt.tight_layout()
    plt.savefig(ASSETS_DIR / "fare_comparison.png", dpi=150)
    plt.close()
    print("fare_comparison.png saved")

def plot_pickup_comparison():
    strategies = ["Baseline 1", "Baseline 2", "Two-Step (Ours)"]
    pickups = [133.9, 107.0, 81.2]
    colors = ["#ff9999", "#66b3ff", "#99ff99"]
    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(strategies, pickups, color=colors, edgecolor="black", linewidth=1.2)
    for b, p in zip(bars, pickups):
        ax.text(b.get_x() + b.get_width()/2, b.get_height() + 1, f"{p:.1f}", ha="center", fontsize=12, fontweight="bold")
    ax.set_ylabel("Avg Daily Pickups", fontsize=12)
    ax.set_title("Strategy Comparison: Average Daily Pickups", fontsize=14, fontweight="bold")
    ax.set_ylim(0, 160)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    plt.tight_layout()
    plt.savefig(ASSETS_DIR / "pickup_comparison.png", dpi=150)
    plt.close()
    print("pickup_comparison.png saved")

def main():
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    plot_fare_comparison()
    plot_pickup_comparison()
    print("All charts generated in assets/")

if __name__ == "__main__":
    main()

