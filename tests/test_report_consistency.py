"""Guard the checked-in public metrics against stale headline values."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_reference_snapshot_matches_readme_headlines():
    snapshot = json.loads((ROOT / "outputs/reference_metrics.json").read_text(encoding="utf-8"))
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    two_step = snapshot["static"]["two_step"]
    assert f"{two_step['ndcg_at_3']:.4f}" in readme
    assert f"{two_step['hit_at_3']:.4f}" in readme
    assert "0.9978" not in readme
    assert "0.9988" not in readme


def test_generated_report_contains_interpretation_boundary():
    report = (ROOT / "outputs/evaluation_report.md").read_text(encoding="utf-8")
    assert "single-driver historical-market simulator" in report
    assert "not identifiable" in report


def test_markdown_uses_github_compatible_display_math_delimiters():
    offenders = []
    for path in ROOT.rglob("*.md"):
        text = path.read_text(encoding="utf-8")
        if (
            "\\[\n" in text
            or "\n\\]" in text
            or "\\operatorname" in text
            or "^*" in text
            or "^{*}" in text
        ):
            offenders.append(str(path.relative_to(ROOT)))
    assert offenders == []


def test_forecasting_snapshot_matches_documented_claims():
    forecast = json.loads((ROOT / "outputs/forecast_evaluation.json").read_text(encoding="utf-8"))
    benchmark = json.loads((ROOT / "outputs/forecasting_benchmark.json").read_text(encoding="utf-8"))
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    demand = forecast["demand"]
    ensemble = forecast["ensemble"]
    assert demand["lightgbm_mae"] < demand["historical_mae"]
    assert ensemble["paired_timestamp_bootstrap"]["ci95_low"] > 0.0
    full_mae = forecast["feature_ablation"]["full"]["mae"]
    for name in ("without_lags", "without_rolling", "without_neighborhood"):
        assert forecast["feature_ablation"][name]["mae"] > full_mae
    comparison = benchmark["paired_rollout"]["forecast_vs_historical"]
    assert comparison["mean_difference"] < 0.0
    assert comparison["ci95_low"] < 0.0 < comparison["ci95_high"]
    assert f"{ensemble['demand_mae']:.4f}" in readme
    assert f"-${abs(comparison['mean_difference']):.2f}" in readme


def test_graph_snapshot_is_leakage_safe_and_documents_uncertainty():
    snapshot = json.loads((ROOT / "outputs/graph_benchmark.json").read_text(encoding="utf-8"))
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    report = (ROOT / "outputs/graph_benchmark.md").read_text(encoding="utf-8")
    assert snapshot["training_end_exclusive"] == snapshot["validation_start"]
    baseline = snapshot["models"]["non_graph_lightgbm"]
    graphsage = snapshot["models"]["graphsage"]
    assert graphsage["mae"] < baseline["mae"]
    comparison = snapshot["paired_slot_mae_reduction"]["graphsage"]
    assert comparison["ci95_low"] < 0.0 < comparison["ci95_high"]
    assert f"{graphsage['mae']:.4f}" in readme
    assert "graph-neural contribution is not statistically supported" in report
