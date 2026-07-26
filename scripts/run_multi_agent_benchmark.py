"""Benchmark existing strategies in the finite-demand multi-driver simulator."""
from __future__ import annotations

import argparse
import importlib.util
import json
import random
import statistics
import sys
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from src.audit.statistics import paired_comparison
from src.eval.rollout_core import MarketCell, load_travel_time_matrix, load_trip_market
from src.simulator.multi_agent import MultiAgentConfig, simulate_multi_agent

ROOT = Path(__file__).resolve().parents[1]
START = datetime(2023, 1, 25)
END = datetime(2023, 2, 1)
ZONE_COUNT = 263


def _load_strategy(path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module.recommend


def _sample_start_zones(
    market: dict[int, MarketCell],
    *,
    driver_count: int,
    seed: int,
) -> tuple[int, ...]:
    weights = [len(market.get(zone - 1, ())) for zone in range(1, ZONE_COUNT + 1)]
    if sum(weights) == 0:
        return (132,) * driver_count
    return tuple(random.Random(seed).choices(range(1, ZONE_COUNT + 1), weights=weights, k=driver_count))


def _summarize(results) -> dict[str, float | int]:
    fields = (
        "average_driver_revenue",
        "fulfilled_trips",
        "average_idle_minutes",
        "driver_utilization",
        "demand_fulfillment_rate",
        "zone_saturation_rate",
        "peak_zone_supply",
    )
    summary: dict[str, float | int] = {"runs": len(results)}
    for field in fields:
        values = [float(getattr(result, field)) for result in results]
        summary[field] = statistics.fmean(values)
        summary[f"{field}_std"] = statistics.stdev(values) if len(values) > 1 else 0.0
    summary["first_run"] = asdict(results[0])
    return summary


def _currency(value: float) -> str:
    return f"-${abs(value):.2f}" if value < 0.0 else f"${value:.2f}"


def _markdown(report: dict[str, object]) -> str:
    comparison = report["paired_revenue"]["two_step_vs_single_step"]
    single_hot = report["paired_revenue"]["single_step_vs_hot_zone"]
    lines = [
        "# Multi-Agent Simulator Benchmark",
        "",
        f"Configuration: {report['driver_count']} drivers, configured demand/supply ratio "
        f"{report['demand_supply_ratio']:.2f}, {report['runs']} paired seeds, seven days per seed.",
        "Demand is finite and every trip can be assigned at most once.",
        "",
        "| Strategy | Revenue/driver | Fulfilled trips | Utilization | Idle min/driver | Saturated attempts |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    labels = {"hot_zone": "Hot Zone", "single_step": "Single-Step", "two_step": "Two-Step"}
    for name in ("hot_zone", "single_step", "two_step"):
        values = report["strategies"][name]
        lines.append(
            f"| {labels[name]} | ${values['average_driver_revenue']:.2f} | "
            f"{values['fulfilled_trips']:.1f} | {values['driver_utilization']:.2%} | "
            f"{values['average_idle_minutes']:.1f} | {values['zone_saturation_rate']:.2%} |"
        )
    lines.extend(
        [
            "",
            f"Paired Two-Step minus Single-Step revenue per driver: {_currency(comparison['mean_difference'])}, "
            f"95% bootstrap CI [{_currency(comparison['ci95_low'])}, {_currency(comparison['ci95_high'])}], "
            f"paired t-test p={comparison['paired_t_pvalue']:.3g}, Wilcoxon p="
            f"{comparison['wilcoxon_pvalue']:.3g}, Cohen's dz={comparison['cohen_dz']:.3f}.",
            "",
            f"Single-Step minus Hot Zone is {_currency(single_hot['mean_difference'])} per driver, 95% CI "
            f"[{_currency(single_hot['ci95_low'])}, {_currency(single_hot['ci95_high'])}], Cohen's dz="
            f"{single_hot['cohen_dz']:.3f}.",
            "",
            "`zone_saturation_rate` is the fraction of pickup attempts made in zone-slots where competing "
            "supply exceeded the remaining trip inventory. Utilization is passenger-trip minutes divided by "
            "total driver-horizon minutes; relocation and unmatched search are idle time.",
            "",
        ]
    )
    lines.extend(
        [
            "## Demand/supply sensitivity",
            "",
            "Single-Step with the same fleet size; higher ratios add finite trip inventory while preserving the "
            "historical zone/time distribution.",
            "",
            "| Demand/supply ratio | Revenue/driver | Utilization | Fulfillment | Saturated attempts |",
            "|---:|---:|---:|---:|---:|",
        ]
    )
    for ratio, values in report["ratio_sensitivity"].items():
        lines.append(
            f"| {float(ratio):.2f} | ${values['average_driver_revenue']:.2f} | "
            f"{values['driver_utilization']:.2%} | {values['demand_fulfillment_rate']:.2%} | "
            f"{values['zone_saturation_rate']:.2%} |"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--drivers", type=int, default=50)
    parser.add_argument("--demand-supply-ratio", type=float, default=1.0)
    parser.add_argument("--runs", type=int, default=30)
    parser.add_argument("--sensitivity-runs", type=int, default=10)
    parser.add_argument("--seed", type=int, default=20230722)
    parser.add_argument("--output", type=Path, default=ROOT / "outputs/multi_agent_benchmark.json")
    parser.add_argument("--report", type=Path, default=ROOT / "outputs/multi_agent_benchmark.md")
    args = parser.parse_args()
    if args.runs < 2:
        parser.error("--runs must be at least 2 for paired statistics")
    if not 1 <= args.sensitivity_runs <= args.runs:
        parser.error("--sensitivity-runs must be in 1..--runs")

    market = load_trip_market(ROOT / "data/processed/validation_uncleaned.parquet", start=START, end=END)
    travel_times = load_travel_time_matrix(ROOT / "data/processed/travel_time_matrix_dijkstra.csv")
    strategies = {
        "hot_zone": _load_strategy(ROOT / "src/2_recommendation_algorithm/baseline_1.py", "multi_agent_b1"),
        "single_step": _load_strategy(ROOT / "src/2_recommendation_algorithm/baseline_2_2.py", "multi_agent_b2"),
        "two_step": _load_strategy(ROOT / "src/2_recommendation_algorithm/improved_strategy.py", "multi_agent_two"),
    }
    results = {name: [] for name in strategies}
    for index in range(args.runs):
        seed = args.seed + index
        start_zones = _sample_start_zones(market, driver_count=args.drivers, seed=seed)
        config = MultiAgentConfig(
            driver_count=args.drivers,
            demand_supply_ratio=args.demand_supply_ratio,
            seed=seed,
            start_location_ids=start_zones,
        )
        for name, strategy in strategies.items():
            results[name].append(
                simulate_multi_agent(
                    strategy=strategy,
                    market=market,
                    travel_times=travel_times,
                    start=START,
                    end=END,
                    config=config,
                )
            )

    revenue = {
        name: [result.average_driver_revenue for result in strategy_results]
        for name, strategy_results in results.items()
    }
    ratio_sensitivity = {}
    for ratio in (0.5, 1.0, 2.0):
        if ratio == args.demand_supply_ratio:
            ratio_results = results["single_step"][: args.sensitivity_runs]
        else:
            ratio_results = []
            for index in range(args.sensitivity_runs):
                seed = args.seed + index
                config = MultiAgentConfig(
                    driver_count=args.drivers,
                    demand_supply_ratio=ratio,
                    seed=seed,
                    start_location_ids=_sample_start_zones(market, driver_count=args.drivers, seed=seed),
                )
                ratio_results.append(
                    simulate_multi_agent(
                        strategy=strategies["single_step"],
                        market=market,
                        travel_times=travel_times,
                        start=START,
                        end=END,
                        config=config,
                    )
                )
        ratio_sensitivity[f"{ratio:.2f}"] = _summarize(ratio_results)
    report = {
        "runs": args.runs,
        "driver_count": args.drivers,
        "demand_supply_ratio": args.demand_supply_ratio,
        "base_seed": args.seed,
        "strategies": {name: _summarize(strategy_results) for name, strategy_results in results.items()},
        "ratio_sensitivity": ratio_sensitivity,
        "paired_revenue": {
            "two_step_vs_single_step": paired_comparison(revenue["two_step"], revenue["single_step"]),
            "two_step_vs_hot_zone": paired_comparison(revenue["two_step"], revenue["hot_zone"]),
            "single_step_vs_hot_zone": paired_comparison(revenue["single_step"], revenue["hot_zone"]),
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    args.report.write_text(_markdown(report), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
