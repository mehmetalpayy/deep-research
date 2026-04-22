from typing import Optional
from pydantic import BaseModel, Field


class WebSearchItem(BaseModel):
    query: str = Field(description="The search query to execute")
    reason: str = Field(description="Why this search is important for the research")


class WebSearchPlan(BaseModel):
    searches: list[WebSearchItem] = Field(description="List of searches to perform")


class ReportData(BaseModel):
    short_summary: str = Field(description="2-3 sentence summary of key findings")
    markdown_report: str = Field(description="Full markdown-formatted research report")
    follow_up_questions: list[str] = Field(description="Suggested questions for further research")


class TriageResult(BaseModel):
    needs_clarification: bool = Field(description="Whether the query needs clarifying questions")
    reason: str = Field(description="Explanation for the decision")


class ClarificationQuestions(BaseModel):
    questions: list[str] = Field(description="List of clarifying questions to ask")


class SearchResult(BaseModel):
    summary: str = Field(description="Concise summary of the search results")
