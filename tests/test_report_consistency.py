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
        if "\\[\n" in text or "\n\\]" in text or "\\operatorname" in text or "^*" in text or "^{*}" in text:
            offenders.append(str(path.relative_to(ROOT)))
    assert offenders == []


def test_evaluation_metric_table_does_not_use_raw_pipes_inside_math():
    problem_statement = (ROOT / "docs/problem_statement.md").read_text(encoding="utf-8")
    table = problem_statement.split("### Evaluation Metrics", 1)[1].split("### Constraints", 1)[0]
    formula_rows = [line for line in table.splitlines() if line.startswith("| **")]
    assert formula_rows
    assert all(line.count("|") == 4 for line in formula_rows)
    assert "\\lvert Q\\rvert" in table
    assert "|Q|" not in table


def test_multi_agent_snapshot_conserves_demand_and_documents_competition():
    snapshot = json.loads((ROOT / "outputs/multi_agent_benchmark.json").read_text(encoding="utf-8"))
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for strategy in snapshot["strategies"].values():
        run = strategy["first_run"]
        assert run["initial_trip_inventory"] == run["fulfilled_trips"] + run["remaining_trip_inventory"]
        assert run["competing_pickup_attempts"] > 0
        assert run["realized_demand_supply_ratio"] == snapshot["demand_supply_ratio"]
    sensitivity = snapshot["ratio_sensitivity"]
    assert sensitivity["0.50"]["driver_utilization"] < sensitivity["2.00"]["driver_utilization"]
    assert sensitivity["0.50"]["zone_saturation_rate"] > sensitivity["2.00"]["zone_saturation_rate"]
    comparison = snapshot["paired_revenue"]["single_step_vs_hot_zone"]
    assert comparison["ci95_low"] > 0.0
    assert f"{comparison['mean_difference']:.2f}" in readme


def test_rl_snapshot_is_temporally_isolated_and_matches_readme():
    snapshot = json.loads((ROOT / "outputs/rl_benchmark.json").read_text(encoding="utf-8"))
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    report = (ROOT / "outputs/rl_benchmark.md").read_text(encoding="utf-8")
    assert snapshot["training_window"]["end_exclusive"] == snapshot["evaluation_window"]["start"]
    for strategy in snapshot["evaluation"]["strategies"].values():
        run = strategy["first_run"]
        assert run["initial_trip_inventory"] == run["fulfilled_trips"] + run["remaining_trip_inventory"]
    dqn = snapshot["evaluation"]["paired_revenue"]["dqn_vs_single_step"]
    double_dqn = snapshot["evaluation"]["paired_revenue"]["double_dqn_vs_single_step"]
    assert dqn["ci95_low"] > 0.0
    assert double_dqn["ci95_high"] < 0.0
    assert f"{dqn['mean_difference']:.2f}" in readme
    assert "not training uncertainty or causal deployment lift" in report


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


def test_social_preview_uses_current_verified_headlines():
    preview = (ROOT / "assets/social-preview.svg").read_text(encoding="utf-8")
    combined = json.loads((ROOT / "outputs/benchmark_report.json").read_text(encoding="utf-8"))
    forecast_mae = combined["methods"]["forecasting_enhanced"]["demand_mae"]
    dqn_lift = combined["methods"]["dqn"]["difference_vs_original"]["mean_difference"]
    assert f"{forecast_mae:.4f}" in preview
    assert f"+${dqn_lift:.2f}" in preview
    assert "0.9978" not in preview
    assert "0.9988" not in preview
