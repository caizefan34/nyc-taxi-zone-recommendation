"""Combine checked-in forecasting, graph, simulator, and RL evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_NAMES = (
    "forecast_evaluation",
    "forecasting_benchmark",
    "multi_agent_benchmark",
    "rl_benchmark",
    "graph_benchmark",
)


def _load_sources(root: Path) -> dict[str, dict[str, object]]:
    return {name: json.loads((root / "outputs" / f"{name}.json").read_text(encoding="utf-8")) for name in SOURCE_NAMES}


def build_report(root: Path = ROOT) -> dict[str, object]:
    """Extract one deterministic, endpoint-aware benchmark snapshot."""
    sources = _load_sources(root)
    forecast = sources["forecast_evaluation"]
    forecast_policy = sources["forecasting_benchmark"]
    multi_agent = sources["multi_agent_benchmark"]
    rl = sources["rl_benchmark"]
    graph = sources["graph_benchmark"]

    ensemble_comparison = forecast["ensemble"]["paired_timestamp_bootstrap"]
    forecast_policy_comparison = forecast_policy["paired_rollout"]["forecast_vs_historical"]
    dqn_comparison = rl["evaluation"]["paired_revenue"]["dqn_vs_single_step"]
    double_comparison = rl["evaluation"]["paired_revenue"]["double_dqn_vs_single_step"]
    graph_comparison = graph["paired_slot_mae_reduction"]["graphsage"]
    return {
        "sources": [f"outputs/{name}.json" for name in SOURCE_NAMES],
        "evaluation_boundaries": {
            "forecast_validation": forecast["split"],
            "forecast_policy": {
                "runs": forecast_policy["runs"],
                "simulator": "legacy single-driver historical-market simulator",
            },
            "multi_agent_policy": {
                "runs": rl["evaluation"]["runs"],
                "drivers": rl["evaluation"]["drivers"],
                "training_window": rl["training_window"],
                "evaluation_window": rl["evaluation_window"],
            },
            "graph_validation": {
                "training_end_exclusive": graph["training_end_exclusive"],
                "validation_start": graph["validation_start"],
                "validation_end": graph["validation_end"],
            },
        },
        "methods": {
            "original_single_step": {
                "legacy_daily_fare": forecast_policy["rollout"]["historical"]["mean_daily_fare"],
                "multi_agent_revenue_per_driver": rl["evaluation"]["strategies"]["single_step"][
                    "average_driver_revenue"
                ],
            },
            "forecasting_enhanced": {
                "demand_mae": forecast["ensemble"]["demand_mae"],
                "historical_demand_mae": forecast["demand"]["historical_mae"],
                "mae_improvement": ensemble_comparison,
                "legacy_daily_fare": forecast_policy["rollout"]["forecast"]["mean_daily_fare"],
                "fare_difference_vs_original": forecast_policy_comparison,
            },
            "dqn": {
                "revenue_per_driver": rl["evaluation"]["strategies"]["dqn"]["average_driver_revenue"],
                "difference_vs_original": dqn_comparison,
            },
            "double_dqn": {
                "revenue_per_driver": rl["evaluation"]["strategies"]["double_dqn"]["average_driver_revenue"],
                "difference_vs_original": double_comparison,
            },
            "graphsage_enhanced": {
                "demand_mae": graph["models"]["graphsage"]["mae"],
                "non_graph_mae": graph["models"]["non_graph_lightgbm"]["mae"],
                "mae_reduction": graph_comparison,
            },
        },
        "ablations": {
            "forecast_features": forecast["feature_ablation"],
            "multi_agent_demand_supply": multi_agent["ratio_sensitivity"],
            "graph_features": graph["models"],
            "dqn_vs_double_dqn": rl["evaluation"]["paired_revenue"]["double_dqn_vs_dqn"],
        },
    }


def _currency(value: float) -> str:
    return f"-${abs(value):.2f}" if value < 0.0 else f"${value:.2f}"


def _markdown(report: dict[str, object]) -> str:
    methods = report["methods"]
    original = methods["original_single_step"]
    forecast = methods["forecasting_enhanced"]
    dqn = methods["dqn"]
    double_dqn = methods["double_dqn"]
    graph = methods["graphsage_enhanced"]
    forecast_mae = forecast["mae_improvement"]
    forecast_fare = forecast["fare_difference_vs_original"]
    dqn_difference = dqn["difference_vs_original"]
    double_difference = double_dqn["difference_vs_original"]
    graph_difference = graph["mae_reduction"]
    ablations = report["ablations"]

    lines = [
        "# Combined Research Benchmark",
        "",
        "This report combines checked-in evidence without treating incompatible endpoints as one leaderboard. "
        "Forecast MAE, legacy single-driver fare, and finite-demand multi-agent revenue are not directly comparable.",
        "",
        "## Original heuristic reference",
        "",
        f"Single-Step earns ${original['legacy_daily_fare']:.2f}/day in the legacy single-driver simulator and "
        f"${original['multi_agent_revenue_per_driver']:.2f}/driver in the 50-driver finite-demand simulator.",
        "",
        "## Primary comparisons",
        "",
        "| Method | Endpoint | Result | Difference vs matched baseline | 95% CI | Effect size |",
        "|---|---|---:|---:|---:|---:|",
        f"| Forecasting-enhanced model | Demand MAE | {forecast['demand_mae']:.4f} | "
        f"{forecast_mae['mean_mae_improvement']:+.4f} | "
        f"[{forecast_mae['ci95_low']:+.4f}, {forecast_mae['ci95_high']:+.4f}] | "
        f"dz={forecast_mae['cohen_dz']:.3f} |",
        f"| Forecasting-enhanced heuristic | Legacy fare/day | ${forecast['legacy_daily_fare']:.2f} | "
        f"{_currency(forecast_fare['mean_difference'])} | "
        f"[{_currency(forecast_fare['ci95_low'])}, {_currency(forecast_fare['ci95_high'])}] | "
        f"dz={forecast_fare['cohen_dz']:.3f} |",
        f"| DQN | Multi-agent revenue/driver | ${dqn['revenue_per_driver']:.2f} | "
        f"{_currency(dqn_difference['mean_difference'])} | "
        f"[{_currency(dqn_difference['ci95_low'])}, {_currency(dqn_difference['ci95_high'])}] | "
        f"dz={dqn_difference['cohen_dz']:.3f} |",
        f"| Double DQN | Multi-agent revenue/driver | ${double_dqn['revenue_per_driver']:.2f} | "
        f"{_currency(double_difference['mean_difference'])} | "
        f"[{_currency(double_difference['ci95_low'])}, {_currency(double_difference['ci95_high'])}] | "
        f"dz={double_difference['cohen_dz']:.3f} |",
        f"| GraphSAGE-enhanced model | Demand MAE | {graph['demand_mae']:.4f} | "
        f"{graph_difference['mean_difference']:+.4f} | "
        f"[{graph_difference['ci95_low']:+.4f}, {graph_difference['ci95_high']:+.4f}] | "
        f"dz={graph_difference['cohen_dz']:.3f} |",
        "",
        "Positive MAE differences mean error reduction; positive revenue differences mean higher simulator revenue.",
        "",
        "## Interpretation",
        "",
        "- Supervised forecasting materially improves demand MAE, but its downstream heuristic does not improve "
        "legacy rollout fare; predictive accuracy and policy value are different objectives.",
        "- DQN is the only learned policy with a positive paired multi-agent revenue interval versus Single-Step, "
        "but it uses one training seed and an estimated simulator, so it is not a causal deployment result.",
        "- Double DQN underperforms both DQN and Single-Step in the matched simulator.",
        "- GraphSAGE has a slightly better MAE point estimate than non-graph LightGBM, but its interval crosses "
        "zero and OD message features without embeddings perform better.",
        "- The default recommender remains unchanged because no method has evidence across training uncertainty, "
        "market drift, and real driver response.",
        "",
        "## Ablation summary",
        "",
        "| Ablation | Best/reference | Removed/alternative | Outcome |",
        "|---|---:|---:|---|",
        f"| Forecast lag features | {ablations['forecast_features']['full']['mae']:.4f} MAE | "
        f"{ablations['forecast_features']['without_lags']['mae']:.4f} MAE | Lags are necessary |",
        f"| Forecast rolling features | {ablations['forecast_features']['full']['mae']:.4f} MAE | "
        f"{ablations['forecast_features']['without_rolling']['mae']:.4f} MAE | Rolling history is necessary |",
        f"| Graph representation | {ablations['graph_features']['od_messages']['mae']:.4f} MAE | "
        f"{ablations['graph_features']['graphsage']['mae']:.4f} MAE | Static embedding adds no gain |",
        f"| Deep RL target | ${dqn['revenue_per_driver']:.2f}/driver DQN | "
        f"${double_dqn['revenue_per_driver']:.2f}/driver Double DQN | Double DQN is worse |",
        "",
        "## Statistical boundary",
        "",
        "All confidence intervals are paired bootstrap intervals from their source benchmark. Forecast and graph "
        "intervals use held-out half-hour timestamps; policy intervals use matched simulator seeds. They do not "
        "include month-to-month sampling, model-training seeds, structural simulator error, or deployment "
        "interference.",
        "",
        "## Source snapshots",
        "",
    ]
    lines.extend(f"- `{source}`" for source in report["sources"])
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "outputs/benchmark_report.json")
    parser.add_argument("--report", type=Path, default=ROOT / "outputs/benchmark_report.md")
    args = parser.parse_args()
    report = build_report()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    args.report.write_text(_markdown(report), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
