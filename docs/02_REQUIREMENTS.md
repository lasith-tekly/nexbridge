# NexBridge - Requirements

## Overview

This document defines the functional requirements, business rules,
user workflows, and validation rules for NexBridge.

---

## Functional Requirements

### FR-01: Protocol Transformation
- System must accept XML payloads as input
- System must produce JSON payloads as output
- System must support configurable source and target schemas
- System must handle optional and required fields differently
- System must preserve data fidelity across transformation

### FR-02: Data Classification
- System must classify every field in a payload before transformation
- Classification must use the 4-tier registry (T1/T2/T3/T4)
- Classification registry must be configurable by domain experts
- Payload must inherit the highest tier of any field it contains
- Classification result must be included in the audit log

### FR-03: Orchestration
- Orchestrator must be the sole entity that releases a payload
- Orchestrator must dispatch fields to agents based on tier
- Orchestrator must collect and compare all agent outputs
- Orchestrator must enforce confidence thresholds per tier
- Orchestrator must make go / hold / escalate decisions

### FR-04: Agent Processing
- Interpreter Agent must parse and semantically map XML fields
- Validator Agent must check fields against schema constraints
- Translator Agent must construct the target JSON payload
- Audit Agent must log every transformation decision
- All agents must return structured outputs with confidence scores

### FR-05: Tier 1 Dual-Agent Verification
- Any payload containing a T1 field must trigger dual-agent flow
- Interpreter Agent must run twice independently for T1 fields
- Orchestrator must compare both outputs before proceeding
- Any divergence between outputs must trigger HOLD
- Human escalation must be raised on any T1 divergence

### FR-06: Confidence Thresholds
- Tier 1 threshold = 1.0 — no exceptions
- Tier 2 threshold = 0.95
- Tier 3 threshold = 0.80
- Tier 4 threshold = 0.0 (best effort)
- Any field below its tier threshold must trigger the appropriate action

### FR-07: Audit Logging
- Every field transformation must produce an audit log entry
- Every orchestrator decision must be logged with reasoning
- Every escalation must include full field trace
- Audit logs must be immutable — never modified or deleted
- Audit logs must be exportable as structured JSON

### FR-08: API Layer
- System must expose a REST API via FastAPI
- API must accept XML payload and target schema as input
- API must return transformed JSON payload + audit log
- API must return structured error responses on failure
- API must support async processing for large payloads

### FR-09: Demo UI
- UI must allow paste of raw XML payload
- UI must allow definition of target JSON schema
- UI must show real-time agent processing status
- UI must display tier classification per field
- UI must display confidence scores per field
- UI must show go / hold / escalate decision with reasoning
- UI must display full audit log after transformation

---

## Business Rules

### Classification Rules
```
BR-01: A field not found in the registry defaults to Tier 4
BR-02: If ANY field in a payload is T1, entire payload is T1
BR-03: Classification registry is the single source of truth
BR-04: Only @TechLead can approve changes to T1 field mappings
BR-05: Classification registry is loaded at startup and cached
```

### Confidence Rules
```
BR-06: T1 confidence below 1.0 → HOLD, no exceptions
BR-07: T2 confidence below 0.95 → FLAG anomaly, may proceed
BR-08: T3 confidence below 0.80 → LOG only, non-blocking
BR-09: T4 fields → always proceed regardless of confidence
BR-10: Confidence scores must be between 0.0 and 1.0
```

### Orchestrator Rules
```
BR-11: Orchestrator is the ONLY agent that can release payload
BR-12: All other agents are advisory to the orchestrator
BR-13: Orchestrator must not release if any T1 field is below threshold
BR-14: Orchestrator must not release if validator flags T1 anomaly
BR-15: Orchestrator must log its decision reasoning before releasing
```

### Dual Agent Rules
```
BR-16: Dual agent runs must be independent — no shared state
BR-17: Outputs are compared field by field
BR-18: Divergence = any difference in mapping or confidence
BR-19: Divergence always results in HOLD regardless of tier
BR-20: Human must explicitly resolve before retry is allowed
```

---

## User Workflows

### Workflow 1: Standard Transformation (T3/T4 payload)
```
1. User submits XML payload via API or demo UI
2. Parser extracts fields
3. Orchestrator classifies all fields via registry
4. Orchestrator determines payload tier = T3 or T4
5. Interpreter Agent maps all fields (single run)
6. Validator Agent checks constraints
7. Translator Agent builds JSON payload
8. Audit Agent logs transformation
9. Orchestrator checks confidence — all above threshold
10. Orchestrator releases JSON payload
11. User receives: JSON payload + audit log
```

### Workflow 2: High-Stakes Transformation (T1/T2 payload)
```
1. User submits XML payload via API or demo UI
2. Parser extracts fields
3. Orchestrator classifies all fields — detects T1 field
4. Orchestrator triggers DUAL interpreter runs
5. Both interpreter outputs returned to orchestrator
6. Orchestrator compares outputs field by field
7a. If outputs MATCH:
    → Validator checks constraints
    → Translator builds JSON
    → Audit logs full trace
    → Orchestrator releases if confidence = 1.0
7b. If outputs DIVERGE or confidence < 1.0:
    → Orchestrator triggers HOLD
    → Audit logs divergence details
    → Human escalation raised
    → User notified with full field trace
```

### Workflow 3: Schema Change Adaptation
```
1. Domain expert updates classification registry
2. New field mappings added with tier assignments
3. Registry reloads at next API startup
4. Interpreter Agent automatically handles new fields
5. No code changes required
```

---

## Validation Rules

### Input Validation
```
VR-01: XML payload must be well-formed XML
VR-02: Target schema must be valid JSON schema
VR-03: Classification registry must be loaded before processing
VR-04: ANTHROPIC_API_KEY must be present in environment
VR-05: Empty payloads must return structured error, not crash
```

### Output Validation
```
VR-06: Output JSON must validate against target schema
VR-07: All T1 fields must appear in audit log
VR-08: Confidence scores must be present for all fields
VR-09: Orchestrator decision must be present in response
VR-10: Audit log must have timestamp for every entry
```

---

**Document Version:** 1.0
**Project:** NexBridge
**Maintained By:** Lasith Jayarathne (@TechLead)
**Last Updated:** March 2026
