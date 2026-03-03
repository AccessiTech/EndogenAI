"""worker.py — Temporal Worker startup for agent-runtime.

Registers IntentionWorkflow and RuntimeActivities with the Temporal task queue.
"""
from __future__ import annotations

import asyncio
import signal
from typing import Any

import structlog
from temporalio.client import Client
from temporalio.worker import Worker

from agent_runtime.activities import RuntimeActivities
from agent_runtime.workflow import IntentionWorkflow

logger: structlog.BoundLogger = structlog.get_logger(__name__)


async def run_worker(
    temporal_url: str = "localhost:7233",
    namespace: str = "endogenai",
    task_queue: str = "brain-runtime",
    motor_output_url: str = "http://localhost:8163",
    executive_agent_url: str = "http://localhost:8161",
) -> None:
    """Connect to Temporal and start the worker.

    Runs indefinitely until SIGINT or SIGTERM received.
    """
    logger.info(
        "worker.connecting",
        temporal_url=temporal_url,
        namespace=namespace,
        task_queue=task_queue,
    )

    client = await Client.connect(temporal_url, namespace=namespace)

    activities = RuntimeActivities(
        motor_output_url=motor_output_url,
        executive_agent_url=executive_agent_url,
    )

    worker = Worker(
        client,
        task_queue=task_queue,
        workflows=[IntentionWorkflow],
        activities=[
            activities.decompose_goal,
            activities.dispatch_to_motor_output,
            activities.emit_partial_feedback,
        ],
    )

    logger.info("worker.started", task_queue=task_queue)

    stop_event = asyncio.Event()

    def _handle_signal(sig: Any) -> None:
        logger.info("worker.shutdown_signal", signal=sig)
        stop_event.set()

    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, _handle_signal, sig)

    async with worker:
        await stop_event.wait()
        logger.info("worker.stopping")
