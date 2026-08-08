"""Provider-backed planners for the mobility agent.

The default ``_EchoPlanner`` needs no model API. These planners drive a real
LLM provider through the same ``planner(prompt, tool_names) -> {"tool": str,
"arguments": dict}`` seam, so the agent's tools stay untouched.

Provider libraries are imported lazily inside each planner so that importing
this module never requires an API key or an installed SDK when the caller only
uses echo mode.
"""
from __future__ import annotations

import json
import os
from typing import Callable, Optional

from src.agents.llm_agent import TOOL_NAMES, _EchoPlanner

_PROVIDER_MISSING = (
    "Provider SDK '{lib}' is not installed. Install the optional extra "
    "('pip install -e \".[agent]\"') or use the default echo planner."
)


def _tool_schema() -> dict:
    """JSON schema describing the agent's tools (for provider tool-calling)."""
    return {
        "type": "function",
        "function": {
            "name": "run_mobility_tool",
            "description": (
                "Run one platform tool: recommend / forecast / simulate / evaluate. "
                "Every result is simulator or offline evidence, never production."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "tool": {"type": "string", "enum": list(TOOL_NAMES)},
                    "arguments": {"type": "object", "description": "Tool arguments (see platform docs)."},
                },
                "required": ["tool", "arguments"],
            },
        },
    }


class AnthropicPlanner:
    """Planner backed by the Anthropic API (tool-calling).

    Args:
        api_key: Anthropic API key. Defaults to the ANTHROPIC_API_KEY env var.
        model: Model name, e.g. ``claude-sonnet-5``.
        max_tokens: Cap on the model's tool-call JSON.
        timeout_seconds: Request timeout.

    The planner sends the user prompt plus the tool schema and returns the
    model's tool call. Without a valid key/sdk the SDK raises; callers should
    fall back to ``planner_from_env`` for a graceful echo-mode default.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-sonnet-5",
        max_tokens: int = 512,
        timeout_seconds: float = 60.0,
    ):
        self.model = model
        self.max_tokens = max_tokens
        self.timeout_seconds = timeout_seconds
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("AnthropicPlanner requires an API key (argument or ANTHROPIC_API_KEY env var)")
        try:
            from anthropic import Anthropic  # lazy import: SDK is optional
        except ImportError as exc:
            raise ImportError(_PROVIDER_MISSING.format(lib="anthropic")) from exc
        self._client = Anthropic(api_key=self.api_key)

    def plan(self, prompt: str, tool_names: tuple[str, ...]) -> dict:
        response = self._client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            timeout=self.timeout_seconds,
            system=(
                "You are a mobility operations assistant. Call the tool that best "
                "answers the user's question. Answer in the user's language. Never "
                "invent metrics; the tool output is the only evidence."
            ),
            tools=[_tool_schema()],
            messages=[{"role": "user", "content": prompt}],
        )
        for block in response.content:
            if getattr(block, "type", None) == "tool_use" and block.name == "run_mobility_tool":
                tool = block.input.get("tool")
                if tool not in tool_names:
                    raise ValueError(f"Provider returned unknown tool '{tool}'. Use one of {tool_names}")
                return {"tool": tool, "arguments": block.input.get("arguments") or {}}
        raise ValueError("Provider returned no tool call for this prompt")


class OpenAICompatiblePlanner:
    """Planner for any OpenAI-compatible chat-completions endpoint.

    Uses the built-in ``json`` module, so it works with OpenAI, local OpenAI-
    compatible servers (vLLM, Ollama), and proxies without extra SDKs.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.openai.com/v1",
        model: str = "gpt-4o-mini",
        timeout_seconds: float = 60.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds
        self._api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self._api_key:
            raise ValueError("OpenAICompatiblePlanner requires an API key (argument or OPENAI_API_KEY env var)")

    def plan(self, prompt: str, tool_names: tuple[str, ...]) -> dict:
        import urllib.request

        payload = json.dumps(
            {
                "model": self.model,
                "tools": [_tool_schema()],
                "tool_choice": "auto",
                "messages": [
                    {"role": "system", "content": (
                        "You are a mobility operations assistant. Call the tool that "
                        "best answers the user's question. Never invent metrics."
                    )},
                    {"role": "user", "content": prompt},
                ],
            }
        ).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self._api_key}",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=self.timeout_seconds) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        for choice in body.get("choices", []):
            for msg in choice.get("message", {}).get("tool_calls", []):
                fn = msg.get("function") or {}
                if fn.get("name") == "run_mobility_tool":
                    call = json.loads(fn.get("arguments") or "{}")
                    tool = call.get("tool")
                    if tool not in tool_names:
                        raise ValueError(f"Provider returned unknown tool '{tool}'. Use one of {tool_names}")
                    return {"tool": tool, "arguments": call.get("arguments") or {}}
        raise ValueError("Provider returned no tool call for this prompt")


def planner_from_env() -> Callable[[str, tuple[str, ...]], dict]:
    """Return a provider-backed planner if a key is configured, else echo mode.

    Resolution order:
    1. ``ANTHROPIC_API_KEY`` set  -> ``AnthropicPlanner``
    2. ``OPENAI_API_KEY`` set     -> ``OpenAICompatiblePlanner`` (OpenAI endpoint)
    3. otherwise                  -> ``_EchoPlanner`` (no provider, deterministic)

    This lets a deployment start in echo mode and flip to a real provider by
    setting one environment variable — no code change.
    """
    if os.getenv("ANTHROPIC_API_KEY"):
        return AnthropicPlanner().plan
    if os.getenv("OPENAI_API_KEY"):
        return OpenAICompatiblePlanner().plan
    return _EchoPlanner().plan
