"""
Tests for ClassificationRegistry

The registry is the foundation of NexBridge's safety layer.
If it misclassifies a T1 field, the entire governance model fails.
These tests must be comprehensive and never skipped.
"""

import json
import pytest
from pathlib import Path

from backend.core.classification.registry import ClassificationRegistry
from backend.core.models import FieldClassification, Tier
from backend.core.constants import CONFIDENCE_THRESHOLDS


class TestClassificationRegistry:
    """Test suite for ClassificationRegistry class."""

    # --- Basic Classification Tests ---

    def test_weight_limit_classifies_as_t1(self, registry):
        """weight_limit must classify as T1 with threshold=1.0"""
        # Arrange: registry fixture loaded

        # Act
        result = registry.classify("weight_limit")

        # Assert
        assert result.field_name == "weight_limit"
        assert result.tier == Tier.T1
        assert result.confidence_threshold == 1.0
        assert result.label == "Safety Critical"

    def test_contract_type_classifies_as_t2(self, registry):
        """contract_type must classify as T2 with threshold=0.95"""
        # Arrange: registry fixture loaded

        # Act
        result = registry.classify("contract_type")

        # Assert
        assert result.field_name == "contract_type"
        assert result.tier == Tier.T2
        assert result.confidence_threshold == 0.95
        assert result.label == "Operationally Sensitive"

    def test_employee_id_classifies_as_t3(self, registry):
        """employee_id must classify as T3 with threshold=0.80"""
        # Arrange: registry fixture loaded

        # Act
        result = registry.classify("employee_id")

        # Assert
        assert result.field_name == "employee_id"
        assert result.tier == Tier.T3
        assert result.confidence_threshold == 0.80
        assert result.label == "Business Important"

    def test_office_location_classifies_as_t4(self, registry):
        """office_location must classify as T4 with threshold=0.0"""
        # Arrange: registry fixture loaded

        # Act
        result = registry.classify("office_location")

        # Assert
        assert result.field_name == "office_location"
        assert result.tier == Tier.T4
        assert result.confidence_threshold == 0.0
        assert result.label == "Informational"

    def test_classify_returns_field_classification_model(self, registry):
        """classify() must return FieldClassification Pydantic model"""
        # Arrange: registry fixture loaded

        # Act
        result = registry.classify("weight_limit")

        # Assert
        assert isinstance(result, FieldClassification)

    def test_field_classification_is_frozen(self, registry):
        """FieldClassification must be immutable after creation"""
        # Arrange
        result = registry.classify("weight_limit")

        # Act & Assert
        with pytest.raises(Exception):
            result.tier = Tier.T2  # must raise — frozen model

    # --- Unknown Field Tests ---

    def test_unknown_field_defaults_to_t4(self, registry):
        """Unknown field name must default to T4"""
        # Arrange: registry fixture loaded

        # Act
        result = registry.classify("unknown_field_xyz")

        # Assert
        assert result.field_name == "unknown_field_xyz"
        assert result.tier == Tier.T4
        assert result.label == "Informational"

    def test_unknown_field_never_raises_classification_error(self, registry):
        """Unknown fields must never raise ClassificationError"""
        # Arrange: registry fixture loaded

        # Act & Assert — no exception should be raised
        result = registry.classify("completely_unknown_field")
        assert result.tier == Tier.T4

    def test_unknown_field_threshold_is_zero(self, registry):
        """Unknown field must have threshold=0.0"""
        # Arrange: registry fixture loaded

        # Act
        result = registry.classify("unknown_field_xyz")

        # Assert
        assert result.confidence_threshold == 0.0

    # --- Payload Tier Tests ---

    def test_payload_tier_all_t3_fields(self, registry):
        """Payload with only T3 fields must return tier=3"""
        # Arrange
        field_names = ["employee_id", "department", "job_title"]

        # Act
        payload_tier = registry.get_payload_tier(field_names)

        # Assert
        assert payload_tier == 3

    def test_payload_tier_mix_t2_and_t3(self, registry):
        """Payload with mix of T2 and T3 must return tier=2 (highest risk)"""
        # Arrange
        field_names = ["contract_type", "employee_id", "department"]

        # Act
        payload_tier = registry.get_payload_tier(field_names)

        # Assert
        assert payload_tier == 2

    @pytest.mark.safety
    def test_payload_tier_with_t1_field(self, registry):
        """
        SAFETY CRITICAL: ANY T1 field in payload must return tier=1.
        This test must NEVER be skipped or marked xfail.
        """
        # Arrange — mix of T1, T2, T3, T4 fields
        field_names = [
            "weight_limit",      # T1
            "contract_type",     # T2
            "employee_id",       # T3
            "office_location",   # T4
        ]

        # Act
        payload_tier = registry.get_payload_tier(field_names)

        # Assert
        assert payload_tier == 1, "ANY T1 field must result in payload tier 1"

    def test_payload_tier_single_field(self, registry):
        """Single field list must work correctly"""
        # Arrange
        field_names = ["contract_type"]  # T2 field

        # Act
        payload_tier = registry.get_payload_tier(field_names)

        # Assert
        assert payload_tier == 2

    def test_payload_tier_empty_list(self, registry):
        """Empty field list must return default tier=4"""
        # Arrange
        field_names = []

        # Act
        payload_tier = registry.get_payload_tier(field_names)

        # Assert
        assert payload_tier == 4

    # --- list_fields_by_tier Tests ---

    def test_list_fields_by_tier_t1_contains_weight_limit(self, registry):
        """T1 field list must contain weight_limit"""
        # Arrange: registry fixture loaded

        # Act
        t1_fields = registry.list_fields_by_tier(1)

        # Assert
        assert "weight_limit" in t1_fields
        assert all(
            registry.classify(field).tier == Tier.T1
            for field in t1_fields
        )

    def test_list_fields_by_tier_t2_contains_contract_type(self, registry):
        """T2 field list must contain contract_type"""
        # Arrange: registry fixture loaded

        # Act
        t2_fields = registry.list_fields_by_tier(2)

        # Assert
        assert "contract_type" in t2_fields
        assert all(
            registry.classify(field).tier == Tier.T2
            for field in t2_fields
        )

    def test_list_fields_by_tier_t3_contains_employee_id(self, registry):
        """T3 field list must contain employee_id"""
        # Arrange: registry fixture loaded

        # Act
        t3_fields = registry.list_fields_by_tier(3)

        # Assert
        assert "employee_id" in t3_fields
        assert all(
            registry.classify(field).tier == Tier.T3
            for field in t3_fields
        )

    def test_list_fields_by_tier_t4_contains_office_location(self, registry):
        """T4 field list must contain office_location"""
        # Arrange: registry fixture loaded

        # Act
        t4_fields = registry.list_fields_by_tier(4)

        # Assert
        assert "office_location" in t4_fields
        assert all(
            registry.classify(field).tier == Tier.T4
            for field in t4_fields
        )

    def test_list_fields_by_tier_invalid_tier_returns_empty(self, registry):
        """Invalid tier number must return empty list"""
        # Arrange: registry fixture loaded

        # Act
        result = registry.list_fields_by_tier(99)

        # Assert
        assert result == []

    # --- REGISTRY_PATH Override Test ---

    def test_registry_path_override_loads_custom_registry(
        self, tmp_path, monkeypatch
    ):
        """
        REGISTRY_PATH environment variable must override default registry.
        Custom registry must be loaded instead of default.
        """
        # Arrange — create custom registry JSON
        custom_registry = {
            "version": "1.0-custom",
            "domain": "test",
            "default_tier": 4,
            "fields": {
                "custom_critical": {
                    "tier": 1,
                    "label": "Safety Critical",
                    "threshold": 1.0,
                    "description": "Custom T1 field for testing"
                }
            }
        }

        custom_path = tmp_path / "custom_registry.json"
        with open(custom_path, "w") as f:
            json.dump(custom_registry, f)

        # Set REGISTRY_PATH env var using monkeypatch (auto-cleanup)
        monkeypatch.setenv("REGISTRY_PATH", str(custom_path))

        # Act — create new registry instance with custom path
        registry = ClassificationRegistry()

        # Assert — custom field is present
        result = registry.classify("custom_critical")
        assert result.tier == Tier.T1
        assert result.confidence_threshold == 1.0

        # Assert — default fields are NOT present
        weight_limit_result = registry.classify("weight_limit")
        assert weight_limit_result.tier == Tier.T4  # defaults to T4 as unknown

    # --- Safety-Critical Test ---

    @pytest.mark.safety
    def test_payload_tier_t1_field_safety_critical(self, registry):
        """
        SAFETY CRITICAL TEST.
        Payload tier must be 1 when ANY T1 field is present.
        This test must NEVER be skipped or marked xfail.
        """
        # Arrange — payload with one T1 field and other tiers
        field_names = [
            "max_load",          # T1 — this triggers tier 1
            "access_level",      # T2
            "start_date",        # T3
            "notes",             # T4
        ]

        # Act
        payload_tier = registry.get_payload_tier(field_names)

        # Assert
        assert payload_tier == 1, (
            "SAFETY FAILURE: Payload with T1 field must have tier=1. "
            "This is a critical safety requirement."
        )
