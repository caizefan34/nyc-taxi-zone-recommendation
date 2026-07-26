"""Simulator calibration: multi-dim alignment of simulator to real-world statistics.

Supports calibration of:
- Demand distribution (zone-level pickup counts)
- Fare / revenue distribution
- Travel time distribution
- Reward scale (v1 v2 alignment)

Usage:
    python -m src.simulator.calibration --config configs/calibration.yaml
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass
class CalibrationConfig:
    """Multi-dimensional calibration configuration.

    Each calibration type supports its own factor, optional per-zone factors,
    and scaling parameters.
    """
    demand_factor: float = 1.0
    fare_factor: float = 0.80
    travel_time_factor: float = 1.0
    reward_factor: float = 0.80
    demand_offset: float = 0.0
    fare_offset: float = 0.0
    use_per_zone: bool = False
    zone_factors_path: str | None = None
    source: str = "default"
    calibration_date: str = ""


def load_calibration_config(path: str | Path = "configs/calibration.yaml") -> CalibrationConfig:
    """Load calibration config from YAML file.

    Returns:
        Populated CalibrationConfig instance.
    """
    p = Path(path)
    if not p.exists():
        return CalibrationConfig()

    with open(p, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    if raw is None:
        return CalibrationConfig()

    cfg = raw.get("calibration", raw)
    return CalibrationConfig(
        demand_factor=float(cfg.get("demand_factor", 1.0)),
        fare_factor=float(cfg.get("fare_factor", 0.80)),
        travel_time_factor=float(cfg.get("travel_time_factor", 1.0)),
        reward_factor=float(cfg.get("reward_factor", 0.80)),
        demand_offset=float(cfg.get("demand_offset", 0.0)),
        fare_offset=float(cfg.get("fare_offset", 0.0)),
        use_per_zone=bool(cfg.get("use_per_zone", False)),
        zone_factors_path=cfg.get("zone_factors_path"),
        source=str(cfg.get("source", "default")),
        calibration_date=str(cfg.get("calibration_date", "")),
    )


def calibrate_demand(base_demand: float, config: CalibrationConfig | None = None) -> float:
    """Calibrate demand value using config factor and offset."""
    c = config or CalibrationConfig()
    return max(0.0, base_demand * c.demand_factor + c.demand_offset)


def calibrate_fare(base_fare: float, config: CalibrationConfig | None = None) -> float:
    """Calibrate fare value."""
    c = config or CalibrationConfig()
    return max(0.0, base_fare * c.fare_factor + c.fare_offset)


def calibrate_travel_time(base_time: float, config: CalibrationConfig | None = None) -> float:
    """Calibrate travel time value."""
    c = config or CalibrationConfig()
    return max(1.0, base_time * c.travel_time_factor)


def calibrate_reward(simulator_reward: float, config: CalibrationConfig | None = None) -> float:
    """Convert simulator reward to calibrated (real-world equivalent) reward.

    Returns:
        Calibrated reward value.
    """
    c = config or CalibrationConfig()
    return simulator_reward * c.reward_factor


def calibrate_v2_to_v1(v2_revenue: float) -> float:
    """Convert v2 simulator revenue to estimated v1-equivalent (backward compat)."""
    return calibrate_reward(v2_revenue)


def calibrate_v1_to_v2(v1_revenue: float) -> float:
    """Convert v1 revenue to estimated v2-equivalent (backward compat)."""
    c = load_calibration_config()
    return v1_revenue / c.reward_factor if c.reward_factor > 0 else v1_revenue


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
        v2 = json.loads(v2_path.read_text(encoding="utf-8"))
        dqn = v2.get("dqn", {})
        v2_reward = dqn.get("avg_reward_per_driver", 0.0)
        results["v2_dqn_reward"] = v2_reward
        results["v2_double_dqn_reward"] = v2.get("double_dqn", {}).get("avg_reward_per_driver", 0.0)
        results["v2_iql_fqe"] = v2.get("iql", {}).get("avg_reward_per_driver", 0.0)
        results["v2_mf_single"] = v2.get("mean_field", {}).get("single_agent_reward", 0.0)
        results["v2_mf_multi"] = v2.get("mean_field", {}).get("multi_agent_reward", 0.0)

    if v1_path.exists():
        v1 = json.loads(v1_path.read_text(encoding="utf-8"))
        env = v1.get("environment", {})
        results["v1_reward_scale"] = env.get("reward_scale", 0.0)
        results["v1_driver_count"] = float(env.get("driver_count", 0))
        results["v1_demand_supply_ratio"] = env.get("demand_supply_ratio", 0.0)
        eval_data = v1.get("evaluation", {})
        results["v1_hot_zone_reward"] = eval_data.get("hot_zone", {}).get("avg_reward", 0.0)

    if "v2_dqn_reward" in results and "v1_hot_zone_reward" in results and results["v1_hot_zone_reward"] > 0:
        results["reward_factor"] = results["v1_hot_zone_reward"] / results["v2_dqn_reward"]
    else:
        results["reward_factor"] = CalibrationConfig().reward_factor

    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Simulator calibration tool")
    parser.add_argument("--config", type=Path, default=None, help="Calibration YAML config path")
    parser.add_argument("--output", type=Path, default=None, help="Output JSON path")
    args = parser.parse_args()

    if args.config:
        cfg = load_calibration_config(args.config)
        print(f"Loaded calibration config from {args.config}")
        print(f"  reward_factor={cfg.reward_factor}, demand_factor={cfg.demand_factor}")
        print(f"  fare_factor={cfg.fare_factor}, travel_time_factor={cfg.travel_time_factor}")

    results = run_calibration()
    output = json.dumps(results, indent=2)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output + "\n", encoding="utf-8")
        print(f"Calibration results written to {args.output}")
    else:
        print(output)


if __name__ == "__main__":
    main()
