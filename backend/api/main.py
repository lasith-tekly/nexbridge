"""
NexBridge FastAPI application — entry point and route definitions.

Part of the NexBridge transformation pipeline.
See docs/SOLUTION_AGENTS.md for full specification.
"""

# Standard library
import time

# Third-party
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError

load_dotenv()

# Local — core pipeline
from backend.core.state import NexBridgeState
from backend.core.orchestrator import build_graph
from backend.core.exceptions import ParseError, RegistryNotFoundError
from backend.core.classification.registry import ClassificationRegistry, list_available_registries

# Local — API schemas
from backend.api.schemas import (
    TransformRequestSchema,
    TransformResponseSchema,
    HealthResponse,
    RegistryResponse,
    RegistryFieldInfo,
    RegistriesResponse,
    ClassifyRequest,
    ClassifyResponse,
    AnalyseRequest,
    AnalyseResponse,
    ExportRequest,
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
        # a. Validate registry_id exists before entering the pipeline —
        # RegistryNotFoundError raised inside graph.invoke() may be
        # wrapped by LangGraph and miss the typed except clause below.
        ClassificationRegistry.load(request.registry_id)

        # b. Record start time in milliseconds
        start_ms = time.time_ns() // 1_000_000

        # c. Build initial NexBridgeState — registry_id passed into state
        state: NexBridgeState = {
            "raw_payload": request.payload,
            "source_format": request.source_format,
            "target_format": request.target_format,
            "target_schema": request.target_schema,
            "root_element": request.root_element,
            "registry_id": request.registry_id,
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

        # d. Run pipeline
        graph = build_graph()
        result = graph.invoke(state)

        # e. Calculate processing time
        processing_time_ms = (time.time_ns() // 1_000_000) - start_ms

        # f. Get anomaly count from validation_result
        anomaly_count = (
            result.get("validation_result", {}).get("anomaly_count", 0)
        )

        # g. Return response
        return TransformResponseSchema(
            decision=result["decision"],
            decision_reason=result["decision_reason"],
            payload_tier=result["payload_tier"],
            translated_payload=result["translated_payload"],
            confidence_scores=result["confidence_scores"],
            anomaly_count=anomaly_count,
            processing_time_ms=processing_time_ms,
        )

    except RegistryNotFoundError as e:
        raise HTTPException(
            status_code=404,
            detail=f"Registry '{e.registry_id}' not found. Available: {', '.join(e.available)}"
        )
    except ParseError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        print(f"[API] Unhandled pipeline error: {e}")
        raise HTTPException(status_code=500, detail="Internal pipeline error")


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Return service status and registry field count."""
    try:
        registry = ClassificationRegistry()
        return HealthResponse(
            status="ok",
            version="0.3.0",
            registry_fields=len(registry.list_all_fields()),
        )
    except Exception as e:
        print(f"[API] Health check — registry unavailable: {e}")
        return HealthResponse(
            status="degraded",
            version="0.3.0",
            registry_fields=0,
        )


@app.get("/registry", response_model=RegistryResponse)
async def get_registry(
    registry_id: str = Query(default="default", description="Registry ID to load")
) -> RegistryResponse:
    """Return full classification registry with tier and threshold per field."""
    try:
        registry = ClassificationRegistry.load(registry_id)
        all_fields = registry.list_all_fields()
        fields = {
            field_name: RegistryFieldInfo(
                tier=field_data["tier"],
                label=field_data["label"],
                threshold=field_data["threshold"],
            )
            for field_name, field_data in all_fields.items()
        }
        return RegistryResponse(
            version=registry.get_version(),
            domain=registry.get_domain(),
            field_count=len(fields),
            fields=fields,
        )
    except RegistryNotFoundError as e:
        raise HTTPException(
            status_code=404,
            detail=f"Registry '{e.registry_id}' not found. Available: {', '.join(e.available)}"
        )
    except Exception as e:
        print(f"[API] Registry load error: {e}")
        raise HTTPException(status_code=500, detail="Registry unavailable")


@app.post("/classify", response_model=ClassifyResponse)
async def classify(request: ClassifyRequest) -> ClassifyResponse:
    """Classify a list of field names and return tier assignments."""
    try:
        registry = ClassificationRegistry.load(request.registry_id)
        classifications = {}
        for field_name in request.field_names:
            fc = registry.classify(field_name)
            classifications[field_name] = RegistryFieldInfo(
                tier=fc.tier.value,
                label=fc.label,
                threshold=fc.confidence_threshold,
            )
        payload_tier = registry.get_payload_tier(request.field_names)
        return ClassifyResponse(
            payload_tier=payload_tier,
            classifications=classifications,
        )
    except RegistryNotFoundError as e:
        raise HTTPException(
            status_code=404,
            detail=f"Registry '{e.registry_id}' not found. Available: {', '.join(e.available)}"
        )
    except Exception as e:
        print(f"[API] Classify error: {e}")
        raise HTTPException(status_code=500, detail="Classification failed")


@app.get("/registries", response_model=RegistriesResponse)
async def list_registries() -> RegistriesResponse:
    """Return the list of available registry IDs."""
    registries = list_available_registries()
    return RegistriesResponse(registries=registries, count=len(registries))


@app.post("/registry/analyse", response_model=AnalyseResponse)
async def analyse_registry(request: AnalyseRequest) -> AnalyseResponse:
    """Stub — Registry analysis is available in Phase 4."""
    raise HTTPException(
        status_code=501,
        detail="Registry analysis is available in Phase 4. Use registry.json directly for now.",
    )


@app.post("/registry/export", response_model=None)
async def export_registry(request: ExportRequest) -> None:
    """Stub — Registry export is available in Phase 4."""
    raise HTTPException(
        status_code=501,
        detail="Registry export is available in Phase 4. Use registry.json directly for now.",
    )
