from agents import Agent, Runner

from utils.models import ClarificationQuestions
from prompts.clarifying import CLARIFYING_PROMPT


def new_clarifying_agent() -> Agent:
    return Agent(
        name="Clarifying Agent",
        instructions=CLARIFYING_PROMPT,
        model="gpt-4.1",
        output_type=ClarificationQuestions,
    )


async def generate_clarification_questions(query: str) -> list[str]:
    agent = new_clarifying_agent()
    result = await Runner.run(agent, f"Generate clarifying questions for: {query}")
    questions = result.final_output_as(ClarificationQuestions)
    return questions.questions
