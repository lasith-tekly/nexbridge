# NexBridge - Technical Architecture

## Overview

NexBridge is a multi-agent orchestration system built on LangGraph.
The architecture separates concerns clearly — the orchestrator governs,
agents process, and FastAPI exposes the pipeline as a REST service.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    CLIENT LAYER                         │
│         React Demo UI  |  REST API Consumers            │
└──────────────────────────┬──────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────┐
│                   FASTAPI LAYER                         │
│              backend/api/main.py                        │
│     POST /transform  |  GET /health  |  GET /registry   │
└──────────────────────────┬──────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────┐
│               NEXBRIDGE CORE ENGINE                     │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │           ORCHESTRATION AGENT                   │   │
│  │         core/orchestrator.py                    │   │
│  │                                                 │   │
│  │  • Reads Classification Registry               │   │
│  │  • Assigns tier protocol                       │   │
│  │  • Dispatches to agents via LangGraph          │   │
│  │  • Enforces confidence thresholds              │   │
│  │  • Makes GO / HOLD / ESCALATE decision         │   │
│  │  • Only entity that releases payload           │   │
│  └──────────────┬──────────────────────────────────┘   │
│                 │                                       │
│  ┌──────────────▼──────────────────────────────────┐   │
│  │         LANGGRAPH STATE MACHINE                 │   │
│  │                                                 │   │
│  │  classify → interpret → validate → translate   │   │
│  │       ↓ (T1 only)                              │   │
│  │  dual_interpret → compare → go/hold            │   │
│  └──────────────┬──────────────────────────────────┘   │
│                 │                                       │
│  ┌──────────────▼──────────────────────────────────┐   │
│  │              AGENT LAYER                        │   │
│  │                                                 │   │
│  │  interpreter.py  validator.py  translator.py   │   │
│  │                    audit.py                    │   │
│  └──────────────┬──────────────────────────────────┘   │
│                 │                                       │
│  ┌──────────────▼──────────────────────────────────┐   │
│  │         CLASSIFICATION REGISTRY                 │   │
│  │      core/classification/registry.py            │   │
│  │                                                 │   │
│  │  Field name → Tier mapping (JSON config)       │   │
│  │  Loaded at startup, cached in memory           │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

---

## LangGraph State Machine

### NexBridgeState (Shared State Object)
```python
class NexBridgeState(TypedDict):
    # Input
    raw_xml: str
    target_schema: dict

    # Classification
    field_classifications: dict[str, FieldClassification]
    payload_tier: int

    # Interpreter outputs
    interpreter_run_1: dict[str, FieldMapping]
    interpreter_run_2: dict[str, FieldMapping]  # T1 only
    interpreter_agreed: dict[str, FieldMapping]

    # Validation
    validation_results: dict[str, ValidationResult]
    anomalies: list[Anomaly]

    # Translation
    translated_payload: dict

    # Audit
    audit_log: list[AuditEntry]

    # Orchestrator decision
    decision: Literal["GO", "HOLD", "ESCALATE"]
    decision_reason: str
    confidence_scores: dict[str, float]
```

### Graph Nodes
```
classify_fields      → reads registry, assigns tier per field
interpret_fields     → LLM interprets XML field semantics
dual_interpret       → runs interpreter twice (T1 only)
compare_outputs      → checks for divergence (T1 only)
validate_fields      → checks constraints and anomalies
translate_payload    → builds target JSON
log_audit            → writes immutable audit entries
make_decision        → GO / HOLD / ESCALATE
```

### Graph Edges
```
classify_fields
    → dual_interpret    (if payload_tier == 1)
    → interpret_fields  (if payload_tier > 1)

dual_interpret
    → compare_outputs

compare_outputs
    → validate_fields   (if outputs match)
    → make_decision     (HOLD if diverged)

interpret_fields
    → validate_fields

validate_fields
    → translate_payload

translate_payload
    → log_audit

log_audit
    → make_decision
```

---

## Backend Architecture

### File Structure
```
backend/
├── core/
│   ├── orchestrator.py              ← LangGraph graph definition
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── interpreter.py           ← Field semantic mapping
│   │   ├── validator.py             ← Schema constraint checking
│   │   ├── translator.py            ← JSON payload construction
│   │   └── audit.py                 ← Audit log management
│   ├── classification/
│   │   ├── __init__.py
│   │   └── registry.py              ← Tier classification registry
│   ├── models.py                    ← Pydantic + LangGraph state
│   └── exceptions.py                ← Custom exception classes
├── api/
│   ├── __init__.py
│   ├── main.py                      ← FastAPI app + routes
│   ├── schemas.py                   ← API request/response models
│   └── dependencies.py              ← Shared FastAPI dependencies
├── tests/
│   ├── test_registry.py
│   ├── test_interpreter.py
│   ├── test_orchestrator.py
│   └── test_api.py
├── requirements.txt
└── .env
```

### Key Dependencies
```
langchain==1.2.10          AI agent toolkit
langgraph                  Multi-agent state machine
langchain-anthropic==1.3.4 Claude API integration
fastapi                    REST API framework
uvicorn                    ASGI server
pydantic                   Data validation
python-dotenv              Environment variable loading
pytest                     Testing framework
```

---

## Frontend Architecture

### File Structure
```
frontend/
├── src/
│   ├── components/
│   │   ├── PayloadInput.tsx          ← XML paste area
│   │   ├── SchemaInput.tsx           ← Target schema definition
│   │   ├── AgentPipeline.tsx         ← Visual agent flow
│   │   ├── AgentCard.tsx             ← Per-agent status card
│   │   ├── TierBadge.tsx             ← Tier classification badge
│   │   ├── ConfidenceBar.tsx         ← Confidence score display
│   │   ├── TransformResult.tsx       ← Final JSON output
│   │   └── AuditLog.tsx              ← Audit log viewer
│   ├── services/
│   │   └── nexbridgeApi.ts           ← FastAPI integration
│   ├── types/
│   │   └── nexbridge.types.ts        ← TypeScript type definitions
│   ├── constants/
│   │   └── tiers.ts                  ← Tier colour constants
│   ├── App.tsx
│   └── main.tsx
├── package.json
└── tailwind.config.js
```

---

## API Design

### POST /transform
```
Request:
{
  "xml_payload": "<flight>...</flight>",
  "target_schema": { ... },
  "options": {
    "strict_mode": true
  }
}

Response:
{
  "status": "GO" | "HOLD" | "ESCALATE",
  "transformed_payload": { ... },
  "decision_reason": "...",
  "confidence_scores": { "field": 0.98 },
  "audit_log": [ ... ],
  "processing_time_ms": 1240
}
```

### GET /registry
```
Response:
{
  "fields": [
    { "field_name": "MTOW", "tier": 1, "label": "Safety Critical" },
    { "field_name": "FlightNumber", "tier": 2, "label": "Operationally Sensitive" }
  ]
}
```

### GET /health
```
Response:
{
  "status": "healthy",
  "registry_loaded": true,
  "agent_count": 4
}
```

---

## Environment Variables

```
ANTHROPIC_API_KEY=          Required. Claude API key.
NEXBRIDGE_ENV=development   development | production
LOG_LEVEL=DEBUG             DEBUG | INFO | WARNING | ERROR
T1_CONFIDENCE_THRESHOLD=1.0 Hardcoded. Do not change.
T2_CONFIDENCE_THRESHOLD=0.95 Hardcoded. Do not change.
PORT=8000                   FastAPI port
```

---

**Document Version:** 1.0
**Project:** NexBridge
**Maintained By:** Lasith Jayarathne (@TechLead)
**Last Updated:** March 2026
