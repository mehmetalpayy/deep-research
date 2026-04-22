from agents import Agent, Runner

from utils.models import TriageResult
from prompts.triage import TRIAGE_PROMPT


def new_triage_agent() -> Agent:
    return Agent(
        name="Triage Agent",
        instructions=TRIAGE_PROMPT,
        model="gpt-4.1",
        output_type=TriageResult,
    )


async def check_needs_clarification(query: str) -> bool:
    agent = new_triage_agent()
    result = await Runner.run(agent, query)
    triage_result = result.final_output_as(TriageResult)
    return triage_result.needs_clarification
