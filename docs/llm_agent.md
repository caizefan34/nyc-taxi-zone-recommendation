# LLM Mobility Agent

> **Status:** Operational. Provider-backed planners are implemented and tested
> (mocked provider — no live calls in CI). Runs in deterministic `echo` mode
> by default; set one environment variable to use a real LLM.

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
- `src/agents/planners.py` — provider-backed planners + `planner_from_env`.
- `src/agents/__init__.py` — public exports.
- `tests/test_llm_agent.py` — 11 tests, no network, no API key.
- `tests/test_planners.py` — 12 tests against a mocked provider (no live calls).

Every planner speaks the same seam: `planner(prompt, tool_names) -> {"tool":
str, "arguments": dict}`. The tools stay untouched when swapping planners.

## Honesty contract

Every tool call returns a labeled `evaluation_type` (`simulation`,
`historical_replay`, `offline`). The agent's answer cites tool output verbatim
and never fabricates metrics. Nothing produced here is production or A/B
evidence.

## Providers

| Planner | SDK / transport | Model |
|---|---|---|
| `AnthropicPlanner` | `anthropic` (optional extra `.[agent]`) | `claude-sonnet-5` |
| `OpenAICompatiblePlanner` | `urllib` (no SDK — works with OpenAI, vLLM, Ollama) | `gpt-4o-mini` |

Provider SDKs are imported lazily, so echo mode stays dependency-free.
Planners never fall back silently: without a key they raise, and
`planner_from_env()` is the intended "flip by env var" entry point.

## Wire a provider

Set one environment variable — no code change:

```bash
# Preferred: Anthropic
export ANTHROPIC_API_KEY=sk-...
python -c "from src.agents import MobilityAgent, planner_from_env; \
print(MobilityAgent(planner=planner_from_env(), model='claude-sonnet-5').handle('simulate two_step 20 drivers').answer)"
```

```bash
# Or any OpenAI-compatible endpoint (OpenAI, vLLM, Ollama...)
export OPENAI_API_KEY=sk-...
```

Without either key the agent runs in deterministic `echo` mode.

## Run

```bash
python -c "from src.agents import MobilityAgent; a = MobilityAgent(); print(a.handle('simulate two_step').answer)"
```
