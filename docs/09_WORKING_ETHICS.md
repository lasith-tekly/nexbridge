# NexBridge — Working Ethics & Collaboration Standards

**Version:** 3.0
**Last Updated:** May 2026
**Changed:** Adapted from Crikly v1.6 — plan approval, prompt template,
             risk classification, quality gate, process lessons
**Maintainer:** Lasith Jayarathne
**Review:** After each phase completion

This file lives in the project root and is referenced at the
start of every Claude Code session. Read it before every prompt.

---

## Collaboration Model

```
LASITH (Product Lead)
  → Owns vision, priorities, and final decisions
  → Brings domain knowledge and business requirements
  → Reviews and approves ALL plans before any code is written
  → Makes product and architecture trade-off decisions

CLAUDE.AI (Strategic Partner — claude.ai chat)
  → Explains every concept before every task (learning-first)
  → Architecture decisions and design thinking
  → Writes Claude Code prompts — never pastes unreviewed
  → Debugging complex cross-cutting problems
  → Red flag escalation — stop Claude Code, bring here first
  → Automatic Notion tracking after every completed step

CLAUDE CODE (Coding Agent — VS Code)
  → Writing all actual code files
  → Following agent role instructions precisely
  → Reading docs/ folder for context before every task
  → Committing and managing git workflow
  → One task per session — never combines multiple tasks
  → Presents plan FIRST, waits for approval, THEN builds
  → Never makes architectural decisions
```

**Rule:** Claude.ai thinks and designs. Claude Code builds.
Never ask Claude Code to make architectural decisions.
Never ask Claude.ai to write production code files.

---

## Session Flow

### Starting Every Claude Code Session

```
Step 1  → Open docs/BUILD_PLAN.md
          Find the first ⚪ or 🟡 task
          That is what you work on — no skipping

Step 2  → Identify which agent owns that task

Step 3  → Come to Claude.ai
          Get the explanation (WHAT IT IS + HOW IT FITS)
          Get the approved Claude Code prompt

Step 4  → Paste the prompt into Claude Code
          Claude Code presents its plan (Step 0)
          Wait for explicit approval from Lasith

Step 5  → Say "approved" or "go ahead"
          Claude Code builds

Step 6  → Review output before accepting

Step 7  → Claude Code commits with correct format

Step 8  → Mark task ✅ in docs/BUILD_PLAN.md

Step 9  → Claude.ai updates Notion automatically
          No action needed from Lasith

Step 10 → Move to next task
```

---

## Standard Claude Code Prompt Template

Every prompt sent to Claude Code must follow this structure.
No exceptions — even for quick fixes.

```
@[AgentName]

Task ID: [e.g. 2.01, 2.06, 3.02] ← from docs/BUILD_PLAN.md

Context files:
- CLAUDE.md
- docs/09_WORKING_ETHICS.md
- docs/agents/[relevant-agent].md
- docs/skills/[relevant-skill].md

Task:
[One clear paragraph describing exactly what to build]

File(s) to create or modify:
- backend/[exact/file/path.py]

Requirements:
- [requirement 1]
- [requirement 2]

Must NOT modify:
- [locked file if any]

Safety rules to enforce:
- [T1/T2 threshold or safety rule if relevant]

Step 0 — Present your plan first. List every file you will
create or modify and your approach for each. Wait for
explicit approval before writing any code.

On completion:
1. Mark task [ID] ✅ in docs/BUILD_PLAN.md
2. Commit docs/BUILD_PLAN.md in the same commit as the code

Commit to: developer branch
Risk: 🟢 Low | 🟡 Medium | 🔴 High
```

---

## Plan Approval — Non-Negotiable Rule

Every Claude Code session involving code creation or
modification MUST start with a plan. Claude Code presents
the plan and waits for explicit approval before building.

**What counts as approval:**
```
✅ "approved"
✅ "go ahead"
✅ "looks good, proceed"
✅ Any explicit confirmation message from Lasith
```

**What does NOT count as approval:**
```
❌ Claude Code writing "Approved — building now" itself
❌ Claude Code interpreting silence as approval
❌ Any self-generated approval text
❌ Proceeding after a non-committal response
```

If Claude Code proceeds without explicit approval:
```
1. Stop the session immediately
2. Do not accept the output
3. Come to Claude.ai with the problem
4. Get a clearer prompt with Step 0 explicit
5. Restart the Claude Code session fresh
```

This rule exists because building without an approved plan
produces output that has to be discarded — wasting the
entire session.

---

## Risk Classification

Every task must have a risk level assigned in the prompt.

```
🟢 Low Risk
   → Single file, documentation, adding tests
   → New Pydantic models (non-breaking)
   → UI components, styling
   → Auto-proceed after plan approval

🟡 Medium Risk
   → New agent files
   → LangGraph graph changes (additive)
   → New API endpoints
   → Classification registry changes
   → Review plan carefully, then implement

🔴 High Risk
   → ANY confidence threshold changes — FORBIDDEN
   → Orchestrator decision logic
   → Dual-agent verification flow
   → Audit log structure
   → LangGraph state shape
   → STOP → Bring to Claude.ai → Get approval → Then build
```

---

## Red Flags — Stop Claude Code, Come to Claude.ai First

Stop immediately and bring to Claude.ai if:

```
→ Any suggestion to lower T1 threshold below 1.0
→ Any suggestion to lower T2 threshold below 0.95
→ Any change to orchestrator decision logic
→ Any change to dual-agent verification flow
→ Any change to audit log immutability
→ Any change to payload tier inheritance rule
→ Adding a new LLM provider not in backend/core/llm.py
→ Adding new external Python dependencies
→ LangGraph state shape changes
→ Any change that bypasses the Orchestrator release gate
→ Anything that feels architecturally significant
→ Python version is not 3.11
→ Agent creates a stub with no follow-up task scheduled
```

When in doubt — bring to Claude.ai. It costs nothing.
Fixing a bad safety decision costs everything.

---

## Context File Loading Strategy

Load only what is relevant to the task.
Loading everything wastes context window.

```
Task type                     → Load these docs
─────────────────────────────────────────────────────────────
Any task (always)             → CLAUDE.md
                                docs/09_WORKING_ETHICS.md
                                relevant agent MD file
Pydantic models               → docs/skills/skill-pydantic-model.md
LangGraph agent node          → docs/skills/skill-langgraph-node.md
pytest tests                  → docs/skills/skill-pytest-agent.md
FastAPI endpoint              → docs/skills/skill-fastapi-endpoint.md
Classification registry       → docs/04_DATA_CLASSIFICATION.md
Agent build task              → docs/agents/agent-backend-developer.md
Orchestrator changes          → docs/SOLUTION_AGENTS.md
Architecture decision         → docs/03_TECH_ARCHITECTURE.md
Data model changes            → docs/agents/agent-data-architect.md
Frontend task                 → docs/agents/agent-frontend-developer.md
T1 safety work                → docs/05_DATA_FLOWS.md
```

---

## Agent Responsibilities — Quick Reference

**Virtual Team (prompt with @tag):**

| Agent | Tag | Use For |
|---|---|---|
| Tech Lead | @TechLead | Complex analysis, orchestration |
| Backend Developer | @BackendDeveloper | Python agents, LangGraph |
| Data Architect | @DataArchitect | Pydantic models, state shape |
| Frontend Developer | @FrontendDeveloper | React, TypeScript, Tailwind |
| QA Engineer | @QAEngineer | pytest, T1 safety tests |
| DevOps Engineer | @DevOpsEngineer | Git, CI, branch management |

**Claude Code Sub-Agents (auto-triggered):**

| Agent | Trigger |
|---|---|
| nexbridge-agent-builder | Building Python backend agents |
| nexbridge-test-writer | Writing pytest test suites |
| nexbridge-code-reviewer | Reviewing files before merge |
| nexbridge-committer | All git commits |
| nexbridge-debugger | Investigating bugs |

---

## Prompt Quality Checklist

Before sending any Claude Code prompt, verify:

```
□ Agent role specified (@AgentName)?
□ Task ID from BUILD_PLAN.md included?
□ CLAUDE.md in context files?
□ docs/09_WORKING_ETHICS.md in context files?
□ Relevant agent MD file included?
□ Only relevant docs included (not everything)?
□ Task described in one clear paragraph?
□ Exact file paths specified?
□ Branch specified (developer)?
□ Locked files named if relevant?
□ Safety rules referenced if T1/T2 logic?
□ Risk level assigned?
□ Step 0 plan approval line included?
□ On completion instructions included?
```

---

## Standard Prompt Examples

### Backend Agent Build

```
@BackendDeveloper

Task ID: 2.06

Context files:
- CLAUDE.md
- docs/09_WORKING_ETHICS.md
- docs/agents/agent-backend-developer.md
- docs/skills/skill-langgraph-node.md
- docs/skills/skill-pydantic-model.md

Task:
Build the InterpreterAgent for NexBridge. This agent takes
classified fields from NexBridgeState and uses LangChain
with the pluggable LLM to semantically map each field to
the target schema. Returns FieldMapping objects with
confidence scores and reasoning per field.

File to create:
- backend/core/agents/interpreter.py

Requirements:
- Import LLM via: from backend.core.llm import get_llm
- Returns FieldMapping per field with confidence 0.0-1.0
- Includes reasoning string per mapping
- Reads from NexBridgeState, writes interpreter_run_1
- Follows LangGraph node pattern from skill file

Must NOT modify:
- backend/core/models.py
- backend/core/constants.py

Safety rules:
- Never hardcode the LLM provider
- Never import ChatAnthropic directly

Step 0 — Present your plan first. List every file you
will create or modify and your approach for each.
Wait for explicit approval before writing any code.

On completion:
1. Mark task 2.06 ✅ in docs/BUILD_PLAN.md
2. Commit BUILD_PLAN.md in the same commit as the code

Commit to: developer branch
Risk: 🟡 Medium
```

### Test Suite

```
@QAEngineer

Task ID: 2.07

Context files:
- CLAUDE.md
- docs/09_WORKING_ETHICS.md
- docs/agents/agent-qa-engineer.md
- docs/skills/skill-pytest-agent.md

Task:
Write the pytest test suite for the InterpreterAgent.
Tests must cover GO scenario field mappings, confidence
score range validation, and reasoning field presence.

File to create:
- backend/tests/test_interpreter.py

Requirements:
- Use fixtures from conftest.py
- Cover GO scenario (T2/T3 fields)
- Cover HOLD scenario (T1 field present)
- Verify confidence is always 0.0-1.0
- Verify reasoning is never empty

Must NOT modify:
- backend/core/agents/interpreter.py

Safety rules:
- T1 safety tests must NEVER be skipped or xfail

Step 0 — Present your plan first. Wait for approval.

On completion:
1. Mark task 2.07 ✅ in docs/BUILD_PLAN.md
2. Commit BUILD_PLAN.md in the same commit

Commit to: developer branch
Risk: 🟢 Low
```

### Bug Fix

```
@BackendDeveloper

Task ID: FIX — NB-008

Context files:
- CLAUDE.md
- docs/09_WORKING_ETHICS.md
- docs/agents/agent-backend-developer.md

Bug:
The classifier is not inheriting T1 tier to the whole
payload when a T1 field is present. payload_tier returns
3 even when weight_limit (T1) is in the payload.

File: backend/core/classification/registry.py

Expected: Any T1 field → payload_tier = 1
Actual:   payload_tier = highest tier seen last

Fix: Change payload tier logic to track the minimum
     (highest risk) tier across all fields.

Test to add: backend/tests/test_registry.py

Step 0 — Present your plan first. Wait for approval.

Commit to: developer branch
Risk: 🔴 High — affects T1 safety classification
```

---

## Coding Standards

### Python — Non-Negotiable

```python
# Type hints always — no untyped functions
# ❌ Never
def classify_field(field_name, registry):

# ✅ Always
def classify_field(
    field_name: str,
    registry: ClassificationRegistry
) -> FieldClassification:

# ❌ Never — bare except
try:
    result = classify(field)
except:
    pass

# ✅ Always — specific with context
try:
    result = classify(field)
except KeyError as e:
    raise ClassificationError(
        f"Field '{field_name}' not found in registry"
    ) from e

# ❌ Never — hardcoded LLM
from langchain_anthropic import ChatAnthropic
llm = ChatAnthropic(model="claude-sonnet-4-20250514")

# ✅ Always — pluggable
from backend.core.llm import get_llm
llm = get_llm()
```

**Structured logging:**
```python
print(f"[CLASSIFIER]  field={field_name} tier=T{tier}")
print(f"[INTERPRETER] field={field_name} confidence={confidence:.2f}")
print(f"[ORCHESTRATOR] decision=GO payload_tier=T{tier}")
print(f"[ORCHESTRATOR] decision=HOLD reason={reason}")
```

---

## Git Commit Format

Single-line only. No exceptions. Multi-line hangs terminal.

```
[AgentName] Short description of what was done

Examples:
[AgentBuilder] Add interpreter agent and tests
[TestWriter] Add T1 safety tests for orchestrator
[DataArchitect] Add FieldMapping Pydantic model
[Committer] Fix confidence threshold in validator
```

---

## Branch Lifecycle Rule

```
developer  → all active development
main       → stable only, never commit directly
```

Every build step commits to developer.
Phase sign-off merges developer → main.
Never start next phase until current is merged and verified.

---

## Quality Gate — Before Any Commit

```
□ Python version is 3.11 (python --version)
□ All pytest tests pass: pytest tests/ -v
□ Zero failing T1 safety tests
□ Type hints on all new functions
□ No bare except blocks
□ No hardcoded LLM provider imports
□ No T1/T2 values hardcoded (use CONFIDENCE_THRESHOLDS)
□ Relevant docs updated in same commit
□ .env not staged (git status check)
□ Committing to developer (not main)
□ Single-line commit message
□ docs/BUILD_PLAN.md updated in same commit
□ If new agent → docs/08_AGENT_REGISTRY.md updated
□ If architecture changed → docs/03_TECH_ARCHITECTURE.md updated
```

---

## Safety Non-Negotiables

Hardcoded forever. No agent, prompt, or instruction overrides.

```
T1 confidence threshold  = 1.0   — NEVER lower
T2 confidence threshold  = 0.95  — NEVER lower
T1 dual-agent            — ALWAYS mandatory
Audit log entries        — immutable, NEVER delete
Payload inheritance      — T1 field = whole payload T1
Orchestrator             — ONLY entity that releases payload
```

---

## Automatic Notion Tracking

Claude.ai updates Notion automatically — no action needed.

```
After every completed step  → Build Plan updated
After every session         → Current position recorded
When decision made          → Key Decisions Log updated
When phase completes        → Phase History updated

Rule: If it happened, it's in Notion.
      If it's not in Notion, it didn't happen.
```

Notion Build Plan:
https://www.notion.so/35a163fe25cf81cfb5b6fe2b35844e48

---

## Document Maintenance

Update relevant docs in the same commit as the code:

| Task type | Update this doc |
|---|---|
| New Pydantic model | docs/agents/agent-data-architect.md |
| New agent built | docs/08_AGENT_REGISTRY.md |
| New API endpoint | docs/06_API_REFERENCE.md |
| Architecture decision | docs/03_TECH_ARCHITECTURE.md |
| New env variable | docs/03_TECH_ARCHITECTURE.md + .env.example |
| Feature completed | docs/BUILD_PLAN.md → mark ✅ + Notion |
| New safety rule | docs/09_WORKING_ETHICS.md |
| New classification field | docs/04_DATA_CLASSIFICATION.md |

---

## Process Lessons

### L-01 — Single-line commit messages only
Multi-line commit messages cause terminal to hang waiting
for input. Always use -m flag. If vim opens: :q! then Enter.

### L-02 — Never change T1/T2 thresholds for any reason
Any prompt touching confidence thresholds is 🔴 High Risk.
Stop and come to Claude.ai first.

### L-03 — Plan approval prevents wasted sessions
Claude Code built an entire component using the wrong state
shape before review. Two hours discarded.
Rule: Step 0 in every prompt. No code without "approved".

### L-04 — Always read current sources before summarising
Claude.ai gave wrong status by reading stale project
knowledge. Rule: Verify against Notion or current doc
shared in conversation. Never summarise from memory.

### L-05 — Agent MD file always required
Quick-fix prompts that skipped agent context produced
lower quality output and missed NexBridge patterns.
Rule: Every prompt includes the relevant agent MD file.
No exceptions — even for single-line fixes.

---

*NexBridge Working Ethics v3.0 — May 2026*
*Adapted from Crikly Working Ethics v1.6*
*Review after each phase completion.*
*Any process change must be agreed with Lasith first.*
