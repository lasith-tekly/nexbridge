"""
Tests for TranslatorAgent

The TranslatorAgent is a deterministic JSON builder that constructs target
payloads from interpreter field mappings with type conversion. No LLM involved.
These tests validate all translation scenarios, type conversions, and edge cases.
"""

import pytest
from unittest.mock import Mock
from backend.core.agents.translator import (
    translator_node,
    _convert_value_to_type,
)
from backend.core.state import NexBridgeState
from backend.core.models import FieldMapping, Tier


class TestTranslatorNode:
    """Test suite for translator_node function."""

    # --- Happy Path Tests ---

    def test_translator_node_single_field_string_type(self):
        """
        Single FieldMapping with string type maps correctly to target JSON.
        Verifies target_field becomes key and transformed_value becomes value.
        """
        # Arrange
        mock_mapping = Mock(spec=FieldMapping)
        mock_mapping.field_name = "employee_id"
        mock_mapping.target_field = "id"
        mock_mapping.transformed_value = "E-12345"
        mock_mapping.tier = Tier.T3

        state: NexBridgeState = {
            "raw_payload": "<record></record>",
            "source_format": "xml",
            "target_format": "json",
            "target_schema": {"id": "string"},
            "field_classifications": {},
            "payload_tier": 3,
            "interpreter_run_1": {"employee_id": mock_mapping},
            "interpreter_run_2": {},
            "validation_result": {},
            "translated_payload": None,
            "decision": None,
            "decision_reason": None,
            "confidence_scores": {},
            "audit_log": [],
            "processing_start_ms": 0,
        }

        # Act
        result = translator_node(state)

        # Assert
        assert "translated_payload" in result
        assert result["translated_payload"] is not None
        assert len(result["translated_payload"]) == 1
        assert result["translated_payload"]["id"] == "E-12345"

    def test_translator_node_multiple_fields(self):
        """
        Multiple FieldMappings all appear in translated_payload.
        Verifies keys are target_field names, not source field names.
        """
        # Arrange
        mock_mapping_1 = Mock(spec=FieldMapping)
        mock_mapping_1.field_name = "employee_id"
        mock_mapping_1.target_field = "id"
        mock_mapping_1.transformed_value = "E-12345"
        mock_mapping_1.tier = Tier.T3

        mock_mapping_2 = Mock(spec=FieldMapping)
        mock_mapping_2.field_name = "department"
        mock_mapping_2.target_field = "dept_code"
        mock_mapping_2.transformed_value = "OPS"
        mock_mapping_2.tier = Tier.T3

        mock_mapping_3 = Mock(spec=FieldMapping)
        mock_mapping_3.field_name = "start_date"
        mock_mapping_3.target_field = "hire_date"
        mock_mapping_3.transformed_value = "2024-03-01"
        mock_mapping_3.tier = Tier.T3

        state: NexBridgeState = {
            "raw_payload": "<record></record>",
            "source_format": "xml",
            "target_format": "json",
            "target_schema": {
                "id": "string",
                "dept_code": "string",
                "hire_date": "string",
            },
            "field_classifications": {},
            "payload_tier": 3,
            "interpreter_run_1": {
                "employee_id": mock_mapping_1,
                "department": mock_mapping_2,
                "start_date": mock_mapping_3,
            },
            "interpreter_run_2": {},
            "validation_result": {},
            "translated_payload": None,
            "decision": None,
            "decision_reason": None,
            "confidence_scores": {},
            "audit_log": [],
            "processing_start_ms": 0,
        }

        # Act
        result = translator_node(state)

        # Assert
        assert len(result["translated_payload"]) == 3
        assert result["translated_payload"]["id"] == "E-12345"
        assert result["translated_payload"]["dept_code"] == "OPS"
        assert result["translated_payload"]["hire_date"] == "2024-03-01"
        # Verify source field names are NOT in output
        assert "employee_id" not in result["translated_payload"]
        assert "department" not in result["translated_payload"]
        assert "start_date" not in result["translated_payload"]

    # --- Type Conversion Tests ---

    def test_translator_node_type_conversion_number(self):
        """
        Target schema type 'number' converts string to float.
        """
        # Arrange
        mock_mapping = Mock(spec=FieldMapping)
        mock_mapping.field_name = "weight_limit"
        mock_mapping.target_field = "max_load"
        mock_mapping.transformed_value = "250"
        mock_mapping.tier = Tier.T1

        state: NexBridgeState = {
            "raw_payload": "<record></record>",
            "source_format": "xml",
            "target_format": "json",
            "target_schema": {"max_load": "number"},
            "field_classifications": {},
            "payload_tier": 1,
            "interpreter_run_1": {"weight_limit": mock_mapping},
            "interpreter_run_2": {},
            "validation_result": {},
            "translated_payload": None,
            "decision": None,
            "decision_reason": None,
            "confidence_scores": {},
            "audit_log": [],
            "processing_start_ms": 0,
        }

        # Act
        result = translator_node(state)

        # Assert
        assert result["translated_payload"]["max_load"] == 250.0
        assert isinstance(result["translated_payload"]["max_load"], float)

    def test_translator_node_type_conversion_integer(self):
        """
        Target schema type 'integer' converts string to int.
        """
        # Arrange
        mock_mapping = Mock(spec=FieldMapping)
        mock_mapping.field_name = "count"
        mock_mapping.target_field = "quantity"
        mock_mapping.transformed_value = "42"
        mock_mapping.tier = Tier.T3

        state: NexBridgeState = {
            "raw_payload": "<record></record>",
            "source_format": "xml",
            "target_format": "json",
            "target_schema": {"quantity": "integer"},
            "field_classifications": {},
            "payload_tier": 3,
            "interpreter_run_1": {"count": mock_mapping},
            "interpreter_run_2": {},
            "validation_result": {},
            "translated_payload": None,
            "decision": None,
            "decision_reason": None,
            "confidence_scores": {},
            "audit_log": [],
            "processing_start_ms": 0,
        }

        # Act
        result = translator_node(state)

        # Assert
        assert result["translated_payload"]["quantity"] == 42
        assert isinstance(result["translated_payload"]["quantity"], int)

    def test_translator_node_type_conversion_float_variant(self):
        """
        Target schema type 'float' (synonym for 'number') converts to float.
        """
        # Arrange
        mock_mapping = Mock(spec=FieldMapping)
        mock_mapping.field_name = "price"
        mock_mapping.target_field = "cost"
        mock_mapping.transformed_value = "99.99"
        mock_mapping.tier = Tier.T3

        state: NexBridgeState = {
            "raw_payload": "<record></record>",
            "source_format": "xml",
            "target_format": "json",
            "target_schema": {"cost": "float"},
            "field_classifications": {},
            "payload_tier": 3,
            "interpreter_run_1": {"price": mock_mapping},
            "interpreter_run_2": {},
            "validation_result": {},
            "translated_payload": None,
            "decision": None,
            "decision_reason": None,
            "confidence_scores": {},
            "audit_log": [],
            "processing_start_ms": 0,
        }

        # Act
        result = translator_node(state)

        # Assert
        assert result["translated_payload"]["cost"] == 99.99
        assert isinstance(result["translated_payload"]["cost"], float)

    def test_translator_node_type_conversion_int_variant(self):
        """
        Target schema type 'int' (synonym for 'integer') converts to int.
        """
        # Arrange
        mock_mapping = Mock(spec=FieldMapping)
        mock_mapping.field_name = "count"
        mock_mapping.target_field = "total"
        mock_mapping.transformed_value = "100"
        mock_mapping.tier = Tier.T3

        state: NexBridgeState = {
            "raw_payload": "<record></record>",
            "source_format": "xml",
            "target_format": "json",
            "target_schema": {"total": "int"},
            "field_classifications": {},
            "payload_tier": 3,
            "interpreter_run_1": {"count": mock_mapping},
            "interpreter_run_2": {},
            "validation_result": {},
            "translated_payload": None,
            "decision": None,
            "decision_reason": None,
            "confidence_scores": {},
            "audit_log": [],
            "processing_start_ms": 0,
        }

        # Act
        result = translator_node(state)

        # Assert
        assert result["translated_payload"]["total"] == 100
        assert isinstance(result["translated_payload"]["total"], int)

    # --- Graceful Fallback Tests ---

    def test_translator_node_type_conversion_fallback_number(self):
        """
        Invalid value for 'number' type falls back to string gracefully.
        """
        # Arrange
        mock_mapping = Mock(spec=FieldMapping)
        mock_mapping.field_name = "weight"
        mock_mapping.target_field = "max_load"
        mock_mapping.transformed_value = "abc"  # Invalid for float
        mock_mapping.tier = Tier.T3

        state: NexBridgeState = {
            "raw_payload": "<record></record>",
            "source_format": "xml",
            "target_format": "json",
            "target_schema": {"max_load": "number"},
            "field_classifications": {},
            "payload_tier": 3,
            "interpreter_run_1": {"weight": mock_mapping},
            "interpreter_run_2": {},
            "validation_result": {},
            "translated_payload": None,
            "decision": None,
            "decision_reason": None,
            "confidence_scores": {},
            "audit_log": [],
            "processing_start_ms": 0,
        }

        # Act
        result = translator_node(state)

        # Assert - graceful fallback to string
        assert result["translated_payload"]["max_load"] == "abc"
        assert isinstance(result["translated_payload"]["max_load"], str)

    def test_translator_node_type_conversion_fallback_integer(self):
        """
        Invalid value for 'integer' type falls back to string gracefully.
        """
        # Arrange
        mock_mapping = Mock(spec=FieldMapping)
        mock_mapping.field_name = "count"
        mock_mapping.target_field = "quantity"
        mock_mapping.transformed_value = "xyz"  # Invalid for int
        mock_mapping.tier = Tier.T3

        state: NexBridgeState = {
            "raw_payload": "<record></record>",
            "source_format": "xml",
            "target_format": "json",
            "target_schema": {"quantity": "integer"},
            "field_classifications": {},
            "payload_tier": 3,
            "interpreter_run_1": {"count": mock_mapping},
            "interpreter_run_2": {},
            "validation_result": {},
            "translated_payload": None,
            "decision": None,
            "decision_reason": None,
            "confidence_scores": {},
            "audit_log": [],
            "processing_start_ms": 0,
        }

        # Act
        result = translator_node(state)

        # Assert - graceful fallback to string
        assert result["translated_payload"]["quantity"] == "xyz"
        assert isinstance(result["translated_payload"]["quantity"], str)

    # --- Early Exit Tests ---

    def test_translator_node_early_exit_on_hold(self):
        """
        When decision is already HOLD, translator skips work and returns None.
        Verifies no fields are built when HOLD is set.
        """
        # Arrange
        mock_mapping = Mock(spec=FieldMapping)
        mock_mapping.field_name = "employee_id"
        mock_mapping.target_field = "id"
        mock_mapping.transformed_value = "E-12345"
        mock_mapping.tier = Tier.T3

        state: NexBridgeState = {
            "raw_payload": "<record></record>",
            "source_format": "xml",
            "target_format": "json",
            "target_schema": {"id": "string"},
            "field_classifications": {},
            "payload_tier": 3,
            "interpreter_run_1": {"employee_id": mock_mapping},
            "interpreter_run_2": {},
            "validation_result": {},
            "translated_payload": None,
            "decision": "HOLD",  # Already decided HOLD
            "decision_reason": "T1 confidence below threshold",
            "confidence_scores": {},
            "audit_log": [],
            "processing_start_ms": 0,
        }

        # Act
        result = translator_node(state)

        # Assert
        assert result["translated_payload"] is None
        assert result["decision"] == "HOLD"  # Unchanged
        # Verify state unchanged except translated_payload
        assert result["interpreter_run_1"] == state["interpreter_run_1"]

    # --- Edge Case Tests ---

    def test_translator_node_empty_interpreter_run_1(self):
        """
        Empty interpreter_run_1 produces empty dict, not None.
        """
        # Arrange
        state: NexBridgeState = {
            "raw_payload": "<record></record>",
            "source_format": "xml",
            "target_format": "json",
            "target_schema": {"id": "string"},
            "field_classifications": {},
            "payload_tier": 3,
            "interpreter_run_1": {},  # Empty
            "interpreter_run_2": {},
            "validation_result": {},
            "translated_payload": None,
            "decision": None,
            "decision_reason": None,
            "confidence_scores": {},
            "audit_log": [],
            "processing_start_ms": 0,
        }

        # Act
        result = translator_node(state)

        # Assert
        assert result["translated_payload"] == {}
        assert result["translated_payload"] is not None

    def test_translator_node_target_field_not_in_schema(self):
        """
        When target_field not in target_schema, value kept as-is (defaults to string).
        """
        # Arrange
        mock_mapping = Mock(spec=FieldMapping)
        mock_mapping.field_name = "custom_field"
        mock_mapping.target_field = "unknown_target"
        mock_mapping.transformed_value = "some_value"
        mock_mapping.tier = Tier.T3

        state: NexBridgeState = {
            "raw_payload": "<record></record>",
            "source_format": "xml",
            "target_format": "json",
            "target_schema": {"id": "string"},  # Does not contain unknown_target
            "field_classifications": {},
            "payload_tier": 3,
            "interpreter_run_1": {"custom_field": mock_mapping},
            "interpreter_run_2": {},
            "validation_result": {},
            "translated_payload": None,
            "decision": None,
            "decision_reason": None,
            "confidence_scores": {},
            "audit_log": [],
            "processing_start_ms": 0,
        }

        # Act
        result = translator_node(state)

        # Assert - defaults to string type, value unchanged
        assert result["translated_payload"]["unknown_target"] == "some_value"

    def test_translator_node_immutable_state(self):
        """
        Verifies original state dict is not mutated in place.
        """
        # Arrange
        mock_mapping = Mock(spec=FieldMapping)
        mock_mapping.field_name = "employee_id"
        mock_mapping.target_field = "id"
        mock_mapping.transformed_value = "E-12345"
        mock_mapping.tier = Tier.T3

        state: NexBridgeState = {
            "raw_payload": "<record></record>",
            "source_format": "xml",
            "target_format": "json",
            "target_schema": {"id": "string"},
            "field_classifications": {},
            "payload_tier": 3,
            "interpreter_run_1": {"employee_id": mock_mapping},
            "interpreter_run_2": {},
            "validation_result": {},
            "translated_payload": None,
            "decision": None,
            "decision_reason": None,
            "confidence_scores": {},
            "audit_log": [],
            "processing_start_ms": 0,
        }

        state_id_before = id(state)

        # Act
        result = translator_node(state)

        # Assert - new state object returned, not mutated
        assert id(result) != state_id_before
        assert state["translated_payload"] is None  # Original unchanged


class TestConvertValueToType:
    """Test suite for _convert_value_to_type helper function."""

    def test_convert_value_to_type_number(self):
        """
        String '250' with type 'number' converts to float 250.0.
        """
        result = _convert_value_to_type("250", "number", "test_field")
        assert result == 250.0
        assert isinstance(result, float)

    def test_convert_value_to_type_integer(self):
        """
        String '42' with type 'integer' converts to int 42.
        """
        result = _convert_value_to_type("42", "integer", "test_field")
        assert result == 42
        assert isinstance(result, int)

    def test_convert_value_to_type_string(self):
        """
        Any value with type 'string' remains unchanged.
        """
        result = _convert_value_to_type("test_value", "string", "test_field")
        assert result == "test_value"

    def test_convert_value_to_type_boolean(self):
        """
        Value with type 'boolean' remains unchanged (no special handling).
        """
        result = _convert_value_to_type(True, "boolean", "test_field")
        assert result is True

    def test_convert_value_to_type_invalid_number(self):
        """
        Invalid value 'abc' for type 'number' falls back to string 'abc'.
        """
        result = _convert_value_to_type("abc", "number", "test_field")
        assert result == "abc"
        assert isinstance(result, str)

    def test_convert_value_to_type_invalid_integer(self):
        """
        Invalid value 'xyz' for type 'integer' falls back to string 'xyz'.
        """
        result = _convert_value_to_type("xyz", "integer", "test_field")
        assert result == "xyz"
        assert isinstance(result, str)
