from dataclasses import dataclass
from typing import Optional

from utils.models import ReportData


# --- Workflow I/O (Temporal serializes dataclasses natively) ---

@dataclass
class UserQueryInput:
    query: str


@dataclass
class SingleClarificationInput:
    answer: str


@dataclass
class ResearchStatus:
    original_query: str | None
    clarification_questions: list[str]
    clarification_responses: list[str]
    status: str


@dataclass
class InteractiveResearchResult:
    short_summary: str
    markdown_report: str
    follow_up_questions: list[str]


# --- Research manager internal types ---

@dataclass
class ClarificationResult:
    needs_clarifications: bool
    questions: Optional[list[str]] = None
    report_data: Optional[ReportData] = None
