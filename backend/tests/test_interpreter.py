"""
Tests for InterpreterAgent

The InterpreterAgent is the AI brain of NexBridge — it performs semantic
field mapping from XML to target JSON schema with confidence scoring.
These tests must validate all happy paths, error conditions, and edge cases.
"""

import pytest
from unittest.mock import Mock, MagicMock
from backend.core.agents.interpreter import (
    interpreter_node,
    _extract_field_value_from_xml,
    _build_target_fields_list,
    _build_llm_prompt,
)
from backend.core.state import NexBridgeState
from backend.core.models import FieldMapping, Tier
from backend.core.exceptions import LLMError


class TestInterpreterNode:
    """Test suite for interpreter_node function."""

    # --- Happy Path Tests ---

    def test_interpreter_node_go_scenario_single_field(self, mocker):
        """
        GO scenario: Valid XML with single T3 field maps successfully
        with confidence score in valid range.
        """
        # Arrange
        xml_payload = """<record>
    <employee_id>E-12345</employee_id>
</record>"""
        target_schema = {"id": "string"}
        field_classifications = {
            "employee_id": {
                "tier": Tier.T3,
                "label": "Business Important",
            }
        }

        state: NexBridgeState = {
            "raw_payload": xml_payload,
            "source_format": "xml",
            "target_format": "json",
            "target_schema": target_schema,
            "field_classifications": field_classifications,
            "payload_tier": 3,
            "interpreter_run_1": {},
            "interpreter_run_2": {},
            "validation_result": {},
            "translated_payload": None,
            "decision": None,
            "decision_reason": None,
            "confidence_scores": {},
            "parsed_fields": {},
            "root_element": None,
            "audit_log": [],
            "processing_start_ms": 0,
        }

        # Mock LLM response
        mock_field_mapping = Mock(spec=FieldMapping)
        mock_field_mapping.field_name = "employee_id"
        mock_field_mapping.target_field = "id"
        mock_field_mapping.transformed_value = "E-12345"
        mock_field_mapping.confidence = 0.98
        mock_field_mapping.reasoning = "Direct semantic match between employee_id and id"
        mock_field_mapping.tier = Tier.T3
        mock_field_mapping.model_dump.return_value = {
            "field_name": "employee_id",
            "target_field": "id",
            "transformed_value": "E-12345",
            "confidence": 0.98,
            "reasoning": "Direct semantic match between employee_id and id",
            "tier": 3,
        }

        # Mock get_llm and structured_llm
        mock_llm = MagicMock()
        mock_structured_llm = MagicMock()
        mock_structured_llm.invoke.return_value = mock_field_mapping
        mock_llm.with_structured_output.return_value = mock_structured_llm

        mocker.patch(
            "backend.core.agents.interpreter.get_llm",
            return_value=mock_llm
        )

        # Act
        result = interpreter_node(state)

        # Assert
        assert "interpreter_run_1" in result
        assert "confidence_scores" in result
        assert "employee_id" in result["interpreter_run_1"]
        assert result["interpreter_run_1"]["employee_id"]["target_field"] == "id"
        assert result["interpreter_run_1"]["employee_id"]["confidence"] == 0.98
        assert result["confidence_scores"]["employee_id"] == 0.98

    def test_interpreter_node_multiple_fields(self, mocker):
        """
        Test with 3+ fields to verify all are processed correctly.
        """
        # Arrange
        xml_payload = """<record>
    <employee_id>E-12345</employee_id>
    <department>Operations</department>
    <start_date>2024-03-01</start_date>
</record>"""
        target_schema = {
            "id": "string",
            "dept_code": "string",
            "start_date": "string",
        }
        field_classifications = {
            "employee_id": {"tier": Tier.T3, "label": "Business Important"},
            "department": {"tier": Tier.T3, "label": "Business Important"},
            "start_date": {"tier": Tier.T3, "label": "Business Important"},
        }

        state: NexBridgeState = {
            "raw_payload": xml_payload,
            "source_format": "xml",
            "target_format": "json",
            "target_schema": target_schema,
            "field_classifications": field_classifications,
            "payload_tier": 3,
            "interpreter_run_1": {},
            "interpreter_run_2": {},
            "validation_result": {},
            "translated_payload": None,
            "decision": None,
            "decision_reason": None,
            "confidence_scores": {},
            "parsed_fields": {},
            "root_element": None,
            "audit_log": [],
            "processing_start_ms": 0,
        }

        # Mock LLM responses for each field
        call_count = [0]

        def mock_invoke_side_effect(prompt):
            call_count[0] += 1
            call_num = call_count[0]

            # First call - employee_id
            if call_num == 1:
                m = Mock(spec=FieldMapping)
                m.field_name = "employee_id"
                m.target_field = "id"
                m.transformed_value = "E-12345"
                m.confidence = 0.98
                m.reasoning = "Direct match"
                m.tier = Tier.T3
                m.model_dump.return_value = {
                    "field_name": "employee_id",
                    "target_field": "id",
                    "transformed_value": "E-12345",
                    "confidence": 0.98,
                    "reasoning": "Direct match",
                    "tier": 3,
                }
                return m
            # Second call - department
            elif call_num == 2:
                m = Mock(spec=FieldMapping)
                m.field_name = "department"
                m.target_field = "dept_code"
                m.transformed_value = "Operations"
                m.confidence = 0.92
                m.reasoning = "Semantic match"
                m.tier = Tier.T3
                m.model_dump.return_value = {
                    "field_name": "department",
                    "target_field": "dept_code",
                    "transformed_value": "Operations",
                    "confidence": 0.92,
                    "reasoning": "Semantic match",
                    "tier": 3,
                }
                return m
            # Third call - start_date
            else:
                m = Mock(spec=FieldMapping)
                m.field_name = "start_date"
                m.target_field = "start_date"
                m.transformed_value = "2024-03-01"
                m.confidence = 1.0
                m.reasoning = "Exact match"
                m.tier = Tier.T3
                m.model_dump.return_value = {
                    "field_name": "start_date",
                    "target_field": "start_date",
                    "transformed_value": "2024-03-01",
                    "confidence": 1.0,
                    "reasoning": "Exact match",
                    "tier": 3,
                }
                return m

        mock_llm = MagicMock()
        mock_structured_llm = MagicMock()
        mock_structured_llm.invoke.side_effect = mock_invoke_side_effect
        mock_llm.with_structured_output.return_value = mock_structured_llm

        mocker.patch(
            "backend.core.agents.interpreter.get_llm",
            return_value=mock_llm
        )

        # Act
        result = interpreter_node(state)

        # Assert — all three fields processed
        assert len(result["interpreter_run_1"]) == 3
        assert len(result["confidence_scores"]) == 3
        assert "employee_id" in result["interpreter_run_1"]
        assert "department" in result["interpreter_run_1"]
        assert "start_date" in result["interpreter_run_1"]
        assert result["confidence_scores"]["employee_id"] == 0.98
        assert result["confidence_scores"]["department"] == 0.92
        assert result["confidence_scores"]["start_date"] == 1.0

    def test_interpreter_node_confidence_boundary_values(self, mocker):
        """
        Test confidence scoring at boundary values (0.0, 0.5, 1.0).
        """
        # Arrange
        xml_payload = """<record>
    <test_field>test_value</test_field>
</record>"""
        target_schema = {"test_output": "string"}
        field_classifications = {
            "test_field": {"tier": Tier.T3, "label": "Business Important"},
        }

        state: NexBridgeState = {
            "raw_payload": xml_payload,
            "source_format": "xml",
            "target_format": "json",
            "target_schema": target_schema,
            "field_classifications": field_classifications,
            "payload_tier": 3,
            "interpreter_run_1": {},
            "interpreter_run_2": {},
            "validation_result": {},
            "translated_payload": None,
            "decision": None,
            "decision_reason": None,
            "confidence_scores": {},
            "parsed_fields": {},
            "root_element": None,
            "audit_log": [],
            "processing_start_ms": 0,
        }

        # Test confidence = 0.0 (minimum)
        mock_field_mapping = Mock(spec=FieldMapping)
        mock_field_mapping.confidence = 0.0
        mock_field_mapping.target_field = "test_output"
        mock_field_mapping.model_dump.return_value = {
            "field_name": "test_field",
            "target_field": "test_output",
            "transformed_value": "test_value",
            "confidence": 0.0,
            "reasoning": "No match",
            "tier": 3,
        }

        mock_llm = MagicMock()
        mock_structured_llm = MagicMock()
        mock_structured_llm.invoke.return_value = mock_field_mapping
        mock_llm.with_structured_output.return_value = mock_structured_llm

        mocker.patch(
            "backend.core.agents.interpreter.get_llm",
            return_value=mock_llm
        )

        # Act
        result = interpreter_node(state)

        # Assert
        assert result["confidence_scores"]["test_field"] == 0.0

        # Test confidence = 1.0 (maximum)
        mock_field_mapping.confidence = 1.0
        mock_field_mapping.model_dump.return_value["confidence"] = 1.0

        result = interpreter_node(state)
        assert result["confidence_scores"]["test_field"] == 1.0

    # --- Error Condition Tests ---

    def test_interpreter_node_llm_failure_raises_llm_error(self, mocker):
        """
        LLM failure: Mock LLM to raise exception → verify LLMError
        with correct provider.
        """
        # Arrange
        xml_payload = """<record>
    <employee_id>E-12345</employee_id>
</record>"""
        target_schema = {"id": "string"}
        field_classifications = {
            "employee_id": {"tier": Tier.T3, "label": "Business Important"},
        }

        state: NexBridgeState = {
            "raw_payload": xml_payload,
            "source_format": "xml",
            "target_format": "json",
            "target_schema": target_schema,
            "field_classifications": field_classifications,
            "payload_tier": 3,
            "interpreter_run_1": {},
            "interpreter_run_2": {},
            "validation_result": {},
            "translated_payload": None,
            "decision": None,
            "decision_reason": None,
            "confidence_scores": {},
            "parsed_fields": {},
            "root_element": None,
            "audit_log": [],
            "processing_start_ms": 0,
        }

        # Mock LLM to raise exception
        mock_llm = MagicMock()
        mock_structured_llm = MagicMock()
        mock_structured_llm.invoke.side_effect = Exception("API timeout")
        mock_llm.with_structured_output.return_value = mock_structured_llm

        mocker.patch(
            "backend.core.agents.interpreter.get_llm",
            return_value=mock_llm
        )

        # Mock LLM_PROVIDER env var
        mocker.patch("backend.core.agents.interpreter.os.getenv", return_value="anthropic")

        # Act & Assert
        with pytest.raises(LLMError) as exc_info:
            interpreter_node(state)

        assert exc_info.value.provider == "anthropic"
        assert "API timeout" in str(exc_info.value)

    def test_interpreter_node_invalid_confidence_raises_value_error(self, mocker):
        """
        Invalid confidence: Mock LLM to return confidence = 1.5 → verify ValueError.
        """
        # Arrange
        xml_payload = """<record>
    <employee_id>E-12345</employee_id>
</record>"""
        target_schema = {"id": "string"}
        field_classifications = {
            "employee_id": {"tier": Tier.T3, "label": "Business Important"},
        }

        state: NexBridgeState = {
            "raw_payload": xml_payload,
            "source_format": "xml",
            "target_format": "json",
            "target_schema": target_schema,
            "field_classifications": field_classifications,
            "payload_tier": 3,
            "interpreter_run_1": {},
            "interpreter_run_2": {},
            "validation_result": {},
            "translated_payload": None,
            "decision": None,
            "decision_reason": None,
            "confidence_scores": {},
            "parsed_fields": {},
            "root_element": None,
            "audit_log": [],
            "processing_start_ms": 0,
        }

        # Mock LLM to return invalid confidence
        mock_field_mapping = Mock(spec=FieldMapping)
        mock_field_mapping.confidence = 1.5  # Invalid!
        mock_field_mapping.model_dump.return_value = {
            "field_name": "employee_id",
            "target_field": "id",
            "transformed_value": "E-12345",
            "confidence": 1.5,
            "reasoning": "Test",
            "tier": 3,
        }

        mock_llm = MagicMock()
        mock_structured_llm = MagicMock()
        mock_structured_llm.invoke.return_value = mock_field_mapping
        mock_llm.with_structured_output.return_value = mock_structured_llm

        mocker.patch(
            "backend.core.agents.interpreter.get_llm",
            return_value=mock_llm
        )

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            interpreter_node(state)

        assert "Invalid confidence 1.5" in str(exc_info.value)
        assert "employee_id" in str(exc_info.value)
        assert "[0.0, 1.0]" in str(exc_info.value)

    def test_interpreter_node_invalid_confidence_negative(self, mocker):
        """
        Invalid confidence: Negative value should raise ValueError.
        """
        # Arrange
        xml_payload = """<record>
    <employee_id>E-12345</employee_id>
</record>"""
        target_schema = {"id": "string"}
        field_classifications = {
            "employee_id": {"tier": Tier.T3, "label": "Business Important"},
        }

        state: NexBridgeState = {
            "raw_payload": xml_payload,
            "source_format": "xml",
            "target_format": "json",
            "target_schema": target_schema,
            "field_classifications": field_classifications,
            "payload_tier": 3,
            "interpreter_run_1": {},
            "interpreter_run_2": {},
            "validation_result": {},
            "translated_payload": None,
            "decision": None,
            "decision_reason": None,
            "confidence_scores": {},
            "parsed_fields": {},
            "root_element": None,
            "audit_log": [],
            "processing_start_ms": 0,
        }

        # Mock LLM to return negative confidence
        mock_field_mapping = Mock(spec=FieldMapping)
        mock_field_mapping.confidence = -0.5
        mock_field_mapping.model_dump.return_value = {
            "field_name": "employee_id",
            "target_field": "id",
            "transformed_value": "E-12345",
            "confidence": -0.5,
            "reasoning": "Test",
            "tier": 3,
        }

        mock_llm = MagicMock()
        mock_structured_llm = MagicMock()
        mock_structured_llm.invoke.return_value = mock_field_mapping
        mock_llm.with_structured_output.return_value = mock_structured_llm

        mocker.patch(
            "backend.core.agents.interpreter.get_llm",
            return_value=mock_llm
        )

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            interpreter_node(state)

        assert "Invalid confidence" in str(exc_info.value)

    # --- Edge Case Tests ---

    def test_interpreter_node_empty_field_classifications(self, mocker):
        """
        Empty field_classifications: Pass empty dict → verify empty output dicts.
        """
        # Arrange
        xml_payload = """<record>
    <employee_id>E-12345</employee_id>
</record>"""
        target_schema = {"id": "string"}
        field_classifications = {}  # Empty!

        state: NexBridgeState = {
            "raw_payload": xml_payload,
            "source_format": "xml",
            "target_format": "json",
            "target_schema": target_schema,
            "field_classifications": field_classifications,
            "payload_tier": 4,
            "interpreter_run_1": {},
            "interpreter_run_2": {},
            "validation_result": {},
            "translated_payload": None,
            "decision": None,
            "decision_reason": None,
            "confidence_scores": {},
            "parsed_fields": {},
            "root_element": None,
            "audit_log": [],
            "processing_start_ms": 0,
        }

        # Mock LLM (will be called once to get structured output, but invoke not called)
        mock_llm = MagicMock()
        mock_structured_llm = MagicMock()
        mock_llm.with_structured_output.return_value = mock_structured_llm

        mocker.patch(
            "backend.core.agents.interpreter.get_llm",
            return_value=mock_llm
        )

        # Act
        result = interpreter_node(state)

        # Assert — no fields processed
        assert result["interpreter_run_1"] == {}
        assert result["confidence_scores"] == {}
        mock_structured_llm.invoke.assert_not_called()

    def test_interpreter_node_xml_missing_field_returns_empty_string(self, mocker):
        """
        XML with missing field: Field in classification but not in XML
        → verify empty string handling.
        """
        # Arrange
        xml_payload = """<record>
    <employee_id>E-12345</employee_id>
</record>"""
        target_schema = {"id": "string", "dept": "string"}
        field_classifications = {
            "employee_id": {"tier": Tier.T3, "label": "Business Important"},
            "department": {"tier": Tier.T3, "label": "Business Important"},  # Missing!
        }

        state: NexBridgeState = {
            "raw_payload": xml_payload,
            "source_format": "xml",
            "target_format": "json",
            "target_schema": target_schema,
            "field_classifications": field_classifications,
            "payload_tier": 3,
            "interpreter_run_1": {},
            "interpreter_run_2": {},
            "validation_result": {},
            "translated_payload": None,
            "decision": None,
            "decision_reason": None,
            "confidence_scores": {},
            "parsed_fields": {},
            "root_element": None,
            "audit_log": [],
            "processing_start_ms": 0,
        }

        # Mock LLM responses
        def mock_invoke_side_effect(prompt):
            m = Mock(spec=FieldMapping)
            if "employee_id" in prompt:
                m.field_name = "employee_id"
                m.transformed_value = "E-12345"
                m.confidence = 0.98
            else:
                m.field_name = "department"
                m.transformed_value = ""  # Empty value
                m.confidence = 0.5
            m.target_field = "test"
            m.reasoning = "test"
            m.tier = Tier.T3
            m.model_dump.return_value = {
                "field_name": m.field_name,
                "target_field": m.target_field,
                "transformed_value": m.transformed_value,
                "confidence": m.confidence,
                "reasoning": m.reasoning,
                "tier": 3,
            }
            return m

        mock_llm = MagicMock()
        mock_structured_llm = MagicMock()
        mock_structured_llm.invoke.side_effect = mock_invoke_side_effect
        mock_llm.with_structured_output.return_value = mock_structured_llm

        mocker.patch(
            "backend.core.agents.interpreter.get_llm",
            return_value=mock_llm
        )

        # Act
        result = interpreter_node(state)

        # Assert — both fields processed, department has empty value
        assert len(result["interpreter_run_1"]) == 2
        assert "department" in result["interpreter_run_1"]

    def test_interpreter_node_state_immutability(self, mocker):
        """
        State immutability: Verify original state is not mutated (check object IDs).
        """
        # Arrange
        xml_payload = """<record>
    <employee_id>E-12345</employee_id>
</record>"""
        target_schema = {"id": "string"}
        field_classifications = {
            "employee_id": {"tier": Tier.T3, "label": "Business Important"},
        }

        state: NexBridgeState = {
            "raw_payload": xml_payload,
            "source_format": "xml",
            "target_format": "json",
            "target_schema": target_schema,
            "field_classifications": field_classifications,
            "payload_tier": 3,
            "interpreter_run_1": {},
            "interpreter_run_2": {},
            "validation_result": {},
            "translated_payload": None,
            "decision": None,
            "decision_reason": None,
            "confidence_scores": {},
            "parsed_fields": {},
            "root_element": None,
            "audit_log": [],
            "processing_start_ms": 0,
        }

        # Store original object IDs
        original_state_id = id(state)
        original_interpreter_run_1_id = id(state["interpreter_run_1"])
        original_confidence_scores_id = id(state["confidence_scores"])

        # Mock LLM
        mock_field_mapping = Mock(spec=FieldMapping)
        mock_field_mapping.field_name = "employee_id"
        mock_field_mapping.target_field = "id"
        mock_field_mapping.transformed_value = "E-12345"
        mock_field_mapping.confidence = 0.98
        mock_field_mapping.reasoning = "Test"
        mock_field_mapping.tier = Tier.T3
        mock_field_mapping.model_dump.return_value = {
            "field_name": "employee_id",
            "target_field": "id",
            "transformed_value": "E-12345",
            "confidence": 0.98,
            "reasoning": "Test",
            "tier": 3,
        }

        mock_llm = MagicMock()
        mock_structured_llm = MagicMock()
        mock_structured_llm.invoke.return_value = mock_field_mapping
        mock_llm.with_structured_output.return_value = mock_structured_llm

        mocker.patch(
            "backend.core.agents.interpreter.get_llm",
            return_value=mock_llm
        )

        # Act
        result = interpreter_node(state)

        # Assert — new state returned, original not mutated
        assert id(result) != original_state_id
        assert id(result["interpreter_run_1"]) != original_interpreter_run_1_id
        assert id(result["confidence_scores"]) != original_confidence_scores_id
        # Original state should still have empty dicts
        assert state["interpreter_run_1"] == {}
        assert state["confidence_scores"] == {}


class TestExtractFieldValueFromXml:
    """Test suite for _extract_field_value_from_xml helper function."""

    def test_extract_field_value_basic(self):
        """Extract simple field from valid XML."""
        # Arrange
        xml_payload = """<record>
    <employee_id>E-12345</employee_id>
</record>"""

        # Act
        result = _extract_field_value_from_xml(xml_payload, "employee_id")

        # Assert
        assert result == "E-12345"

    def test_extract_field_value_nested(self):
        """Extract nested field from XML."""
        # Arrange
        xml_payload = """<record>
    <employee>
        <employee_id>E-12345</employee_id>
    </employee>
</record>"""

        # Act
        result = _extract_field_value_from_xml(xml_payload, "employee_id")

        # Assert
        assert result == "E-12345"

    def test_extract_field_value_missing_field(self):
        """Missing field returns empty string."""
        # Arrange
        xml_payload = """<record>
    <employee_id>E-12345</employee_id>
</record>"""

        # Act
        result = _extract_field_value_from_xml(xml_payload, "department")

        # Assert
        assert result == ""

    def test_extract_field_value_malformed_xml(self):
        """Malformed XML returns empty string (graceful handling)."""
        # Arrange
        xml_payload = "<record><employee_id>E-12345"  # Malformed!

        # Act
        result = _extract_field_value_from_xml(xml_payload, "employee_id")

        # Assert
        assert result == ""

    def test_extract_field_value_empty_xml(self):
        """Empty XML returns empty string."""
        # Arrange
        xml_payload = ""

        # Act
        result = _extract_field_value_from_xml(xml_payload, "employee_id")

        # Assert
        assert result == ""

    def test_extract_field_value_strips_whitespace(self):
        """Field value whitespace is stripped."""
        # Arrange
        xml_payload = """<record>
    <employee_id>  E-12345  </employee_id>
</record>"""

        # Act
        result = _extract_field_value_from_xml(xml_payload, "employee_id")

        # Assert
        assert result == "E-12345"

    def test_extract_field_value_empty_element(self):
        """Empty element returns empty string."""
        # Arrange
        xml_payload = """<record>
    <employee_id></employee_id>
</record>"""

        # Act
        result = _extract_field_value_from_xml(xml_payload, "employee_id")

        # Assert
        assert result == ""


class TestBuildTargetFieldsList:
    """Test suite for _build_target_fields_list helper function."""

    def test_build_target_fields_list_single_field(self):
        """Single field formats correctly."""
        # Arrange
        target_schema = {"id": "string"}

        # Act
        result = _build_target_fields_list(target_schema)

        # Assert
        assert result == "- id (string)"

    def test_build_target_fields_list_multiple_fields(self):
        """Multiple fields format correctly with one per line."""
        # Arrange
        target_schema = {
            "id": "string",
            "dept_code": "string",
            "start_date": "string",
        }

        # Act
        result = _build_target_fields_list(target_schema)

        # Assert
        lines = result.split("\n")
        assert len(lines) == 3
        assert "- id (string)" in result
        assert "- dept_code (string)" in result
        assert "- start_date (string)" in result

    def test_build_target_fields_list_empty_schema(self):
        """Empty schema returns empty string."""
        # Arrange
        target_schema = {}

        # Act
        result = _build_target_fields_list(target_schema)

        # Assert
        assert result == ""

    def test_build_target_fields_list_different_types(self):
        """Fields with different types format correctly."""
        # Arrange
        target_schema = {
            "id": "string",
            "age": "number",
            "is_active": "boolean",
        }

        # Act
        result = _build_target_fields_list(target_schema)

        # Assert
        assert "- id (string)" in result
        assert "- age (number)" in result
        assert "- is_active (boolean)" in result


class TestInterpreterRun2Node:
    """Test suite for interpreter_run_2_node (T1 dual-agent verification)."""

    def test_interpreter_run_2_node_returns_interpreter_run_2(self, mocker):
        """
        interpreter_run_2_node populates interpreter_run_2 in state.
        Verifies that interpreter_run_1 is not modified.
        """
        # Arrange
        xml_payload = """<record>
    <weight_limit>250</weight_limit>
</record>"""
        target_schema = {"max_load": "number"}

        # Create proper FieldClassification object
        from backend.core.models import FieldClassification
        mock_classification = Mock(spec=FieldClassification)
        mock_classification.tier = Tier.T1
        mock_classification.label = "Safety Critical"
        mock_classification.confidence_threshold = 1.0

        field_classifications = {
            "weight_limit": mock_classification,
        }

        state: NexBridgeState = {
            "raw_payload": xml_payload,
            "source_format": "xml",
            "target_format": "json",
            "target_schema": target_schema,
            "field_classifications": field_classifications,
            "payload_tier": 1,
            "interpreter_run_1": {},
            "interpreter_run_2": {},
            "validation_result": {},
            "translated_payload": None,
            "decision": None,
            "decision_reason": None,
            "confidence_scores": {},
            "parsed_fields": {},
            "root_element": None,
            "audit_log": [],
            "processing_start_ms": 0,
        }

        # Mock LLM response
        mock_field_mapping = Mock(spec=FieldMapping)
        mock_field_mapping.field_name = "weight_limit"
        mock_field_mapping.target_field = "max_load"
        mock_field_mapping.transformed_value = 250
        mock_field_mapping.confidence = 1.0
        mock_field_mapping.reasoning = "Direct semantic match"
        mock_field_mapping.tier = Tier.T1
        mock_field_mapping.model_dump.return_value = {
            "field_name": "weight_limit",
            "target_field": "max_load",
            "transformed_value": 250,
            "confidence": 1.0,
            "reasoning": "Direct semantic match",
            "tier": 1,
        }

        mock_llm = MagicMock()
        mock_structured_llm = MagicMock()
        mock_structured_llm.invoke.return_value = mock_field_mapping
        mock_llm.with_structured_output.return_value = mock_structured_llm

        mocker.patch(
            "backend.core.agents.interpreter.get_llm",
            return_value=mock_llm
        )

        # Act
        from backend.core.agents.interpreter import interpreter_run_2_node
        result = interpreter_run_2_node(state)

        # Assert
        assert "interpreter_run_2" in result
        assert "weight_limit" in result["interpreter_run_2"]
        assert result["interpreter_run_2"]["weight_limit"]["target_field"] == "max_load"
        assert result["interpreter_run_2"]["weight_limit"]["confidence"] == 1.0
        # Verify interpreter_run_1 was not modified (should still be empty)
        assert result["interpreter_run_1"] == {}

    def test_interpreter_run_2_node_independent_execution(self, mocker):
        """
        interpreter_run_2_node executes independently from run_1.
        Verifies that existing interpreter_run_1 data is unchanged.
        """
        # Arrange
        xml_payload = """<record>
    <weight_limit>250</weight_limit>
</record>"""
        target_schema = {"max_load": "number"}

        # Create proper FieldClassification object
        from backend.core.models import FieldClassification
        mock_classification = Mock(spec=FieldClassification)
        mock_classification.tier = Tier.T1
        mock_classification.label = "Safety Critical"
        mock_classification.confidence_threshold = 1.0

        field_classifications = {
            "weight_limit": mock_classification,
        }

        # Pre-populate interpreter_run_1 with existing data
        existing_run_1_data = {
            "weight_limit": {
                "field_name": "weight_limit",
                "target_field": "weight_capacity",  # Different target!
                "transformed_value": 250,
                "confidence": 1.0,
                "reasoning": "Run 1 mapping",
                "tier": 1,
            }
        }

        state: NexBridgeState = {
            "raw_payload": xml_payload,
            "source_format": "xml",
            "target_format": "json",
            "target_schema": target_schema,
            "field_classifications": field_classifications,
            "payload_tier": 1,
            "interpreter_run_1": existing_run_1_data,
            "interpreter_run_2": {},
            "validation_result": {},
            "translated_payload": None,
            "decision": None,
            "decision_reason": None,
            "confidence_scores": {"weight_limit": 1.0},
            "parsed_fields": {},
            "root_element": None,
            "audit_log": [],
            "processing_start_ms": 0,
        }

        # Mock LLM response for run_2 (different target_field)
        mock_field_mapping = Mock(spec=FieldMapping)
        mock_field_mapping.field_name = "weight_limit"
        mock_field_mapping.target_field = "max_load"  # Different from run_1!
        mock_field_mapping.transformed_value = 250
        mock_field_mapping.confidence = 1.0
        mock_field_mapping.reasoning = "Run 2 mapping"
        mock_field_mapping.tier = Tier.T1
        mock_field_mapping.model_dump.return_value = {
            "field_name": "weight_limit",
            "target_field": "max_load",
            "transformed_value": 250,
            "confidence": 1.0,
            "reasoning": "Run 2 mapping",
            "tier": 1,
        }

        mock_llm = MagicMock()
        mock_structured_llm = MagicMock()
        mock_structured_llm.invoke.return_value = mock_field_mapping
        mock_llm.with_structured_output.return_value = mock_structured_llm

        mocker.patch(
            "backend.core.agents.interpreter.get_llm",
            return_value=mock_llm
        )

        # Act
        from backend.core.agents.interpreter import interpreter_run_2_node
        result = interpreter_run_2_node(state)

        # Assert
        assert "interpreter_run_2" in result
        assert result["interpreter_run_2"]["weight_limit"]["target_field"] == "max_load"
        # Verify interpreter_run_1 is unchanged (same content)
        assert result["interpreter_run_1"] == existing_run_1_data
        assert result["interpreter_run_1"]["weight_limit"]["target_field"] == "weight_capacity"

    def test_interpreter_run_2_node_produces_same_structure_as_run1(self, mocker):
        """
        interpreter_run_2_node produces same dict structure as interpreter_node.
        Both should have identical field mapping structure.
        """
        # Arrange
        xml_payload = """<record>
    <weight_limit>250</weight_limit>
    <clearance_level>L3</clearance_level>
</record>"""
        target_schema = {
            "max_load": "number",
            "access_level": "string",
        }

        # Create proper FieldClassification objects
        from backend.core.models import FieldClassification
        mock_classification_1 = Mock(spec=FieldClassification)
        mock_classification_1.tier = Tier.T1
        mock_classification_1.label = "Safety Critical"
        mock_classification_1.confidence_threshold = 1.0

        mock_classification_2 = Mock(spec=FieldClassification)
        mock_classification_2.tier = Tier.T1
        mock_classification_2.label = "Safety Critical"
        mock_classification_2.confidence_threshold = 1.0

        field_classifications = {
            "weight_limit": mock_classification_1,
            "clearance_level": mock_classification_2,
        }

        state: NexBridgeState = {
            "raw_payload": xml_payload,
            "source_format": "xml",
            "target_format": "json",
            "target_schema": target_schema,
            "field_classifications": field_classifications,
            "payload_tier": 1,
            "interpreter_run_1": {},
            "interpreter_run_2": {},
            "validation_result": {},
            "translated_payload": None,
            "decision": None,
            "decision_reason": None,
            "confidence_scores": {},
            "parsed_fields": {},
            "root_element": None,
            "audit_log": [],
            "processing_start_ms": 0,
        }

        # Mock LLM responses
        call_count = [0]

        def mock_invoke_side_effect(prompt):
            call_count[0] += 1
            call_num = call_count[0]

            m = Mock(spec=FieldMapping)
            if call_num == 1:
                m.field_name = "weight_limit"
                m.target_field = "max_load"
                m.transformed_value = 250
                m.confidence = 1.0
                m.reasoning = "Mapping 1"
                m.tier = Tier.T1
                m.model_dump.return_value = {
                    "field_name": "weight_limit",
                    "target_field": "max_load",
                    "transformed_value": 250,
                    "confidence": 1.0,
                    "reasoning": "Mapping 1",
                    "tier": 1,
                }
            else:
                m.field_name = "clearance_level"
                m.target_field = "access_level"
                m.transformed_value = "L3"
                m.confidence = 1.0
                m.reasoning = "Mapping 2"
                m.tier = Tier.T1
                m.model_dump.return_value = {
                    "field_name": "clearance_level",
                    "target_field": "access_level",
                    "transformed_value": "L3",
                    "confidence": 1.0,
                    "reasoning": "Mapping 2",
                    "tier": 1,
                }
            return m

        mock_llm = MagicMock()
        mock_structured_llm = MagicMock()
        mock_structured_llm.invoke.side_effect = mock_invoke_side_effect
        mock_llm.with_structured_output.return_value = mock_structured_llm

        mocker.patch(
            "backend.core.agents.interpreter.get_llm",
            return_value=mock_llm
        )

        # Act - Run both interpreter_node and interpreter_run_2_node
        from backend.core.agents.interpreter import interpreter_node, interpreter_run_2_node

        # Reset mock for run_1
        call_count[0] = 0
        run1_result = interpreter_node(state)

        # Reset mock for run_2
        call_count[0] = 0
        run2_result = interpreter_run_2_node(state)

        # Assert - Both have same field names
        assert set(run1_result["interpreter_run_1"].keys()) == {"weight_limit", "clearance_level"}
        assert set(run2_result["interpreter_run_2"].keys()) == {"weight_limit", "clearance_level"}

        # Assert - Both have same dict keys (field structure)
        run1_field_keys = set(run1_result["interpreter_run_1"]["weight_limit"].keys())
        run2_field_keys = set(run2_result["interpreter_run_2"]["weight_limit"].keys())

        assert run1_field_keys == run2_field_keys
        assert "target_field" in run1_field_keys
        assert "transformed_value" in run1_field_keys
        assert "confidence" in run1_field_keys
        assert "reasoning" in run1_field_keys
        assert "tier" in run1_field_keys

    def test_interpreter_run_2_node_does_not_populate_confidence_scores(self, mocker):
        """
        interpreter_run_2_node does NOT populate confidence_scores.
        Only interpreter_node (run_1) populates confidence_scores.
        """
        # Arrange
        xml_payload = """<record>
    <weight_limit>250</weight_limit>
</record>"""
        target_schema = {"max_load": "number"}

        # Create proper FieldClassification object
        from backend.core.models import FieldClassification
        mock_classification = Mock(spec=FieldClassification)
        mock_classification.tier = Tier.T1
        mock_classification.label = "Safety Critical"
        mock_classification.confidence_threshold = 1.0

        field_classifications = {
            "weight_limit": mock_classification,
        }

        state: NexBridgeState = {
            "raw_payload": xml_payload,
            "source_format": "xml",
            "target_format": "json",
            "target_schema": target_schema,
            "field_classifications": field_classifications,
            "payload_tier": 1,
            "interpreter_run_1": {},
            "interpreter_run_2": {},
            "validation_result": {},
            "translated_payload": None,
            "decision": None,
            "decision_reason": None,
            "confidence_scores": {},
            "parsed_fields": {},
            "root_element": None,
            "audit_log": [],
            "processing_start_ms": 0,
        }

        # Mock LLM response
        mock_field_mapping = Mock(spec=FieldMapping)
        mock_field_mapping.field_name = "weight_limit"
        mock_field_mapping.target_field = "max_load"
        mock_field_mapping.transformed_value = 250
        mock_field_mapping.confidence = 1.0
        mock_field_mapping.reasoning = "Direct semantic match"
        mock_field_mapping.tier = Tier.T1
        mock_field_mapping.model_dump.return_value = {
            "field_name": "weight_limit",
            "target_field": "max_load",
            "transformed_value": 250,
            "confidence": 1.0,
            "reasoning": "Direct semantic match",
            "tier": 1,
        }

        mock_llm = MagicMock()
        mock_structured_llm = MagicMock()
        mock_structured_llm.invoke.return_value = mock_field_mapping
        mock_llm.with_structured_output.return_value = mock_structured_llm

        mocker.patch(
            "backend.core.agents.interpreter.get_llm",
            return_value=mock_llm
        )

        # Act
        from backend.core.agents.interpreter import interpreter_run_2_node
        result = interpreter_run_2_node(state)

        # Assert - confidence_scores should still be empty
        assert result["confidence_scores"] == {}


class TestBuildLlmPrompt:
    """Test suite for _build_llm_prompt helper function."""

    def test_build_llm_prompt_t1_field(self):
        """T1 field prompt contains all required elements."""
        # Arrange
        field_name = "weight_limit"
        field_value = "250"
        tier = 1
        tier_label = "Safety Critical"
        target_schema = {"max_permitted_load": "number"}

        # Act
        result = _build_llm_prompt(
            field_name=field_name,
            field_value=field_value,
            tier=tier,
            tier_label=tier_label,
            target_schema=target_schema
        )

        # Assert
        assert "weight_limit" in result
        assert "250" in result
        assert "T1" in result
        assert "Safety Critical" in result
        assert "max_permitted_load" in result
        assert "0.95-1.0" in result
        assert "confidence" in result.lower()

    def test_build_llm_prompt_t2_field(self):
        """T2 field prompt contains correct tier information."""
        # Arrange
        field_name = "contract_type"
        field_value = "FULL_TIME"
        tier = 2
        tier_label = "Operationally Sensitive"
        target_schema = {"emp_type": "string"}

        # Act
        result = _build_llm_prompt(
            field_name=field_name,
            field_value=field_value,
            tier=tier,
            tier_label=tier_label,
            target_schema=target_schema
        )

        # Assert
        assert "contract_type" in result
        assert "FULL_TIME" in result
        assert "T2" in result
        assert "Operationally Sensitive" in result
        assert "emp_type" in result

    def test_build_llm_prompt_t3_field(self):
        """T3 field prompt contains correct tier information."""
        # Arrange
        field_name = "employee_id"
        field_value = "E-12345"
        tier = 3
        tier_label = "Business Important"
        target_schema = {"id": "string"}

        # Act
        result = _build_llm_prompt(
            field_name=field_name,
            field_value=field_value,
            tier=tier,
            tier_label=tier_label,
            target_schema=target_schema
        )

        # Assert
        assert "employee_id" in result
        assert "E-12345" in result
        assert "T3" in result
        assert "Business Important" in result
        assert "id" in result

    def test_build_llm_prompt_multiple_target_fields(self):
        """Prompt with multiple target fields lists all correctly."""
        # Arrange
        field_name = "employee_id"
        field_value = "E-12345"
        tier = 3
        tier_label = "Business Important"
        target_schema = {
            "id": "string",
            "emp_id": "string",
            "employee_code": "string",
        }

        # Act
        result = _build_llm_prompt(
            field_name=field_name,
            field_value=field_value,
            tier=tier,
            tier_label=tier_label,
            target_schema=target_schema
        )

        # Assert
        assert "id" in result
        assert "emp_id" in result
        assert "employee_code" in result

    def test_build_llm_prompt_contains_instructions(self):
        """Prompt contains semantic mapping instructions."""
        # Arrange
        field_name = "test"
        field_value = "value"
        tier = 3
        tier_label = "Business Important"
        target_schema = {"output": "string"}

        # Act
        result = _build_llm_prompt(
            field_name=field_name,
            field_value=field_value,
            tier=tier,
            tier_label=tier_label,
            target_schema=target_schema
        )

        # Assert
        assert "semantic" in result.lower()
        assert "confidence" in result.lower()
        assert "reasoning" in result.lower()
        assert "transformed_value" in result.lower()
