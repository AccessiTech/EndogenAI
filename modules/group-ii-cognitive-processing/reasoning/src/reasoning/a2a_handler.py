"""A2A task handler for the Decision-Making & Reasoning Layer.

Handles incoming A2A task delegations:
- run_inference: run a reasoning inference and store the trace
- create_plan: generate a causal plan for a goal
- query_traces: semantic search over stored inference traces
- run_full_reasoning: run inference + optional plan in one call
"""

from __future__ import annotations

from typing import Any

import structlog

from reasoning.inference import InferencePipeline
from reasoning.models import ReasoningRequest, ReasoningResult, ReasoningStrategy
from reasoning.planner import CausalPlanner
from reasoning.store import ReasoningStore

logger: structlog.BoundLogger = structlog.get_logger(__name__)


class A2AHandler:
    """Handles incoming A2A task delegations for reasoning processing."""

    def __init__(
        self,
        store: ReasoningStore,
        pipeline: InferencePipeline,
        planner: CausalPlanner,
    ) -> None:
        self._store = store
        self._pipeline = pipeline
        self._planner = planner

    async def handle(self, task_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Dispatch an A2A task by type."""
        match task_type:
            case "run_inference":
                return await self._run_inference(payload)

            case "create_plan":
                return await self._create_plan(payload)

            case "query_traces":
                items = await self._store.query_traces(
                    query=str(payload["query"]),
                    n_results=int(payload.get("n_results", 5)),
                )
                return {"items": [item.model_dump() for item in items]}

            case "run_full_reasoning":
                return await self._run_full_reasoning(payload)

            case _:
                raise ValueError(f"Unknown A2A task type: {task_type!r}")

    async def _run_inference(self, payload: dict[str, Any]) -> dict[str, Any]:
        trace = await self._pipeline.run_inference(
            query=str(payload["query"]),
            context=list(payload.get("context", [])),
            strategy=ReasoningStrategy(
                payload.get("strategy", ReasoningStrategy.DEDUCTIVE)
            ),
            model_override=payload.get("model"),
        )
        await self._store.store_trace(trace)
        return trace.model_dump()

    async def _create_plan(self, payload: dict[str, Any]) -> dict[str, Any]:
        plan = await self._planner.create_plan(
            goal=str(payload["goal"]),
            context=list(payload.get("context", [])),
        )
        await self._store.store_plan(plan)
        return plan.model_dump()

    async def _run_full_reasoning(self, payload: dict[str, Any]) -> dict[str, Any]:
        request = ReasoningRequest(
            query=str(payload["query"]),
            context=list(payload.get("context", [])),
            strategy=ReasoningStrategy(
                payload.get("strategy", ReasoningStrategy.DEDUCTIVE)
            ),
            include_plan=bool(payload.get("include_plan", False)),
            model=payload.get("model"),
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
                goal=request.query,
                context=request.context,
                inference_traces=[trace],
            )
            await self._store.store_plan(plan)

        result = ReasoningResult(trace=trace, plan=plan)
        return result.model_dump()
