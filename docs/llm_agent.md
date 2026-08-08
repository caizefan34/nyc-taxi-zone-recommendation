# LLM Mobility Agent (Scaffold)

> **Status:** Scaffold / reference implementation — `echo` mode, no model
> provider, no API key required. Ready to be wired to a real LLM backend.

## What it is

A **tool-using conversational layer** over the decision platform. The agent
does **not** make decisions — the platform's policies do. The agent renders,
explains, and answers operational questions by calling platform tools:

| Tool | What it runs | Evaluation type |
|---|---|---|
| `recommend` | Decision engine → `Two-Step Horizon` policy | simulation |
| `forecast` | Historical-average demand estimate | historical replay |
| `simulate` | Finite-demand multi-agent simulator rollout | simulation |
| `evaluate` | Stored benchmark / shadow-evaluation artifacts | offline |

## Design

- `src/agents/llm_agent.py` — `MobilityAgent` + `_EchoPlanner`.
- `src/agents/__init__.py` — public exports.
- `tests/test_llm_agent.py` — 11 tests, no network, no API key.

The default `_EchoPlanner` requires **no model provider**: it echoes the tool
the prompt mentions and the platform tool executes it. This keeps the scaffold
deterministic and testable while leaving a clean seam — replace
`planner=...` with a model-backed planner and the tools stay untouched.

## Honesty contract

Every tool call returns a labeled `evaluation_type` (`simulation`,
`historical_replay`, `offline`). The agent's answer cites tool output verbatim
and never fabricates metrics. Nothing produced here is production or A/B
evidence.

## Wire to a real LLM

1. Implement `planner(prompt, tool_names) -> {"tool": str, "arguments": dict}`
   that calls your provider (OpenAI/Anthropic/local) with the tool schema.
2. Pass it to `MobilityAgent(planner=...)`.
3. Run `agent.handle(prompt)` and stream `turn.answer`.

## Run

```bash
python -c "from src.agents import MobilityAgent; a = MobilityAgent(); print(a.handle('simulate two_step').answer)"
```
