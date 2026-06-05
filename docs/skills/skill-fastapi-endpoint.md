# Skill — FastAPI Endpoints

## When To Use This Skill

Load this file before writing any FastAPI endpoint,
router, schema, or middleware in NexBridge.

---

## App Setup Pattern

```python
# backend/api/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api.routers import transform, registry, health

app = FastAPI(
    title="NexBridge API",
    description="Governed AI transformation middleware",
    version="0.1.0",
)

# CORS — allow React frontend on localhost:3000
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(health.router)
app.include_router(transform.router)
app.include_router(registry.router)
```

---

## Standard Endpoint Pattern

```python
from fastapi import APIRouter, HTTPException
from backend.core.models import TransformRequest, TransformResponse

router = APIRouter()

@router.post(
    "/transform",
    response_model=TransformResponse,
    summary="Transform XML payload to JSON",
    description="Runs the full NexBridge governed pipeline.",
)
async def transform_payload(request: TransformRequest) -> TransformResponse:
    """
    Receives an XML payload and target schema.
    Returns governed JSON transformation or HOLD decision.
    """
    try:
        result = await run_pipeline(
            xml_payload=request.xml_payload,
            target_schema=request.target_schema,
        )
        return result

    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    except Exception as e:
        raise HTTPException(status_code=500, detail="Pipeline error")
```

---

## NexBridge Endpoints Reference

```
POST /transform     Run full pipeline, returns TransformResponse
GET  /health        Health check, returns version + status
GET  /registry      Return full classification registry
POST /classify      Classify a single field (utility endpoint)
```

---

## Health Endpoint Pattern

```python
@router.get("/health")
async def health_check():
    return {
        "status":  "ok",
        "version": "0.1.0",
        "phase":   "2",
    }
```

---

## Error Response Pattern

```python
from fastapi import HTTPException
from pydantic import BaseModel

class ErrorResponse(BaseModel):
    detail:    str
    field:     str | None = None
    code:      str | None = None

# Usage in endpoint
raise HTTPException(
    status_code=422,
    detail={
        "detail": "T1 field confidence below threshold",
        "field":  "weight_limit",
        "code":   "T1_THRESHOLD_BREACH",
    }
)
```

---

## Request / Response Schema Pattern

```python
# backend/api/schemas.py
# Separate from core models — these are the API contracts

from pydantic import BaseModel, Field

class TransformRequest(BaseModel):
    xml_payload:   str  = Field(..., min_length=1,
                                description="Raw XML string from System A")
    target_schema: dict = Field(...,
                                description="Target JSON schema from System B")

    model_config = {
        "json_schema_extra": {
            "example": {
                "xml_payload": "<record><employee_id>E-12345</employee_id></record>",
                "target_schema": {"id": "string"},
            }
        }
    }
```

---

## Async Pipeline Call Pattern

```python
import asyncio
from backend.core.orchestrator import build_graph
from backend.core.state import NexBridgeState
import time

async def run_pipeline(
    xml_payload:   str,
    target_schema: dict,
) -> TransformResponse:

    graph = build_graph()

    initial_state = NexBridgeState(
        xml_payload=xml_payload,
        target_schema=target_schema,
        field_classifications={},
        payload_tier=0,
        interpreter_run_1={},
        interpreter_run_2={},
        validation_result={},
        translated_payload=None,
        decision=None,
        decision_reason=None,
        confidence_scores={},
        audit_log=[],
        processing_start_ms=int(time.time() * 1000),
    )

    # LangGraph invoke (sync wrapped in executor for async endpoint)
    loop   = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None,
        graph.invoke,
        initial_state,
    )

    return TransformResponse(
        status=result["decision"],
        transformed_payload=result["translated_payload"],
        payload_tier=result["payload_tier"],
        decision_reason=result["decision_reason"],
        confidence_scores=result["confidence_scores"],
        field_classifications=result["field_classifications"],
        field_mappings=result["interpreter_run_1"],
        divergence=result.get("divergence"),
        audit_log=result["audit_log"],
        processing_time_ms=int(time.time() * 1000)
                           - result["processing_start_ms"],
    )
```

---

## Running the API

```bash
# Development
uvicorn backend.api.main:app --reload --port 8000

# Docs (auto-generated)
open http://localhost:8000/docs

# Health check
curl http://localhost:8000/health
```

---

## NexBridge API Rules

```
✅ All endpoints use Pydantic v2 request/response models
✅ POST /transform always returns TransformResponse shape
✅ HOLD decision returns 200 (not 4xx) — it is a valid outcome
✅ CORS must allow localhost:3000 in development
✅ Errors use HTTPException with structured detail dict
❌ Never return raw state dict from endpoints
❌ Never expose audit_log internals beyond TransformResponse
❌ Never allow pipeline bypass via API parameters
```
