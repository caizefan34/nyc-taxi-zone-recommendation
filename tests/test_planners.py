"""Tests for provider-backed planners (mocked provider — no real API calls).

These verify the planner contract and argument plumbing against a mocked
provider. They do NOT call a real LLM, and nothing here claims a live
provider was exercised (Rule: scientific honesty).
"""
from __future__ import annotations

import json
import sys
import types
from pathlib import Path
from unittest import mock

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.agents import MobilityAgent  # noqa: E402
from src.agents.llm_agent import _EchoPlanner  # noqa: E402
from src.agents.planners import (  # noqa: E402
    AnthropicPlanner,
    OpenAICompatiblePlanner,
    planner_from_env,
)


def _fake_anthropic_response(tool="forecast", arguments=None):
    """Minimal stand-in for an Anthropic messages API response."""
    block = mock.Mock()
    block.type = "tool_use"
    block.name = "run_mobility_tool"
    block.input = {"tool": tool, "arguments": arguments or {"zone_id": 132}}
    response = mock.Mock()
    response.content = [block]
    return response


def _patch_anthropic(response):
    """Install a fake `anthropic` module and patch the lazy import."""
    anthropic = mock.Mock()
    client = anthropic.Anthropic.return_value
    client.messages.create.return_value = response
    module = types.ModuleType("anthropic")
    module.Anthropic = anthropic.Anthropic
    return mock.patch.dict("sys.modules", {"anthropic": module})


class TestAnthropicPlanner:
    def test_requires_api_key(self):
        with mock.patch.dict("os.environ", {}, clear=False):
            with mock.patch("os.getenv", return_value=None):
                with pytest.raises(ValueError):
                    AnthropicPlanner(api_key=None)

    def test_missing_sdk_raises(self):
        with mock.patch.dict("sys.modules", {"anthropic": None}):
            with mock.patch("os.getenv", return_value="sk-test"):
                with pytest.raises(ImportError):
                    AnthropicPlanner(api_key="sk-test")

    def test_plans_from_tool_use_block(self):
        with _patch_anthropic(_fake_anthropic_response("forecast", {"zone_id": 132})):
            planner = AnthropicPlanner(api_key="sk-test")

            plan = planner.plan("what is zone 132 demand?", ("recommend", "forecast", "simulate", "evaluate"))

            assert plan == {"tool": "forecast", "arguments": {"zone_id": 132}}
            call_kwargs = planner._client.messages.create.call_args[1]
            assert call_kwargs["model"] == "claude-sonnet-5"
            assert call_kwargs["messages"][0]["content"] == "what is zone 132 demand?"
            assert any(t["function"]["name"] == "run_mobility_tool" for t in call_kwargs["tools"])

    def test_agent_runs_tool_from_provider_plan(self):
        with _patch_anthropic(_fake_anthropic_response("forecast", {"zone_id": 132})):
            planner = AnthropicPlanner(api_key="sk-test")

            agent = MobilityAgent(planner=planner.plan, model="claude-sonnet-5")
            turn = agent.handle("how busy is zone 132?")

            assert turn.dispatches[0]["tool"] == "forecast"
            assert turn.dispatches[0]["evaluation_type"] == "historical_replay"
            assert "Historical average" in turn.answer

    def test_unknown_tool_from_provider_raises(self):
        with _patch_anthropic(_fake_anthropic_response("nope")):
            planner = AnthropicPlanner(api_key="sk-test")
            with pytest.raises(ValueError):
                planner.plan("hi", ("recommend",))

    def test_no_tool_call_raises(self):
        with _patch_anthropic(mock.Mock(content=[mock.Mock(type="text", text="no tool here")])):
            planner = AnthropicPlanner(api_key="sk-test")
            with pytest.raises(ValueError):
                planner.plan("hi", ("recommend",))


class TestPlannerFromEnv:
    def test_echo_when_no_key(self):
        with mock.patch.dict("os.environ", {}, clear=True):
            planner = planner_from_env()
            assert planner.__self__.__class__ is _EchoPlanner

    def test_anthropic_when_key_set(self):
        with mock.patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-test"}, clear=True):
            module = types.ModuleType("anthropic")
            module.Anthropic = mock.Mock()
            with mock.patch.dict("sys.modules", {"anthropic": module}):
                planner = planner_from_env()
                assert isinstance(planner.__self__, AnthropicPlanner)

    def test_openai_when_anthropic_missing(self):
        with mock.patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test"}, clear=True):
            with mock.patch("urllib.request.urlopen"):
                planner = planner_from_env()
                assert isinstance(planner.__self__, OpenAICompatiblePlanner)

    def test_echo_agent_still_works_without_env(self):
        with mock.patch.dict("os.environ", {}, clear=True):
            agent = MobilityAgent()
            turn = agent.handle("recommend zone 161")
            assert turn.dispatches[0]["tool"] == "recommend"


class TestOpenAICompatiblePlanner:
    def test_requires_api_key(self):
        with mock.patch("os.getenv", return_value=None):
            with pytest.raises(ValueError):
                OpenAICompatiblePlanner(api_key=None)

    def test_plans_from_tool_calls(self):
        body = {
            "choices": [
                {
                    "message": {
                        "tool_calls": [
                            {
                                "function": {
                                    "name": "run_mobility_tool",
                                    "arguments": '{"tool": "evaluate", "arguments": {"model_name": "two_step"}}',
                                }
                            }
                        ]
                    }
                }
            ]
        }
        with mock.patch("urllib.request.urlopen") as urlopen:
            resp = mock.Mock()
            resp.read.return_value = json.dumps(body).encode("utf-8")
            urlopen.return_value.__enter__.return_value = resp
            planner = OpenAICompatiblePlanner(api_key="sk-test")
            plan = planner.plan("how is two_step?", ("recommend", "forecast", "simulate", "evaluate"))
            assert plan == {"tool": "evaluate", "arguments": {"model_name": "two_step"}}
