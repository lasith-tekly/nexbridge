"""
Tests for POST /registry/propose-mappings endpoint and mapping_proposer agent.

AirNova scenario:
  System A (FMS): weight_limit (T1), fuel_load (T1), flight_number (T3), gate_number (T4)
  System B (GSP): max_permitted_load, max_fuel_capacity, flight_code, departure_gate
  Domain: flight-ops
"""

import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from backend.api.main import app

client = TestClient(app)

# ── AirNova test fixtures ─────────────────────────────────────────────────────

SYSTEM_A_FIELDS = [
    {"name": "weight_limit", "tier": 1, "threshold": 1.0},
    {"name": "fuel_load", "tier": 1, "threshold": 1.0},
    {"name": "flight_number", "tier": 3, "threshold": 0.80},
    {"name": "gate_number", "tier": 4, "threshold": 0.0},
]

SYSTEM_B_FIELDS = [
    "max_permitted_load",
    "max_fuel_capacity",
    "flight_code",
    "departure_gate",
]

VALID_REQUEST = {
    "domain": "flight-ops",
    "source_system": "FMS",
    "target_system": "GSP",
    "system_a_fields": SYSTEM_A_FIELDS,
    "system_b_fields": SYSTEM_B_FIELDS,
}

# ── Mock LLM response matching AirNova scenario ───────────────────────────────

MOCK_LLM_JSON = {
    "system_b_tiers": {
        "max_permitted_load": {"tier": 1, "reasoning": "Maximum load is safety-critical."},
        "max_fuel_capacity": {"tier": 1, "reasoning": "Fuel capacity is safety-critical."},
        "flight_code": {"tier": 3, "reasoning": "Flight identifier is business-important."},
        "departure_gate": {"tier": 4, "reasoning": "Gate number is informational metadata."},
    },
    "proposed_mappings": [
        {
            "source_field": "weight_limit",
            "target_field": "max_permitted_load",
            "confidence": 0.98,
            "reasoning": "Both represent maximum permissible load weight.",
        },
        {
            "source_field": "fuel_load",
            "target_field": "max_fuel_capacity",
            "confidence": 0.97,
            "reasoning": "Both describe fuel quantity constraints.",
        },
        {
            "source_field": "flight_number",
            "target_field": "flight_code",
            "confidence": 0.95,
            "reasoning": "Both are identifiers for the flight.",
        },
        {
            "source_field": "gate_number",
            "target_field": "departure_gate",
            "confidence": 0.93,
            "reasoning": "Both refer to the departure gate location.",
        },
    ],
}

# Scenario where gate_number (T4) maps to max_permitted_load (T1) — cross-tier mismatch
MOCK_LLM_JSON_MISMATCH = {
    "system_b_tiers": {
        "max_permitted_load": {"tier": 1, "reasoning": "Safety-critical load constraint."},
        "max_fuel_capacity": {"tier": 1, "reasoning": "Safety-critical fuel constraint."},
        "flight_code": {"tier": 3, "reasoning": "Business identifier."},
        "departure_gate": {"tier": 4, "reasoning": "Informational metadata."},
    },
    "proposed_mappings": [
        {
            "source_field": "weight_limit",
            "target_field": "max_permitted_load",
            "confidence": 0.98,
            "reasoning": "Same concept.",
        },
        {
            "source_field": "fuel_load",
            "target_field": "max_fuel_capacity",
            "confidence": 0.97,
            "reasoning": "Same concept.",
        },
        {
            "source_field": "flight_number",
            "target_field": "flight_code",
            "confidence": 0.95,
            "reasoning": "Same concept.",
        },
        {
            # Intentional tier mismatch: T4 source → T1 target
            "source_field": "gate_number",
            "target_field": "max_permitted_load",
            "confidence": 0.10,
            "reasoning": "Forced mismatch for testing.",
        },
    ],
}


def _mock_llm(raw_json: dict) -> MagicMock:
    """Return a mock LLM whose .invoke() returns the given dict as JSON content."""
    mock_response = MagicMock()
    mock_response.content = json.dumps(raw_json)
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = mock_response
    return mock_llm


# =============================================================================
# TestProposeMappingsEndpoint — happy path
# =============================================================================

class TestProposeMappingsEndpoint:
    """Tests for POST /registry/propose-mappings — happy path."""

    def test_returns_200(self):
        with patch(
            "backend.core.agents.mapping_proposer.get_llm",
            return_value=_mock_llm(MOCK_LLM_JSON),
        ):
            response = client.post("/registry/propose-mappings", json=VALID_REQUEST)
        assert response.status_code == 200

    def test_returns_system_b_tiers_for_all_fields(self):
        """system_b_tiers must contain an entry for every System B field."""
        with patch(
            "backend.core.agents.mapping_proposer.get_llm",
            return_value=_mock_llm(MOCK_LLM_JSON),
        ):
            response = client.post("/registry/propose-mappings", json=VALID_REQUEST)
        data = response.json()
        assert set(data["system_b_tiers"].keys()) == set(SYSTEM_B_FIELDS)

    def test_system_b_tiers_have_tier_threshold_reasoning(self):
        """Each SystemBTierResult must have tier, threshold, and reasoning."""
        with patch(
            "backend.core.agents.mapping_proposer.get_llm",
            return_value=_mock_llm(MOCK_LLM_JSON),
        ):
            response = client.post("/registry/propose-mappings", json=VALID_REQUEST)
        for name, result in response.json()["system_b_tiers"].items():
            assert "tier" in result, f"Missing tier for {name}"
            assert "threshold" in result, f"Missing threshold for {name}"
            assert "reasoning" in result, f"Missing reasoning for {name}"

    def test_system_b_threshold_matches_tier_constant(self):
        """threshold in each SystemBTierResult must match CONFIDENCE_THRESHOLDS[tier]."""
        from backend.core.constants import CONFIDENCE_THRESHOLDS

        with patch(
            "backend.core.agents.mapping_proposer.get_llm",
            return_value=_mock_llm(MOCK_LLM_JSON),
        ):
            response = client.post("/registry/propose-mappings", json=VALID_REQUEST)
        for result in response.json()["system_b_tiers"].values():
            assert result["threshold"] == CONFIDENCE_THRESHOLDS[result["tier"]]

    def test_returns_proposed_mappings_for_all_system_a_fields(self):
        """proposed_mappings must contain one entry per System A field."""
        with patch(
            "backend.core.agents.mapping_proposer.get_llm",
            return_value=_mock_llm(MOCK_LLM_JSON),
        ):
            response = client.post("/registry/propose-mappings", json=VALID_REQUEST)
        data = response.json()
        source_fields = {m["source_field"] for m in data["proposed_mappings"]}
        expected = {f["name"] for f in SYSTEM_A_FIELDS}
        assert source_fields == expected

    def test_proposed_mappings_have_all_required_keys(self):
        """Each MappingProposal must include all required keys."""
        required = {
            "source_field", "target_field", "confidence", "reasoning",
            "source_tier", "target_tier", "tier_mismatch",
            "effective_tier", "effective_threshold",
        }
        with patch(
            "backend.core.agents.mapping_proposer.get_llm",
            return_value=_mock_llm(MOCK_LLM_JSON),
        ):
            response = client.post("/registry/propose-mappings", json=VALID_REQUEST)
        for m in response.json()["proposed_mappings"]:
            assert required.issubset(m.keys())

    def test_response_echoes_domain_and_systems(self):
        """Response must echo domain, source_system, and target_system."""
        with patch(
            "backend.core.agents.mapping_proposer.get_llm",
            return_value=_mock_llm(MOCK_LLM_JSON),
        ):
            response = client.post("/registry/propose-mappings", json=VALID_REQUEST)
        data = response.json()
        assert data["domain"] == "flight-ops"
        assert data["source_system"] == "FMS"
        assert data["target_system"] == "GSP"


# =============================================================================
# TestProposeMappingsTierLogic — tier calculations in Python
# =============================================================================

class TestProposeMappingsTierLogic:
    """Tests for effective_tier, tier_mismatch, and tier_mismatches list."""

    def test_no_tier_mismatch_when_tiers_match(self):
        """weight_limit (T1) → max_permitted_load (T1): tier_mismatch must be False."""
        with patch(
            "backend.core.agents.mapping_proposer.get_llm",
            return_value=_mock_llm(MOCK_LLM_JSON),
        ):
            response = client.post("/registry/propose-mappings", json=VALID_REQUEST)
        mappings = {m["source_field"]: m for m in response.json()["proposed_mappings"]}
        assert mappings["weight_limit"]["tier_mismatch"] is False
        assert mappings["fuel_load"]["tier_mismatch"] is False

    def test_tier_mismatch_true_when_tiers_differ(self):
        """gate_number (T4) → max_permitted_load (T1) must have tier_mismatch=True."""
        with patch(
            "backend.core.agents.mapping_proposer.get_llm",
            return_value=_mock_llm(MOCK_LLM_JSON_MISMATCH),
        ):
            response = client.post("/registry/propose-mappings", json=VALID_REQUEST)
        mappings = {m["source_field"]: m for m in response.json()["proposed_mappings"]}
        assert mappings["gate_number"]["tier_mismatch"] is True

    def test_effective_tier_is_most_restrictive_tier(self):
        """effective_tier must be min(source_tier, target_tier) — highest risk wins."""
        with patch(
            "backend.core.agents.mapping_proposer.get_llm",
            return_value=_mock_llm(MOCK_LLM_JSON_MISMATCH),
        ):
            response = client.post("/registry/propose-mappings", json=VALID_REQUEST)
        mappings = {m["source_field"]: m for m in response.json()["proposed_mappings"]}
        # gate_number (T4) → max_permitted_load (T1): effective = min(4,1) = 1
        gate_mapping = mappings["gate_number"]
        assert gate_mapping["source_tier"] == 4
        assert gate_mapping["target_tier"] == 1
        assert gate_mapping["effective_tier"] == 1  # min(4, 1) = 1

    def test_effective_tier_correct_for_matching_tiers(self):
        """When both tiers match, effective_tier equals that tier."""
        with patch(
            "backend.core.agents.mapping_proposer.get_llm",
            return_value=_mock_llm(MOCK_LLM_JSON),
        ):
            response = client.post("/registry/propose-mappings", json=VALID_REQUEST)
        mappings = {m["source_field"]: m for m in response.json()["proposed_mappings"]}
        # weight_limit (T1) → max_permitted_load (T1): effective = min(1,1) = 1
        assert mappings["weight_limit"]["effective_tier"] == 1
        # flight_number (T3) → flight_code (T3): effective = min(3,3) = 3
        assert mappings["flight_number"]["effective_tier"] == 3

    def test_effective_threshold_matches_effective_tier(self):
        """effective_threshold must equal CONFIDENCE_THRESHOLDS[effective_tier]."""
        from backend.core.constants import CONFIDENCE_THRESHOLDS

        with patch(
            "backend.core.agents.mapping_proposer.get_llm",
            return_value=_mock_llm(MOCK_LLM_JSON_MISMATCH),
        ):
            response = client.post("/registry/propose-mappings", json=VALID_REQUEST)
        for m in response.json()["proposed_mappings"]:
            assert m["effective_threshold"] == CONFIDENCE_THRESHOLDS[m["effective_tier"]]

    def test_tier_mismatches_list_contains_mismatched_source_fields(self):
        """tier_mismatches must list source_field names where tier_mismatch=True."""
        with patch(
            "backend.core.agents.mapping_proposer.get_llm",
            return_value=_mock_llm(MOCK_LLM_JSON_MISMATCH),
        ):
            response = client.post("/registry/propose-mappings", json=VALID_REQUEST)
        data = response.json()
        assert "gate_number" in data["tier_mismatches"]

    def test_tier_mismatches_empty_when_all_tiers_match(self):
        """tier_mismatches must be empty when every mapping has matching tiers."""
        with patch(
            "backend.core.agents.mapping_proposer.get_llm",
            return_value=_mock_llm(MOCK_LLM_JSON),
        ):
            response = client.post("/registry/propose-mappings", json=VALID_REQUEST)
        assert response.json()["tier_mismatches"] == []


# =============================================================================
# TestProposeMappingsValidation — 422 on empty lists
# =============================================================================

class TestProposeMappingsValidation:
    """Tests for request validation — 422 on empty field lists."""

    def test_returns_422_when_system_a_fields_empty(self):
        """Empty system_a_fields must return HTTP 422."""
        payload = {**VALID_REQUEST, "system_a_fields": []}
        response = client.post("/registry/propose-mappings", json=payload)
        assert response.status_code == 422

    def test_returns_422_when_system_b_fields_empty(self):
        """Empty system_b_fields must return HTTP 422."""
        payload = {**VALID_REQUEST, "system_b_fields": []}
        response = client.post("/registry/propose-mappings", json=payload)
        assert response.status_code == 422

    def test_returns_422_when_domain_missing(self):
        """Missing domain must return HTTP 422."""
        payload = {k: v for k, v in VALID_REQUEST.items() if k != "domain"}
        response = client.post("/registry/propose-mappings", json=payload)
        assert response.status_code == 422

    def test_returns_422_when_source_system_missing(self):
        """Missing source_system must return HTTP 422."""
        payload = {k: v for k, v in VALID_REQUEST.items() if k != "source_system"}
        response = client.post("/registry/propose-mappings", json=payload)
        assert response.status_code == 422


# =============================================================================
# TestProposeMappingsLLMErrors — 500 on LLM failures
# =============================================================================

class TestProposeMappingsLLMErrors:
    """Tests for LLM failure paths."""

    def test_returns_500_when_llm_raises(self):
        """LLM exception must return HTTP 500."""
        mock_llm = MagicMock()
        mock_llm.invoke.side_effect = RuntimeError("LLM unavailable")
        with patch(
            "backend.core.agents.mapping_proposer.get_llm",
            return_value=mock_llm,
        ):
            response = client.post("/registry/propose-mappings", json=VALID_REQUEST)
        assert response.status_code == 500

    def test_returns_500_when_llm_returns_non_json(self):
        """Non-JSON LLM response must return HTTP 500 mentioning parse failure."""
        mock_response = MagicMock()
        mock_response.content = "Sorry, I cannot help with that."
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = mock_response
        with patch(
            "backend.core.agents.mapping_proposer.get_llm",
            return_value=mock_llm,
        ):
            response = client.post("/registry/propose-mappings", json=VALID_REQUEST)
        assert response.status_code == 500
        assert "non-JSON" in response.json()["detail"] or "500" in str(response.status_code)


# =============================================================================
# TestFloatThresholdInExport — confirm float fix holds
# =============================================================================

class TestFloatThresholdInExport:
    """Confirm threshold 1.0 exports as float, not integer."""

    def test_t1_threshold_exports_as_float(self):
        """T1 threshold must appear as 1.0 (float) not 1 (int) in exported JSON."""
        payload = {
            "fields": [
                {
                    "field_name": "weight_limit",
                    "tier": 1,
                    "label": "Safety Critical",
                    "threshold": 1.0,
                    "confirmed_individually": True,
                }
            ],
            "integration_name": "float-test",
        }
        response = client.post("/registry/export", json=payload)
        assert response.status_code == 200
        content = json.loads(response.json()["content"])
        threshold_value = content["fields"]["weight_limit"]["threshold"]
        assert isinstance(threshold_value, float), (
            f"Expected float, got {type(threshold_value).__name__}: {threshold_value}"
        )
        assert threshold_value == 1.0
