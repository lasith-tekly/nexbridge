"""
NexBridge FastAPI application — entry point and route definitions.

Part of the NexBridge transformation pipeline.
See docs/SOLUTION_AGENTS.md for full specification.
"""

# Standard library
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

# Third-party
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError

load_dotenv()

# Local — core pipeline
from backend.core.state import NexBridgeState
from backend.core.orchestrator import build_graph
from backend.core.exceptions import ParseError, RegistryNotFoundError, NexBridgeError
from backend.core.constants import CONFIDENCE_THRESHOLDS
from backend.core.classification.registry import ClassificationRegistry, list_available_registries
from backend.core.format_registry import get_parser
from backend.core.agents.registry_analyser import analyse_fields

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
    AnalysedField,
    AnalyseResponse,
    ExportRequest,
    ExportResponse,
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
    """
    Analyse a payload's fields and return AI-suggested tier classifications.

    Extracts field names from the payload, runs a single LLM batch call,
    and returns suggested tiers with reasoning for each field.
    """
    try:
        parser = get_parser(request.source_format)
        field_names = parser.extract_field_names(request.payload)

        results = analyse_fields(
            field_names=field_names,
            source_format=request.source_format,
            context=request.context,
        )

        return AnalyseResponse(
            fields=[AnalysedField(**r) for r in results],
            source_format=request.source_format,
            field_count=len(results),
        )
    except ParseError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except NexBridgeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        print(f"[API] Unhandled analyse error: {e}")
        raise HTTPException(status_code=500, detail="Internal analyse error")


@app.post("/registry/export", response_model=ExportResponse)
async def export_registry(request: ExportRequest) -> ExportResponse:
    """
    Build and optionally save a registry.json from confirmed field classifications.

    Validates T1 safety rules, serialises to JSON, writes to REGISTRY_DIR if set,
    and returns the full content for client-side download.
    """
    # a. Validate T1 safety rules before touching the filesystem
    for field in request.fields:
        if field.tier == 1:
            if field.threshold != CONFIDENCE_THRESHOLDS[1]:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"T1 field '{field.field_name}' must have threshold 1.0. "
                        f"Received: {field.threshold}"
                    ),
                )
            if not field.confirmed_individually:
                raise HTTPException(
                    status_code=400,
                    detail=f"T1 field '{field.field_name}' requires individual confirmation.",
                )

    # b. Build registry dict
    registry: dict = {
        "version": "1.0",
        "domain": request.integration_name,
        "created_by": "registry-builder",
        "created_at": datetime.now(timezone.utc).isoformat()[:10],
        "field_count": len(request.fields),
        "fields": {},
    }

    for field in request.fields:
        entry: dict = {
            "tier": field.tier,
            "label": field.label,
            "threshold": field.threshold,
        }
        if field.description:
            entry["description"] = field.description
        if field.confirmed_individually:
            entry["confirmed_individually"] = True
        registry["fields"][field.field_name] = entry

    # c. Serialise
    content = json.dumps(registry, indent=2)
    filename = f"{request.integration_name}.json"

    # d. Save to REGISTRY_DIR if configured
    registry_dir = os.getenv("REGISTRY_DIR")
    saved = False
    if registry_dir:
        path = Path(registry_dir) / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        saved = True
        print(f"[REGISTRY_EXPORT] Saved {filename} to {registry_dir}")
    else:
        print(f"[REGISTRY_EXPORT] REGISTRY_DIR not set — returning content only")

    # e. Return response
    return ExportResponse(
        filename=filename,
        content=content,
        field_count=len(request.fields),
        t1_count=sum(1 for f in request.fields if f.tier == 1),
        registry_id=request.integration_name,
        saved_to_server=saved,
    )
