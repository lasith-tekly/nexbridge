"""
Tests for POST /registry/export endpoint and related schemas (Task 4.03).

Covers:
  - ExportField schema: defaults, tier/threshold constraints
  - ExportRequest schema: required fields, defaults
  - ExportResponse schema: construction, ge=0 constraints
  - POST /registry/export endpoint:
      - Happy path: T4-only, T1 field, content correctness, file save
      - T1 safety validation: threshold enforcement, individual confirmation
      - Content structure: required JSON keys, domain, description/confirmed_individually
        conditional inclusion
  - Regression: old stub tests (501 + "Phase 4") must NO LONGER pass

Safety note:
  T1 safety validation tests must never be skipped or marked xfail.
  T1 confidence threshold is hardcoded at 1.0; any field with tier=1 and
  threshold < 1.0 must be rejected with 400.
"""

import json
import os

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from backend.api.main import app
from backend.api.schemas import ExportField, ExportRequest, ExportResponse


# ── Module-level TestClient ────────────────────────────────────────────────────

client = TestClient(app)


# ── Shared field factory helpers ───────────────────────────────────────────────

def _t4_field(**overrides) -> dict:
    """Minimal valid T4 (Informational) field dict."""
    base = {
        "field_name": "employee_id",
        "tier": 4,
        "label": "Informational",
        "threshold": 0.75,
    }
    base.update(overrides)
    return base


def _t1_field(**overrides) -> dict:
    """Minimal valid T1 (Safety Critical) field dict — confirmed + threshold=1.0."""
    base = {
        "field_name": "weight_limit",
        "tier": 1,
        "label": "Safety Critical",
        "threshold": 1.0,
        "confirmed_individually": True,
    }
    base.update(overrides)
    return base


def _t2_field(**overrides) -> dict:
    """Minimal valid T2 (Operationally Critical) field dict."""
    base = {
        "field_name": "clearance_level",
        "tier": 2,
        "label": "Operationally Critical",
        "threshold": 0.95,
    }
    base.update(overrides)
    return base


def _export_body(**overrides) -> dict:
    """Minimal valid POST /registry/export request body."""
    base = {
        "integration_name": "flight-ops",
        "fields": [_t4_field()],
    }
    base.update(overrides)
    return base


# =============================================================================
# TestExportFieldSchema
# =============================================================================

class TestExportFieldSchema:
    """Pydantic validation tests for ExportField."""

    def test_export_field_confirmed_individually_defaults_to_false(self):
        """confirmed_individually must default to False when not provided."""
        field = ExportField(
            field_name="employee_id",
            tier=4,
            label="Informational",
            threshold=0.75,
        )
        assert field.confirmed_individually is False

    def test_export_field_confirmed_individually_true_accepted(self):
        """confirmed_individually=True must be accepted without error."""
        field = ExportField(
            field_name="weight_limit",
            tier=1,
            label="Safety Critical",
            threshold=1.0,
            confirmed_individually=True,
        )
        assert field.confirmed_individually is True

    def test_export_field_description_defaults_to_empty_string(self):
        """description must default to '' when not provided."""
        field = ExportField(
            field_name="department",
            tier=3,
            label="Business Important",
            threshold=0.97,
        )
        assert field.description == ""

    def test_export_field_description_accepts_non_empty_string(self):
        """description must accept an arbitrary non-empty string."""
        field = ExportField(
            field_name="start_date",
            tier=4,
            label="Informational",
            threshold=0.75,
            description="Employee start date in ISO-8601 format",
        )
        assert field.description == "Employee start date in ISO-8601 format"

    @pytest.mark.parametrize("tier", [1, 2, 3, 4])
    def test_export_field_tier_valid_range_accepted(self, tier: int):
        """tier values 1–4 (inclusive) must all be accepted."""
        field = ExportField(
            field_name="some_field",
            tier=tier,
            label="Test",
            threshold=1.0 if tier == 1 else 0.75,
        )
        assert field.tier == tier

    @pytest.mark.parametrize("tier", [0, 5, -1, 100])
    def test_export_field_tier_out_of_range_raises(self, tier: int):
        """tier values outside 1–4 must raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            ExportField(
                field_name="some_field",
                tier=tier,
                label="Test",
                threshold=0.75,
            )
        assert "tier" in str(exc_info.value)

    @pytest.mark.parametrize("threshold", [0.0, 0.5, 0.95, 1.0])
    def test_export_field_threshold_valid_range_accepted(self, threshold: float):
        """threshold values in [0.0, 1.0] must all be accepted."""
        field = ExportField(
            field_name="some_field",
            tier=4,
            label="Informational",
            threshold=threshold,
        )
        assert field.threshold == threshold

    @pytest.mark.parametrize("threshold", [-0.01, 1.01, -1.0, 2.0])
    def test_export_field_threshold_out_of_range_raises(self, threshold: float):
        """threshold values outside [0.0, 1.0] must raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            ExportField(
                field_name="some_field",
                tier=4,
                label="Informational",
                threshold=threshold,
            )
        assert "threshold" in str(exc_info.value)

    def test_export_field_field_name_required(self):
        """field_name is required — omitting it must raise ValidationError."""
        with pytest.raises(ValidationError):
            ExportField(tier=4, label="Informational", threshold=0.75)  # type: ignore[call-arg]

    def test_export_field_tier_required(self):
        """tier is required — omitting it must raise ValidationError."""
        with pytest.raises(ValidationError):
            ExportField(field_name="x", label="Informational", threshold=0.75)  # type: ignore[call-arg]

    def test_export_field_label_required(self):
        """label is required — omitting it must raise ValidationError."""
        with pytest.raises(ValidationError):
            ExportField(field_name="x", tier=4, threshold=0.75)  # type: ignore[call-arg]

    def test_export_field_threshold_required(self):
        """threshold is required — omitting it must raise ValidationError."""
        with pytest.raises(ValidationError):
            ExportField(field_name="x", tier=4, label="Informational")  # type: ignore[call-arg]


# =============================================================================
# TestExportRequestSchema
# =============================================================================

class TestExportRequestSchema:
    """Pydantic validation tests for ExportRequest."""

    def test_export_request_integration_name_required(self):
        """integration_name is required — omitting it must raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            ExportRequest(
                fields=[
                    ExportField(
                        field_name="x",
                        tier=4,
                        label="Informational",
                        threshold=0.75,
                    )
                ]
            )  # type: ignore[call-arg]
        assert "integration_name" in str(exc_info.value)

    def test_export_request_domain_defaults_to_custom(self):
        """domain must default to 'custom' when not provided."""
        req = ExportRequest(
            integration_name="hr-system",
            fields=[
                ExportField(
                    field_name="employee_id",
                    tier=4,
                    label="Informational",
                    threshold=0.75,
                )
            ],
        )
        assert req.domain == "custom"

    def test_export_request_domain_accepts_custom_value(self):
        """domain accepts any non-empty string value."""
        req = ExportRequest(
            integration_name="flight-ops",
            domain="aviation",
            fields=[
                ExportField(
                    field_name="employee_id",
                    tier=4,
                    label="Informational",
                    threshold=0.75,
                )
            ],
        )
        assert req.domain == "aviation"

    def test_export_request_fields_required(self):
        """fields is required — omitting it must raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            ExportRequest(integration_name="hr-system")  # type: ignore[call-arg]
        assert "fields" in str(exc_info.value)

    def test_export_request_fields_accepts_multiple_entries(self):
        """fields must accept a list with more than one ExportField entry."""
        req = ExportRequest(
            integration_name="hr-system",
            fields=[
                ExportField(field_name="employee_id", tier=4, label="Informational", threshold=0.75),
                ExportField(field_name="department", tier=3, label="Business Important", threshold=0.97),
                ExportField(field_name="weight_limit", tier=1, label="Safety Critical", threshold=1.0, confirmed_individually=True),
            ],
        )
        assert len(req.fields) == 3

    def test_export_request_valid_construction(self):
        """A fully-specified ExportRequest must construct without error."""
        req = ExportRequest(
            integration_name="cargo-ops",
            domain="aviation",
            fields=[
                ExportField(
                    field_name="max_load",
                    tier=1,
                    label="Safety Critical",
                    threshold=1.0,
                    confirmed_individually=True,
                    description="Maximum permitted cargo load in kg",
                )
            ],
        )
        assert req.integration_name == "cargo-ops"
        assert req.domain == "aviation"
        assert len(req.fields) == 1


# =============================================================================
# TestExportResponseSchema
# =============================================================================

class TestExportResponseSchema:
    """Pydantic validation tests for ExportResponse."""

    def _base_response(self, **overrides) -> dict:
        """Return a minimal valid kwargs dict for ExportResponse construction."""
        base = {
            "filename": "flight-ops.json",
            "content": '{"version": "1.0"}',
            "field_count": 2,
            "t1_count": 1,
            "registry_id": "flight-ops",
            "saved_to_server": False,
        }
        base.update(overrides)
        return base

    def test_export_response_valid_construction(self):
        """ExportResponse must construct without error with all valid fields."""
        resp = ExportResponse(**self._base_response())
        assert resp.filename == "flight-ops.json"
        assert resp.registry_id == "flight-ops"
        assert resp.saved_to_server is False

    def test_export_response_field_count_zero_accepted(self):
        """field_count=0 is the minimum valid value (ge=0 boundary)."""
        resp = ExportResponse(**self._base_response(field_count=0, t1_count=0))
        assert resp.field_count == 0

    def test_export_response_field_count_negative_raises(self):
        """field_count=-1 must raise ValidationError (ge=0 constraint)."""
        with pytest.raises(ValidationError) as exc_info:
            ExportResponse(**self._base_response(field_count=-1))
        assert "field_count" in str(exc_info.value)

    def test_export_response_t1_count_zero_accepted(self):
        """t1_count=0 is the minimum valid value (ge=0 boundary)."""
        resp = ExportResponse(**self._base_response(t1_count=0))
        assert resp.t1_count == 0

    def test_export_response_t1_count_negative_raises(self):
        """t1_count=-1 must raise ValidationError (ge=0 constraint)."""
        with pytest.raises(ValidationError) as exc_info:
            ExportResponse(**self._base_response(t1_count=-1))
        assert "t1_count" in str(exc_info.value)

    def test_export_response_saved_to_server_accepts_true(self):
        """saved_to_server=True must be accepted without error."""
        resp = ExportResponse(**self._base_response(saved_to_server=True))
        assert resp.saved_to_server is True

    def test_export_response_filename_required(self):
        """filename is required — omitting it must raise ValidationError."""
        kwargs = self._base_response()
        del kwargs["filename"]
        with pytest.raises(ValidationError):
            ExportResponse(**kwargs)

    def test_export_response_content_required(self):
        """content is required — omitting it must raise ValidationError."""
        kwargs = self._base_response()
        del kwargs["content"]
        with pytest.raises(ValidationError):
            ExportResponse(**kwargs)


# =============================================================================
# TestExportEndpointHappyPath
# =============================================================================

class TestExportEndpointHappyPath:
    """Happy-path tests for POST /registry/export."""

    def test_export_t4_only_returns_200(self):
        """A valid T4-only export request must return HTTP 200."""
        response = client.post("/registry/export", json=_export_body())
        assert response.status_code == 200

    def test_export_t4_only_filename_matches_integration_name(self):
        """filename in response must equal '{integration_name}.json'."""
        response = client.post("/registry/export", json=_export_body(integration_name="hr-system"))
        data = response.json()
        assert data["filename"] == "hr-system.json"

    def test_export_t4_only_field_count_correct(self):
        """field_count must equal the number of fields in the request."""
        body = _export_body(fields=[_t4_field(field_name="f1"), _t4_field(field_name="f2")])
        response = client.post("/registry/export", json=body)
        data = response.json()
        assert data["field_count"] == 2

    def test_export_t4_only_t1_count_is_zero(self):
        """t1_count must be 0 when no T1 fields are present."""
        response = client.post("/registry/export", json=_export_body())
        data = response.json()
        assert data["t1_count"] == 0

    def test_export_t4_only_saved_to_server_false_without_registry_dir(self, monkeypatch):
        """saved_to_server must be False when REGISTRY_DIR env var is not set."""
        monkeypatch.delenv("REGISTRY_DIR", raising=False)
        response = client.post("/registry/export", json=_export_body())
        data = response.json()
        assert data["saved_to_server"] is False

    def test_export_with_t1_field_returns_200(self):
        """A payload including a fully-confirmed T1 field must return HTTP 200."""
        body = _export_body(fields=[_t1_field()])
        response = client.post("/registry/export", json=body)
        assert response.status_code == 200

    def test_export_with_t1_field_t1_count_is_one(self):
        """t1_count must equal 1 when exactly one T1 field is in the request."""
        body = _export_body(fields=[_t1_field()])
        response = client.post("/registry/export", json=body)
        data = response.json()
        assert data["t1_count"] == 1

    def test_export_with_mixed_tiers_t1_count_correct(self):
        """t1_count must count only tier=1 fields from a mixed-tier request."""
        body = _export_body(fields=[
            _t1_field(field_name="weight_limit"),
            _t1_field(field_name="equipment_class"),
            _t2_field(field_name="clearance_level"),
            _t4_field(field_name="employee_id"),
        ])
        response = client.post("/registry/export", json=body)
        data = response.json()
        assert data["t1_count"] == 2
        assert data["field_count"] == 4

    def test_export_content_is_valid_json(self):
        """content in response must be parseable JSON (json.loads must not raise)."""
        response = client.post("/registry/export", json=_export_body())
        data = response.json()
        parsed = json.loads(data["content"])
        assert isinstance(parsed, dict)

    def test_export_registry_id_matches_integration_name(self):
        """registry_id in response must equal the integration_name from the request."""
        body = _export_body(integration_name="cargo-ops")
        response = client.post("/registry/export", json=body)
        data = response.json()
        assert data["registry_id"] == "cargo-ops"

    def test_export_saved_to_server_true_when_registry_dir_set(self, monkeypatch, tmp_path):
        """saved_to_server must be True when REGISTRY_DIR is set to a valid directory."""
        monkeypatch.setenv("REGISTRY_DIR", str(tmp_path))
        response = client.post("/registry/export", json=_export_body(integration_name="test-reg"))
        data = response.json()
        assert data["saved_to_server"] is True

    def test_export_file_written_when_registry_dir_set(self, monkeypatch, tmp_path):
        """The registry JSON file must be physically written to REGISTRY_DIR."""
        monkeypatch.setenv("REGISTRY_DIR", str(tmp_path))
        body = _export_body(integration_name="test-reg")
        client.post("/registry/export", json=body)
        expected_path = tmp_path / "test-reg.json"
        assert expected_path.exists(), f"Expected file not found: {expected_path}"

    def test_export_written_file_content_is_valid_json(self, monkeypatch, tmp_path):
        """The written file must contain valid JSON that matches response content."""
        monkeypatch.setenv("REGISTRY_DIR", str(tmp_path))
        body = _export_body(integration_name="test-reg")
        response = client.post("/registry/export", json=body)
        resp_content = response.json()["content"]
        file_content = (tmp_path / "test-reg.json").read_text(encoding="utf-8")
        assert file_content == resp_content

    def test_export_saved_to_server_false_when_registry_dir_not_set(self, monkeypatch):
        """saved_to_server must be False when REGISTRY_DIR is not in the environment."""
        monkeypatch.delenv("REGISTRY_DIR", raising=False)
        response = client.post("/registry/export", json=_export_body())
        assert response.json()["saved_to_server"] is False


# =============================================================================
# TestExportEndpointT1SafetyValidation  —  CRITICAL SAFETY TESTS
# =============================================================================

class TestExportEndpointT1SafetyValidation:
    """
    CRITICAL SAFETY TESTS for POST /registry/export T1 enforcement.

    These tests MUST NEVER be skipped or marked xfail.
    T1 confidence threshold is hardcoded at 1.0.
    T1 fields require both threshold=1.0 AND confirmed_individually=True.
    Any violation must produce HTTP 400 before any file I/O occurs.
    """

    def test_t1_field_with_low_threshold_returns_400(self):
        """
        CRITICAL SAFETY TEST.
        T1 field with threshold=0.95 (< 1.0) must be rejected with HTTP 400.
        The T1 confidence threshold is hardcoded at 1.0 and must never be lowered.
        """
        body = _export_body(fields=[
            _t1_field(threshold=0.95)
        ])
        response = client.post("/registry/export", json=body)
        assert response.status_code == 400

    def test_t1_field_low_threshold_detail_mentions_field_name(self):
        """
        CRITICAL SAFETY TEST.
        The 400 error detail must mention the offending field name.
        """
        body = _export_body(fields=[
            _t1_field(field_name="weight_limit", threshold=0.95)
        ])
        response = client.post("/registry/export", json=body)
        detail = response.json()["detail"]
        assert "weight_limit" in detail

    def test_t1_field_low_threshold_detail_mentions_threshold_1_0(self):
        """
        CRITICAL SAFETY TEST.
        The 400 error detail must mention 'threshold 1.0' to guide the caller.
        """
        body = _export_body(fields=[
            _t1_field(field_name="weight_limit", threshold=0.95)
        ])
        response = client.post("/registry/export", json=body)
        detail = response.json()["detail"]
        assert "1.0" in detail

    def test_t1_field_with_threshold_0_returns_400(self):
        """
        CRITICAL SAFETY TEST.
        T1 field with threshold=0.0 must also be rejected with HTTP 400.
        """
        body = _export_body(fields=[
            _t1_field(threshold=0.0)
        ])
        response = client.post("/registry/export", json=body)
        assert response.status_code == 400

    def test_t1_field_not_confirmed_individually_returns_400(self):
        """
        CRITICAL SAFETY TEST.
        T1 field with threshold=1.0 but confirmed_individually=False must be
        rejected with HTTP 400. Individual confirmation is mandatory for T1 fields.
        """
        body = _export_body(fields=[
            _t1_field(confirmed_individually=False)
        ])
        response = client.post("/registry/export", json=body)
        assert response.status_code == 400

    def test_t1_field_not_confirmed_detail_mentions_field_name(self):
        """
        CRITICAL SAFETY TEST.
        The 400 detail for a T1 field lacking individual confirmation must
        mention the offending field name.
        """
        body = _export_body(fields=[
            _t1_field(field_name="clearance_level", confirmed_individually=False)
        ])
        response = client.post("/registry/export", json=body)
        detail = response.json()["detail"]
        assert "clearance_level" in detail

    def test_t1_field_not_confirmed_detail_mentions_individual_confirmation(self):
        """
        CRITICAL SAFETY TEST.
        The 400 detail for a T1 field lacking individual confirmation must
        mention 'individual confirmation' to guide the caller.
        """
        body = _export_body(fields=[
            _t1_field(confirmed_individually=False)
        ])
        response = client.post("/registry/export", json=body)
        detail = response.json()["detail"]
        assert "individual confirmation" in detail.lower() or "confirmed" in detail.lower()

    def test_t1_field_correct_threshold_and_confirmed_returns_200(self):
        """
        CRITICAL SAFETY TEST.
        A T1 field with threshold=1.0 AND confirmed_individually=True must
        pass both safety checks and return HTTP 200.
        """
        body = _export_body(fields=[
            _t1_field(threshold=1.0, confirmed_individually=True)
        ])
        response = client.post("/registry/export", json=body)
        assert response.status_code == 200

    def test_mixed_payload_with_bad_t1_returns_400(self):
        """
        CRITICAL SAFETY TEST.
        A payload containing both valid T4 fields and an invalid T1 field
        (threshold < 1.0) must be rejected — the entire export is blocked.
        """
        body = _export_body(fields=[
            _t4_field(field_name="employee_id"),
            _t4_field(field_name="department"),
            _t1_field(field_name="weight_limit", threshold=0.9),
        ])
        response = client.post("/registry/export", json=body)
        assert response.status_code == 400

    def test_multiple_t1_fields_second_invalid_returns_400(self):
        """
        CRITICAL SAFETY TEST.
        When multiple T1 fields are present and only the second is invalid,
        the endpoint must still return 400.
        """
        body = _export_body(fields=[
            _t1_field(field_name="weight_limit", threshold=1.0, confirmed_individually=True),
            _t1_field(field_name="equipment_class", threshold=0.95, confirmed_individually=True),
        ])
        response = client.post("/registry/export", json=body)
        assert response.status_code == 400
        detail = response.json()["detail"]
        assert "equipment_class" in detail

    def test_t1_safety_check_fires_before_file_write(self, monkeypatch, tmp_path):
        """
        CRITICAL SAFETY TEST.
        When REGISTRY_DIR is set and an invalid T1 field is present,
        the 400 must be returned and NO file must be written to disk.
        """
        monkeypatch.setenv("REGISTRY_DIR", str(tmp_path))
        body = _export_body(
            integration_name="danger-reg",
            fields=[_t1_field(threshold=0.95)]
        )
        response = client.post("/registry/export", json=body)
        assert response.status_code == 400
        assert not (tmp_path / "danger-reg.json").exists()


# =============================================================================
# TestExportEndpointContentStructure
# =============================================================================

class TestExportEndpointContentStructure:
    """Tests verifying the structure and values of the exported JSON content."""

    def _get_content(self, body: dict) -> dict:
        """POST the body, assert 200, and return parsed content dict."""
        response = client.post("/registry/export", json=body)
        assert response.status_code == 200, f"Unexpected status: {response.json()}"
        return json.loads(response.json()["content"])

    def test_content_has_version_key(self):
        """Exported JSON content must include a 'version' key."""
        content = self._get_content(_export_body())
        assert "version" in content

    def test_content_has_domain_key(self):
        """Exported JSON content must include a 'domain' key."""
        content = self._get_content(_export_body())
        assert "domain" in content

    def test_content_has_fields_key(self):
        """Exported JSON content must include a 'fields' key."""
        content = self._get_content(_export_body())
        assert "fields" in content

    def test_content_domain_equals_integration_name(self):
        """
        The 'domain' in exported content must equal integration_name,
        not the request.domain parameter.
        """
        body = _export_body(integration_name="flight-ops", domain="aviation")
        content = self._get_content(body)
        assert content["domain"] == "flight-ops"

    def test_content_domain_not_request_domain(self):
        """
        Confirms the 'domain' value is derived from integration_name
        rather than the request.domain field.
        """
        body = _export_body(integration_name="cargo-ops", domain="custom-domain")
        content = self._get_content(body)
        assert content["domain"] != "custom-domain"
        assert content["domain"] == "cargo-ops"

    def test_content_field_count_matches_fields_length(self):
        """field_count in content must equal the number of entries in content['fields']."""
        body = _export_body(fields=[
            _t4_field(field_name="f1"),
            _t4_field(field_name="f2"),
            _t4_field(field_name="f3"),
        ])
        content = self._get_content(body)
        assert content["field_count"] == len(content["fields"])

    def test_content_field_count_matches_response_field_count(self):
        """field_count in content must match field_count in the API response."""
        body = _export_body(fields=[_t4_field(field_name="f1"), _t4_field(field_name="f2")])
        response = client.post("/registry/export", json=body)
        data = response.json()
        content = json.loads(data["content"])
        assert content["field_count"] == data["field_count"]

    def test_content_fields_contains_each_requested_field(self):
        """Each field_name in the request must appear as a key in content['fields']."""
        body = _export_body(fields=[
            _t4_field(field_name="employee_id"),
            _t4_field(field_name="department"),
        ])
        content = self._get_content(body)
        assert "employee_id" in content["fields"]
        assert "department" in content["fields"]

    def test_content_field_entry_has_tier_label_threshold(self):
        """Each field entry in content must contain 'tier', 'label', and 'threshold'."""
        content = self._get_content(_export_body(fields=[_t4_field(field_name="employee_id")]))
        entry = content["fields"]["employee_id"]
        assert "tier" in entry
        assert "label" in entry
        assert "threshold" in entry

    def test_content_description_included_when_non_empty(self):
        """'description' must appear in the field entry when it is non-empty."""
        body = _export_body(fields=[
            _t4_field(field_name="start_date", description="ISO-8601 date field")
        ])
        content = self._get_content(body)
        entry = content["fields"]["start_date"]
        assert "description" in entry
        assert entry["description"] == "ISO-8601 date field"

    def test_content_description_omitted_when_empty(self):
        """'description' must NOT appear in the field entry when it is empty string."""
        body = _export_body(fields=[
            _t4_field(field_name="employee_id", description="")
        ])
        content = self._get_content(body)
        entry = content["fields"]["employee_id"]
        assert "description" not in entry

    def test_content_description_omitted_by_default(self):
        """'description' must NOT appear in the field entry when not provided."""
        body = _export_body(fields=[_t4_field(field_name="department")])
        content = self._get_content(body)
        entry = content["fields"]["department"]
        assert "description" not in entry

    def test_content_confirmed_individually_included_when_true(self):
        """'confirmed_individually' must appear in the field entry when True."""
        body = _export_body(fields=[_t1_field(field_name="weight_limit")])
        content = self._get_content(body)
        entry = content["fields"]["weight_limit"]
        assert "confirmed_individually" in entry
        assert entry["confirmed_individually"] is True

    def test_content_confirmed_individually_omitted_when_false(self):
        """'confirmed_individually' must NOT appear in the field entry when False."""
        body = _export_body(fields=[_t4_field(field_name="employee_id")])
        content = self._get_content(body)
        entry = content["fields"]["employee_id"]
        assert "confirmed_individually" not in entry

    def test_content_confirmed_individually_omitted_by_default(self):
        """'confirmed_individually' must NOT appear by default (default=False → omitted)."""
        field_body = _t4_field(field_name="department")
        # Ensure confirmed_individually is not set
        field_body.pop("confirmed_individually", None)
        body = _export_body(fields=[field_body])
        content = self._get_content(body)
        entry = content["fields"]["department"]
        assert "confirmed_individually" not in entry

    def test_content_version_is_string(self):
        """The 'version' value in content must be a non-empty string."""
        content = self._get_content(_export_body())
        assert isinstance(content["version"], str)
        assert content["version"] != ""

    def test_content_fields_is_dict(self):
        """The 'fields' value in content must be a dict (not a list)."""
        content = self._get_content(_export_body())
        assert isinstance(content["fields"], dict)


# =============================================================================
# TestExportStubRegressionCheck
# =============================================================================

class TestExportStubRegressionCheck:
    """
    Regression tests verifying the old 501 stub behaviour no longer applies.

    The endpoint was previously a stub returning 501 Not Implemented.
    Now that task 4.03 has implemented it, the stub response must never
    appear again for valid requests.
    """

    def test_export_valid_t4_request_does_not_return_501(self):
        """A valid T4-only export request must NOT return 501 (stub removed)."""
        response = client.post("/registry/export", json=_export_body())
        assert response.status_code != 501

    def test_export_valid_t1_request_does_not_return_501(self):
        """A valid T1 export request must NOT return 501 (stub removed)."""
        body = _export_body(fields=[_t1_field()])
        response = client.post("/registry/export", json=body)
        assert response.status_code != 501

    def test_export_valid_request_does_not_reference_phase_4(self):
        """A valid export request must NOT return a detail referencing 'Phase 4'."""
        response = client.post("/registry/export", json=_export_body())
        if response.status_code != 200:
            detail = response.json().get("detail", "")
            assert "Phase 4" not in detail
