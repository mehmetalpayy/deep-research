<h1 align="center"><strong>deep-research</strong></h1>

<p align="center">
  <em>A durable multi-agent research assistant — Temporal orchestrates the pipeline so a crash never loses your work.</em>
</p>

---

## Overview

**deep-research** is a terminal-first AI research agent built on [OpenAI Agents SDK](https://github.com/openai/openai-agents-python) and [Temporal](https://temporal.io). You give it a topic, it asks clarifying questions if needed, fans out parallel web searches, and synthesises everything into a structured markdown report — all from your terminal.

The key idea: every LLM call is a durable Temporal Activity. If the process crashes mid-research — after 8 of 9 searches have completed — Temporal replays from the last checkpoint. No redundant API calls, no lost progress, no starting over.

---

## How It Works

```
run_cli.py  ──► Temporal Client ──► InteractiveResearchWorkflow
                                          │
                              ┌───────────┴───────────┐
                         Triage Agent          (if vague)
                              │               Clarifying Agent
                              │                      │
                         Planner Agent  ◄────────────┘
                              │
                    ┌─────────┼─────────┐
               Search      Search    Search  ...  (parallel)
               Agent       Agent     Agent
                    └─────────┼─────────┘
                              │
                         Writer Agent
                              │
                         markdown report
```

**The pipeline:**

1. **Triage** — decides if the query is specific enough or needs clarification
2. **Clarify** — generates 3 targeted questions, collects answers from the terminal
3. **Plan** — creates 5–10 focused web search queries
4. **Search** — executes all searches concurrently via `WebSearchTool`
5. **Write** — synthesises results into a structured markdown report with follow-up questions

---

## Repository Structure

```
deep-research/
├── run_cli.py              # Entry point — interactive terminal client
├── run_worker.py           # Temporal worker process
├── research_agents/        # One file per agent
│   ├── triage_agent.py
│   ├── clarifying_agent.py
│   ├── planner_agent.py
│   ├── search_agent.py
│   └── writer_agent.py
├── workflows/              # Temporal workflow + orchestrator
│   ├── research_workflow.py
│   └── research_manager.py
├── prompts/                # System prompts, one file per agent
│   ├── triage.py
│   ├── clarifying.py
│   ├── planner.py
│   ├── search.py
│   └── writer.py
├── utils/
│   ├── models.py           # Pydantic models for agent output_type
│   ├── types.py            # Dataclasses for Temporal workflow I/O
│   └── logger.py           # Rich-based structured logger
├── pyproject.toml
└── .env.example
```

---

## Quick Start

**Requirements:** Python 3.10+, [`uv`](https://astral.sh/uv), [Temporal CLI](https://docs.temporal.io/cli), an OpenAI API key.

```bash
# 1. Install dependencies
uv sync

# 2. Configure environment
cp .env.example .env
# → open .env and set OPENAI_API_KEY
```

---

## Running

Three processes, three terminals:

**Terminal 1 — Temporal server:**
```bash
temporal server start-dev
```

**Terminal 2 — Worker:**
```bash
uv run run_worker.py
```

**Terminal 3 — Research CLI:**
```bash
uv run run_cli.py
```

You'll see:

```
╭─────────────────────────────────────────────╮
│  Deep Research Agent                        │
│  Powered by Temporal + OpenAI Agents SDK    │
╰─────────────────────────────────────────────╯

Connected to Temporal

Research topic: █

──────────── Clarifying Questions ──────────────
Q1: What is your budget range?
  Answer: █

Q2: Are you looking for hotels or boutique stays?
  Answer: █

Q3: What dates are you travelling?
  Answer: █

──────────── Research in Progress ──────────────
⠸ Searching the web and writing report...

──────────── Research Complete ─────────────────

╭─ Summary ──────────────────────────────────────╮
│ ...                                            │
╰────────────────────────────────────────────────╯

# Full Markdown Report
...

──────────── Follow-up Questions ───────────────
  • ...
```

---

## Design Choices

**Temporal for durability.** Each LLM call is a retried Activity. Network blips, rate limits, and crashes are handled automatically — the workflow picks up exactly where it left off.

**Human-in-the-loop via Workflow Updates.** Clarification questions are collected through Temporal's `@workflow.update` mechanism. The workflow pauses mid-execution, waits for terminal input, then continues — all within a single durable execution.

**Parallel search.** All search queries from the planner run concurrently with `asyncio.gather`. A 9-query plan takes roughly the same wall time as a single search.

**Prompts as a first-class concern.** Each agent's system prompt lives in its own file under `prompts/`. Swap or tune a prompt without touching agent logic.

**Pydantic for agent output, dataclasses for workflow I/O.** Agent `output_type=` requires a Pydantic `BaseModel`. Temporal serialises workflow inputs/outputs natively from dataclasses — so `UserQueryInput`, `ResearchStatus`, etc. live in `utils/types.py` as `@dataclass`, while `WebSearchPlan`, `ReportData`, etc. are Pydantic models in `utils/models.py`.

**One model for everything.** All agents use `gpt-4.1` by default. Writer and search agents benefit from the stronger reasoning; triage and clarification are fast enough that a smaller model would barely save cost.

---

## Troubleshooting

**`Failed to connect to Temporal`** — Temporal server is not running. Start it with `temporal server start-dev`.

**Worker crashes with a sandbox violation** — Any import of `rich`, `os.path`, or other non-deterministic code at the top level of `research_workflow.py` will fail. Always wrap such imports in `workflow.unsafe.imports_passed_through()`.

**`OPENAI_API_KEY` errors** — Copy `.env.example` to `.env` and fill in your key. Also set `OPENAI_AGENTS_DISABLE_TRACING=1` to suppress non-fatal tracing noise.
