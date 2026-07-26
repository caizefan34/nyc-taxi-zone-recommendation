"""Combined benchmark consistency and endpoint-boundary tests."""

from __future__ import annotations

import json

from scripts.generate_combined_benchmark import ROOT, _markdown, build_report


def test_combined_benchmark_includes_all_required_methods():
    report = build_report(ROOT)
    assert set(report["methods"]) == {
        "original_single_step",
        "forecasting_enhanced",
        "dqn",
        "double_dqn",
        "graphsage_enhanced",
    }
    assert report["methods"]["dqn"]["difference_vs_original"]["ci95_low"] > 0.0
    graph = report["methods"]["graphsage_enhanced"]["mae_reduction"]
    assert graph["ci95_low"] < 0.0 < graph["ci95_high"]


def test_combined_markdown_preserves_incompatible_endpoint_warning():
    markdown = _markdown(build_report(ROOT))
    assert "not directly comparable" in markdown
    assert "Forecasting-enhanced heuristic" in markdown
    assert "GraphSAGE-enhanced model" in markdown
    assert "The default recommender remains unchanged" in markdown


def test_checked_in_combined_report_matches_source_snapshots():
    report = build_report(ROOT)
    checked_json = json.loads((ROOT / "outputs/benchmark_report.json").read_text(encoding="utf-8"))
    checked_markdown = (ROOT / "outputs/benchmark_report.md").read_text(encoding="utf-8")
    assert checked_json == report
    assert checked_markdown == _markdown(report)
