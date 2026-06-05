# NexBridge - Agent Registry

## Overview

This document is the single source of truth for all
NexBridge solution agents — the AI agents that run
inside the NexBridge pipeline at runtime.

This is separate from the virtual development team
(the @TechLead, @BackendDeveloper etc. who BUILD NexBridge).
These are the agents NexBridge RUNS when transforming data.

---

## Agent Status Legend

```
🟢 Active     — Fully implemented and tested
🟡 In Progress — Currently being built
🔴 Locked     — Core logic. Changes need @TechLead approval
⚪ Planned    — Not yet started
```

---

## Runtime Agents

### Orchestration Agent
```
Status:    🟡 In Progress → 🔴 Locked when complete
File:      backend/core/orchestrator.py
Role:      Central control plane. Governs all other agents.

Responsibilities:
- Reads Classification Registry at startup
- Classifies all fields in incoming payload
- Determines payload tier (highest field tier)
- Routes to correct LangGraph path
- Dispatches tasks to specialist agents
- Collects and compares all agent outputs
- Enforces confidence thresholds per tier
- Makes GO / HOLD / ESCALATE decision
- Only agent that can release a payload

Inputs:
- raw_xml (string)
- target_schema (dict)
- Classification Registry (loaded at startup)

Outputs:
- decision (GO / HOLD / ESCALATE)
- decision_reason (string)
- transformed_payload (dict or None)
- audit_log (list)

LOCKED RULES (never change without @TechLead):
- T1 confidence threshold = 1.0
- T2 confidence threshold = 0.95
- Dual agent mandatory for ALL T1 fields
- Orchestrator is the ONLY release gate
```

---

### Interpreter Agent
```
Status:    🟡 In Progress
File:      backend/core/agents/interpreter.py
Role:      Semantic field mapping via Claude API

Responsibilities:
- Receives individual XML field + value
- Understands the semantic meaning of the field
- Maps to the most appropriate target JSON field
- Returns confidence score for the mapping
- Provides reasoning for the mapping decision

Inputs:
- field_name (string)
- field_value (string)
- field_tier (int)
- target_schema (dict)
- domain_context (string)

Outputs:
- target_field (string)
- transformed_value (any)
- confidence (float 0.0-1.0)
- reasoning (string)

LangChain Integration:
- Uses ChatAnthropic with claude-sonnet-4-20250514
- Structured output parsing via Pydantic
- Prompt template loaded from prompts/interpreter.txt

T1 Behaviour:
- Called twice independently for any T1 field
- Second call has no knowledge of first call result
- Orchestrator compares both outputs
```

---

### Validator Agent
```
Status:    ⚪ Planned (Phase 2)
File:      backend/core/agents/validator.py
Role:      Schema constraint and anomaly detection

Responsibilities:
- Validates transformed value against target schema type
- Checks value ranges and constraints
- Cross-checks field dependencies
- Flags anomalies with severity level
- Does NOT block payload (advisory only)
- Orchestrator decides action based on flags

Inputs:
- field_name (string)
- transformed_value (any)
- target_schema (dict)
- tier (int)

Outputs:
- valid (bool)
- anomaly (bool)
- severity (LOW / MEDIUM / HIGH / None)
- detail (string)

Anomaly Severity Rules:
- HIGH   → T1 or T2 field out of valid range
- MEDIUM → T3 field missing or unexpected type
- LOW    → T4 field issue
```

---

### Translator Agent
```
Status:    ⚪ Planned (Phase 1)
File:      backend/core/agents/translator.py
Role:      Final JSON payload construction

Responsibilities:
- Takes all agreed interpreter mappings
- Constructs target JSON payload
- Applies field naming conventions of target schema
- Handles optional vs required field rules
- Enforces target API contract

Inputs:
- interpreter_agreed (dict of FieldMapping)
- target_schema (dict)
- validation_results (dict)

Outputs:
- translated_payload (dict)
- missing_required_fields (list)
- omitted_fields (list)
```

---

### Audit Agent
```
Status:    ⚪ Planned (Phase 3)
File:      backend/core/agents/audit.py
Role:      Immutable transformation audit logging

Responsibilities:
- Creates audit entry for every field transformation
- Records orchestrator decision with full reasoning
- Records escalation details with field trace
- Ensures log entries are immutable
- Provides audit log export

Inputs:
- All state from NexBridgeState
- Decision and reasoning from orchestrator

Outputs:
- audit_log (list of AuditEntry)
- Each entry contains: timestamp, field, tier,
  original value, transformed value, confidence,
  agent, decision, reasoning

LOCKED RULES:
- Audit entries are NEVER deleted
- Audit entries are NEVER modified after creation
- Every T1 field MUST have an audit entry
```

---

## Classification Registry

```
Status:    🟡 In Progress
File:      backend/core/classification/registry.py
Config:    backend/core/classification/registry.json
Role:      Maps field names to risk tiers

Responsibilities:
- Loads registry.json at API startup
- Caches registry in memory
- Provides classify_field(field_name) method
- Returns FieldClassification with tier + threshold
- Unknown fields default to Tier 4

LOCKED RULES:
- T1 fields can only be added with @TechLead approval
- Registry is read-only at runtime
- Default tier for unknown fields = 4
```

---

## LangGraph State

```
File:   backend/core/models.py
Class:  NexBridgeState

All agents read from and write to this shared state.
No agent communicates directly with another agent.
All communication goes through shared state.
```

---

## Change Impact Matrix

| If you change... | Impact on... | Risk |
|---|---|---|
| orchestrator.py | Entire pipeline | 🔴 High |
| registry.py | All tier decisions | 🔴 High |
| interpreter.py | T1 dual-agent flow | 🔴 High |
| validator.py | Anomaly detection | 🟡 Medium |
| translator.py | Output payload shape | 🟡 Medium |
| audit.py | Compliance logging | 🔴 High |
| registry.json | Field tier assignments | 🟡 Medium |
| models.py (state) | All agents | 🔴 High |

---

**Document Version:** 1.0
**Project:** NexBridge
**Maintained By:** Lasith Jayarathne (@TechLead)
**Last Updated:** March 2026
