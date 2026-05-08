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
  → Explains every concept before any task
  → Architecture decisions and design thinking
  → Generating project docs and specifications
  → Explaining LangChain/LangGraph concepts
  → Reviewing code quality and approach
  → Debugging complex problems
  → Automatic Notion tracking after every step

CLAUDE CODE (Coding Environment — VS Code)
  → Writing all actual code files
  → Running tests and validating outputs
  → Committing and managing git workflow
  → Delegating to specialised sub-agents
```

---

## Learning-First Approach — MANDATORY

This is the most important working rule.
Every task must be explained in Claude.ai BEFORE
Claude Code builds anything.

### The Explanation Format

Before every task, Claude.ai must provide:

```
WHAT IT IS:
  Plain English description of the concept
  No jargon without explanation

HOW IT FITS INTO NEXBRIDGE:
  Where it sits in the architecture
  What it connects to
  Why NexBridge needs it specifically

THEN:
  The Claude Code task prompt
```

### When This Applies

```
✅ Before EVERY task — no exceptions
✅ Even for simple tasks
✅ Even for tasks we have done before
✅ Especially for new concepts
```

### Why This Matters

```
Lasith is using this project as a learning curve
to deeply understand AI agent architecture,
LangGraph, Pydantic, FastAPI, and LLM abstraction.

The goal is not just to ship NexBridge —
it is to understand every decision made
and every pattern used.
```

---

## Automatic Notion Tracking — ALWAYS ON

Claude.ai automatically updates Notion after every
completed step. Lasith never needs to ask.

### What Gets Updated Automatically

```
After every completed build step:
  → Notion Build Status page
     Change step status from ⚪ to ✅
     Update next step marker to 🟡

After every session:
  → Notion Build Status with current position

After a phase completes:
  → Notion Phase History page
     Mark complete with date

When a key decision is made:
  → Notion Key Decisions Log
     Add new ADR entry
```

### Notion Page IDs

```
Build Status:   353163fe-25cf-810b-aa1d-e97337acf470
Phase History:  353163fe-25cf-8188-868b-e2016e0eda2c
Decisions Log:  353163fe-25cf-8168-82ca-f96373b587aa
```

---

## Pluggable LLM Architecture — ADR-014

NexBridge uses a pluggable LLM backend.
Default is Anthropic API for the POC.
Any LangChain-compatible model can be swapped in.

### Why This Matters

```
NexBridge is open source. Any organisation
that clones it must be able to:

1. Use their own LLM provider
2. Self-host models for data privacy
3. Fine-tune on their own audit logs
4. Never send sensitive data externally
```

### Supported Providers

```
anthropic  → default, used for POC
ollama     → self-hosted open source models
openai     → OpenAI API
huggingface → HuggingFace models
custom     → any LangChain-compatible model
```

### The Abstraction Layer

```python
# backend/core/llm.py
# Always import from here — never import
# ChatAnthropic directly in agent files

from backend.core.llm import get_llm

llm = get_llm()  # reads from config/env
```

### Self-Learning Roadmap

```
Phase 2 (now):   Anthropic API default
Phase 3:         RAG on audit logs
Phase 4:         Fine-tuned org-specific model
Phase 5:         Fully self-hosted, no external calls
```

---

## How We Work — Session Flow

### Starting a Session

```
1. Open new Claude.ai thread
   → nexbridge-context skill loads automatically
   → Instantly oriented, no re-explanation needed

2. Discuss the next task
   → Claude.ai explains concept + architecture fit

3. Claude Code executes
   → Sub-agents build, test, commit

4. Claude.ai updates Notion automatically
```

---

## Claude Code Sub-Agents

```
nexbridge-agent-builder  → building Python backend agents
nexbridge-test-writer    → writing pytest test suites
nexbridge-code-reviewer  → reviewing files before merge
nexbridge-committer      → all git commits
nexbridge-debugger       → investigating bugs
```

---

## Coding Standards

### Python (Backend)

```python
# Standard import order
from typing import Optional, List, Dict

from fastapi import APIRouter
from langchain_core.language_models import BaseChatModel
from langgraph.graph import StateGraph
from pydantic import BaseModel

from backend.core.llm import get_llm
from backend.core.models import NexBridgeState
```

**Naming conventions:**
```
Files:      snake_case.py
Classes:    PascalCase
Functions:  snake_case()
Constants:  UPPER_SNAKE_CASE
Agents:     *_agent.py
```

**Always use type hints and docstrings:**
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

**Structured logging:**
```python
print(f"[INTERPRETER] field={field_name} tier={tier} confidence={confidence:.2f}")
print(f"[ORCHESTRATOR] decision=GO payload_tier=T{highest_tier}")
print(f"[ORCHESTRATOR] decision=HOLD reason=T1_below_threshold field={field}")
```

### TypeScript (Frontend)

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

```
main        → stable only, never commit directly
developer   → all active development
```

**Commit format — single line only:**
```
[AgentName] Short description
```

---

## Safety Non-Negotiables

```
T1 confidence threshold  = 1.0   — NEVER change
T2 confidence threshold  = 0.95  — NEVER change
T1 dual-agent            — ALWAYS mandatory
Audit log entries        — immutable, NEVER delete
Payload inheritance      — T1 field = whole payload T1
Orchestrator             — ONLY release gate
```

---

## Red Flags — Discuss in Claude.ai First

```
- Any confidence threshold change
- Orchestrator decision logic changes
- Dual-agent verification flow changes
- Audit log structure changes
- T1 field downgrade suggestions
- New external dependencies
- LangGraph state shape changes
- LLM provider changes
```

---

## Document Maintenance

| Event | Action |
|---|---|
| Step completed | Notion Build Status (automatic) |
| Key decision | Notion Decisions Log (automatic) |
| Phase complete | Notion Phase History (automatic) |
| Architecture change | docs/03_TECH_ARCHITECTURE.md |
| New agent added | docs/08_AGENT_REGISTRY.md |
| API change | docs/06_API_REFERENCE.md |

---

**Document Version:** 2.1
**Project:** NexBridge
**Maintained By:** Lasith Jayarathne (@TechLead)
**Last Updated:** May 2026
**Changes from v2.0:** Added learning-first approach,
  pluggable LLM architecture (ADR-014),
  self-learning roadmap.
