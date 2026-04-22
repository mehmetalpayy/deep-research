"""
Terminal CLI for Deep Research Agent.

Run with: uv run run_cli.py
Requires Temporal worker running: uv run run_worker.py
"""

import asyncio
import uuid
from datetime import timedelta

from dotenv import load_dotenv
from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.styles import Style
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.rule import Rule
from rich.theme import Theme
from temporalio.client import Client
from temporalio.common import RetryPolicy
from temporalio.contrib.openai_agents import ModelActivityParameters, OpenAIAgentsPlugin

load_dotenv()

from utils.types import SingleClarificationInput, UserQueryInput
from workflows.research_workflow import InteractiveResearchWorkflow

TASK_QUEUE = "deep-research-queue"

theme = Theme({
    "info": "cyan",
    "success": "bold green",
    "warning": "bold yellow",
    "question": "bold magenta",
})

console = Console(theme=theme)

prompt_style = Style.from_dict({
    "prompt": "#00aaff bold",
    "question-label": "#cc66ff bold",
})


async def connect_temporal() -> Client:
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
    return await Client.connect(
        "localhost:7233",
        namespace="default",
        plugins=[openai_plugin],
    )


async def run_once(client: Client, session: PromptSession) -> bool:
    """Run a single research session. Returns False if user wants to exit."""

    console.print()

    # Get research query
    try:
        query = await session.prompt_async(
            HTML("<prompt>Research topic (or 'exit' to quit): </prompt>"),
            style=prompt_style,
        )
    except (EOFError, KeyboardInterrupt):
        return False

    query = query.strip()
    if not query or query.lower() in ("exit", "quit", "q"):
        return False

    console.print()

    # Start workflow
    workflow_id = f"research-{uuid.uuid4().hex[:8]}"

    with Progress(SpinnerColumn(), TextColumn("[info]{task.description}"), console=console, transient=True) as progress:
        progress.add_task("Analyzing your query...", total=None)
        handle = await client.start_workflow(
            InteractiveResearchWorkflow.run,
            id=workflow_id,
            task_queue=TASK_QUEUE,
        )
        status = await handle.execute_update(
            InteractiveResearchWorkflow.start_research,
            UserQueryInput(query=query),
        )

    # Handle clarification questions
    if status.status == "awaiting_clarification":
        console.print(Rule("[question]Clarifying Questions[/question]", style="magenta"))
        console.print("[dim]Please answer the following to refine the research.[/dim]")
        console.print()

        for i, question in enumerate(status.clarification_questions, start=1):
            console.print(f"[question]Q{i}:[/question] {question}")
            try:
                answer = await session.prompt_async(
                    HTML("<prompt>  Answer: </prompt>"),
                    style=prompt_style,
                )
            except (EOFError, KeyboardInterrupt):
                return False

            await handle.execute_update(
                InteractiveResearchWorkflow.provide_clarification,
                SingleClarificationInput(answer=answer.strip()),
            )
            console.print()

    # Wait for research to complete
    console.print(Rule("[info]Research in Progress[/info]", style="cyan"))
    console.print()

    with Progress(SpinnerColumn(), TextColumn("[info]{task.description}"), console=console, transient=True) as progress:
        progress.add_task("Searching the web and writing report...", total=None)
        result = await handle.result()

    # Display results
    console.print()
    console.print(Rule("[success]Research Complete[/success]", style="green"))
    console.print()

    console.print(Panel(
        result.short_summary,
        title="[bold green]Summary[/bold green]",
        border_style="green",
    ))
    console.print()

    console.print(Markdown(result.markdown_report))

    if result.follow_up_questions:
        console.print()
        console.print(Rule("[dim]Follow-up Questions[/dim]", style="dim"))
        for question in result.follow_up_questions:
            console.print(f"  [dim]•[/dim] {question}")

    console.print()
    return True


async def main() -> None:
    console.print()
    console.print(Panel.fit(
        "[bold blue]Deep Research Agent[/bold blue]\n[dim]Powered by Temporal + OpenAI Agents SDK[/dim]",
        border_style="blue",
    ))
    console.print()

    # Connect to Temporal (once, reused across sessions)
    with Progress(SpinnerColumn(), TextColumn("[info]{task.description}"), console=console, transient=True) as progress:
        progress.add_task("Connecting to Temporal...", total=None)
        try:
            client = await connect_temporal()
        except Exception as e:
            console.print(f"[red]Failed to connect to Temporal: {e}[/red]")
            console.print("[warning]Make sure Temporal server and worker are running.[/warning]")
            return

    console.print("[success]Connected to Temporal[/success]")

    session = PromptSession()

    # Research loop
    while True:
        should_continue = await run_once(client, session)
        if not should_continue:
            break

        console.print(Rule(style="dim"))

    console.print()
    console.print("[dim]Goodbye![/dim]")
    console.print()


if __name__ == "__main__":
    asyncio.run(main())
