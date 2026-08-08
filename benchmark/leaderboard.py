"""Leaderboard generation for the Urban Mobility Benchmark.

Rebuilds `docs/leaderboard.md` from checked-in benchmark artifacts in
`outputs/*.json`. This is a deterministic aggregation over stored results —
it does NOT re-run models and does NOT fabricate metrics.

Canonical sources:
- `outputs/reference_metrics.json` — static diagnostics (NDCG@3, Hit@3, Utility@1)
  and 100-seed legacy single-driver daily fare for hot_zone / single_step / two_step.
- `outputs/multi_agent_benchmark.json` — 30-run multi-agent per-driver revenue/utilization.
- `outputs/rl_benchmark.json` — multi-seed RL policy per-driver revenue/utilization.
- `outputs/forecast_evaluation.json`, `outputs/graph_benchmark.json` — forecast MAE/RMSE.

All figures are SIMULATOR / HISTORICAL-REPLAY outcomes only.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def json_load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _num(value: Any, digits: int = 4, prefix: str = "") -> str:
    if value is None:
        return "—"
    try:
        f = float(value)
    except (TypeError, ValueError):
        return "—"
    if f != f:  # NaN
        return "—"
    return f"{prefix}{f:.{digits}f}"


def _load_reference(root: Path) -> dict[str, Any]:
    path = root / "outputs" / "reference_metrics.json"
    return json_load(path) if path.exists() else {}


def _reference_policy_rows(ref: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    static = ref.get("static") or {}
    rollout = ref.get("rollout") or {}
    fares = rollout.get("mean_daily_fare") or {}
    name_map = {
        "baseline_1": ("hot_zone", "Hot Zone"),
        "baseline_2": ("single_step", "Single-Step"),
        "two_step": ("two_step", "Two-Step Horizon"),
    }
    for key, (slug, label) in name_map.items():
        s = static.get(key) or {}
        rows.append({
            "model": slug, "label": label, "source": "reference_metrics (static + 100-seed rollout)",
            "ndcg": s.get("ndcg_at_3"), "hit": s.get("hit_at_3"),
            "utility": s.get("reference_two_step_utility_at_1"),
            "daily_fare": fares.get(key), "revenue_per_driver": None, "utilization": None,
            "kind": "policy",
        })
    return rows


def _load_json_any(root: Path, name: str) -> dict[str, Any]:
    path = root / "outputs" / name
    return json_load(path) if path.exists() else {}


def _multi_agent_policy_rows(root: Path) -> list[dict[str, Any]]:
    doc = _load_json_any(root, "multi_agent_benchmark.json")
    strategies = doc.get("strategies") or {}
    rows: list[dict[str, Any]] = []
    for slug in ("hot_zone", "single_step", "two_step"):
        entry = strategies.get(slug) or {}
        if not entry:
            continue
        rows.append({
            "model": slug, "label": {"hot_zone": "Hot Zone", "single_step": "Single-Step",
                                     "two_step": "Two-Step Horizon"}[slug],
            "source": "multi_agent_benchmark (finite-demand, 30 runs)",
            "ndcg": None, "hit": None, "utility": None, "daily_fare": None,
            "revenue_per_driver": entry.get("average_driver_revenue"),
            "utilization": entry.get("driver_utilization"), "kind": "policy",
        })
    return rows


def _rl_policy_rows(root: Path) -> list[dict[str, Any]]:
    doc = _load_json_any(root, "rl_benchmark.json")
    strategies = (doc.get("evaluation") or {}).get("strategies") or {}
    rows: list[dict[str, Any]] = []
    for slug in ("dqn", "double_dqn", "finite_horizon"):
        entry = strategies.get(slug) or {}
        if not entry:
            continue
        rows.append({
            "model": slug, "label": {"dqn": "DQN", "double_dqn": "Double DQN",
                                     "finite_horizon": "Finite Horizon"}[slug],
            "source": "rl_benchmark (multi-seed)",
            "ndcg": None, "hit": None, "utility": None, "daily_fare": None,
            "revenue_per_driver": entry.get("average_driver_revenue"),
            "utilization": entry.get("driver_utilization"), "kind": "policy",
        })
    return rows


def _forecast_rows(root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    fe = _load_json_any(root, "forecast_evaluation.json")
    demand = fe.get("demand") or {}
    rows.append({"model": "historical_average", "label": "Historical Average",
                 "mae": demand.get("historical_mae"), "rmse": demand.get("historical_rmse")})
    rows.append({"model": "lightgbm", "label": "LightGBM",
                 "mae": demand.get("lightgbm_mae"), "rmse": demand.get("lightgbm_rmse")})
    ensemble = fe.get("ensemble") or {}
    rows.append({"model": "ensemble", "label": "Ensemble (LGB+XGB)",
                 "mae": ensemble.get("demand_mae"), "rmse": None})

    graph = _load_json_any(root, "graph_benchmark.json")
    models = graph.get("models") or {}
    for slug, label in (("graphsage", "GraphSAGE"), ("gat", "GAT"), ("od_messages", "OD Messages")):
        entry = models.get(slug) or {}
        if entry:
            rows.append({"model": slug, "label": label,
                         "mae": entry.get("mae"), "rmse": None})

    return rows


def _render_policy(rows: list[dict[str, Any]]) -> str:
    lines = [
        "## Policy Leaderboard",
        "",
        "| Model | Endpoint | NDCG@3 | Hit@3 | Utility@1 | Daily Fare | Revenue/Driver | Utilization |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for r in rows:
        lines.append(
            f"| {r['label']} (`{r['model']}`) | {r['source']} | "
            f"{_num(r['ndcg'])} | {_num(r['hit'])} | {_num(r['utility'], 2)} | "
            f"{_num(r['daily_fare'], 2, '$')} | {_num(r['revenue_per_driver'], 2, '$')} | "
            f"{_num(r['utilization'])} |"
        )
    return "\n".join(lines)


def _render_forecast(rows: list[dict[str, Any]]) -> str:
    lines = ["## Forecast Leaderboard (held-out)", "", "| Model | MAE | RMSE |", "|---|---:|---:|"]
    for r in rows:
        lines.append(f"| {r['label']} (`{r['model']}`) | {_num(r['mae'])} | {_num(r['rmse'])} |")
    return "\n".join(lines)


def build_leaderboard_markdown(root: Path = ROOT) -> str:
    ref = _load_reference(root)
    policy_rows = (
        _reference_policy_rows(ref)
        + _multi_agent_policy_rows(root)
        + _rl_policy_rows(root)
    )
    forecast_rows = _forecast_rows(root)

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    header = f"""# Leaderboard

> Open Urban Mobility Benchmark — Public Leaderboard

**Evaluation type:** SIMULATOR / HISTORICAL-REPLAY only. These are not production
revenue estimates and no real-world A/B results are reported.

_Regenerated: {now} by `python benchmark/run.py --leaderboard`_

## Scope & Honesty Statement

- All numbers below are extracted from checked-in benchmark artifacts in `outputs/`.
- **Endpoints are not comparable across rows**: NDCG@3/Hit@3/Utility@1 come from a
  3,360-query static diagnostic; Daily Fare from a 100-seed legacy single-driver rollout;
  Revenue/Driver + Utilization from the finite-demand multi-agent simulator. Do not rank
  across endpoints.
- No production revenue, deployment, or real-world A/B evidence exists in this repository.
"""

    sections = [
        header,
        _render_policy(policy_rows),
        "",
        _render_forecast(forecast_rows),
        "",
        "## External Submissions",
        "",
        "> No external submissions yet. See `docs/external_contribution.md` to submit a model.",
        "",
        "## How to Regenerate",
        "",
        "```bash",
        "python benchmark/run.py --leaderboard",
        "```",
        "",
    ]
    return "\n".join(sections)


if __name__ == "__main__":
    md = build_leaderboard_markdown()
    out = ROOT / "docs" / "leaderboard.md"
    out.write_text(md, encoding="utf-8")
    print(f"leaderboard written to {out}")
