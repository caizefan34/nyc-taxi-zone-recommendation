"""Train DQN/Double-DQN on pre-holdout data and benchmark the learned policies."""

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

import numpy as np
import torch

from src.audit.statistics import paired_comparison
from src.common.data_loader import DataLoader
from src.eval.rollout_core import MarketCell, load_travel_time_matrix, load_trip_market
from src.rl import DQNStrategy, ObservationEncoder, RLEnvConfig, TaxiRepositionEnv
from src.rl.dqn import DQNConfig, train_agent
from src.simulator.multi_agent import MultiAgentConfig, simulate_multi_agent

ROOT = Path(__file__).resolve().parents[1]
TRAIN_START = datetime(2023, 1, 18)
TRAIN_END = datetime(2023, 1, 25)
EVAL_START = datetime(2023, 1, 25)
EVAL_END = datetime(2023, 2, 1)
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
    return tuple(random.Random(seed).choices(range(1, ZONE_COUNT + 1), weights=weights, k=driver_count))


def _summarize(results) -> dict[str, object]:
    fields = (
        "average_driver_revenue",
        "fulfilled_trips",
        "average_idle_minutes",
        "driver_utilization",
        "demand_fulfillment_rate",
        "zone_saturation_rate",
    )
    summary: dict[str, object] = {"runs": len(results)}
    for field in fields:
        values = [float(getattr(result, field)) for result in results]
        summary[field] = statistics.fmean(values)
        summary[f"{field}_std"] = statistics.stdev(values) if len(values) > 1 else 0.0
    summary["first_run"] = asdict(results[0])
    return summary


def _currency(value: float) -> str:
    return f"-${abs(value):.2f}" if value < 0.0 else f"${value:.2f}"


def _markdown(report: dict[str, object]) -> str:
    lines = [
        "# DQN and Double-DQN Benchmark",
        "",
        "Training uses only Jan 18--24 finite-market episodes. Evaluation uses Jan 25--31 with 50 drivers, "
        f"demand/supply ratio 1.0, and {report['evaluation']['runs']} paired seeds.",
        "",
        "| Strategy | Revenue/driver | Fulfilled trips | Utilization | Saturated attempts |",
        "|---|---:|---:|---:|---:|",
    ]
    labels = {
        "hot_zone": "Hot Zone",
        "single_step": "Single-Step",
        "finite_horizon": "Finite Horizon",
        "dqn": "DQN",
        "double_dqn": "Double DQN",
    }
    for name in labels:
        values = report["evaluation"]["strategies"][name]
        lines.append(
            f"| {labels[name]} | ${values['average_driver_revenue']:.2f} | "
            f"{values['fulfilled_trips']:.1f} | {values['driver_utilization']:.2%} | "
            f"{values['zone_saturation_rate']:.2%} |"
        )
    lines.extend(
        [
            "",
            "## Training diagnostics",
            "",
            "| Algorithm | Interactions | First-20 return | Last-20 return | Last-100 loss |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for name, label in (("dqn", "DQN"), ("double_dqn", "Double DQN")):
        values = report["training"][name]
        first_returns = values["episode_returns"][:20]
        lines.append(
            f"| {label} | {values['interaction_steps']} | {statistics.fmean(first_returns):.2f} | "
            f"{values['mean_return_last_20']:.2f} | {values['mean_loss_last_100']:.3f} |"
        )
    lines.extend(["", "## Paired comparisons", ""])
    comparison_labels = {
        "dqn_vs_single_step": "DQN minus Single-Step",
        "double_dqn_vs_single_step": "Double DQN minus Single-Step",
        "double_dqn_vs_dqn": "Double DQN minus DQN",
    }
    for name, label in comparison_labels.items():
        values = report["evaluation"]["paired_revenue"][name]
        lines.append(
            f"- {label}: {_currency(values['mean_difference'])}/driver, 95% CI "
            f"[{_currency(values['ci95_low'])}, {_currency(values['ci95_high'])}], "
            f"paired t p={values['paired_t_pvalue']:.3g}, Wilcoxon p={values['wilcoxon_pvalue']:.3g}, "
            f"Cohen's dz={values['cohen_dz']:.3f}."
        )
    lines.extend(
        [
            "",
            "The policies see training-derived demand/fare, travel time, candidate utility, and expected background "
            "supply. They do not observe evaluation trip inventory or future arrivals.",
            "",
            "DQN improves on Single-Step inside this simulator, while Double DQN does not. This is a single training "
            "seed with 20 evaluation-market seeds, so the confidence intervals measure paired simulator variation, "
            "not training uncertainty or causal deployment lift. The default recommender is unchanged.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--episodes", type=int, default=300)
    parser.add_argument("--runs", type=int, default=20)
    parser.add_argument("--drivers", type=int, default=50)
    parser.add_argument("--candidate-count", type=int, default=20)
    parser.add_argument("--seed", type=int, default=20230722)
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--dqn-model", type=Path, default=ROOT / "data/processed/dqn_policy.pt")
    parser.add_argument("--double-model", type=Path, default=ROOT / "data/processed/double_dqn_policy.pt")
    parser.add_argument("--output", type=Path, default=ROOT / "outputs/rl_benchmark.json")
    parser.add_argument("--report", type=Path, default=ROOT / "outputs/rl_benchmark.md")
    args = parser.parse_args()
    if args.runs < 2:
        parser.error("--runs must be at least 2 for paired statistics")

    loader = DataLoader(ROOT)
    demand, fare = loader.load_zone_statistics()
    demand = np.asarray(demand, dtype=np.float32).reshape(336, ZONE_COUNT)
    fare = np.asarray(fare, dtype=np.float32).reshape(336, ZONE_COUNT)
    travel_times = load_travel_time_matrix(ROOT / "data/processed/travel_time_matrix_dijkstra.csv")
    train_market = load_trip_market(
        ROOT / "data/processed/train_cleaned.parquet",
        start=TRAIN_START,
        end=TRAIN_END,
    )
    env_config = RLEnvConfig(
        candidate_count=args.candidate_count,
        background_driver_count=args.drivers - 1,
        demand_supply_ratio=1.0,
    )
    env = TaxiRepositionEnv(
        market=train_market,
        demand_features=demand,
        fare_features=fare,
        travel_times=travel_times,
        start=TRAIN_START,
        end=TRAIN_END,
        config=env_config,
    )
    training_config = DQNConfig()
    dqn, dqn_training = train_agent(
        env,
        episodes=args.episodes,
        config=training_config,
        double_dqn=False,
        seed=args.seed,
        device=args.device,
    )
    double_dqn, double_training = train_agent(
        env,
        episodes=args.episodes,
        config=training_config,
        double_dqn=True,
        seed=args.seed,
        device=args.device,
    )
    dqn.save(args.dqn_model)
    double_dqn.save(args.double_model)

    encoder = ObservationEncoder(
        demand,
        fare,
        travel_times,
        candidate_count=args.candidate_count,
        background_driver_count=args.drivers - 1,
    )
    strategies = {
        "hot_zone": _load_strategy(ROOT / "src/2_recommendation_algorithm/baseline_1.py", "rl_b1"),
        "single_step": _load_strategy(ROOT / "src/2_recommendation_algorithm/baseline_2_2.py", "rl_b2"),
        "finite_horizon": _load_strategy(
            ROOT / "src/2_recommendation_algorithm/improved_strategy.py",
            "rl_finite_horizon",
        ),
        "dqn": DQNStrategy(dqn, encoder).recommend,
        "double_dqn": DQNStrategy(double_dqn, encoder).recommend,
    }
    evaluation_market = load_trip_market(
        ROOT / "data/processed/validation_uncleaned.parquet",
        start=EVAL_START,
        end=EVAL_END,
    )
    results = {name: [] for name in strategies}
    for index in range(args.runs):
        seed = args.seed + index
        config = MultiAgentConfig(
            driver_count=args.drivers,
            demand_supply_ratio=1.0,
            seed=seed,
            start_location_ids=_sample_start_zones(
                evaluation_market,
                driver_count=args.drivers,
                seed=seed,
            ),
        )
        for name, strategy in strategies.items():
            results[name].append(
                simulate_multi_agent(
                    strategy=strategy,
                    market=evaluation_market,
                    travel_times=travel_times,
                    start=EVAL_START,
                    end=EVAL_END,
                    config=config,
                )
            )
    revenue = {
        name: [result.average_driver_revenue for result in strategy_results]
        for name, strategy_results in results.items()
    }
    report = {
        "training_window": {"start": TRAIN_START.isoformat(), "end_exclusive": TRAIN_END.isoformat()},
        "evaluation_window": {"start": EVAL_START.isoformat(), "end_exclusive": EVAL_END.isoformat()},
        "environment": asdict(env_config),
        "optimization": asdict(training_config),
        "device": args.device,
        "training": {"dqn": dqn_training, "double_dqn": double_training},
        "evaluation": {
            "runs": args.runs,
            "drivers": args.drivers,
            "strategies": {name: _summarize(strategy_results) for name, strategy_results in results.items()},
            "paired_revenue": {
                "dqn_vs_single_step": paired_comparison(revenue["dqn"], revenue["single_step"]),
                "double_dqn_vs_single_step": paired_comparison(revenue["double_dqn"], revenue["single_step"]),
                "double_dqn_vs_dqn": paired_comparison(revenue["double_dqn"], revenue["dqn"]),
            },
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    args.report.write_text(_markdown(report), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
