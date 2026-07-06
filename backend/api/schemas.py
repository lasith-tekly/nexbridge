"""
schemas — API request and response Pydantic models for the NexBridge FastAPI layer.

Part of the NexBridge transformation pipeline.
See docs/SOLUTION_AGENTS.md for full specification.
"""

from typing import Optional

from pydantic import BaseModel, Field, field_validator

from backend.core.models import Decision


# ── Request schemas ───────────────────────────────────────────────────────────

class TransformRequestSchema(BaseModel):
    """Request payload for the POST /transform endpoint."""

    payload: str = Field(
        ...,
        description="Raw input payload string (XML or JSON)"
    )
    source_format: str = Field(
        ...,
        description="Input format: 'xml' or 'json'"
    )
    target_format: str = Field(
        ...,
        description="Output format: 'xml' or 'json'"
    )
    target_schema: dict[str, str] = Field(
        ...,
        description="Target field name → type mapping (e.g. {'id': 'string'})"
    )
    root_element: str = Field(
        default="payload",
        description="Root element tag name for XML output"
    )
    registry_id: str = Field(
        default="default",
        description="Registry ID to use for field classification"
    )

    @field_validator("source_format")
    @classmethod
    def validate_source_format(cls, v: str) -> str:
        """Reject any format string that is not 'xml' or 'json'."""
        if v not in ("xml", "json"):
            raise ValueError(
                f"source_format must be 'xml' or 'json', got '{v}'"
            )
        return v

    @field_validator("target_format")
    @classmethod
    def validate_target_format(cls, v: str) -> str:
        """Reject any format string that is not 'xml' or 'json'."""
        if v not in ("xml", "json"):
            raise ValueError(
                f"target_format must be 'xml' or 'json', got '{v}'"
            )
        return v

    @field_validator("payload")
    @classmethod
    def validate_payload_not_empty(cls, v: str) -> str:
        """Reject empty or whitespace-only payloads."""
        if not v.strip():
            raise ValueError("payload must not be empty")
        return v


class ClassifyRequest(BaseModel):
    """Request payload for the POST /classify endpoint."""

    field_names: list[str] = Field(
        ...,
        description="List of field names to classify against the registry"
    )
    registry_id: str = Field(
        default="default",
        description="Registry ID to use for field classification"
    )

    @field_validator("field_names")
    @classmethod
    def validate_field_names_not_empty(cls, v: list[str]) -> list[str]:
        """Reject an empty field_names list."""
        if not v:
            raise ValueError("field_names must not be empty")
        return v


# ── Response schemas ──────────────────────────────────────────────────────────

class TransformResponseSchema(BaseModel):
    """Response from the POST /transform endpoint."""

    decision: Decision = Field(
        ...,
        description="Orchestrator decision: GO, HOLD, or ESCALATE"
    )
    decision_reason: str = Field(
        ...,
        description="Human-readable explanation of the decision"
    )
    payload_tier: int = Field(
        ...,
        ge=1,
        le=4,
        description="Overall payload risk tier (1=highest, 4=lowest)"
    )
    translated_payload: Optional[str] = Field(
        default=None,
        description="Serialised output string (XML or JSON), None if HOLD"
    )
    confidence_scores: dict[str, float] = Field(
        ...,
        description="Per-field confidence scores (0.0–1.0)"
    )
    anomaly_count: int = Field(
        ...,
        ge=0,
        description="Number of anomalies detected by the validator"
    )
    processing_time_ms: int = Field(
        ...,
        ge=0,
        description="Total pipeline processing time in milliseconds"
    )


class RegistryFieldInfo(BaseModel):
    """Classification details for a single registered field."""

    tier: int = Field(
        ...,
        ge=1,
        le=4,
        description="Classification tier (1=Safety Critical, 4=Informational)"
    )
    label: str = Field(
        ...,
        description="Human-readable tier label"
    )
    threshold: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence threshold for this tier (T1=1.0, T2=0.95)"
    )


class RegistryResponse(BaseModel):
    """Response from the GET /registry endpoint."""

    version: str = Field(
        ...,
        description="Registry version string"
    )
    domain: str = Field(
        ...,
        description="Registry domain (e.g. 'aviation')"
    )
    field_count: int = Field(
        ...,
        ge=0,
        description="Total number of registered fields"
    )
    fields: dict[str, RegistryFieldInfo] = Field(
        ...,
        description="Field name → RegistryFieldInfo mapping"
    )


class HealthResponse(BaseModel):
    """Response from the GET /health endpoint."""

    status: str = Field(
        default="ok",
        description="Service status"
    )
    version: str = Field(
        default="0.3.0",
        description="NexBridge API version"
    )
    registry_fields: int = Field(
        ...,
        ge=0,
        description="Number of fields loaded in the classification registry"
    )


class ClassifyResponse(BaseModel):
    """Response from the POST /classify endpoint."""

    payload_tier: int = Field(
        ...,
        ge=1,
        le=4,
        description="Overall payload tier derived from supplied field names"
    )
    classifications: dict[str, RegistryFieldInfo] = Field(
        ...,
        description="Per-field classification results"
    )


class RegistriesResponse(BaseModel):
    """Response from the GET /registries endpoint."""

    registries: list[str] = Field(
        ...,
        description="List of available registry IDs"
    )
    count: int = Field(
        ...,
        ge=0,
        description="Total number of available registries"
    )


# ── Phase 4 stub schemas ──────────────────────────────────────────────────────

class AnalyseRequest(BaseModel):
    """Request payload for the POST /registry/analyse stub endpoint."""

    payload: str = Field(
        ...,
        description="Raw payload to analyse"
    )
    source_format: str = Field(
        default="xml",
        description="Input format: 'xml' or 'json'"
    )


class AnalysedField(BaseModel):
    """Suggested tier classification for a single field."""

    field_name: str = Field(
        ...,
        description="Field name from the payload"
    )
    suggested_tier: int = Field(
        ...,
        ge=1,
        le=4,
        description="Suggested classification tier (1–4)"
    )
    suggested_label: str = Field(
        ...,
        description="Human-readable tier label"
    )
    reasoning: str = Field(
        ...,
        description="LLM reasoning for the suggestion"
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score for the suggestion"
    )


class AnalyseResponse(BaseModel):
    """Response from the POST /registry/analyse stub endpoint."""

    fields: list[AnalysedField] = Field(
        ...,
        description="Suggested field classifications"
    )
    source_format: str = Field(
        ...,
        description="Input format used"
    )
    field_count: int = Field(
        ...,
        ge=0,
        description="Number of fields analysed"
    )


class ExportField(BaseModel):
    """A single field definition for registry export."""

    field_name: str = Field(
        ...,
        description="Field name"
    )
    tier: int = Field(
        ...,
        ge=1,
        le=4,
        description="Classification tier (1–4)"
    )
    label: str = Field(
        ...,
        description="Human-readable tier label"
    )
    threshold: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence threshold for this tier"
    )
    description: str = Field(
        default="",
        description="Optional field description"
    )


class ExportRequest(BaseModel):
    """Request payload for the POST /registry/export stub endpoint."""

    fields: list[ExportField] = Field(
        ...,
        description="Fields to export to registry"
    )
    domain: str = Field(
        default="custom",
        description="Registry domain name"
    )
