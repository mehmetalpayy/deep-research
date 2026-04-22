# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the System

Three processes must run simultaneously:

```bash
# Terminal 1 — Temporal server
temporal server start-dev

# Terminal 2 — Temporal worker
uv run run_worker.py

# Terminal 3 — Research CLI
uv run run_cli.py
```

Install dependencies: `uv sync`

## Architecture

This is a **durable multi-agent research pipeline** built on Temporal + OpenAI Agents SDK. The critical design principle: every LLM call is a Temporal Activity, making the pipeline crash-safe and resumable.

### Request flow

```
run_cli.py → Temporal Client → InteractiveResearchWorkflow (run_worker.py executes this)
                                        │
                              Triage → Clarify → Plan → Search (parallel) → Write
```

### Key structural decisions

**Temporal sandbox restrictions** — `workflows/research_workflow.py` must import anything that uses non-deterministic code (pydantic, rich, agents) inside `workflow.unsafe.imports_passed_through()`. Never import such modules at the top level of workflow files.

**Package naming** — The local agent folder is `research_agents/` (not `agents/`) because `agents` is the name of the OpenAI Agents SDK package. Importing `from agents import Agent, Runner` refers to the SDK; `from research_agents.x import ...` refers to local code.

**Prompts are separate** — Each agent's system prompt lives in `prompts/<agent_name>.py`. Agent files in `research_agents/` only contain the `Agent` factory function and runner logic.

**Models in `utils/`** — Pydantic models shared across agents live in `utils/models.py`. `utils/__init__.py` must NOT import `Logger` (from `utils/logger.py`) because `rich` is not sandbox-safe and would break the Temporal worker.

**Workflow I/O uses dataclasses** — `UserQueryInput`, `SingleClarificationInput`, `ResearchStatus`, `InteractiveResearchResult` in `research_workflow.py` are `@dataclass` (not Pydantic) because Temporal serializes dataclasses natively without a custom converter.

**Agent output types use Pydantic** — `output_type=` in `Agent(...)` requires a Pydantic `BaseModel`.

### Workflow mechanics

`InteractiveResearchWorkflow` uses three Temporal primitives:
- `@workflow.update` — `start_research` and `provide_clarification`: mutate state, run async LLM calls, return a result to the caller
- `@workflow.query` — `get_status`: read-only, synchronous state snapshot
- `workflow.wait_condition` — pauses the workflow deterministically until clarification answers arrive

### Environment variables

```
OPENAI_API_KEY          # required
OPENAI_AGENTS_DISABLE_TRACING=1  # suppresses non-fatal OpenAI tracing errors
```
