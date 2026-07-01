"""
Tests for backend/api/schemas.py — NexBridge FastAPI Pydantic schemas (Task 3.01).

Validates construction, field validation, default values, and constraint
enforcement for all 7 schema classes:
  - TransformRequestSchema
  - TransformResponseSchema
  - ClassifyRequest
  - ClassifyResponse
  - RegistryFieldInfo
  - RegistryResponse
  - HealthResponse
"""

import pytest
from pydantic import ValidationError

from backend.api.schemas import (
    ClassifyRequest,
    ClassifyResponse,
    HealthResponse,
    RegistryFieldInfo,
    RegistryResponse,
    TransformRequestSchema,
    TransformResponseSchema,
)
from backend.core.models import Decision


# ── TestTransformRequestSchema ────────────────────────────────────────────────


class TestTransformRequestSchema:
    """Validates construction, format validators, and payload validator."""

    # ── Happy-path construction ───────────────────────────────────────────────

    def test_transform_request_xml_to_json_constructs_successfully(self):
        """Valid request with source_format='xml' and target_format='json' must construct."""
        req = TransformRequestSchema(
            payload="<record><id>1</id></record>",
            source_format="xml",
            target_format="json",
            target_schema={"id": "string"},
        )
        assert req.payload == "<record><id>1</id></record>"
        assert req.source_format == "xml"
        assert req.target_format == "json"

    def test_transform_request_json_to_xml_constructs_successfully(self):
        """Valid request with source_format='json' and target_format='xml' must construct."""
        req = TransformRequestSchema(
            payload='{"id": "1"}',
            source_format="json",
            target_format="xml",
            target_schema={"id": "string"},
        )
        assert req.source_format == "json"
        assert req.target_format == "xml"

    # ── source_format validation ──────────────────────────────────────────────

    def test_transform_request_invalid_source_format_csv_raises(self):
        """source_format='csv' must raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            TransformRequestSchema(
                payload="<record/>",
                source_format="csv",
                target_format="json",
                target_schema={"id": "string"},
            )
        assert "source_format" in str(exc_info.value)

    def test_transform_request_invalid_source_format_empty_raises(self):
        """source_format='' must raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            TransformRequestSchema(
                payload="<record/>",
                source_format="",
                target_format="json",
                target_schema={"id": "string"},
            )
        assert "source_format" in str(exc_info.value)

    # ── target_format validation ──────────────────────────────────────────────

    def test_transform_request_invalid_target_format_yaml_raises(self):
        """target_format='yaml' must raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            TransformRequestSchema(
                payload="<record/>",
                source_format="xml",
                target_format="yaml",
                target_schema={"id": "string"},
            )
        assert "target_format" in str(exc_info.value)

    # ── payload validation ────────────────────────────────────────────────────

    def test_transform_request_empty_payload_raises(self):
        """payload='' must raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            TransformRequestSchema(
                payload="",
                source_format="xml",
                target_format="json",
                target_schema={"id": "string"},
            )
        assert "payload" in str(exc_info.value)

    def test_transform_request_whitespace_only_payload_raises(self):
        """payload='   ' (whitespace-only) must raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            TransformRequestSchema(
                payload="   ",
                source_format="xml",
                target_format="json",
                target_schema={"id": "string"},
            )
        assert "payload" in str(exc_info.value)

    def test_transform_request_payload_with_surrounding_whitespace_is_accepted(self):
        """A payload that is non-empty after strip must be accepted as-is."""
        req = TransformRequestSchema(
            payload="  <record><id>1</id></record>  ",
            source_format="xml",
            target_format="json",
            target_schema={"id": "string"},
        )
        # Validator only rejects whitespace-only — the original value is kept.
        assert req.payload == "  <record><id>1</id></record>  "

    # ── defaults and optional fields ─────────────────────────────────────────

    def test_transform_request_root_element_defaults_to_payload(self):
        """root_element must default to 'payload' when not provided."""
        req = TransformRequestSchema(
            payload="<record/>",
            source_format="xml",
            target_format="json",
            target_schema={},
        )
        assert req.root_element == "payload"

    def test_transform_request_root_element_accepts_custom_value(self):
        """root_element can be set to any custom string."""
        req = TransformRequestSchema(
            payload="<employee/>",
            source_format="xml",
            target_format="json",
            target_schema={},
            root_element="employee",
        )
        assert req.root_element == "employee"

    def test_transform_request_target_schema_accepts_dict_str_str(self):
        """target_schema must accept a dict[str, str] mapping."""
        schema = {"id": "string", "age": "integer", "active": "boolean"}
        req = TransformRequestSchema(
            payload="<record/>",
            source_format="xml",
            target_format="json",
            target_schema=schema,
        )
        assert req.target_schema == schema


# ── TestTransformResponseSchema ───────────────────────────────────────────────


class TestTransformResponseSchema:
    """Validates construction, Decision enum typing, and numeric field constraints."""

    def _base_response(self, **overrides) -> dict:
        """Return a minimal valid set of keyword arguments."""
        defaults = dict(
            decision=Decision.GO,
            decision_reason="All fields passed",
            payload_tier=3,
            confidence_scores={"id": 0.99},
            anomaly_count=0,
            processing_time_ms=42,
        )
        defaults.update(overrides)
        return defaults

    # ── Happy-path construction ───────────────────────────────────────────────

    def test_transform_response_decision_go_constructs_successfully(self):
        """Valid response with decision=Decision.GO must construct."""
        resp = TransformResponseSchema(**self._base_response(decision=Decision.GO))
        assert resp.decision == Decision.GO

    def test_transform_response_decision_hold_constructs_successfully(self):
        """Valid response with decision=Decision.HOLD must construct."""
        resp = TransformResponseSchema(**self._base_response(decision=Decision.HOLD))
        assert resp.decision == Decision.HOLD

    # ── translated_payload default ────────────────────────────────────────────

    def test_transform_response_translated_payload_defaults_to_none(self):
        """translated_payload must default to None when not provided."""
        resp = TransformResponseSchema(**self._base_response())
        assert resp.translated_payload is None

    # ── payload_tier constraints ──────────────────────────────────────────────

    def test_transform_response_payload_tier_1_accepted(self):
        """payload_tier=1 (T1 Safety Critical) must be accepted."""
        resp = TransformResponseSchema(**self._base_response(payload_tier=1))
        assert resp.payload_tier == 1

    def test_transform_response_payload_tier_4_accepted(self):
        """payload_tier=4 (T4 Informational) must be accepted."""
        resp = TransformResponseSchema(**self._base_response(payload_tier=4))
        assert resp.payload_tier == 4

    def test_transform_response_payload_tier_0_raises(self):
        """payload_tier=0 must raise ValidationError (ge=1 constraint)."""
        with pytest.raises(ValidationError):
            TransformResponseSchema(**self._base_response(payload_tier=0))

    def test_transform_response_payload_tier_5_raises(self):
        """payload_tier=5 must raise ValidationError (le=4 constraint)."""
        with pytest.raises(ValidationError):
            TransformResponseSchema(**self._base_response(payload_tier=5))

    # ── anomaly_count constraints ─────────────────────────────────────────────

    def test_transform_response_anomaly_count_zero_accepted(self):
        """anomaly_count=0 must be accepted (ge=0 boundary)."""
        resp = TransformResponseSchema(**self._base_response(anomaly_count=0))
        assert resp.anomaly_count == 0

    def test_transform_response_anomaly_count_negative_raises(self):
        """anomaly_count=-1 must raise ValidationError (ge=0 constraint)."""
        with pytest.raises(ValidationError):
            TransformResponseSchema(**self._base_response(anomaly_count=-1))

    # ── processing_time_ms constraints ────────────────────────────────────────

    def test_transform_response_processing_time_ms_zero_accepted(self):
        """processing_time_ms=0 must be accepted (ge=0 boundary)."""
        resp = TransformResponseSchema(**self._base_response(processing_time_ms=0))
        assert resp.processing_time_ms == 0

    # ── Decision field type ───────────────────────────────────────────────────

    def test_transform_response_decision_field_is_decision_enum(self):
        """decision field must be a Decision enum instance, not a plain str."""
        resp = TransformResponseSchema(**self._base_response(decision=Decision.GO))
        assert isinstance(resp.decision, Decision)
        # Decision is a str enum — equality with the string value also holds.
        assert resp.decision == "GO"


# ── TestRegistryFieldInfo ─────────────────────────────────────────────────────


class TestRegistryFieldInfo:
    """Validates tier (1-4) and threshold (0.0-1.0) constraints."""

    # ── tier constraints ──────────────────────────────────────────────────────

    def test_registry_field_info_tier_1_accepted(self):
        """tier=1 must be accepted (lower boundary)."""
        info = RegistryFieldInfo(tier=1, label="Safety Critical", threshold=1.0)
        assert info.tier == 1

    def test_registry_field_info_tier_4_accepted(self):
        """tier=4 must be accepted (upper boundary)."""
        info = RegistryFieldInfo(tier=4, label="Informational", threshold=0.8)
        assert info.tier == 4

    def test_registry_field_info_tier_0_raises(self):
        """tier=0 must raise ValidationError (ge=1 constraint)."""
        with pytest.raises(ValidationError):
            RegistryFieldInfo(tier=0, label="Invalid", threshold=1.0)

    def test_registry_field_info_tier_5_raises(self):
        """tier=5 must raise ValidationError (le=4 constraint)."""
        with pytest.raises(ValidationError):
            RegistryFieldInfo(tier=5, label="Invalid", threshold=1.0)

    # ── threshold constraints ─────────────────────────────────────────────────

    def test_registry_field_info_threshold_0_0_accepted(self):
        """threshold=0.0 must be accepted (lower boundary)."""
        info = RegistryFieldInfo(tier=4, label="Informational", threshold=0.0)
        assert info.threshold == 0.0

    def test_registry_field_info_threshold_1_0_accepted(self):
        """threshold=1.0 must be accepted (upper boundary — T1 requirement)."""
        info = RegistryFieldInfo(tier=1, label="Safety Critical", threshold=1.0)
        assert info.threshold == 1.0

    def test_registry_field_info_threshold_below_0_raises(self):
        """threshold=-0.1 must raise ValidationError (ge=0.0 constraint)."""
        with pytest.raises(ValidationError):
            RegistryFieldInfo(tier=2, label="Sensitive", threshold=-0.1)

    def test_registry_field_info_threshold_above_1_raises(self):
        """threshold=1.1 must raise ValidationError (le=1.0 constraint)."""
        with pytest.raises(ValidationError):
            RegistryFieldInfo(tier=2, label="Sensitive", threshold=1.1)


# ── TestHealthResponse ────────────────────────────────────────────────────────


class TestHealthResponse:
    """Validates defaults and registry_fields constraint."""

    def test_health_response_status_defaults_to_ok(self):
        """status must default to 'ok' when not provided."""
        resp = HealthResponse(registry_fields=10)
        assert resp.status == "ok"

    def test_health_response_version_defaults_to_0_3_0(self):
        """version must default to '0.3.0' when not provided."""
        resp = HealthResponse(registry_fields=10)
        assert resp.version == "0.3.0"

    def test_health_response_registry_fields_zero_accepted(self):
        """registry_fields=0 must be accepted (ge=0 boundary)."""
        resp = HealthResponse(registry_fields=0)
        assert resp.registry_fields == 0

    def test_health_response_registry_fields_negative_raises(self):
        """registry_fields=-1 must raise ValidationError (ge=0 constraint)."""
        with pytest.raises(ValidationError):
            HealthResponse(registry_fields=-1)


# ── TestClassifyRequest ───────────────────────────────────────────────────────


class TestClassifyRequest:
    """Validates field_names construction and empty-list rejection."""

    def test_classify_request_valid_field_names_constructs_successfully(self):
        """A non-empty list of field names must construct successfully."""
        req = ClassifyRequest(field_names=["weight_limit", "clearance_level"])
        assert req.field_names == ["weight_limit", "clearance_level"]

    def test_classify_request_empty_list_raises(self):
        """field_names=[] must raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            ClassifyRequest(field_names=[])
        assert "field_names" in str(exc_info.value)


# ── TestClassifyResponse ──────────────────────────────────────────────────────


class TestClassifyResponse:
    """Validates payload_tier constraints and classifications dict."""

    def test_classify_response_payload_tier_1_accepted(self):
        """payload_tier=1 must be accepted (T1 Safety Critical boundary)."""
        resp = ClassifyResponse(payload_tier=1, classifications={})
        assert resp.payload_tier == 1

    def test_classify_response_payload_tier_4_accepted(self):
        """payload_tier=4 must be accepted (T4 Informational boundary)."""
        resp = ClassifyResponse(payload_tier=4, classifications={})
        assert resp.payload_tier == 4

    def test_classify_response_empty_classifications_accepted(self):
        """An empty classifications dict must be accepted."""
        resp = ClassifyResponse(payload_tier=2, classifications={})
        assert resp.classifications == {}

    def test_classify_response_payload_tier_0_raises(self):
        """payload_tier=0 must raise ValidationError (ge=1 constraint)."""
        with pytest.raises(ValidationError):
            ClassifyResponse(payload_tier=0, classifications={})


# ── TestRegistryResponse ──────────────────────────────────────────────────────


class TestRegistryResponse:
    """Validates nested RegistryFieldInfo construction and field_count constraint."""

    def test_registry_response_valid_with_nested_field_info_constructs(self):
        """RegistryResponse with nested RegistryFieldInfo entries must construct."""
        resp = RegistryResponse(
            version="1.0.0",
            domain="aviation",
            field_count=2,
            fields={
                "weight_limit": RegistryFieldInfo(
                    tier=1, label="Safety Critical", threshold=1.0
                ),
                "department": RegistryFieldInfo(
                    tier=4, label="Informational", threshold=0.8
                ),
            },
        )
        assert resp.field_count == 2
        assert resp.domain == "aviation"
        assert resp.fields["weight_limit"].tier == 1
        assert resp.fields["weight_limit"].threshold == 1.0
        assert resp.fields["department"].tier == 4

    def test_registry_response_field_count_zero_accepted(self):
        """field_count=0 must be accepted (ge=0 boundary)."""
        resp = RegistryResponse(
            version="1.0.0",
            domain="aviation",
            field_count=0,
            fields={},
        )
        assert resp.field_count == 0

    def test_registry_response_field_count_negative_raises(self):
        """field_count=-1 must raise ValidationError (ge=0 constraint)."""
        with pytest.raises(ValidationError):
            RegistryResponse(
                version="1.0.0",
                domain="aviation",
                field_count=-1,
                fields={},
            )
