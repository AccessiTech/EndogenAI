"""MCP tool definitions for the Decision-Making & Reasoning Layer.

Exposes logical inference, causal planning, and trace query operations
as MCP-compatible tool handlers.
"""

from __future__ import annotations

from typing import Any

import structlog

from reasoning.inference import InferencePipeline
from reasoning.models import ReasoningRequest, ReasoningResult, ReasoningStrategy
from reasoning.planner import CausalPlanner
from reasoning.store import ReasoningStore

logger: structlog.BoundLogger = structlog.get_logger(__name__)


class MCPTools:
    """MCP tool handler for reasoning layer operations."""

    def __init__(
        self,
        store: ReasoningStore,
        pipeline: InferencePipeline,
        planner: CausalPlanner,
    ) -> None:
        self._store = store
        self._pipeline = pipeline
        self._planner = planner

    async def handle(self, tool_name: str, params: dict[str, Any]) -> Any:
        """Dispatch an MCP tool call by name.

        Supported tools:
        - reasoning.run_inference
        - reasoning.create_plan
        - reasoning.query_traces
        """
        match tool_name:
            case "reasoning.run_inference":
                return await self._run_inference(params)

            case "reasoning.create_plan":
                return await self._create_plan(params)

            case "reasoning.query_traces":
                return await self._query_traces(params)

            case _:
                raise ValueError(f"Unknown MCP tool: {tool_name!r}")

    async def _run_inference(self, params: dict[str, Any]) -> dict[str, Any]:
        request = ReasoningRequest(
            query=str(params["query"]),
            context=list(params.get("context", [])),
            strategy=ReasoningStrategy(params.get("strategy", ReasoningStrategy.DEDUCTIVE)),
            include_plan=bool(params.get("include_plan", False)),
            model=params.get("model"),
        )

        trace = await self._pipeline.run_inference(
            query=request.query,
            context=request.context,
            strategy=request.strategy,
            model_override=request.model,
        )
        await self._store.store_trace(trace)

        plan = None
        if request.include_plan:
            plan = await self._planner.create_plan(
                goal=request.query, context=request.context, inference_traces=[trace]
            )
            await self._store.store_plan(plan)

        result = ReasoningResult(trace=trace, plan=plan)
        return result.model_dump()

    async def _create_plan(self, params: dict[str, Any]) -> dict[str, Any]:
        plan = await self._planner.create_plan(
            goal=str(params["goal"]),
            context=list(params.get("context", [])),
        )
        await self._store.store_plan(plan)
        return plan.model_dump()

    async def _query_traces(self, params: dict[str, Any]) -> list[dict[str, Any]]:
        items = await self._store.query_traces(
            query=str(params["query"]),
            n_results=int(params.get("n_results", 5)),
        )
        return [item.model_dump() for item in items]
