# NexBridge - Data Flows

## Overview

This document describes the critical data flows through the
NexBridge pipeline. Each flow maps the exact path data takes
from input to output, including all agent interactions
and state transitions.

---

## Flow 1: Standard Transformation (T3/T4 Payload)

```
CLIENT
  │
  │  POST /transform
  │  { xml_payload, target_schema }
  │
  ▼
FASTAPI (main.py)
  │
  │  Validates request schema
  │  Creates NexBridgeState
  │
  ▼
ORCHESTRATOR
  │
  │  Loads Classification Registry
  │  Classifies all fields
  │  Determines payload_tier = 3 or 4
  │
  ▼
LANGGRAPH: classify_fields node
  │
  │  state.field_classifications = { field: tier }
  │  state.payload_tier = 3
  │
  ▼
LANGGRAPH: interpret_fields node
  │
  ├── INTERPRETER AGENT
  │     Calls Claude API with field context
  │     Returns field mappings + confidence scores
  │     state.interpreter_run_1 = { field: mapping }
  │     state.confidence_scores = { field: 0.95 }
  │
  ▼
LANGGRAPH: validate_fields node
  │
  ├── VALIDATOR AGENT
  │     Checks value ranges and constraints
  │     Checks required field presence
  │     state.validation_results = { field: result }
  │     state.anomalies = []
  │
  ▼
LANGGRAPH: translate_payload node
  │
  ├── TRANSLATOR AGENT
  │     Builds target JSON from agreed mappings
  │     state.translated_payload = { ... }
  │
  ▼
LANGGRAPH: log_audit node
  │
  ├── AUDIT AGENT
  │     Logs every field transformation
  │     state.audit_log = [ entries ]
  │
  ▼
LANGGRAPH: make_decision node
  │
  ├── ORCHESTRATOR
  │     Checks all confidence scores vs thresholds
  │     All above threshold → GO
  │     state.decision = "GO"
  │
  ▼
FASTAPI
  │
  │  Returns response:
  │  { status: "GO", transformed_payload, audit_log }
  │
  ▼
CLIENT
```

---

## Flow 2: Safety-Critical Transformation (T1 Payload)

```
CLIENT
  │
  │  POST /transform
  │  { xml_payload containing T1 field }
  │
  ▼
FASTAPI → ORCHESTRATOR
  │
  │  Detects T1 field in payload
  │  Sets payload_tier = 1
  │  Routes to dual_interpret node
  │
  ▼
LANGGRAPH: dual_interpret node
  │
  ├── INTERPRETER AGENT (Run 1)
  │     Independent Claude API call
  │     state.interpreter_run_1 = { field: mapping_A }
  │
  ├── INTERPRETER AGENT (Run 2)
  │     Completely independent Claude API call
  │     No shared context with Run 1
  │     state.interpreter_run_2 = { field: mapping_B }
  │
  ▼
LANGGRAPH: compare_outputs node
  │
  ├── ORCHESTRATOR COMPARISON
  │
  │   ┌─────────────────┬──────────────────────────────┐
  │   │   MATCH?        │   ACTION                     │
  │   ├─────────────────┼──────────────────────────────┤
  │   │   YES           │   → proceed to validate      │
  │   │   NO (diverge)  │   → HOLD + escalate          │
  │   └─────────────────┴──────────────────────────────┘
  │
  ▼ (if MATCH)
LANGGRAPH: validate_fields → translate_payload → log_audit
  │
  ▼
LANGGRAPH: make_decision node
  │
  ├── Confidence check for T1 fields
  │
  │   ┌──────────────────┬─────────────────────────────┐
  │   │   CONFIDENCE     │   ACTION                    │
  │   ├──────────────────┼─────────────────────────────┤
  │   │   = 1.0          │   GO                        │
  │   │   < 1.0          │   HOLD + escalate           │
  │   └──────────────────┴─────────────────────────────┘
  │
  ▼ (if GO)
CLIENT receives: { status: "GO", transformed_payload, audit_log }

  ▼ (if HOLD)
CLIENT receives: { status: "HOLD", reason, field_trace, audit_log }
```

---

## Flow 3: Escalation Flow

```
ORCHESTRATOR detects HOLD condition
  │
  │  Conditions:
  │  - T1 dual-agent divergence
  │  - T1 confidence < 1.0
  │  - T1 validator anomaly
  │
  ▼
AUDIT AGENT
  │  Logs HOLD decision with full reasoning
  │  Records all field-level details
  │  Records both interpreter outputs (if diverged)
  │
  ▼
ORCHESTRATOR
  │  Sets state.decision = "HOLD"
  │  Sets state.decision_reason = detailed explanation
  │
  ▼
FASTAPI
  │  Returns 200 with HOLD status (not an error)
  │  { status: "HOLD",
  │    reason: "T1 field MTOW: interpreter divergence",
  │    field_trace: { ... },
  │    audit_log: [ ... ] }
  │
  ▼
CLIENT / HUMAN
  Reviews field trace and audit log
  Resolves ambiguity
  Resubmits with corrected or confirmed values
```

---

## State Transitions

```
INITIAL → CLASSIFYING → INTERPRETING → VALIDATING → TRANSLATING → AUDITING → DECIDED

                ↓ (T1 detected)
          DUAL_INTERPRETING
                ↓
          COMPARING
                ↓ (diverged)
          HELD ────────────────────────────────────────────────────────────►  END
                ↓ (agreed)
          VALIDATING → TRANSLATING → AUDITING → DECIDED
```

---

## Agent Data Contracts

### Interpreter Agent Input
```python
{
  "field_name": str,        # XML field name
  "field_value": str,       # Raw XML value
  "field_tier": int,        # Classification tier
  "target_schema": dict,    # Target JSON schema
  "context": str            # Domain context hint
}
```

### Interpreter Agent Output
```python
{
  "field_name": str,
  "target_field": str,      # Mapped JSON field name
  "transformed_value": Any, # Transformed value
  "confidence": float,      # 0.0 to 1.0
  "reasoning": str          # Why this mapping was chosen
}
```

### Validator Agent Input
```python
{
  "field_name": str,
  "transformed_value": Any,
  "target_schema": dict,
  "tier": int
}
```

### Validator Agent Output
```python
{
  "field_name": str,
  "valid": bool,
  "anomaly": bool,
  "severity": "LOW" | "MEDIUM" | "HIGH" | None,
  "detail": str
}
```

### Audit Entry Structure
```python
{
  "timestamp": str,         # ISO 8601
  "field_name": str,
  "tier": int,
  "original_value": str,
  "transformed_value": Any,
  "confidence": float,
  "agent": str,
  "decision": str,
  "reasoning": str
}
```

---

**Document Version:** 1.0
**Project:** NexBridge
**Maintained By:** Lasith Jayarathne (@TechLead)
**Last Updated:** March 2026
