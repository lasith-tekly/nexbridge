# NexBridge - Agent Orchestration Guide

## Overview

This guide explains how to use the NexBridge virtual agent
team to build the application inside Windsurf. Read this
before starting any development session.

---

## Agent Team at a Glance

```
@TechLead            Complex features, risk analysis, coordination
@ProductManager      Requirements, user stories, business rules
@SolutionArchitect   LangGraph design, API contracts, data flows
@DataArchitect       Pydantic models, state schema, data contracts
@BackendDeveloper    Python, LangChain, LangGraph, FastAPI, tests
@FrontendDeveloper   React, TypeScript, Tailwind, demo UI
@QAEngineer          Tests, confidence validation, edge cases
@DevOpsEngineer      GitHub, CI/CD, environment config
```

---

## How to Use Agents in Windsurf

Type the agent name at the start of your prompt in
Windsurf's chat panel. Windsurf auto-loads AGENTS.md
from the .windsurf/ folder, so the agent already knows
its role and NexBridge context.

```
@BackendDeveloper

Context files:
- docs/09_WORKING_ETHICS.md
- docs/SOLUTION_AGENTS.md

Task:
Implement the ClassificationRegistry in
backend/core/classification/registry.py

Requirements:
- Load registry.json from same directory
- Cache in memory at startup
- classify(field_name) returns FieldClassification
- Unknown fields default to Tier 4
- Log field count on load

Commit to: developer branch
Risk: 🟢 Low
```

---

## Workflow Patterns

### Pattern 1: Simple Task (Single Agent)

For a clear, well-scoped task with no cross-cutting concerns.

```
You → @BackendDeveloper  (implement specific function)
You → @FrontendDeveloper (implement specific component)
You → @QAEngineer        (write tests for that function)
```

Example:
```
Step 1: @BackendDeveloper  → implement registry.py
Step 2: @QAEngineer        → write test_registry.py
```

---

### Pattern 2: Feature Development (Multi-Agent)

For a full feature that needs backend + frontend + tests.

```
Step 1: @ProductManager      → define requirements
Step 2: @BackendDeveloper    → implement backend
Step 3: @FrontendDeveloper   → implement UI
Step 4: @QAEngineer          → write tests
```

Example — Building the Transform endpoint:
```
Step 1: @ProductManager
  Define acceptance criteria for POST /transform

Step 2: @BackendDeveloper
  Implement POST /transform in api/main.py
  Reference: docs/06_API_REFERENCE.md

Step 3: @FrontendDeveloper
  Connect PayloadInput to POST /transform
  Reference: docs/07_FRONTEND_STRUCTURE.md

Step 4: @QAEngineer
  Write end-to-end tests for the transform flow
```

---

### Pattern 3: Complex Feature (TechLead First)

For anything spanning multiple agents, files, or with
unclear risk level. Always start with @TechLead.

```
Step 1: @TechLead            → orchestration plan
Step 2: @ProductManager      → detailed requirements
Step 3: @DataArchitect       → models/schema if needed
Step 4: @SolutionArchitect   → architecture if needed
Step 5: @BackendDeveloper    → implementation
Step 6: @FrontendDeveloper   → UI
Step 7: @QAEngineer          → tests
```

Example — Building the T1 dual-agent flow:
```
Step 1: @TechLead
  Orchestrate the T1 dual-agent verification feature.
  Full context in docs/SOLUTION_AGENTS.md

Step 2: @BackendDeveloper
  Implement dual_interpret node using TechLead plan
  Implement compare node
  Add conditional routing to LangGraph graph

Step 3: @QAEngineer
  Write tests:
  - T1 payload triggers dual runs
  - Divergence returns HOLD
  - Agreement proceeds to validate
```

---

### Pattern 4: Bug Fix

```
Step 1: Describe the bug clearly with error message
Step 2: Go directly to @BackendDeveloper or @FrontendDeveloper
Step 3: @QAEngineer adds regression test after fix
```

---

## Standard Session Prompt Template

Copy this and fill in before every Windsurf session:

```
@[AgentName]

Context files:
- docs/09_WORKING_ETHICS.md
- docs/[relevant doc 1]
- docs/[relevant doc 2]

Task:
[One clear paragraph describing exactly what to build]

File: [exact/file/path.py or .tsx]

Requirements:
- [requirement 1]
- [requirement 2]
- [requirement 3]

Constraints:
- Commit to: developer branch
- Risk level: 🟢 Low / 🟡 Medium / 🔴 High
- Do NOT modify: [locked files if any]
```

---

## Prompt Quality Checklist

Before sending any prompt to Windsurf, verify:

- [ ] Agent role is specified (@AgentName)
- [ ] Relevant context docs are listed
- [ ] Task is described in one clear paragraph
- [ ] File path is explicit and exact
- [ ] Branch is specified (always: developer)
- [ ] Locked files are named if relevant
- [ ] Expected output is clear

---

## Context File Loading Strategy

```
For architecture tasks    → 03_TECH_ARCHITECTURE.md
For new features          → 02_REQUIREMENTS.md + 03_TECH_ARCHITECTURE.md
For backend code          → 03_TECH_ARCHITECTURE.md + 06_API_REFERENCE.md
For agent implementation  → SOLUTION_AGENTS.md + 08_AGENT_REGISTRY.md
For frontend code         → 07_FRONTEND_STRUCTURE.md
For classification work   → 04_DATA_CLASSIFICATION.md
For any risky change      → 08_AGENT_REGISTRY.md first
For testing               → 02_REQUIREMENTS.md + SOLUTION_AGENTS.md
```

---

## NexBridge Phase 1 — Recommended Build Sequence

Use this sequence for Phase 1 (Demo UI):

```
Sprint 1 — React scaffolding
  @FrontendDeveloper → scaffold Vite + React + Tailwind
  @FrontendDeveloper → create folder structure per 07_FRONTEND_STRUCTURE.md
  @FrontendDeveloper → define tier constants in src/constants/tiers.ts
  @FrontendDeveloper → define TypeScript types in nexbridge.types.ts

Sprint 2 — Core UI components
  @FrontendDeveloper → TierBadge.tsx
  @FrontendDeveloper → ConfidenceBar.tsx
  @FrontendDeveloper → AgentCard.tsx
  @FrontendDeveloper → DecisionBadge.tsx

Sprint 3 — Layout and panels
  @FrontendDeveloper → PayloadInput.tsx
  @FrontendDeveloper → SchemaInput.tsx
  @FrontendDeveloper → AgentPipeline.tsx
  @FrontendDeveloper → OutputPanel.tsx + TransformResult.tsx + AuditLog.tsx

Sprint 4 — Mock data and wiring
  @FrontendDeveloper → mock data layer
  @FrontendDeveloper → App.tsx wiring all panels
  @QAEngineer        → manual test checklist for UI
```

---

## Red Flags — Stop and Raise to Claude

Stop Windsurf and discuss with Claude (this chat) if:

- Changing any confidence threshold value
- Modifying orchestrator.py decision logic
- Touching dual-agent verification flow
- Changing NexBridgeState shape
- Any agent suggests downgrading a T1 field
- Adding new external Python dependencies
- Windsurf output looks architecturally wrong

---

**Project:** NexBridge
**Maintained By:** Lasith Jayarathne (@TechLead)
**Last Updated:** March 2026
