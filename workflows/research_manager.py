from __future__ import annotations

import asyncio

from agents import Runner

from research_agents.clarifying_agent import new_clarifying_agent
from research_agents.planner_agent import new_planner_agent
from research_agents.search_agent import new_search_agent
from research_agents.triage_agent import new_triage_agent
from research_agents.writer_agent import new_writer_agent
from utils.models import (
    ClarificationQuestions,
    ReportData,
    TriageResult,
    WebSearchPlan,
)
from utils.types import ClarificationResult


class InteractiveResearchManager:

    def __init__(self):
        self.triage_agent = new_triage_agent()
        self.clarifying_agent = new_clarifying_agent()
        self.planner_agent = new_planner_agent()
        self.search_agent = new_search_agent()
        self.writer_agent = new_writer_agent()

    async def _plan_searches(self, query: str) -> WebSearchPlan:
        print(f"[planner] Creating search plan | query={query[:80]!r}")
        result = await Runner.run(
            self.planner_agent,
            f"Create a search plan for: {query}",
        )
        plan = result.final_output_as(WebSearchPlan)
        print(f"[planner] Plan created | {len(plan.searches)} searches")
        for i, item in enumerate(plan.searches, start=1):
            print(f"[planner]   {i:02d}. {item.query!r} — {item.reason}")
        return plan

    async def _perform_searches(self, search_plan: WebSearchPlan) -> list[str]:
        print(f"[search] Starting {len(search_plan.searches)} concurrent searches")

        async def search(index: int, item) -> str:
            print(
                f"[search] [{index:02d}/{len(search_plan.searches):02d}] Searching: {item.query!r}"
            )
            prompt = f"Search for: {item.query}\nReason: {item.reason}"
            result = await Runner.run(self.search_agent, prompt)
            summary = str(result.final_output)
            print(
                f"[search] [{index:02d}/{len(search_plan.searches):02d}] Done: {item.query!r} | {len(summary)} chars returned"
            )
            return summary

        tasks = [
            search(i, item) for i, item in enumerate(search_plan.searches, start=1)
        ]
        results = await asyncio.gather(*tasks)
        print(f"[search] All {len(results)} searches complete")
        return results

    async def _write_report(self, query: str, search_results: list[str]) -> ReportData:
        total_chars = sum(len(r) for r in search_results)
        print(
            f"[writer] Synthesising report | {len(search_results)} search results | {total_chars} total chars of input"
        )
        prompt = f"Original query: {query}\nSearch results: {search_results}"
        result = await Runner.run(self.writer_agent, prompt)
        report = result.final_output_as(ReportData)
        print(
            f"[writer] Report complete | summary={report.short_summary[:100]!r} | {len(report.follow_up_questions)} follow-up questions"
        )
        return report

    async def _run_research_pipeline(self, query: str) -> ReportData:
        print(f"[pipeline] Starting research pipeline | query={query[:80]!r}")

        search_plan = await self._plan_searches(query)
        search_results = await self._perform_searches(search_plan)
        report = await self._write_report(query, search_results)

        print("[pipeline] Research pipeline complete")
        return report

    async def run_with_clarifications_complete(
        self,
        original_query: str,
        questions: list[str],
        responses: list[str],
    ) -> ReportData:
        print(
            f"[clarify] Building enriched query from {len(responses)} clarification responses"
        )
        context = "\n".join(f"- {q}: {a}" for q, a in zip(questions, responses))
        enriched_query = f"{original_query}\n\nClarifications:\n{context}"
        print(f"[clarify] Enriched query:\n{enriched_query}")
        return await self._run_research_pipeline(enriched_query)

    async def run_with_clarifications_start(self, query: str) -> ClarificationResult:
        print(f"[triage] Evaluating query: {query[:80]!r}")
        triage_result = await Runner.run(self.triage_agent, query)
        verdict = triage_result.final_output_as(TriageResult)
        print(
            f"[triage] needs_clarification={verdict.needs_clarification} | reason={verdict.reason!r}"
        )

        if verdict.needs_clarification:
            print("[clarify] Generating clarifying questions")
            clarify_result = await Runner.run(
                self.clarifying_agent,
                f"Generate clarifying questions for: {query}",
            )
            questions = clarify_result.final_output_as(ClarificationQuestions)
            for i, q in enumerate(questions.questions, start=1):
                print(f"[clarify]   Q{i}: {q!r}")
            return ClarificationResult(
                needs_clarifications=True,
                questions=questions.questions,
            )
        else:
            print("[triage] Query is specific enough — skipping clarification")
            report = await self._run_research_pipeline(query)
            return ClarificationResult(
                needs_clarifications=False,
                report_data=report,
            )
