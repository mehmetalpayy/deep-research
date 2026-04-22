from agents import Agent, Runner

from utils.models import WebSearchPlan
from prompts.planner import PLANNER_PROMPT


def new_planner_agent() -> Agent:
    return Agent(
        name="Planner Agent",
        instructions=PLANNER_PROMPT,
        model="gpt-4.1",
        output_type=WebSearchPlan,
    )


async def create_search_plan(query: str) -> WebSearchPlan:
    agent = new_planner_agent()
    result = await Runner.run(agent, f"Create a search plan for: {query}")
    return result.final_output_as(WebSearchPlan)
