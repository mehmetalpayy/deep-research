from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    import annotated_types
    import pydantic
    import pydantic_core
    from workflows.research_manager import InteractiveResearchManager
    from utils.models import ReportData
    from utils.types import (
        UserQueryInput,
        SingleClarificationInput,
        ResearchStatus,
        InteractiveResearchResult,
    )


@workflow.defn
class InteractiveResearchWorkflow:

    def __init__(self) -> None:
        self.research_manager = InteractiveResearchManager()
        self.original_query: str | None = None
        self.clarification_questions: list[str] = []
        self.clarification_responses: list[str] = []
        self.report_data: ReportData | None = None
        self.research_initialized: bool = False

    def _build_result(self, summary: str, report: str, questions: list[str]) -> InteractiveResearchResult:
        return InteractiveResearchResult(
            short_summary=summary,
            markdown_report=report,
            follow_up_questions=questions,
        )

    @workflow.query
    def get_status(self) -> ResearchStatus:
        if self.report_data:
            status = "completed"
        elif self.clarification_questions and len(self.clarification_responses) < len(self.clarification_questions):
            status = "awaiting_clarification"
        elif self.original_query:
            status = "researching"
        else:
            status = "pending"

        return ResearchStatus(
            original_query=self.original_query,
            clarification_questions=self.clarification_questions,
            clarification_responses=self.clarification_responses,
            status=status,
        )

    @workflow.update
    async def start_research(self, input: UserQueryInput) -> ResearchStatus:
        print(f"[workflow] start_research received | query={input.query!r}")
        self.original_query = input.query

        print("[workflow] Delegating to research_manager.run_with_clarifications_start")
        result = await self.research_manager.run_with_clarifications_start(self.original_query)

        if result.needs_clarifications:
            self.clarification_questions = result.questions
            print(
                f"[workflow] Clarification needed | {len(self.clarification_questions)} questions generated"
                f" | waiting for user input"
            )
        else:
            self.report_data = result.report_data
            print("[workflow] No clarification needed — research complete")

        self.research_initialized = True
        print(f"[workflow] start_research complete | status={self.get_status().status!r}")
        return self.get_status()

    @workflow.update
    async def provide_clarification(self, input: SingleClarificationInput) -> ResearchStatus:
        idx = len(self.clarification_responses) + 1
        total = len(self.clarification_questions)
        print(
            f"[workflow] provide_clarification [{idx}/{total}]"
            f" | answer={input.answer[:60]!r}"
        )
        self.clarification_responses.append(input.answer)

        remaining = total - len(self.clarification_responses)
        if remaining > 0:
            print(f"[workflow] {remaining} clarification(s) still pending")
        else:
            print("[workflow] All clarifications received — research will begin")

        return self.get_status()

    @workflow.run
    async def run(self) -> InteractiveResearchResult:
        print("[workflow] run() started — waiting for start_research update")
        await workflow.wait_condition(lambda: self.research_initialized)
        print("[workflow] Initialized | status=" + self.get_status().status)

        if self.clarification_questions:
            print(
                f"[workflow] Waiting for {len(self.clarification_questions)} clarification(s)"
            )
            await workflow.wait_condition(
                lambda: len(self.clarification_responses) >= len(self.clarification_questions)
            )
            print("[workflow] All clarifications collected — starting research pipeline")
            self.report_data = await self.research_manager.run_with_clarifications_complete(
                self.original_query,
                self.clarification_questions,
                self.clarification_responses,
            )

        print(
            f"[workflow] Workflow complete | summary={self.report_data.short_summary[:80]!r}"
        )
        return self._build_result(
            self.report_data.short_summary,
            self.report_data.markdown_report,
            self.report_data.follow_up_questions,
        )
