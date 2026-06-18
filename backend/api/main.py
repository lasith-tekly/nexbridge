"""
NexBridge FastAPI application — entry point and route definitions.

Part of the NexBridge transformation pipeline.
See docs/SOLUTION_AGENTS.md for full specification.
"""

# Standard library
import time

# Third-party
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError

# Local — core pipeline
from backend.core.state import NexBridgeState
from backend.core.orchestrator import build_graph
from backend.core.exceptions import ParseError

# Local — API schemas
from backend.api.schemas import (
    TransformRequestSchema,
    TransformResponseSchema,
)


# ── App setup ─────────────────────────────────────────────────────────────────

app = FastAPI(
    title="NexBridge API",
    version="0.3.0",
    description="AI-governed middleware for bidirectional format transformation",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.post("/transform", response_model=TransformResponseSchema)
async def transform(request: TransformRequestSchema) -> TransformResponseSchema:
    """
    Transform a payload from source_format to target_format.

    Runs the full NexBridge LangGraph pipeline:
    classification → interpreter → validator → translator → orchestrator.
    Returns GO/HOLD decision with the translated payload.
    """
    try:
        # a. Record start time in milliseconds
        start_ms = time.time_ns() // 1_000_000

        # b. Build initial NexBridgeState
        state: NexBridgeState = {
            "raw_payload": request.payload,
            "source_format": request.source_format,
            "target_format": request.target_format,
            "target_schema": request.target_schema,
            "root_element": request.root_element,
            "field_classifications": {},
            "parsed_fields": {},
            "payload_tier": 0,
            "interpreter_run_1": {},
            "interpreter_run_2": {},
            "validation_result": {},
            "translated_payload": None,
            "decision": None,
            "decision_reason": None,
            "confidence_scores": {},
            "audit_log": [],
            "processing_start_ms": start_ms,
        }

        # c. Run pipeline
        graph = build_graph()
        result = graph.invoke(state)

        # d. Calculate processing time
        processing_time_ms = (time.time_ns() // 1_000_000) - start_ms

        # e. Get anomaly count from validation_result
        anomaly_count = (
            result.get("validation_result", {}).get("anomaly_count", 0)
        )

        # f. Return response
        return TransformResponseSchema(
            decision=result["decision"],
            decision_reason=result["decision_reason"],
            payload_tier=result["payload_tier"],
            translated_payload=result["translated_payload"],
            confidence_scores=result["confidence_scores"],
            anomaly_count=anomaly_count,
            processing_time_ms=processing_time_ms,
        )

    except ParseError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        print(f"[API] Unhandled pipeline error: {e}")
        raise HTTPException(status_code=500, detail="Internal pipeline error")
