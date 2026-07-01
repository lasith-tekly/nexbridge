"""
Tests for backend/api/main.py — NexBridge FastAPI endpoints (Task 3.08).

Validates all six route groups using FastAPI TestClient:
  - GET  /health
  - GET  /registry
  - POST /classify
  - POST /transform   (mocked pipeline via patch("backend.api.main.build_graph"))
  - POST /registry/analyse  (stub — 501)
  - POST /registry/export   (stub — 501)

Mock target:  backend.api.main.build_graph
Safety note:  No T1 safety path is bypassed here; transform tests exercise the
              orchestrator contract through mocked result dicts whose structure
              matches what the real orchestrator produces.
"""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from backend.api.main import app


# ── Module-level TestClient ────────────────────────────────────────────────────

client = TestClient(app)


# ── Shared mock result dicts ───────────────────────────────────────────────────

_GO_RESULT = {
    "decision": "GO",
    "decision_reason": "All fields passed",
    "payload_tier": 3,
    "translated_payload": '{"id": "E-123"}',
    "confidence_scores": {"employee_id": 0.95},
    "validation_result": {"anomaly_count": 0},
    "audit_log": [],
}

_HOLD_RESULT = {
    "decision": "HOLD",
    "decision_reason": "All fields passed",
    "payload_tier": 3,
    "translated_payload": None,
    "confidence_scores": {"employee_id": 0.95},
    "validation_result": {"anomaly_count": 0},
    "audit_log": [],
}

# ── Valid request bodies ───────────────────────────────────────────────────────

_XML_TO_JSON_BODY = {
    "payload": "<employee><id>E-123</id></employee>",
    "source_format": "xml",
    "target_format": "json",
    "target_schema": {"id": "string"},
}

_JSON_TO_XML_BODY = {
    "payload": '{"id": "E-123"}',
    "source_format": "json",
    "target_format": "xml",
    "target_schema": {"id": "string"},
}


# ── Helper: build a mocked graph whose .invoke() returns the given result ──────

def _mock_graph(result: dict) -> MagicMock:
    """Return a MagicMock graph whose .invoke() returns *result*."""
    mock_graph = MagicMock()
    mock_graph.invoke.return_value = result
    return mock_graph


# =============================================================================
# TestHealthEndpoint
# =============================================================================

class TestHealthEndpoint:
    """Tests for GET /health."""

    def test_health_returns_200(self):
        """GET /health must return HTTP 200."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_status_is_ok(self):
        """The 'status' field must be 'ok' when the registry loads correctly."""
        response = client.get("/health")
        data = response.json()
        assert data["status"] == "ok"

    def test_health_version_is_0_3_0(self):
        """The 'version' field must report '0.3.0'."""
        response = client.get("/health")
        data = response.json()
        assert data["version"] == "0.3.0"

    def test_health_registry_fields_is_positive(self):
        """'registry_fields' must be a positive integer when the registry loads."""
        response = client.get("/health")
        data = response.json()
        assert data["registry_fields"] > 0


# =============================================================================
# TestRegistryEndpoint
# =============================================================================

class TestRegistryEndpoint:
    """Tests for GET /registry."""

    def test_registry_returns_200(self):
        """GET /registry must return HTTP 200."""
        response = client.get("/registry")
        assert response.status_code == 200

    def test_registry_has_version(self):
        """Response must contain a non-empty 'version' string."""
        response = client.get("/registry")
        data = response.json()
        assert "version" in data
        assert isinstance(data["version"], str)
        assert data["version"] != ""

    def test_registry_has_domain(self):
        """Response must contain a non-empty 'domain' string."""
        response = client.get("/registry")
        data = response.json()
        assert "domain" in data
        assert isinstance(data["domain"], str)
        assert data["domain"] != ""

    def test_registry_field_count_matches_fields_len(self):
        """'field_count' must equal the length of the 'fields' dict."""
        response = client.get("/registry")
        data = response.json()
        assert data["field_count"] == len(data["fields"])

    def test_registry_each_field_has_tier_label_threshold(self):
        """Every entry in 'fields' must have 'tier', 'label', and 'threshold'."""
        response = client.get("/registry")
        fields = response.json()["fields"]
        assert len(fields) > 0, "Registry must contain at least one field"
        for field_name, info in fields.items():
            assert "tier" in info, f"Field '{field_name}' missing 'tier'"
            assert "label" in info, f"Field '{field_name}' missing 'label'"
            assert "threshold" in info, f"Field '{field_name}' missing 'threshold'"


# =============================================================================
# TestClassifyEndpoint
# =============================================================================

class TestClassifyEndpoint:
    """Tests for POST /classify."""

    def test_classify_known_field_returns_200(self):
        """Classifying a known registry field must return HTTP 200."""
        response = client.post("/classify", json={"field_names": ["employee_id"]})
        assert response.status_code == 200

    def test_classify_payload_tier_in_valid_range(self):
        """'payload_tier' in the response must be between 1 and 4 inclusive."""
        response = client.post("/classify", json={"field_names": ["employee_id"]})
        data = response.json()
        assert 1 <= data["payload_tier"] <= 4

    def test_classify_classifications_has_entry_per_field(self):
        """'classifications' must have exactly one entry per requested field name."""
        field_names = ["employee_id"]
        response = client.post("/classify", json={"field_names": field_names})
        data = response.json()
        assert set(data["classifications"].keys()) == set(field_names)

    def test_classify_unknown_field_defaults_to_tier_4(self):
        """An unknown field name must be classified as Tier 4 (Informational)."""
        response = client.post(
            "/classify", json={"field_names": ["unknown_xyz_field"]}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["classifications"]["unknown_xyz_field"]["tier"] == 4

    def test_classify_empty_field_names_returns_422(self):
        """An empty 'field_names' list must be rejected with HTTP 422."""
        response = client.post("/classify", json={"field_names": []})
        assert response.status_code == 422


# =============================================================================
# TestTransformEndpoint
# =============================================================================

class TestTransformEndpoint:
    """
    Tests for POST /transform.

    All tests in this class patch build_graph so the LangGraph pipeline is
    never executed.  This keeps the tests fast and deterministic while still
    exercising the full request → response contract of the endpoint.
    """

    def test_transform_valid_xml_to_json_returns_200(self):
        """A valid XML→JSON request must return HTTP 200 (GO scenario)."""
        with patch(
            "backend.api.main.build_graph", return_value=_mock_graph(_GO_RESULT)
        ):
            response = client.post("/transform", json=_XML_TO_JSON_BODY)
        assert response.status_code == 200

    def test_transform_valid_json_to_xml_returns_200(self):
        """A valid JSON→XML request must return HTTP 200 (GO scenario)."""
        with patch(
            "backend.api.main.build_graph", return_value=_mock_graph(_GO_RESULT)
        ):
            response = client.post("/transform", json=_JSON_TO_XML_BODY)
        assert response.status_code == 200

    def test_transform_go_decision_in_response(self):
        """When the pipeline returns GO the response 'decision' must be 'GO'."""
        with patch(
            "backend.api.main.build_graph", return_value=_mock_graph(_GO_RESULT)
        ):
            response = client.post("/transform", json=_XML_TO_JSON_BODY)
        data = response.json()
        assert data["decision"] == "GO"

    def test_transform_hold_decision_returns_translated_payload_none(self):
        """
        When the orchestrator returns HOLD the 'translated_payload' in the
        response must be None — the payload must never be released.
        """
        with patch(
            "backend.api.main.build_graph", return_value=_mock_graph(_HOLD_RESULT)
        ):
            response = client.post("/transform", json=_XML_TO_JSON_BODY)
        assert response.status_code == 200
        data = response.json()
        assert data["decision"] == "HOLD"
        assert data["translated_payload"] is None

    def test_transform_invalid_source_format_returns_422(self):
        """
        A request with an unsupported source_format (e.g. 'csv') must be
        rejected with HTTP 422 before the pipeline is invoked.
        """
        bad_body = {**_XML_TO_JSON_BODY, "source_format": "csv"}
        response = client.post("/transform", json=bad_body)
        assert response.status_code == 422

    def test_transform_empty_payload_returns_422(self):
        """
        A request with an empty 'payload' string must be rejected with
        HTTP 422 before the pipeline is invoked.
        """
        bad_body = {**_XML_TO_JSON_BODY, "payload": "   "}
        response = client.post("/transform", json=bad_body)
        assert response.status_code == 422

    def test_transform_processing_time_ms_is_non_negative(self):
        """'processing_time_ms' in the response must be >= 0."""
        with patch(
            "backend.api.main.build_graph", return_value=_mock_graph(_GO_RESULT)
        ):
            response = client.post("/transform", json=_XML_TO_JSON_BODY)
        data = response.json()
        assert data["processing_time_ms"] >= 0

    def test_transform_confidence_scores_in_response(self):
        """
        'confidence_scores' must be present in the response and must be a dict.
        Values must be floats in the range [0.0, 1.0].
        """
        with patch(
            "backend.api.main.build_graph", return_value=_mock_graph(_GO_RESULT)
        ):
            response = client.post("/transform", json=_XML_TO_JSON_BODY)
        data = response.json()
        assert "confidence_scores" in data
        assert isinstance(data["confidence_scores"], dict)
        for field_name, score in data["confidence_scores"].items():
            assert 0.0 <= score <= 1.0, (
                f"confidence_scores['{field_name}'] = {score} is out of range"
            )


# =============================================================================
# TestAnalyseStubEndpoint
# =============================================================================

class TestAnalyseStubEndpoint:
    """Tests for POST /registry/analyse (Phase 4 stub)."""

    def test_analyse_returns_501(self):
        """POST /registry/analyse must return HTTP 501 (Not Implemented)."""
        response = client.post(
            "/registry/analyse", json={"payload": "<test/>"}
        )
        assert response.status_code == 501

    def test_analyse_detail_mentions_phase_4(self):
        """The 501 error detail must mention 'Phase 4' to guide the caller."""
        response = client.post(
            "/registry/analyse", json={"payload": "<test/>"}
        )
        detail = response.json()["detail"]
        assert "Phase 4" in detail


# =============================================================================
# TestExportStubEndpoint
# =============================================================================

class TestExportStubEndpoint:
    """Tests for POST /registry/export (Phase 4 stub)."""

    def test_export_returns_501(self):
        """POST /registry/export must return HTTP 501 (Not Implemented)."""
        response = client.post(
            "/registry/export",
            json={
                "fields": [
                    {
                        "field_name": "x",
                        "tier": 1,
                        "label": "Safety Critical",
                        "threshold": 1.0,
                    }
                ],
                "domain": "test",
            },
        )
        assert response.status_code == 501

    def test_export_detail_mentions_phase_4(self):
        """The 501 error detail must mention 'Phase 4' to guide the caller."""
        response = client.post(
            "/registry/export",
            json={
                "fields": [
                    {
                        "field_name": "x",
                        "tier": 1,
                        "label": "Safety Critical",
                        "threshold": 1.0,
                    }
                ],
                "domain": "test",
            },
        )
        detail = response.json()["detail"]
        assert "Phase 4" in detail
