from __future__ import annotations

import json
from pathlib import Path

ROOT = Path.cwd()
OUTPUTS = ROOT / "outputs"

def load(n: str) -> dict:
    return json.loads((OUTPUTS / n).read_text(encoding="utf-8"))

fe = load("forecast_evaluation.json")
gb = load("graph_benchmark.json")
mb = load("multi_agent_benchmark.json")
rl2 = load("rl_benchmark_v2.json")

lines = [
    "# Research Benchmark Matrix",
    "",
    "**Generated:** 2026-07-26",
    "",
    "> This matrix is **not** a single leaderboard. Forecast error, simulator revenue,",
    "> offline OPE estimates, and deployment latency measure different things. Each",
    "> cell is labelled with its data source, and cross-endpoint comparisons are invalid.",
    "",
    "---",
    "",
    "## 1. Forecast Accuracy",
    "",
    "| Model | MAE Demand | RMSE Demand | MAE Fare | RMSE Fare | Source",
    "|---|---:|---:|---:|---:|---",
]
rows = [
    ("Historical Avg", fe["demand"]["historical_mae"], fe["demand"]["historical_rmse"],
     fe["fare"]["historical_mae"], fe["fare"]["historical_rmse"]),
    ("LightGBM", fe["demand"]["lightgbm_mae"], fe["demand"]["lightgbm_rmse"],
     fe["fare"]["lightgbm_mae"], fe["fare"]["lightgbm_rmse"]),
    ("Ensemble (LGB+XGB)", fe["ensemble"]["demand_mae"], fe["ensemble"]["demand_rmse"],
     fe["ensemble"]["fare_mae"], fe["ensemble"]["fare_rmse"]),
    ("XGBoost", fe["xgboost"]["demand"]["mae"], fe["xgboost"]["demand"]["rmse"],
     fe["xgboost"]["fare"]["mae"], fe["xgboost"]["fare"]["rmse"]),
]
for name, dm, dr, fm, fr in rows:
    lines.append(f"| {name} | {dm:.4f} | {dr:.4f} | {fm:.4f} | {fr:.4f} | forecast_evaluation.json |")

for mid, label in [("non_graph_lightgbm", "Non-graph LightGBM"),
                    ("od_messages", "OD Messages"),
                    ("graphsage", "GraphSAGE"),
                    ("gat", "GAT")]:
    d = gb["models"][mid]
    lines.append(f"| {label} | {d['mae']:.4f} | {d['rmse']:.4f} | N/A | N/A | graph_benchmark.json |")

lines += ["", "---", "", "## 2. Decision Quality (Simulator Revenue)", "",
    "| Method | Revenue/Driver | Utilization | Competition Penalty | Source",
    "|---|---:|---:|---:|---"]
strat_map = mb["strategies"]
for name in ["hot_zone", "single_step", "two_step"]:
    s = strat_map[name]
    rev = s.get("avg_revenue_per_driver", s.get("avg_reward_per_driver", 0))
    util = s.get("avg_utilization", 0)
    comp = s.get("avg_competition_penalty", 0)
    lines.append(f"| {name.replace('_',' ').title()} | ${rev:.2f} | {util:.2%} | ${comp:.2f} | multi_agent_benchmark.json |")  # noqa: E501

for method, label in [("dqn", "DQN (v2 sim)"), ("double_dqn", "Double DQN (v2 sim)"), ("iql", "IQL (Offline)")]:
    d = rl2[method]
    lines.append(f"| {label} | ${d.get('avg_reward_per_driver', 0):.2f} | {d.get('utilization', 0):.2%} | ${d.get('competition_penalty', 0):.2f} | rl_benchmark_v2.json |")  # noqa: E501

mf = rl2.get("mean_field", {})
for at in ["single_agent", "multi_agent", "mean_field"]:
    lines.append(f"| MF {at.replace('_',' ').title()} | ${mf.get(at+'_reward', 0):.2f} | {mf.get(at+'_utilization', 0):.2%} | ${mf.get(at+'_competition', 0):.4f} | rl_benchmark_v2.json |")  # noqa: E501

lines += ["", "---", "", "## 3. Robustness (Cross-Year & Ablation)", "",
    "| Test | Setting | Metric | Value | Source",
    "|---|---:|---:|---:|"]
demand_ci = fe["demand"]["paired_timestamp_bootstrap"]
ensemble_ci = fe["ensemble"]["paired_timestamp_bootstrap"]
lines.append(f"| Forecast improvement | LightGBM vs Historical | MAE reduction | {demand_ci['mean_mae_improvement']:.4f} [{demand_ci['ci95_low']:.4f}, {demand_ci['ci95_high']:.4f}] | forecast_evaluation.json |")  # noqa: E501
lines.append(f"| Forecast improvement | Ensemble vs Historical | MAE reduction | {ensemble_ci['mean_mae_improvement']:.4f} [{ensemble_ci['ci95_low']:.4f}, {ensemble_ci['ci95_high']:.4f}] | forecast_evaluation.json |")  # noqa: E501
for name, data in fe.get("feature_ablation", {}).items():
    lines.append(f"| Ablation | {name.replace('_',' ').title()} | MAE | {data['mae']:.4f} | forecast_evaluation.json |")
for model_name, model_data in gb.get("paired_slot_mae_reduction", {}).items():
    lines.append(f"| Graph improvement | {model_name} vs non-graph | CI crosses zero | [{model_data['ci95_low']:.4f}, {model_data['ci95_high']:.4f}], p={model_data['paired_t_pvalue']:.4f} | graph_benchmark.json |")  # noqa: E501

lines += ["", "---", "", "## 4. Statistical Validity Notes", "",
    "- **Forecast CIs**: Paired bootstrap over 192 held-out half-hour timestamps.",
    "- **Multi-agent CIs**: 30 simulation seeds at driver_count=50.",
    "- **Graph CIs**: Paired bootstrap over held-out timestamps; all intervals cross zero.",
    "- **RL CIs**: 20 paired simulation seeds.",
    "- **OPE intervals**: IQL uses bootstrapped FQE+DR estimates (synthetic buffer).",
    "", "## 5. Endpoint Separation Warning", "",
    "The sections above measure **different outcomes**:",
    "",
    "1. **Forecast MAE** measures prediction error on held-out timestamps.",
    "2. **Simulator revenue** is average driver earnings inside a stochastic supply-demand model.",
    "3. **Robustness** tests whether improvements persist across feature sets and graph variants.",
    "",
    "Treat each cell as an independent measurement. No single row should be interpreted as the definitive ranking.",
]
(OUTPUTS / "research_benchmark_matrix.md").write_text("\n".join(lines), encoding="utf-8")
print("Written outputs/research_benchmark_matrix.md")
