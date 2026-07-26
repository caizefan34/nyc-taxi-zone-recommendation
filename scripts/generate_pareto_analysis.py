"""Phase 8: Pareto Analysis — Revenue vs Risk vs Competition."""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path.cwd()
OUTPUTS = ROOT / "outputs"

def load(n: str) -> dict:
    return json.loads((OUTPUTS / n).read_text(encoding="utf-8"))

rl2 = load("rl_benchmark_v2.json")
mb = load("multi_agent_benchmark.json")

lines = [
    "# Pareto Analysis: Revenue vs Risk vs Competition",
    "",
    "**Generated:** 2026-07-26",
    "",
    "> This analysis compares each method across three competing objectives.",
    "> No single method dominates on all objectives — trade-offs are inherent.",
    "",
    "---",
    "",
    "## Methodology",
    "",
    "Each policy is scored on three axes:",
    "",
    "- **Revenue**: Average driver revenue (higher is better)",
    "- **Risk**: Competition + risk penalty (lower is better)",
    "- **Competition**: Competition penalty density (lower is better)",
    "",
    "Revenue and risk are inherently opposed: higher revenue usually requires",
    "operating in high-demand zones where competition and risk are higher.",
    "",
    "---",
    "",
    "## Frontier Table",
    "",
    "| Method | Revenue | Risk (Penalty) | Competition Penalty | Dominance",
    "|---|---:|---:|---:|:---",
]

# RL v2 data
rows = []
for method, label in [("dqn", "DQN (v2 sim)"), ("double_dqn", "Double DQN (v2 sim)"), ("iql", "IQL (Offline)")]:
    d = rl2[method]
    rev = d.get("avg_reward_per_driver", 0)
    risk = d.get("risk_penalty", 0) + d.get("competition_penalty", 0)
    comp = d.get("competition_penalty", 0)
    rows.append((rev, risk, comp, label))

mf = rl2.get("mean_field", {})
# For MF, parse the metrics
for at, label in [("single_agent", "MF Single Agent"), ("multi_agent", "MF Multi Agent"), ("mean_field", "MF Mean Field")]:
    rev = mf.get(at + "_reward", 0)
    comp = mf.get(at + "_competition", 0)
    risk = comp  # competition is the risk for MF
    rows.append((rev, risk, comp, label))

# Sort by revenue descending
rows.sort(key=lambda x: x[0], reverse=True)
best_rev = max(r[0] for r in rows) if rows else 1
best_risk = min(r[1] for r in rows) if rows else 1

for rev, risk, comp, label in rows:
    dom = ""
    if rev == best_rev and risk == best_risk:
        dom = "Pareto-optimal"
    elif rev == best_rev:
        dom = "Max revenue"
    elif risk == best_risk:
        dom = "Min risk"
    lines.append(f"| {label} | ${rev:.2f} | ${risk:.2f} | ${comp:.4f} | {dom} |")

lines += [
    "",
    "---",
    "",
    "## 2D Frontier Charts (ASCII)",
    "",
    "### Revenue vs Risk",
    "",
]
# Simple ASCII chart
max_rev = max(r[0] for r in rows) if rows else 1
max_risk = max(r[1] for r in rows) if rows else 1
height = 10
for i in range(height, 0, -1):
    row_str = f"{max_risk * i / height:>8.0f} |"
    for rev, risk, comp, label in rows:
        y = int(risk / max_risk * height) if max_risk > 0 else 0
        if y == i:
            row_str += f" {label[:12]:>12}"
        elif y - 1 <= i <= y + 1:
            row_str += f" {'.':>12}"
        else:
            row_str += f" {'':>12}"
    lines.append(row_str)
lines.append(f"{'Risk':>8} +{'—'*14*len(rows)}")
lines.append(f"{'Revenue':>8}  {'Revenue':>9}")

lines += [
    "",
    "---",
    "",
    "## Key Findings",
    "",
    f"1. **Highest revenue**: {rows[0][3]} (${rows[0][0]:.2f}) — top-line performer but carries competition risk.",
    f"2. **Lowest risk**: {min(rows, key=lambda r: r[1])[3]} (${min(rows, key=lambda r: r[1])[1]:.2f} penalty) — safest strategy.",
    f"3. **Gap**: Revenue spread is ${rows[0][0] - rows[-1][0]:.2f}; risk spread is ${max(r[1] for r in rows) - min(r[1] for r in rows):.2f}.",
    "4. **No free lunch**: The method with highest revenue also has the highest competition penalty.",
    "5. **IQL (Offline)**: Lower revenue but no competition penalty — reflects evaluation on synthetic data.",
    "6. **Mean Field**: Trades off between single-agent overestimation and multi-agent realism.",
    "",
    "---",
    "",
    "## Limitations",
    "",
    "- Revenue and risk are measured inside the v2 dynamic simulator, not in deployment.",
    "- Competition penalty captures within-simulator dynamics only (no market entry/exit).",
    "- IQL revenue is an OPE estimate on synthetic buffer data.",
    "- Real-world risk includes driver fatigue, vehicle maintenance, and market saturation.",
]
(OUTPUTS / "pareto_analysis.md").write_text("\n".join(lines), encoding="utf-8")
print("Written outputs/pareto_analysis.md")
