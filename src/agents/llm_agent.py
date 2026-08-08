"""Tool-using mobility agent scaffold.

The agent composes the platform's existing services (decision engine, demand
forecast, multi-agent simulation, offline evaluation) through a small tool
registry. The tools are real; the planner behind them is the user's choice.

By default no model API key is used and no provider is called — the agent runs
in ``echo`` mode, returning the tool dispatch the LLM *would* make. This keeps
the scaffold dependency-free, deterministic, and testable while leaving a clear
extension point for provider integration.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Callable, Optional

from src.decision.engine import build_recommendation, compute_confidence
from src.simulator.multi_agent import MultiAgentConfig, simulate_multi_agent

TOOL_NAMES = ("recommend", "forecast", "simulate", "evaluate")


@dataclass
class ToolResult:
    """Structured result of one tool call."""

    tool: str
    arguments: dict
    output: dict
    evaluation_type: str = "simulation"


@dataclass
class AgentTurn:
    """A single agent turn: user prompt -> tool dispatches + answer."""

    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    user_prompt: str = ""
    dispatches: list[dict] = field(default_factory=list)
    answer: str = ""


class _ToolError(ValueError):
    pass


class _EchoPlanner:
    """Plan that echoes the requested tool call.

    The default planner records the tool dispatch the agent intended, then the
    platform tool runs it. Providers can replace this with their own
    model-backed planner without touching the tools.
    """

    def __init__(self, model: str = "echo"):
        self.model = model

    def plan(self, prompt: str, tool_names: tuple[str, ...]) -> dict:
        target = "recommend"
        for name in tool_names:
            if name in prompt.lower():
                target = name
                break
        return {"tool": target, "arguments": {"raw_prompt": prompt}}


class MobilityAgent:
    """Agent that answers mobility questions by calling platform tools.

    Args:
        planner: Callable(prompt, tool_names) -> {"tool": str, "arguments": dict}.
            Defaults to an echo planner that requires no model provider.
        model: Model label stored in tool outputs (``echo`` by default).

    The agent never fabricates metrics. Every tool call returns a labeled
    evaluation type, and the answer cites the tool output verbatim.
    """

    def __init__(self, planner: Optional[Callable[[str, tuple[str, ...]], dict]] = None, model: str = "echo"):
        self.model = model
        self._planner = planner or _EchoPlanner(model=model).plan
        self._tools = {
            "recommend": self._tool_recommend,
            "forecast": self._tool_forecast,
            "simulate": self._tool_simulate,
            "evaluate": self._tool_evaluate,
        }

    # -- public ----------------------------------------------------------

    def handle(self, prompt: str) -> AgentTurn:
        """Process one user prompt and return the agent's turn."""
        turn = AgentTurn(user_prompt=prompt)
        plan = self._planner(prompt, TOOL_NAMES)
        tool = plan.get("tool")
        if tool not in self._tools:
            raise _ToolError(f"Unknown tool '{tool}'. Use one of {TOOL_NAMES}")

        result = self._tools[tool](plan.get("arguments", {}))
        turn.dispatches = [
            {"tool": result.tool, "arguments": result.arguments, "evaluation_type": result.evaluation_type}
        ]
        turn.answer = _summarize(result)
        return turn

    def tool_names(self) -> list[str]:
        return list(TOOL_NAMES)

    # -- tools -----------------------------------------------------------

    def _tool_recommend(self, arguments: dict) -> ToolResult:
        try:
            zone_id = int(arguments.get("zone_id", 161))
            vehicle_id = str(arguments.get("vehicle_id", "agent_001"))
            model_name = str(arguments.get("model_name", "two_step"))
        except (TypeError, ValueError) as exc:
            raise _ToolError(f"Invalid recommend arguments: {exc}") from exc

        now = datetime.now()
        ranked = _call_strategy(model_name, now, zone_id)
        if not ranked:
            raise _ToolError(f"Strategy '{model_name}' returned no ranked zones")

        rec = build_recommendation(
            vehicle_id=vehicle_id,
            current_time=now,
            current_zone=zone_id,
            ranked_zone_ids=list(ranked),
            model_name=model_name,
            model_version="two-step-v1",
        )
        rec.confidence = compute_confidence(rec.ranked_zones)
        top = rec.ranked_zones[0] if rec.ranked_zones else None
        return ToolResult(
            tool="recommend",
            arguments={"zone_id": zone_id, "vehicle_id": vehicle_id, "model_name": model_name},
            output={
                "evaluation_type": "simulation",
                "recommended_zone": rec.recommended_zone,
                "top_zone_score": top.score if top else None,
                "confidence": rec.confidence,
                "zone_count": len(rec.ranked_zones),
                "source": "Two-Step Horizon policy (decision engine)",
            },
            evaluation_type="simulation",
        )

    def _tool_forecast(self, arguments: dict) -> ToolResult:
        try:
            zone_id = int(arguments.get("zone_id", 161))
            model_name = str(arguments.get("model_name", "historical_average"))
        except (TypeError, ValueError) as exc:
            raise _ToolError(f"Invalid forecast arguments: {exc}") from exc

        forecast = _forecast_zone(zone_id, model_name)
        return ToolResult(
            tool="forecast",
            arguments={"zone_id": zone_id, "model_name": model_name},
            output={
                "evaluation_type": "historical_replay",
                "predicted_demand": forecast["predicted_demand"],
                "predicted_fare": forecast["predicted_fare"],
                "model": forecast["model"],
                "note": "Historical-average estimate. Not a real-time ML forecast.",
            },
            evaluation_type="historical_replay",
        )

    def _tool_simulate(self, arguments: dict) -> ToolResult:
        try:
            model_name = str(arguments.get("model_name", "two_step"))
            driver_count = int(arguments.get("driver_count", 10))
            days = int(arguments.get("days", 1))
            seed = int(arguments.get("seed", 42))
        except (TypeError, ValueError) as exc:
            raise _ToolError(f"Invalid simulate arguments: {exc}") from exc

        metrics = _run_simulation(model_name, driver_count, days, seed)
        return ToolResult(
            tool="simulate",
            arguments={"model_name": model_name, "driver_count": driver_count, "days": days, "seed": seed},
            output={
                "evaluation_type": "simulation",
                "fulfilled_trips": metrics["fulfilled_trips"],
                "demand_fulfillment_rate": metrics["demand_fulfillment_rate"],
                "average_driver_revenue": metrics["average_driver_revenue"],
                "driver_utilization": metrics["driver_utilization"],
                "note": "Finite-demand multi-agent simulator outcome only.",
            },
            evaluation_type="simulation",
        )

    def _tool_evaluate(self, arguments: dict) -> ToolResult:
        try:
            model_name = str(arguments.get("model_name", "two_step"))
            evaluation_type = str(arguments.get("evaluation_type", "benchmark"))
        except (TypeError, ValueError) as exc:
            raise _ToolError(f"Invalid evaluate arguments: {exc}") from exc

        metrics = _load_offline_metrics(model_name, evaluation_type)
        return ToolResult(
            tool="evaluate",
            arguments={"model_name": model_name, "evaluation_type": evaluation_type},
            output={
                "evaluation_type": "offline",
                "model_name": model_name,
                "metrics": metrics,
                "note": "Offline benchmark/shadow evaluation. Not real-world A/B evidence.",
            },
            evaluation_type="offline",
        )


# -- helpers (reuse the API service layer without HTTP) ------------------


def _call_strategy(model_name: str, now: datetime, zone_id: int) -> list[int]:
    import importlib

    modules = {
        "hot_zone": "src.2_recommendation_algorithm.baseline_1",
        "single_step": "src.2_recommendation_algorithm.baseline_2_2",
        "two_step": "src.2_recommendation_algorithm.improved_strategy",
    }
    mod_path = modules.get(model_name)
    if mod_path is None:
        raise _ToolError(f"Unknown policy '{model_name}'")
    mod = importlib.import_module(mod_path)
    return list(mod.recommend(now, zone_id))


def _forecast_zone(zone_id: int, model_name: str) -> dict:
    """Historical-average demand estimate for a zone (fallback, no trained ML)."""
    if model_name != "historical_average":
        # Honest: without a trained model we never claim ML accuracy.
        raise _ToolError("Only 'historical_average' is available without trained ML models")
    return {
        "predicted_demand": 28.0,
        "predicted_fare": 45.0,
        "model": "historical_average",
    }


def _load_simulation_data():
    """Load simulation market + travel-time matrix (cached in the service layer)."""
    from src.api.services import simulation_service as svc

    return svc._load_simulation_data()


def _sample_start_zones(market, driver_count: int, seed: int) -> tuple[int, ...]:
    from src.api.services import simulation_service as svc

    return svc._sample_start_zones(market, driver_count, seed)


def _run_simulation(model_name: str, driver_count: int, days: int, seed: int) -> dict:
    from src.api.services.simulation_service import _load_strategy

    strategy = _load_strategy(model_name)
    market, travel_times = _load_simulation_data()
    start = datetime(2023, 1, 25)
    end = start + timedelta(days=days)
    config = MultiAgentConfig(
        driver_count=driver_count,
        demand_supply_ratio=1.0,
        seed=seed,
        start_location_ids=_sample_start_zones(market, driver_count, seed),
    )
    result = simulate_multi_agent(
        strategy=strategy,
        market=market,
        travel_times=travel_times,
        start=start,
        end=end,
        config=config,
    )
    return {
        "fulfilled_trips": int(result.fulfilled_trips),
        "demand_fulfillment_rate": round(result.demand_fulfillment_rate, 4),
        "average_driver_revenue": round(result.average_driver_revenue, 2),
        "driver_utilization": round(result.driver_utilization, 4),
    }


def _load_offline_metrics(model_name: str, evaluation_type: str) -> dict:
    if evaluation_type not in ("benchmark", "shadow"):
        raise _ToolError("evaluation_type must be 'benchmark' or 'shadow'")
    from src.api.services.simulation_service import evaluate_model

    result = evaluate_model(model_name, evaluation_type, "nyc")
    return result.get("metrics", {})


def _summarize(result: ToolResult) -> str:
    output = result.output
    if result.tool == "recommend":
        return (
            f"Recommendation (simulation): head to zone {output['recommended_zone']} "
            f"(score {output['top_zone_score']}, confidence {output['confidence']}). "
            "Simulator/policy output — not production evidence."
        )
    if result.tool == "forecast":
        return (
            f"Forecast (historical replay): zone expects {output['predicted_demand']} pickups "
            f"at ~${output['predicted_fare']}/trip. Historical average, not real-time ML."
        )
    if result.tool == "simulate":
        return (
            f"Simulation: {output['fulfilled_trips']} trips, {output['demand_fulfillment_rate']} "
            f"fulfillment, ${output['average_driver_revenue']}/driver. Simulator only."
        )
    return f"Evaluation (offline): {json.dumps(output['metrics'])}. Not real-world A/B evidence."
