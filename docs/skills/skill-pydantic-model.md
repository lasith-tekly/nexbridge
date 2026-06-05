# Skill — Pydantic Models

## When To Use This Skill

Load this file before writing any Pydantic model,
TypedDict, or data class in NexBridge.

---

## Core Models Reference

These models are defined in backend/core/models.py.
Import from here — never redefine elsewhere.

```python
from backend.core.models import (
    FieldClassification,
    FieldMapping,
    AuditEntry,
    TransformRequest,
    TransformResponse,
    Decision,
)
```

---

## Existing Model Definitions

```python
from pydantic import BaseModel, Field
from typing import Optional, Literal
from enum import Enum

# --- Enums ---

class Decision(str, Enum):
    GO       = "GO"
    HOLD     = "HOLD"
    ESCALATE = "ESCALATE"

class Tier(int, Enum):
    T1 = 1  # Safety Critical
    T2 = 2  # Operationally Sensitive
    T3 = 3  # Business Important
    T4 = 4  # Informational

# --- Field Level ---

class FieldClassification(BaseModel):
    field_name:           str
    tier:                 Tier
    confidence_threshold: float
    label:                str

    model_config = {"frozen": True}  # immutable


class FieldMapping(BaseModel):
    field_name:        str
    target_field:      str
    transformed_value: object
    confidence:        float = Field(ge=0.0, le=1.0)
    reasoning:         str
    tier:              Tier


# --- Audit ---

class AuditEntry(BaseModel):
    timestamp:         str
    field_name:        str
    tier:              Tier
    original_value:    str
    transformed_value: object
    confidence:        Optional[float]
    agent:             str
    decision:          str
    reasoning:         str

    model_config = {"frozen": True}  # immutable — never modify


# --- API Request / Response ---

class TransformRequest(BaseModel):
    xml_payload:   str = Field(..., min_length=1)
    target_schema: dict = Field(..., min_length=1)


class TransformResponse(BaseModel):
    status:                Decision
    transformed_payload:   Optional[dict]
    payload_tier:          Tier
    decision_reason:       str
    confidence_scores:     dict[str, float]
    field_classifications: dict[str, FieldClassification]
    field_mappings:        dict[str, FieldMapping]
    divergence:            Optional[dict]
    audit_log:             list[AuditEntry]
    processing_time_ms:    int
```

---

## Standard Model Pattern

When adding a new model to NexBridge:

```python
from pydantic import BaseModel, Field
from typing import Optional

class MyNewModel(BaseModel):
    """
    One-line description of what this model represents.
    """

    # Required fields first
    required_field: str
    another_field:  int = Field(ge=0, description="Must be non-negative")

    # Optional fields after
    optional_field: Optional[str] = None

    # Config at the bottom
    model_config = {
        "frozen": True,          # use if immutable (audit entries etc.)
        "str_strip_whitespace": True,
        "validate_assignment":  True,
    }
```

---

## Validation Patterns

```python
from pydantic import BaseModel, field_validator, model_validator

class FieldMapping(BaseModel):
    confidence: float
    tier:       Tier

    @field_validator("confidence")
    @classmethod
    def confidence_in_range(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError(f"confidence must be 0.0-1.0, got {v}")
        return v

    @model_validator(mode="after")
    def check_t1_threshold(self) -> "FieldMapping":
        """T1 fields must meet 1.0 threshold."""
        if self.tier == Tier.T1 and self.confidence < 1.0:
            raise ValueError(
                f"T1 field confidence {self.confidence} "
                f"below required threshold 1.0"
            )
        return self
```

---

## Confidence Threshold Constants

Always import from here — never hardcode in business logic.

```python
# backend/core/constants.py

CONFIDENCE_THRESHOLDS: dict[int, float] = {
    1: 1.0,   # T1 Safety Critical    — NEVER change
    2: 0.95,  # T2 Ops Sensitive      — NEVER change
    3: 0.80,  # T3 Business Important
    4: 0.0,   # T4 Informational
}
```

---

## NexBridge Model Rules

```
✅ All models use Pydantic v2 (BaseModel)
✅ AuditEntry is always frozen=True (immutable)
✅ FieldClassification is always frozen=True (immutable)
✅ Confidence is always validated 0.0 ≤ x ≤ 1.0
✅ Tier is always an int enum (1, 2, 3, 4)
✅ Decision is always a str enum (GO, HOLD, ESCALATE)
❌ Never use dict for structured data — use a model
❌ Never hardcode threshold values — use CONFIDENCE_THRESHOLDS
❌ Never make AuditEntry mutable
```
