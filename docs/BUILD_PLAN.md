# NexBridge - Master Build Plan

## Overview

This is the master build plan for NexBridge.
It tracks every build step across all phases —
what to build, in what order, which agent, and current status.

Update the status column as each step is completed.

---

## Status Legend

```
⚪ Planned      Not started
🟡 In Progress  Currently being built
✅ Complete     Done and committed
🔴 Blocked      Cannot proceed — dependency or issue
```

---

## Setup Phase ✅ Complete

| # | Task | Agent | Status |
|---|---|---|---|
| S1 | Mac dev environment — Python, Node, Git | Manual | ✅ |
| S2 | GitHub repo created (lasith-tekly/nexbridge) | Manual | ✅ |
| S3 | Python venv + dependencies installed | Manual | ✅ |
| S4 | Windsurf opened on NexBridge project | Manual | ✅ |
| S5 | docs/ folder created | Manual | ✅ |
| S6 | All 10 project docs created (01-10) | Claude | ✅ |
| S7 | SOLUTION_AGENTS.md created | Claude | ✅ |
| S8 | AGENT_ORCHESTRATION.md created | Claude | ✅ |
| S9 | AGENTS.md created (.windsurf/) | Claude | ✅ |
| S10 | All 8 agent files created (docs/agents/) | Claude | ✅ |
| S11 | 07_FRONTEND_STRUCTURE.md finalised (v2.1) | Claude | ✅ |
| S12 | developer branch created on GitHub | @DevOpsEngineer | ✅ |

---

## Phase 1 — Demo UI (Week 1)

### Foundation

| # | Task | File | Agent | Status |
|---|---|---|---|---|
| 1.01 | Scaffold Vite + React + TypeScript project | frontend/ | @FrontendDeveloper | ✅ |
| 1.02 | Configure Tailwind CSS | tailwind.config.js | @FrontendDeveloper | ✅ |
| 1.03 | TypeScript types | src/types/nexbridge.types.ts | @FrontendDeveloper | ✅ |
| 1.04 | Tier + decision colour constants | src/constants/tiers.ts | @FrontendDeveloper | ✅ |
| 1.05 | Mock scenario data | src/mocks/transformResponse.ts | @FrontendDeveloper | ✅ |
| 1.06 | API service (Phase 1 mock) | src/services/nexbridgeApi.ts | @FrontendDeveloper | ✅ |
| 1.07 | Commit scaffold to developer branch | — | @DevOpsEngineer | ✅ |

### App Shell

| # | Task | File | Agent | Status |
|---|---|---|---|---|
| 1.08 | App.tsx — 4-step flow + state management | src/App.tsx | @FrontendDeveloper | ✅ |
| 1.09 | ProgressBar.tsx — step indicator | src/components/ProgressBar.tsx | @FrontendDeveloper | ✅ |
| 1.10 | LandingPage.tsx — empty shell | src/pages/LandingPage.tsx | @FrontendDeveloper | ✅ |
| 1.11 | ConfigurePage.tsx — empty shell | src/pages/ConfigurePage.tsx | @FrontendDeveloper | ✅ |
| 1.12 | PipelinePage.tsx — empty shell | src/pages/PipelinePage.tsx | @FrontendDeveloper | ✅ |
| 1.13 | ResultPage.tsx — empty shell | src/pages/ResultPage.tsx | @FrontendDeveloper | ✅ |

### Foundation Components

| # | Task | File | Agent | Status |
|---|---|---|---|---|
| 1.14 | TierBadge.tsx | src/components/TierBadge.tsx | @FrontendDeveloper | ✅ |
| 1.15 | ConfidenceBar.tsx | src/components/ConfidenceBar.tsx | @FrontendDeveloper | 🟡 |
| 1.16 | ScenarioToggle.tsx | src/components/ScenarioToggle.tsx | @FrontendDeveloper | ⚪ |
| 1.17 | DecisionBadge.tsx | src/components/DecisionBadge.tsx | @FrontendDeveloper | ⚪ |

### Page Content — Step 1

| # | Task | File | Agent | Status |
|---|---|---|---|---|
| 1.18 | LandingPage.tsx — full content | src/pages/LandingPage.tsx | @FrontendDeveloper | ⚪ |

### Page Content — Step 2

| # | Task | File | Agent | Status |
|---|---|---|---|---|
| 1.19 | XmlViewer.tsx | src/components/XmlViewer.tsx | @FrontendDeveloper | ⚪ |
| 1.20 | JsonViewer.tsx | src/components/JsonViewer.tsx | @FrontendDeveloper | ⚪ |
| 1.21 | ConfigurePage.tsx — full content | src/pages/ConfigurePage.tsx | @FrontendDeveloper | ⚪ |

### Page Content — Step 3

| # | Task | File | Agent | Status |
|---|---|---|---|---|
| 1.22 | AgentCard.tsx | src/components/AgentCard.tsx | @FrontendDeveloper | ⚪ |
| 1.23 | PipelinePage.tsx — full content + animation | src/pages/PipelinePage.tsx | @FrontendDeveloper | ⚪ |

### Page Content — Step 4

| # | Task | File | Agent | Status |
|---|---|---|---|---|
| 1.24 | AuditLog.tsx | src/components/AuditLog.tsx | @FrontendDeveloper | ⚪ |
| 1.25 | DivergenceDetail.tsx | src/components/DivergenceDetail.tsx | @FrontendDeveloper | ⚪ |
| 1.26 | ResultPage.tsx — full content | src/pages/ResultPage.tsx | @FrontendDeveloper | ⚪ |

### Phase 1 Sign-off

| # | Task | Agent | Status |
|---|---|---|---|
| 1.27 | Full UI review — all 4 steps working with mock data | Manual | ⚪ |
| 1.28 | GO scenario end-to-end in browser | Manual | ⚪ |
| 1.29 | HOLD scenario end-to-end in browser | Manual | ⚪ |
| 1.30 | Merge developer → main | @DevOpsEngineer | ⚪ |

---

## Phase 2 — Core Engine (Week 2)

### Data Models

| # | Task | File | Agent | Status |
|---|---|---|---|---|
| 2.01 | Pydantic models + NexBridgeState | backend/core/models.py | @DataArchitect | ⚪ |
| 2.02 | Custom exception hierarchy | backend/core/exceptions.py | @BackendDeveloper | ⚪ |

### Classification Registry

| # | Task | File | Agent | Status |
|---|---|---|---|---|
| 2.03 | Registry JSON — generic domain fields | backend/core/classification/registry.json | @BackendDeveloper | ⚪ |
| 2.04 | ClassificationRegistry class | backend/core/classification/registry.py | @BackendDeveloper | ⚪ |
| 2.05 | Registry unit tests | backend/tests/test_registry.py | @QAEngineer | ⚪ |

### Interpreter Agent

| # | Task | File | Agent | Status |
|---|---|---|---|---|
| 2.06 | InterpreterAgent class + LangChain integration | backend/core/agents/interpreter.py | @BackendDeveloper | ⚪ |
| 2.07 | Interpreter unit tests | backend/tests/test_interpreter.py | @QAEngineer | ⚪ |

### Translator Agent

| # | Task | File | Agent | Status |
|---|---|---|---|---|
| 2.08 | TranslatorAgent class | backend/core/agents/translator.py | @BackendDeveloper | ⚪ |
| 2.09 | Translator unit tests | backend/tests/test_translator.py | @QAEngineer | ⚪ |

### Orchestrator — Basic Flow

| # | Task | File | Agent | Status |
|---|---|---|---|---|
| 2.10 | LangGraph graph — T3/T4 basic flow | backend/core/orchestrator.py | @BackendDeveloper | ⚪ |
| 2.11 | Orchestrator unit tests — basic flow | backend/tests/test_orchestrator.py | @QAEngineer | ⚪ |

### Validator Agent

| # | Task | File | Agent | Status |
|---|---|---|---|---|
| 2.12 | ValidatorAgent class | backend/core/agents/validator.py | @BackendDeveloper | ⚪ |
| 2.13 | Validator unit tests | backend/tests/test_validator.py | @QAEngineer | ⚪ |

### T1 Safety Layer

| # | Task | File | Agent | Status |
|---|---|---|---|---|
| 2.14 | T1 dual-agent pattern in orchestrator | backend/core/orchestrator.py | @BackendDeveloper | ⚪ |
| 2.15 | Divergence detection + HOLD logic | backend/core/orchestrator.py | @BackendDeveloper | ⚪ |
| 2.16 | T1 safety tests — divergence + threshold | backend/tests/test_orchestrator.py | @QAEngineer | ⚪ |

### Phase 2 Sign-off

| # | Task | Agent | Status |
|---|---|---|---|
| 2.17 | All unit tests passing: pytest tests/ -v | @QAEngineer | ⚪ |
| 2.18 | T3/T4 XML → JSON transformation confirmed | Manual | ⚪ |
| 2.19 | T1 HOLD scenario confirmed in tests | @QAEngineer | ⚪ |
| 2.20 | Merge developer → main | @DevOpsEngineer | ⚪ |

---

## Phase 3 — FastAPI Integration (Week 3)

### FastAPI Layer

| # | Task | File | Agent | Status |
|---|---|---|---|---|
| 3.01 | API request/response Pydantic schemas | backend/api/schemas.py | @DataArchitect | ⚪ |
| 3.02 | FastAPI app + POST /transform endpoint | backend/api/main.py | @BackendDeveloper | ⚪ |
| 3.03 | GET /registry endpoint | backend/api/main.py | @BackendDeveloper | ⚪ |
| 3.04 | GET /health endpoint | backend/api/main.py | @BackendDeveloper | ⚪ |
| 3.05 | POST /classify endpoint | backend/api/main.py | @BackendDeveloper | ⚪ |
| 3.06 | API endpoint tests | backend/tests/test_api.py | @QAEngineer | ⚪ |

### Audit Agent

| # | Task | File | Agent | Status |
|---|---|---|---|---|
| 3.07 | AuditAgent class — immutable logging | backend/core/agents/audit.py | @BackendDeveloper | ⚪ |
| 3.08 | Audit unit tests | backend/tests/test_audit.py | @QAEngineer | ⚪ |

### Frontend — Connect to Real Backend

| # | Task | File | Agent | Status |
|---|---|---|---|---|
| 3.09 | Update nexbridgeApi.ts — real API calls | src/services/nexbridgeApi.ts | @FrontendDeveloper | ⚪ |
| 3.10 | Remove mock data from pipeline flow | src/pages/PipelinePage.tsx | @FrontendDeveloper | ⚪ |
| 3.11 | Handle real API loading + error states | src/pages/ | @FrontendDeveloper | ⚪ |

### Phase 3 Sign-off

| # | Task | Agent | Status |
|---|---|---|---|
| 3.12 | Full end-to-end: paste XML → run → see result | Manual | ⚪ |
| 3.13 | GO scenario works with real backend | Manual | ⚪ |
| 3.14 | HOLD scenario works with real backend | Manual | ⚪ |
| 3.15 | Audit log shows real transformation entries | Manual | ⚪ |
| 3.16 | All tests passing: pytest tests/ -v | @QAEngineer | ⚪ |
| 3.17 | Merge developer → main | @DevOpsEngineer | ⚪ |

---

## Phase 4 — Public Launch (Week 4)

### Repository

| # | Task | Agent | Status |
|---|---|---|---|
| 4.01 | README.md with demo screenshot or GIF | @DevOpsEngineer | ⚪ |
| 4.02 | CONTRIBUTING.md | @DevOpsEngineer | ⚪ |
| 4.03 | CHANGELOG.md | @DevOpsEngineer | ⚪ |
| 4.04 | GitHub repo made public | Manual | ⚪ |
| 4.05 | First GitHub issue created for community | Manual | ⚪ |

### Package

| # | Task | Agent | Status |
|---|---|---|---|
| 4.06 | pyproject.toml for pip package | @DevOpsEngineer | ⚪ |
| 4.07 | pip install nexbridge working from PyPI | @DevOpsEngineer | ⚪ |

### GitHub Actions CI

| # | Task | File | Agent | Status |
|---|---|---|---|---|
| 4.08 | CI pipeline — run tests on push | .github/workflows/ci.yml | @DevOpsEngineer | ⚪ |

### Launch

| # | Task | Agent | Status |
|---|---|---|---|
| 4.09 | LinkedIn article published | Manual | ⚪ |
| 4.10 | LinkedIn demo post with visual | Manual | ⚪ |
| 4.11 | Final merge developer → main | @DevOpsEngineer | ⚪ |

---

## How To Use This File

### At the start of every session
Check this file to know exactly where we are
and what the next step is.

### When a step is complete
Update the status from ⚪ to ✅ in Windsurf.

### When something is blocked
Update to 🔴 and note the blocker below the table.

### Current step
Find the first 🟡 or ⚪ in the list — that is next.

---

## Current Step

```
Phase 1 — Step 1.08
App.tsx — 4-step flow + state management
Status: 🟡 In Progress
```

---

**Document Version:** 1.0
**Project:** NexBridge
**Maintained By:** Lasith Jayarathne
**Last Updated:** March 2026
