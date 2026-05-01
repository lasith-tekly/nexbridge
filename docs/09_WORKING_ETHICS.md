# NexBridge - Working Ethics & Collaboration Standards

## Overview

This document defines how we work together to build NexBridge.
It covers the collaboration model between Lasith (Product Lead),
Claude.ai (strategic partner), and Claude Code (coding environment).

All work on NexBridge must follow these guidelines.

---

## Collaboration Model

```
LASITH (Product Lead)
  → Owns vision, priorities, and final decisions
  → Brings domain knowledge and requirements
  → Reviews and approves all outputs

CLAUDE.AI (Strategic Partner — this chat)
  → Architecture decisions and design thinking
  → Generating project docs and specifications
  → Explaining LangChain/LangGraph concepts
  → Reviewing code quality and approach
  → Debugging complex problems
  → Brainstorming and trade-off analysis
  → Automatic Notion tracking after every step

CLAUDE CODE (Coding Environment — VS Code)
  → Writing all actual code files
  → Running tests and validating outputs
  → Committing and managing git workflow
  → Delegating to specialised sub-agents
```

---

## Automatic Notion Tracking — ALWAYS ON

Claude.ai automatically updates Notion after every completed step.
Lasith never needs to ask for this — it happens by default.

### What Gets Updated Automatically

```
After every completed build step:
  → Notion Build Status page
     Change step status from ⚪ to ✅
     Update "Next step" field

After every session:
  → Notion Build Status page
     Record current position
     Note any decisions made

After a phase completes:
  → Notion Phase History page
     Mark phase complete with date
     Record what was delivered

When a key decision is made:
  → Notion Key Decisions Log
     Add new ADR entry
```

### Notion Page IDs

```
Master Hub:     353163fe-25cf-81b4-a444-f68d698912cf
Build Status:   353163fe-25cf-810b-aa1d-e97337acf470
Phase History:  353163fe-25cf-8188-868b-e2016e0eda2c
Decisions Log:  353163fe-25cf-8168-82ca-f96373b587aa
```

---

## How We Work — Session Flow

### Starting a New Session (Claude.ai)

The nexbridge-context skill loads automatically.
No re-explanation of the project needed.
Claude.ai is already oriented from the first message.

### Starting a New Session (Claude Code)

CLAUDE.md loads automatically when VS Code opens.
No context setup needed.

### Standard Task Flow

```
1. Claude.ai discusses and plans the task
2. Claude Code executes via sub-agents
3. Sub-agents build, test, and commit
4. Claude.ai updates Notion automatically
5. Move to next step
```

---

## Claude Code Sub-Agents

### When To Use Each Agent

```
nexbridge-agent-builder  → building any Python backend agent
nexbridge-test-writer    → writing pytest test suites
nexbridge-code-reviewer  → reviewing any file before merge
nexbridge-committer      → all git commits
nexbridge-debugger       → investigating any bug or error
```

### How To Trigger Sub-Agents

In Claude Code, describe your task naturally:
```
"build the interpreter agent"
→ nexbridge-agent-builder spawns automatically

"debug: pytest failing on test_orchestrator"
→ nexbridge-debugger spawns automatically

"commit these changes"
→ nexbridge-committer spawns automatically
```

---

## Claude Code Standards

### Skill Files — Always Read First

```
Before building a LangGraph node:
  read docs/skills/skill-langgraph-node.md

Before building a Pydantic model:
  read docs/skills/skill-pydantic-model.md

Before writing tests:
  read docs/skills/skill-pytest-agent.md

Before building a FastAPI endpoint:
  read docs/skills/skill-fastapi-endpoint.md
```

### Commit Rules

```
✅ Single-line commit messages only
   (multi-line hangs the terminal)
✅ Always commit to developer branch
✅ Run pytest before every backend commit
✅ Format: [AgentName] Short description

❌ Never commit to main directly
❌ Never commit .env or secrets
❌ Never commit failing tests
❌ Never open vim for commit messages
   (if vim opens: :q! then Enter)
```

---

## Coding Standards

### Python (Backend)

**File organisation:**
```python
"""
Module docstring — purpose and key concepts
"""
# Standard library
from typing import Optional, List, Dict

# Third-party
from fastapi import APIRouter
from langchain_anthropic import ChatAnthropic
from langgraph.graph import StateGraph
from pydantic import BaseModel

# Local
from backend.core.models import NexBridgeState
from backend.core.classification.registry import ClassificationRegistry
```

**Naming conventions:**
```
Files:      snake_case.py
Classes:    PascalCase
Functions:  snake_case()
Constants:  UPPER_SNAKE_CASE
Private:    _leading_underscore()
Agents:     *_agent.py
```

**Always use type hints:**
```python
def classify_field(
    field_name: str,
    registry: ClassificationRegistry
) -> FieldClassification:
    """
    Classify a field by looking it up in the registry.

    Args:
        field_name: The XML field name to classify
        registry: Loaded classification registry

    Returns:
        FieldClassification with tier and threshold
    """
```

**Structured logging for all agent decisions:**
```python
print(f"[INTERPRETER] field={field_name} tier={tier} confidence={confidence:.2f}")
print(f"[ORCHESTRATOR] decision=GO payload_tier=T{highest_tier}")
print(f"[ORCHESTRATOR] decision=HOLD reason=T1_below_threshold field={field}")
print(f"[VALIDATOR] anomaly=True field={field} severity=HIGH")
```

### TypeScript (Frontend)

**Tier colour constants — always use these, never deviate:**
```typescript
export const TIER_COLOURS = {
  1: { bg: 'bg-red-500',   text: 'text-red-500',   label: 'Safety Critical' },
  2: { bg: 'bg-amber-500', text: 'text-amber-500', label: 'Operationally Sensitive' },
  3: { bg: 'bg-blue-500',  text: 'text-blue-500',  label: 'Business Important' },
  4: { bg: 'bg-gray-500',  text: 'text-gray-500',  label: 'Informational' },
} as const;
```

---

## Git Workflow

### Branch Strategy
```
main        → stable, demo-ready only. Never commit directly.
developer   → all active development goes here
```

### Commit Message Format
```
Single line only — no exceptions:
[AgentName] Short description of what was done

Examples:
[AgentBuilder] Add interpreter agent and tests
[TestWriter] Add T1 safety tests for orchestrator
[Committer] Fix confidence threshold in validator
```

---

## Safety-Critical Non-Negotiables

These rules can never be overridden by any agent or any instruction:

```
T1 confidence threshold  = 1.0   — NEVER change
T2 confidence threshold  = 0.95  — NEVER change
T1 dual-agent            — ALWAYS mandatory
Audit log entries        — immutable, NEVER delete
Payload inheritance      — T1 field = whole payload is T1
Orchestrator             — ONLY entity that releases payload
```

---

## Red Flags — Stop and Discuss in Claude.ai First

Stop Claude Code and discuss in Claude.ai if:
- Any confidence threshold value change is suggested
- Modifying orchestrator decision logic
- Touching dual-agent verification flow
- Changing audit log structure
- Any change that could downgrade a T1 field
- Adding new external Python dependencies
- Changing LangGraph state shape

---

## Document Maintenance

| Event | Document to update |
|---|---|
| New feature added | 02_REQUIREMENTS.md |
| Architecture change | 03_TECH_ARCHITECTURE.md |
| New classification field | 04_DATA_CLASSIFICATION.md |
| New agent added | 08_AGENT_REGISTRY.md |
| Phase completed | 10_PHASE_HISTORY.md |
| API change | 06_API_REFERENCE.md |
| Key decision made | Notion Key Decisions Log (automatic) |
| Step completed | Notion Build Status (automatic) |

---

**Document Version:** 2.0
**Project:** NexBridge
**Maintained By:** Lasith Jayarathne (@TechLead)
**Last Updated:** May 2026
**Changes from v1.0:** Updated for Claude Code (replacing Windsurf),
  added automatic Notion tracking rules, added sub-agent guidelines,
  added skill file loading standards.
