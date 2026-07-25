"""Build the checked-in metrics snapshot and Markdown report from experiment artifacts."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = ROOT / "outputs"


def _read(name: str):
    path = OUTPUTS / name
    if not path.exists():
        raise FileNotFoundError(
            f"Missing {path}. Run the corresponding evaluation target before generating the report."
        )
    return json.loads(path.read_text(encoding="utf-8"))


def build_snapshot() -> dict[str, object]:
    static = {
        "baseline_1": _read("audit_b1_static.json"),
        "baseline_2": _read("audit_b2_static.json"),
        "two_step": _read("audit_improved_static.json"),
    }
    paired = _read("paired_rollout_audit.json")
    horizon = _read("horizon_audit.json")
    evidence = _read("research_audit_evidence.json")
    robustness = _read("robustness_audit.json")
    parameters = _read("parameter_selection.json")
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "static": static,
        "rollout": {
            "runs": paired["runs"],
            "base_seed": paired["base_seed"],
            "mean_daily_fare": {
                name: sum(values) / len(values)
                for name, values in paired["daily_fares"].items()
            },
            "comparisons": paired["comparisons"],
        },
        "horizon": horizon,
        "fairness": evidence["fairness"],
        "counterfactual_identifiability": evidence["counterfactual_identifiability"],
        "robustness": robustness,
        "parameter_selection": parameters,
    }


def render(snapshot: dict[str, object]) -> str:
    static = snapshot["static"]
    rollout = snapshot["rollout"]
    fairness = snapshot["fairness"]
    comparisons = rollout["comparisons"]
    horizon = snapshot["horizon"]
    parameters = snapshot["parameter_selection"]
    lines = [
        "# Reproducible Evaluation Report",
        "",
        f"> Generated from machine-readable artifacts at `{snapshot['generated_at']}`.",
        (
            "> Static metrics measure agreement with the public two-step reference objective; "
            "they are not counterfactual revenue estimates."
        ),
        "",
        "## Static diagnostic",
        "",
        "| Strategy | NDCG@3 | Hit@3 | Reference utility@1 | Mean latency (ms) |",
        "|---|---:|---:|---:|---:|",
    ]
    for key, label in (("baseline_1", "Baseline 1"), ("baseline_2", "Baseline 2"), ("two_step", "Two-step")):
        item = static[key]
        lines.append(
            f"| {label} | {item['ndcg_at_3']:.4f} | {item['hit_at_3']:.4f} | "
            f"{item['reference_two_step_utility_at_1']:.4f} | {item['average_recommend_time_ms']:.3f} |"
        )
    lines.extend(
        [
            "",
            "## Paired 100-seed rollout",
            "",
            "| Strategy | Mean daily fare |",
            "|---|---:|",
            f"| Baseline 1 | ${rollout['mean_daily_fare']['baseline_1']:.2f} |",
            f"| Baseline 2 | ${rollout['mean_daily_fare']['baseline_2']:.2f} |",
            f"| Two-step | ${rollout['mean_daily_fare']['two_step']:.2f} |",
            "",
            "| Comparison | Mean difference | Bootstrap 95% CI | Paired t p | Cohen dz |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for key, label in (
        ("two_step_vs_baseline_1", "Two-step - Baseline 1"),
        ("two_step_vs_baseline_2", "Two-step - Baseline 2"),
        ("baseline_2_vs_baseline_1", "Baseline 2 - Baseline 1"),
    ):
        item = comparisons[key]
        lines.append(
            f"| {label} | ${item['mean_difference']:.2f} | "
            f"[${item['ci95_low']:.2f}, ${item['ci95_high']:.2f}] | "
            f"{item['paired_t_pvalue']:.3g} | {item['cohen_dz']:.3f} |"
        )
    lines.extend(
        [
            "",
            "## Horizon comparison",
            "",
            "| Horizon | NDCG@3 | Hit@3 | Coverage | Mean daily fare | Query latency (ms) |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    for key in ("1", "2", "3", "5", "adaptive"):
        item = horizon[key]
        lines.append(
            f"| {key} | {item['static']['ndcg_at_3']:.4f} | {item['static']['hit_at_3']:.4f} | "
            f"{item['static']['coverage']:.2%} | ${item['rollout']['average_daily_fare']:.2f} | "
            f"{item['static']['average_recommend_time_ms']:.3f} |"
        )
    lines.extend(
        [
            "",
            "## Static parameter grid",
            "",
            (
                "The best public-reference configuration is shown for diagnostics only; "
                "the same public labels must not be treated as an untouched test set."
            ),
            "",
            "| Half-saturation | Gamma | Candidate pool | NDCG@3 | Hit@3 |",
            "|---:|---:|---:|---:|---:|",
            f"| {parameters[0]['pickup_half_saturation']:.0f} | {parameters[0]['gamma']:.2f} | "
            f"{parameters[0]['candidate_pool_size']} | {parameters[0]['ndcg_at_3']:.4f} | "
            f"{parameters[0]['hit_at_3']:.4f} |",
            "",
            "## Exposure concentration",
            "",
            "| Strategy | Coverage | Gini | Effective zones | Airport exposure | Premium-fare exposure |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    for key, label in (("baseline_1", "Baseline 1"), ("baseline_2", "Baseline 2"), ("two_step", "Two-step")):
        item = fairness[key]
        lines.append(
            f"| {label} | {item['coverage']:.2%} | {item['gini']:.3f} | "
            f"{item['effective_zone_count']:.2f} | {item['airport_exposure_share']:.2%} | "
            f"{item['premium_fare_zone_exposure_share']:.2%} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation boundary",
            "",
            (
                "The rollout is a fixed single-driver historical-market simulator. It does not model competing "
                "drivers, demand depletion, congestion, supply-demand feedback, or equilibrium. Its confidence "
                "intervals quantify Monte Carlo seed variation only."
            ),
            "",
            (
                "IPS, SNIPS, and doubly robust evaluation are not identifiable from the TLC trip table because "
                "logged recommendation actions and behavior propensities are absent."
            ),
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    snapshot = build_snapshot()
    (OUTPUTS / "reference_metrics.json").write_text(
        json.dumps(snapshot, indent=2) + "\n",
        encoding="utf-8",
    )
    (OUTPUTS / "evaluation_report.md").write_text(render(snapshot), encoding="utf-8")
    print("Wrote outputs/reference_metrics.json and outputs/evaluation_report.md")


if __name__ == "__main__":
    main()
