from agents import Agent, Runner, WebSearchTool

from utils.models import SearchResult
from prompts.search import SEARCH_PROMPT


def new_search_agent() -> Agent:
    return Agent(
        name="Search Agent",
        instructions=SEARCH_PROMPT,
        model="gpt-4.1",
        tools=[WebSearchTool()],
        output_type=SearchResult,
    )


async def perform_web_search(query: str, reason: str) -> str:
    agent = new_search_agent()
    prompt = f"Search for: {query}\nReason for search: {reason}\n\nSearch the web and provide a summary of the results."
    result = await Runner.run(agent, prompt)
    search_result = result.final_output_as(SearchResult)
    return search_result.summary
