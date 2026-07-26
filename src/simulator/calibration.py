"""Simulator calibration: align v1 and v2 revenue estimates.

v1 (multi_agent): Uses real TLC data from src/1_data_clean; competition is implicit
                  through finite trip inventory.
v2 (DynamicSimulator): Fully synthetic supply-demand dynamics; competition is explicit
                       through driver payoff interaction.

Usage:
    python -m src.simulator.calibration --help
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

# Calibration factors derived from running "stay" strategy on both simulators.
# v1 historical avg: ~$1,500/driver/week (from rl_benchmark.json environment.reward_scale)
# v2 current avg:    ~$1,865/driver/week (from rl_benchmark_v2.json DQN stay policy)
# Factor = v1_hot_zone_reward / v2_dqn_reward ≈ 1500 / 1865 ≈ 0.804
_CALIBRATION_FACTOR = 0.80  # v1 revenue = v2 revenue * factor


def calibrate_v2_to_v1(v2_revenue: float) -> float:
    """Convert v2 simulator revenue to estimated v1-equivalent.

    Args:
        v2_revenue: Revenue per driver from DynamicSimulator v2.

    Returns:
        Estimated revenue per driver in v1 simulator.
    """
    return v2_revenue * _CALIBRATION_FACTOR


def calibrate_v1_to_v2(v1_revenue: float) -> float:
    """Convert v1 revenue to estimated v2-equivalent.

    Args:
        v1_revenue: Revenue per driver from multi-agent v1 simulator.

    Returns:
        Estimated revenue per driver in v2 DynamicSimulator.
    """
    return v1_revenue / _CALIBRATION_FACTOR


def run_calibration() -> dict[str, float]:
    """Run calibration on current benchmark outputs.

    Reads the committed benchmark JSONs and computes calibration
    metrics between v1 and v2 simulators.

    Returns:
        Dict with calibration metrics.
    """
    root = Path(__file__).resolve().parents[2]
    v2_path = root / "outputs" / "rl_benchmark_v2.json"
    v1_path = root / "outputs" / "rl_benchmark.json"

    results: dict[str, float] = {}

    if v2_path.exists():
        v2 = json.loads(v2_path.read_text())
        dqn = v2.get("dqn", {})
        v2_reward = dqn.get("avg_reward_per_driver", 0.0)
        results["v2_dqn_reward"] = v2_reward
        results["v2_double_dqn_reward"] = v2.get("double_dqn", {}).get("avg_reward_per_driver", 0.0)
        results["v2_iql_fqe"] = v2.get("iql", {}).get("avg_reward_per_driver", 0.0)
        results["v2_mf_single"] = v2.get("mean_field", {}).get("single_agent_reward", 0.0)
        results["v2_mf_multi"] = v2.get("mean_field", {}).get("multi_agent_reward", 0.0)

    if v1_path.exists():
        v1 = json.loads(v1_path.read_text())
        env = v1.get("environment", {})
        results["v1_reward_scale"] = env.get("reward_scale", 0.0)
        results["v1_driver_count"] = float(env.get("driver_count", 0))
        results["v1_demand_supply_ratio"] = env.get("demand_supply_ratio", 0.0)
        eval_data = v1.get("evaluation", {})
        results["v1_hot_zone_reward"] = eval_data.get("hot_zone", {}).get("avg_reward", 0.0)

    if "v2_dqn_reward" in results and "v1_hot_zone_reward" in results and results["v1_hot_zone_reward"] > 0:
        results["calibration_factor"] = results["v1_hot_zone_reward"] / results["v2_dqn_reward"]
    else:
        results["calibration_factor"] = _CALIBRATION_FACTOR

    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Simulator calibration tool")
    parser.add_argument("--output", type=Path, default=None, help="Output JSON path")
    args = parser.parse_args()

    results = run_calibration()
    output = json.dumps(results, indent=2)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output + "\n")
    else:
        print(output)


if __name__ == "__main__":
    main()
