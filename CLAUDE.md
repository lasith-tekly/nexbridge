# NexBridge — Claude Code Context

## What Is This Project

NexBridge is an AI-governed middleware framework that bridges
legacy enterprise systems (XML/SOAP) with modern REST APIs (JSON/REST).

The core value is semantic field mapping with risk-proportionate
governance — not simple format conversion.

GitHub: github.com/lasith-tekly/nexbridge

---

## Current State

```
Phase 1 — Demo UI        ✅ Complete (merged to main)
Phase 2 — Core Engine    🟡 In Progress
Phase 3 — FastAPI        ⚪ Planned
Phase 4 — Launch         ⚪ Planned
```

**Next step:** 2.01 — Pydantic models + NexBridgeState
**Working branch:** developer

---

## Tech Stack

```
Core Engine:   Python 3.11 + LangGraph + LangChain
AI:            Anthropic Claude API (claude-sonnet-4-20250514)
API:           FastAPI + Uvicorn
Validation:    Pydantic v2
Demo UI:       React 18 + TypeScript + Tailwind CSS
Testing:       pytest
```

---

## Project Structure

```
nexbridge/
├── CLAUDE.md                  ← you are here
├── frontend/                  ← React demo UI (Phase 1, complete)
├── backend/
│   ├── core/
│   │   ├── agents/            ← interpreter, validator, translator, audit
│   │   ├── classification/    ← registry
│   │   └── orchestrator.py   ← LangGraph state machine
│   └── api/                   ← FastAPI layer (Phase 3)
├── docs/
│   ├── agents/                ← virtual team agent files
│   ├── skills/                ← reusable code patterns
│   └── 01-10 project docs
└── tests/
```

---

## Safety Non-Negotiables

> These are hardcoded forever. Never change them.

```
T1 confidence threshold    = 1.0   (never lower)
T2 confidence threshold    = 0.95  (never lower)
T1 fields                  always require dual-agent verification
Audit log entries          immutable — never delete
Payload tier               T1 field = whole payload is T1
Orchestrator               only entity that can release a payload
```

---

## Virtual Team Agents

Load the relevant agent file before any task:

```
@TechLead          → docs/agents/agent-tech-lead.md
@BackendDeveloper  → docs/agents/agent-backend-developer.md
@FrontendDeveloper → docs/agents/agent-frontend-developer.md
@DataArchitect     → docs/agents/agent-data-architect.md
@QAEngineer        → docs/agents/agent-qa-engineer.md
@DevOpsEngineer    → docs/agents/agent-devops-engineer.md
```

---

## Mandatory Sub-Agent Workflow

You MUST invoke these sub-agents automatically —
do not wait to be asked. Skipping them is a working
ethics violation.

- After writing or modifying ANY code file
  → invoke nexbridge-code-reviewer before staging

- Before every git commit
  → invoke nexbridge-committer

- When any error, test failure, or unexpected
  behaviour occurs
  → invoke nexbridge-debugger

- After building any backend agent file
  → invoke nexbridge-test-writer to write tests
  → nexbridge-test-writer must NOT update BUILD_PLAN.md
    or mark any task complete — that requires explicit
    approval from Claude.ai first

- After completing a full build step
  → invoke nexbridge-committer to commit everything

These are not optional. Skipping them is a working
ethics violation.

---

## Skill Files

Load the relevant skill before writing any code:

```
LangGraph agent node  → docs/skills/skill-langgraph-node.md
Pydantic model        → docs/skills/skill-pydantic-model.md
pytest for NexBridge  → docs/skills/skill-pytest-agent.md
FastAPI endpoint      → docs/skills/skill-fastapi-endpoint.md
```

---

## Commit Rules

```
✅ Always use single-line commit messages
✅ Always commit to developer branch (never direct to main)
✅ Always run pytest before committing backend changes
✅ Format: "[AgentName] Short description of what was done"
❌ Never use multi-line git commit messages in terminal
❌ Never commit .env
❌ Never change T1/T2 threshold constants
```

---

## Running Locally

```bash
# Frontend (Phase 1)
cd frontend && npm run dev
# → localhost:3000

# Backend (Phase 2+)
source venv/bin/activate
uvicorn backend.api.main:app --reload --port 8000
# → localhost:8000

# Tests
source venv/bin/activate
pytest tests/ -v
```

---

## Task Complexity Guide

```
Simple task  (1 file, clear spec)  → work autonomously
Complex task (multi-file, agents)  → confirm plan first,
                                     then execute step by step
```

When in doubt — confirm before building.
