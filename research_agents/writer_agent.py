from agents import Agent, Runner

from utils.models import ReportData
from prompts.writer import WRITER_PROMPT


def new_writer_agent() -> Agent:
    return Agent(
        name="Writer Agent",
        instructions=WRITER_PROMPT,
        model="gpt-4.1",
        output_type=ReportData,
    )


async def write_report(query: str, search_results: list[str]) -> ReportData:
    combined_results = "\n\n---\n\n".join(search_results)
    prompt = f"Original query: {query}\n\nSearch results:\n{combined_results}"
    agent = new_writer_agent()
    result = await Runner.run(agent, prompt)
    return result.final_output_as(ReportData)
