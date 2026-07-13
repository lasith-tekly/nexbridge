"""
NexBridge Core Pydantic Models

Defines all data models for the NexBridge transformation pipeline.
All models use Pydantic v2 with strict type validation.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Literal
from enum import Enum


# --- Enums ---

class Decision(str, Enum):
    """Orchestrator decision on whether to release the payload."""
    GO = "GO"
    HOLD = "HOLD"
    ESCALATE = "ESCALATE"


class Tier(int, Enum):
    """Field classification tier — determines confidence threshold."""
    T1 = 1  # Safety Critical
    T2 = 2  # Operationally Sensitive
    T3 = 3  # Business Important
    T4 = 4  # Informational


# --- Field Level Models ---

class FieldClassification(BaseModel):
    """
    Result of looking up a field in the classification registry.
    Immutable — never modified after creation.
    """
    field_name: str = Field(
        ...,
        description="Original XML field name as it appears in the payload"
    )
    tier: Tier = Field(
        ...,
        description="Risk classification tier (1=T1, 2=T2, 3=T3, 4=T4)"
    )
    confidence_threshold: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Minimum confidence required before orchestrator proceeds"
    )
    label: str = Field(
        ...,
        description="Human-readable tier label (e.g. 'Safety Critical')"
    )

    model_config = ConfigDict(frozen=True)


class FieldMapping(BaseModel):
    """
    Result of interpreter agent mapping a field to target schema.
    Includes semantic transformation and confidence score.
    """
    field_name: str = Field(
        ...,
        description="Original XML field name"
    )
    target_field: str = Field(
        ...,
        description="Target JSON field name after transformation"
    )
    transformed_value: object = Field(
        ...,
        description="Transformed value in target format"
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score for this mapping (0.0 to 1.0)"
    )
    reasoning: str = Field(
        ...,
        description="LLM reasoning for why this mapping was chosen"
    )
    tier: Tier = Field(
        ...,
        description="Classification tier for this field"
    )
    source: str = Field(
        default="llm",
        description="Mapping source: 'registry' (pre-approved) or 'llm' (inferred)"
    )


# --- Audit ---

class AuditEntry(BaseModel):
    """
    Immutable audit log entry for a single field transformation.
    Append-only — never modified or deleted after creation.
    """
    timestamp: str = Field(
        ...,
        description="ISO 8601 timestamp of when this entry was created"
    )
    field_name: str = Field(
        ...,
        description="Field name that was transformed"
    )
    tier: int = Field(
        ...,
        ge=1,
        le=4,
        description="Tier of this field (1-4)"
    )
    original_value: str = Field(
        ...,
        description="Original value from XML payload"
    )
    transformed_value: object = Field(
        ...,
        description="Transformed value in target format"
    )
    confidence: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Confidence score if applicable (optional for some agents)"
    )
    agent: str = Field(
        ...,
        description="Name of the agent that created this entry"
    )
    decision: str = Field(
        ...,
        description="Decision made by this agent (GO, HOLD, ESCALATE)"
    )
    reasoning: str = Field(
        ...,
        description="Reasoning for the decision"
    )
    source: str = Field(
        default="llm",
        description="Mapping source: 'registry' (pre-approved) or 'llm' (inferred)"
    )

    model_config = ConfigDict(frozen=True)


# --- API Request / Response ---

class TransformRequest(BaseModel):
    """
    Request payload for the /transform API endpoint.
    """
    xml_payload: str = Field(
        ...,
        min_length=1,
        description="XML payload to transform (must not be empty)"
    )
    target_schema: dict = Field(
        ...,
        description="Target JSON schema definition"
    )


class TransformResponse(BaseModel):
    """
    Response from the /transform API endpoint.
    Contains full transformation result including audit trail.
    """
    status: Decision = Field(
        ...,
        description="Final orchestrator decision (GO, HOLD, ESCALATE)"
    )
    transformed_payload: Optional[dict] = Field(
        None,
        description="Transformed JSON payload (None if decision is HOLD)"
    )
    payload_tier: Tier = Field(
        ...,
        description="Highest tier found in the payload (T1 > T2 > T3 > T4)"
    )
    decision_reason: str = Field(
        ...,
        description="Human-readable reason for the orchestrator decision"
    )
    confidence_scores: dict[str, float] = Field(
        ...,
        description="Confidence scores per field (field_name -> confidence)"
    )
    field_classifications: dict = Field(
        ...,
        description="Field classification results from registry lookup"
    )
    field_mappings: dict = Field(
        ...,
        description="Field mapping results from interpreter agent(s)"
    )
    divergence: Optional[dict] = Field(
        None,
        description="Divergence details for T1 dual-agent comparison (if applicable)"
    )
    audit_log: list[AuditEntry] = Field(
        ...,
        description="Complete audit trail of all transformations"
    )
    processing_time_ms: int = Field(
        ...,
        ge=0,
        description="Total processing time in milliseconds"
    )
