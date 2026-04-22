"""
Temporal Worker for Deep Research Agent.

Run with: uv run run_worker.py
"""

import asyncio
import logging
import sys
from datetime import timedelta

from dotenv import load_dotenv
from rich.console import Console
from rich.logging import RichHandler
from temporalio.client import Client
from temporalio.common import RetryPolicy
from temporalio.worker import Worker
from temporalio.contrib.openai_agents import OpenAIAgentsPlugin, ModelActivityParameters

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[
        RichHandler(
            console=Console(file=sys.stderr),
            show_time=True,
            show_level=True,
            show_path=False,
            rich_tracebacks=True,
        )
    ],
)
logging.getLogger("temporalio").setLevel(logging.WARNING)
logging.getLogger("asyncio").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)

from workflows.research_workflow import InteractiveResearchWorkflow

TASK_QUEUE = "deep-research-queue"


async def main():
    openai_plugin = OpenAIAgentsPlugin(
        model_params=ModelActivityParameters(
            start_to_close_timeout=timedelta(seconds=120),
            retry_policy=RetryPolicy(
                initial_interval=timedelta(seconds=1),
                maximum_interval=timedelta(seconds=30),
                backoff_coefficient=2.0,
                maximum_attempts=5,
            ),
        )
    )

    client = await Client.connect(
        "localhost:7233",
        namespace="default",
        plugins=[openai_plugin],
    )

    worker = Worker(
        client,
        task_queue=TASK_QUEUE,
        workflows=[InteractiveResearchWorkflow],
    )

    print("Worker started on task queue: deep-research-queue")
    print("Press Ctrl+C to stop")

    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
