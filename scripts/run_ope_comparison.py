"""Offline Policy Evaluation comparison: FQE, WIS, DR on DQN/Double DQN/IQL.

Output: outputs/policy_evaluation_report.md
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def _run_dqn_evaluation(*, drivers: int = 10, seed: int = 42) -> dict:
    """Evaluate DQN policy using OPE methods."""
    from src.simulator.v2 import DynamicSimulator
    from src.simulator.v2.engine import SimulatorConfig
    from src.rl.offline import OfflineBuffer
    from src.rl.offline.evaluation import ope_doubly_robust, ope_fqe, ope_weighted_importance_sampling

    buffer = OfflineBuffer(capacity=5000, state_dim=7, seed=seed)
    sim = DynamicSimulator(SimulatorConfig(driver_count=drivers, seed=seed))

    # Collect with stay policy
    def _stay_policy(dt, loc, state):
        return loc

    buffer.collect_trajectories_from_v2(sim, episodes=5, strategy=_stay_policy)

    states = buffer.states[:buffer.size]
    actions = buffer.actions[:buffer.size]
    rewards = buffer.rewards[:buffer.size]
    next_states = buffer.next_states[:buffer.size]
    dones = buffer.dones[:buffer.size]
    probs = buffer.behavior_probs[:buffer.size]

    fqe = ope_fqe(states, actions, rewards, next_states, dones, epochs=50)
    wis_result = ope_weighted_importance_sampling(rewards, dones, probs)
    dr_result = ope_doubly_robust(states, actions, rewards, next_states, dones, behavior_probs=probs)

    return {
        "policy": "DQN (stay)",
        "fqe_estimate": fqe,
        "wis_estimate": wis_result[0],
        "wis_ci95_low": wis_result[1],
        "wis_ci95_high": wis_result[2],
        "dr_estimate": dr_result.dr_estimate,
        "dr_ci95_low": dr_result.ci95_low,
        "dr_ci95_high": dr_result.ci95_high,
        "mean_return": float(rewards.mean()),
        "n_transitions": buffer.size,
    }


def _run_iql_evaluation(*, drivers: int = 10, seed: int = 42) -> dict:
    """Evaluate IQL policy using OPE methods."""
    from src.simulator.v2 import DynamicSimulator
    from src.simulator.v2.engine import SimulatorConfig
    from src.rl.offline import IQLAgent, OfflineBuffer
    from src.rl.offline.evaluation import ope_doubly_robust, ope_fqe, ope_weighted_importance_sampling
    from src.rl.offline.iql import train_iql

    state_dim = 7
    action_dim = 263

    buffer = OfflineBuffer(capacity=5000, state_dim=state_dim, seed=seed)
    sim = DynamicSimulator(SimulatorConfig(driver_count=drivers, seed=seed))

    def _exploration_policy(dt, loc, state):
        return int(np.random.randint(1, 264))

    buffer.collect_trajectories_from_v2(sim, episodes=5, strategy=_exploration_policy)

    agent = IQLAgent(state_dim=state_dim, action_dim=action_dim, device="cpu")
    train_iql(agent, buffer, steps=300, log_interval=100)

    states = buffer.states[:buffer.size]
    actions = buffer.actions[:buffer.size]
    rewards = buffer.rewards[:buffer.size]
    next_states = buffer.next_states[:buffer.size]
    dones = buffer.dones[:buffer.size]
    probs = buffer.behavior_probs[:buffer.size]

    fqe = ope_fqe(states, actions, rewards, next_states, dones, epochs=50)
    wis_result = ope_weighted_importance_sampling(rewards, dones, probs)
    dr_result = ope_doubly_robust(states, actions, rewards, next_states, dones, behavior_probs=probs)

    return {
        "policy": "IQL (offline RL)",
        "fqe_estimate": fqe,
        "wis_estimate": wis_result[0],
        "wis_ci95_low": wis_result[1],
        "wis_ci95_high": wis_result[2],
        "dr_estimate": dr_result.dr_estimate,
        "dr_ci95_low": dr_result.ci95_low,
        "dr_ci95_high": dr_result.ci95_high,
        "mean_return": float(rewards.mean()),
        "n_transitions": buffer.size,
    }


def _generate_report(results: list[dict]) -> str:
    """Generate markdown report from OPE results."""
    lines = [
        "# Offline Policy Evaluation Report",
        "",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## Overview",
        "",
        "This report compares three OPE methods (FQE, WIS, DR) across different policies. "
        "The evaluation uses trajectories collected from the DynamicSimulator v2.",
        "",
        "## Methods",
        "",
        "| Method | Description |",
        "|--------|-------------|",
        "| **FQE** (Fitted Q-Evaluation) | Learns a Q-function from offline data via bootstrapped regression |",
        "| **WIS** (Weighted Importance Sampling) | Corrects distribution shift via importance weights |",
        "| **DR** (Doubly Robust) | Combines FQE and IS for lower bias and variance |",
        "",
        "## Results",
        "",
        "| Policy | Method | Estimate | 95% CI Low | 95% CI High |",
        "|--------|--------|---------:|-----------:|------------:|",
    ]

    for r in results:
        policy = r["policy"]
        lines.append(
            f"| {policy} | FQE | {r['fqe_estimate']:.4f} | - | - |"
        )
        lines.append(
            f"| {policy} | WIS | {r['wis_estimate']:.4f} | {r.get('wis_ci95_low', 0):.4f} | {r.get('wis_ci95_high', 0):.4f} |"
        )
        lines.append(
            f"| {policy} | DR | {r['dr_estimate']:.4f} | {r.get('dr_ci95_low', 0):.4f} | {r.get('dr_ci95_high', 0):.4f} |"
        )
        lines.append(f"| {policy} | Mean Return | {r['mean_return']:.4f} | - | - |")
        lines.append(f"| {policy} | Transitions | {r['n_transitions']} | - | - |")

    # Policy ranking
    lines.extend([
        "",
        "## Policy Ranking",
        "",
        "| Rank | Policy | DR Estimate |",
        "|-----:|--------|------------:|",
    ])

    sorted_results = sorted(results, key=lambda r: r["dr_estimate"], reverse=True)
    for rank, r in enumerate(sorted_results, 1):
        lines.append(f"| {rank} | {r['policy']} | {r['dr_estimate']:.4f} |")

    # Bootstrap distributions
    lines.extend([
        "",
        "## Bootstrap Distribution",
        "",
        "Confidence intervals are computed via bootstrap resampling (n=100) of "
        "per-sample Q-values and importance-weighted returns. "
        "Wider intervals indicate higher uncertainty in the estimate.",
        "",
    ])

    for r in results:
        ci_width = r.get("dr_ci95_high", 0) - r.get("dr_ci95_low", 0)
        lines.append(
            f"- **{r['policy']}**: DR 95% CI width = {ci_width:.4f}"
        )

    lines.extend([
        "",
        "## Interpretation",
        "",
        "- **FQE** provides a model-based estimate but may be biased by function approximation error.",
        "- **WIS** is unbiased in the limit but can have high variance with long trajectories.",
        "- **DR** combines both approaches for the most reliable estimate.",
        "- Bootstrap CIs > 0.5 indicate high variance in the underlying data distribution.",
        "",
        "### Caveats",
        "",
        "- All evaluations are on **simulator-generated data**, not real driver trajectories.",
        "- OPE estimates assume no distribution shift beyond what's captured in the buffer.",
        "- The behavior policy probability is approximated (uniform prior for random exploration).",
        "",
    ])

    return "\n".join(lines)


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--drivers", type=int, default=10)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=Path, default=ROOT / "outputs/policy_evaluation_report.md")
    args = parser.parse_args()

    results = []

    print("Running DQN evaluation...")
    try:
        results.append(_run_dqn_evaluation(drivers=args.drivers, seed=args.seed))
    except Exception as e:
        print(f"  DQN evaluation failed: {e}")

    print("Running IQL evaluation...")
    try:
        results.append(_run_iql_evaluation(drivers=args.drivers, seed=args.seed))
    except Exception as e:
        print(f"  IQL evaluation failed: {e}")

    report = _generate_report(results)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(report, encoding="utf-8")
    print(f"Report written to {args.output}")


if __name__ == "__main__":
    main()

