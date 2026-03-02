"""Integration tests for the reasoning module.

These are marked @pytest.mark.integration and are skipped in normal CI runs
(use ``pytest -m integration`` to run them explicitly).

They require:
  - Ollama running at http://localhost:11434 with ``mistral`` pulled
  - ChromaDB running at http://localhost:8000
  - ENDOGENAI_INTEGRATION_TESTS=1 environment variable set
"""

from __future__ import annotations

import os

import pytest

from reasoning.inference import InferencePipeline
from reasoning.models import CausalPlan, InferenceTrace, ReasoningStrategy
from reasoning.planner import CausalPlanner
from reasoning.store import ReasoningStore

_SKIP = pytest.mark.skipif(
    not os.getenv("ENDOGENAI_INTEGRATION_TESTS"),
    reason="Integration tests require ENDOGENAI_INTEGRATION_TESTS=1 and running services",
)


@pytest.mark.integration
@_SKIP
async def test_full_inference_trace_end_to_end() -> None:
    """Run real inference and verify an embedding round-trip to brain.reasoning."""
    pipeline = InferencePipeline(
        model="ollama/mistral",
        api_base="http://localhost:11434",
        temperature=0.0,
    )
    store = ReasoningStore()

    trace = await pipeline.run_inference(
        query="What is the capital of France?",
        context=["France is a country in Western Europe."],
        strategy=ReasoningStrategy.DEDUCTIVE,
    )
    assert isinstance(trace, InferenceTrace)
    assert trace.conclusion

    trace_id = await store.store_trace(trace)
    assert trace_id == trace.id

    results = await store.query_traces("capital of France", n_results=1)
    assert any(r.id == trace.id for r in results)


@pytest.mark.integration
@_SKIP
async def test_full_causal_plan_end_to_end() -> None:
    """Run real causal planning and verify the plan is stored in brain.reasoning."""
    planner = CausalPlanner(
        model="ollama/mistral",
        api_base="http://localhost:11434",
        temperature=0.0,
        horizon=3,
    )
    store = ReasoningStore()

    plan = await planner.create_plan(
        goal="Write and publish a research paper.",
        context=["Academic writing requires structured sections.", "Peer review is standard."],
    )
    assert isinstance(plan, CausalPlan)
    assert plan.goal == "Write and publish a research paper."

    plan_id = await store.store_plan(plan)
    assert plan_id == plan.id


@pytest.mark.integration
@_SKIP
async def test_inference_then_plan_pipeline() -> None:
    """Run the combined inference → planning pipeline end-to-end."""
    pipeline = InferencePipeline(
        model="ollama/mistral",
        api_base="http://localhost:11434",
        temperature=0.0,
    )
    planner = CausalPlanner(
        model="ollama/mistral",
        api_base="http://localhost:11434",
        temperature=0.0,
        horizon=3,
    )
    store = ReasoningStore()

    trace = await pipeline.run_inference(
        query="How can we reduce energy consumption in a data centre?",
        context=["Cooling accounts for ~40% of data centre energy."],
        strategy=ReasoningStrategy.CAUSAL,
    )
    await store.store_trace(trace)

    plan = await planner.create_plan(
        goal="Reduce data centre energy consumption by 30%.",
        context=trace.context,
        inference_traces=[trace],
    )
    await store.store_plan(plan)

    assert plan.trace_ids == [trace.id]
    assert len(plan.steps) > 0
