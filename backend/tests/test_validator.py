"""
Tests for ValidatorAgent

The ValidatorAgent is an advisory anomaly detector that never blocks the pipeline.
These tests validate all three validation checks (target field exists, confidence
threshold, type mismatch) and verify the validator never raises exceptions.
"""

import pytest
from unittest.mock import Mock
from backend.core.agents.validator import validator_node
from backend.core.state import NexBridgeState
from backend.core.models import FieldMapping, FieldClassification, Tier


# --- Fixtures ---

@pytest.fixture
def mock_field_mapping():
    """FieldMapping mock for validator tests."""
    mapping = Mock(spec=FieldMapping)
    mapping.field_name = "employee_id"
    mapping.target_field = "id"
    mapping.transformed_value = "E-12345"
    mapping.tier = Tier.T3
    return mapping


@pytest.fixture
def mock_t1_classification():
    """FieldClassification mock for T1 field."""
    classification = Mock(spec=FieldClassification)
    classification.tier = 1  # Direct int, not Mock()
    classification.confidence_threshold = 1.0
    classification.label = "Safety Critical"
    return classification


@pytest.fixture
def mock_t2_classification():
    """FieldClassification mock for T2 field."""
    classification = Mock(spec=FieldClassification)
    classification.tier = 2
    classification.confidence_threshold = 0.95
    classification.label = "Operationally Sensitive"
    return classification


@pytest.fixture
def mock_t3_classification():
    """FieldClassification mock for T3 field."""
    classification = Mock(spec=FieldClassification)
    classification.tier = 3
    classification.confidence_threshold = 0.80
    classification.label = "Business Important"
    return classification


@pytest.fixture
def mock_t4_classification():
    """FieldClassification mock for T4 field."""
    classification = Mock(spec=FieldClassification)
    classification.tier = 4
    classification.confidence_threshold = 0.0
    classification.label = "Informational"
    return classification


@pytest.fixture
def base_validator_state():
    """Minimal state for validator tests."""
    return {
        "raw_payload": "<record></record>",
        "source_format": "xml",
        "target_format": "json",
        "target_schema": {"id": "string"},
        "field_classifications": {},
        "payload_tier": 3,
        "parsed_fields": {},
        "root_element": None,
        "interpreter_run_1": {},
        "interpreter_run_2": {},
        "validation_result": {},
        "translated_payload": None,
        "decision": None,
        "decision_reason": None,
        "confidence_scores": {},
        "audit_log": [],
        "processing_start_ms": 0,
    }


# --- Test Classes ---

class TestValidatorNode:
    """Test suite for validator_node."""

    # --- No Anomaly Tests ---

    def test_validator_node_all_fields_valid_no_anomalies(
        self, base_validator_state, mock_t3_classification
    ):
        """
        All fields valid produces empty anomalies list and anomaly_count = 0.
        """
        # Arrange
        mock_mapping = Mock(spec=FieldMapping)
        mock_mapping.target_field = "id"
        mock_mapping.transformed_value = "E-12345"

        state = base_validator_state.copy()
        state["interpreter_run_1"] = {"employee_id": mock_mapping}
        state["target_schema"] = {"id": "string"}
        state["field_classifications"] = {"employee_id": mock_t3_classification}
        state["confidence_scores"] = {"employee_id": 0.95}

        # Act
        result = validator_node(state)

        # Assert
        assert result["validation_result"]["anomalies"] == []
        assert result["validation_result"]["anomaly_count"] == 0

    def test_validator_node_checked_fields_count_correct(
        self, base_validator_state, mock_t3_classification
    ):
        """
        3 fields in interpreter_run_1 produces checked_fields = 3.
        """
        # Arrange
        mock_mapping_1 = Mock(spec=FieldMapping)
        mock_mapping_1.target_field = "id"
        mock_mapping_1.transformed_value = "E-12345"

        mock_mapping_2 = Mock(spec=FieldMapping)
        mock_mapping_2.target_field = "dept"
        mock_mapping_2.transformed_value = "OPS"

        mock_mapping_3 = Mock(spec=FieldMapping)
        mock_mapping_3.target_field = "date"
        mock_mapping_3.transformed_value = "2024-01-01"

        state = base_validator_state.copy()
        state["interpreter_run_1"] = {
            "field_1": mock_mapping_1,
            "field_2": mock_mapping_2,
            "field_3": mock_mapping_3,
        }
        state["target_schema"] = {"id": "string", "dept": "string", "date": "string"}
        state["field_classifications"] = {
            "field_1": mock_t3_classification,
            "field_2": mock_t3_classification,
            "field_3": mock_t3_classification,
        }
        state["confidence_scores"] = {
            "field_1": 0.95,
            "field_2": 0.95,
            "field_3": 0.95,
        }

        # Act
        result = validator_node(state)

        # Assert
        assert result["validation_result"]["checked_fields"] == 3

    # --- Check A: target_field_not_in_schema ---

    def test_validator_node_target_field_not_in_schema_t1_high(
        self, base_validator_state, mock_t1_classification
    ):
        """
        T1 field mapping to target_field not in schema produces HIGH severity anomaly.
        """
        # Arrange
        mock_mapping = Mock(spec=FieldMapping)
        mock_mapping.target_field = "unknown_field"
        mock_mapping.transformed_value = "value"

        state = base_validator_state.copy()
        state["interpreter_run_1"] = {"weight_limit": mock_mapping}
        state["target_schema"] = {"id": "string"}  # unknown_field NOT in schema
        state["field_classifications"] = {"weight_limit": mock_t1_classification}
        state["confidence_scores"] = {"weight_limit": 1.0}

        # Act
        result = validator_node(state)

        # Assert
        assert result["validation_result"]["anomaly_count"] == 1
        anomaly = result["validation_result"]["anomalies"][0]
        assert anomaly["check"] == "target_field_not_in_schema"
        assert anomaly["severity"] == "HIGH"
        assert anomaly["field_name"] == "weight_limit"

    def test_validator_node_target_field_not_in_schema_t2_medium(
        self, base_validator_state, mock_t2_classification
    ):
        """
        T2 field mapping to target_field not in schema produces MEDIUM severity anomaly.
        """
        # Arrange
        mock_mapping = Mock(spec=FieldMapping)
        mock_mapping.target_field = "unknown_field"
        mock_mapping.transformed_value = "value"

        state = base_validator_state.copy()
        state["interpreter_run_1"] = {"department": mock_mapping}
        state["target_schema"] = {"id": "string"}
        state["field_classifications"] = {"department": mock_t2_classification}
        state["confidence_scores"] = {"department": 0.95}

        # Act
        result = validator_node(state)

        # Assert
        anomaly = result["validation_result"]["anomalies"][0]
        assert anomaly["severity"] == "MEDIUM"

    def test_validator_node_target_field_not_in_schema_t3_low(
        self, base_validator_state, mock_t3_classification
    ):
        """
        T3 field mapping to target_field not in schema produces LOW severity anomaly.
        """
        # Arrange
        mock_mapping = Mock(spec=FieldMapping)
        mock_mapping.target_field = "unknown_field"
        mock_mapping.transformed_value = "value"

        state = base_validator_state.copy()
        state["interpreter_run_1"] = {"notes": mock_mapping}
        state["target_schema"] = {"id": "string"}
        state["field_classifications"] = {"notes": mock_t3_classification}
        state["confidence_scores"] = {"notes": 0.85}

        # Act
        result = validator_node(state)

        # Assert
        anomaly = result["validation_result"]["anomalies"][0]
        assert anomaly["severity"] == "LOW"

    def test_validator_node_target_field_not_in_schema_check_name(
        self, base_validator_state, mock_t3_classification
    ):
        """
        Verify anomaly check name is exactly 'target_field_not_in_schema'.
        """
        # Arrange
        mock_mapping = Mock(spec=FieldMapping)
        mock_mapping.target_field = "unknown_field"
        mock_mapping.transformed_value = "value"

        state = base_validator_state.copy()
        state["interpreter_run_1"] = {"field": mock_mapping}
        state["target_schema"] = {"id": "string"}
        state["field_classifications"] = {"field": mock_t3_classification}
        state["confidence_scores"] = {"field": 0.85}

        # Act
        result = validator_node(state)

        # Assert
        anomaly = result["validation_result"]["anomalies"][0]
        assert anomaly["check"] == "target_field_not_in_schema"
        assert "unknown_field" in anomaly["detail"]

    # --- Check B: confidence_below_threshold ---

    def test_validator_node_t1_confidence_below_threshold(
        self, base_validator_state, mock_t1_classification
    ):
        """
        T1 field with confidence 0.99 (below 1.0) produces anomaly.
        """
        # Arrange
        mock_mapping = Mock(spec=FieldMapping)
        mock_mapping.target_field = "max_load"
        mock_mapping.transformed_value = "250"

        state = base_validator_state.copy()
        state["interpreter_run_1"] = {"weight_limit": mock_mapping}
        state["target_schema"] = {"max_load": "number"}
        state["field_classifications"] = {"weight_limit": mock_t1_classification}
        state["confidence_scores"] = {"weight_limit": 0.99}

        # Act
        result = validator_node(state)

        # Assert
        assert result["validation_result"]["anomaly_count"] >= 1
        # Find confidence_below_threshold anomaly
        anomalies = [a for a in result["validation_result"]["anomalies"]
                     if a["check"] == "confidence_below_threshold"]
        assert len(anomalies) == 1
        assert anomalies[0]["severity"] == "HIGH"

    def test_validator_node_t2_confidence_below_threshold(
        self, base_validator_state, mock_t2_classification
    ):
        """
        T2 field with confidence 0.94 (below 0.95) produces anomaly.
        """
        # Arrange
        mock_mapping = Mock(spec=FieldMapping)
        mock_mapping.target_field = "dept"
        mock_mapping.transformed_value = "OPS"

        state = base_validator_state.copy()
        state["interpreter_run_1"] = {"department": mock_mapping}
        state["target_schema"] = {"dept": "string"}
        state["field_classifications"] = {"department": mock_t2_classification}
        state["confidence_scores"] = {"department": 0.94}

        # Act
        result = validator_node(state)

        # Assert
        anomalies = [a for a in result["validation_result"]["anomalies"]
                     if a["check"] == "confidence_below_threshold"]
        assert len(anomalies) == 1
        assert anomalies[0]["severity"] == "MEDIUM"

    def test_validator_node_t3_confidence_below_threshold_low_severity(
        self, base_validator_state, mock_t3_classification
    ):
        """
        T3 field with confidence 0.79 (below 0.80) produces LOW severity anomaly.
        """
        # Arrange
        mock_mapping = Mock(spec=FieldMapping)
        mock_mapping.target_field = "notes"
        mock_mapping.transformed_value = "text"

        state = base_validator_state.copy()
        state["interpreter_run_1"] = {"notes": mock_mapping}
        state["target_schema"] = {"notes": "string"}
        state["field_classifications"] = {"notes": mock_t3_classification}
        state["confidence_scores"] = {"notes": 0.79}

        # Act
        result = validator_node(state)

        # Assert
        anomalies = [a for a in result["validation_result"]["anomalies"]
                     if a["check"] == "confidence_below_threshold"]
        assert len(anomalies) == 1
        assert anomalies[0]["severity"] == "LOW"

    def test_validator_node_confidence_anomaly_includes_values(
        self, base_validator_state, mock_t1_classification
    ):
        """
        Confidence anomaly detail includes actual confidence and threshold values.
        """
        # Arrange
        mock_mapping = Mock(spec=FieldMapping)
        mock_mapping.target_field = "max_load"
        mock_mapping.transformed_value = "250"

        state = base_validator_state.copy()
        state["interpreter_run_1"] = {"weight_limit": mock_mapping}
        state["target_schema"] = {"max_load": "number"}
        state["field_classifications"] = {"weight_limit": mock_t1_classification}
        state["confidence_scores"] = {"weight_limit": 0.87}

        # Act
        result = validator_node(state)

        # Assert
        anomalies = [a for a in result["validation_result"]["anomalies"]
                     if a["check"] == "confidence_below_threshold"]
        assert len(anomalies) == 1
        detail = anomalies[0]["detail"]
        assert "0.87" in detail
        assert "1" in detail or "1.0" in detail  # Threshold

    # --- Check C: type_mismatch ---

    def test_validator_node_type_mismatch_number_invalid(
        self, base_validator_state, mock_t3_classification
    ):
        """
        Target type 'number' with value 'abc' produces type_mismatch anomaly.
        """
        # Arrange
        mock_mapping = Mock(spec=FieldMapping)
        mock_mapping.target_field = "count"
        mock_mapping.transformed_value = "abc"

        state = base_validator_state.copy()
        state["interpreter_run_1"] = {"count": mock_mapping}
        state["target_schema"] = {"count": "number"}
        state["field_classifications"] = {"count": mock_t3_classification}
        state["confidence_scores"] = {"count": 0.95}

        # Act
        result = validator_node(state)

        # Assert
        anomalies = [a for a in result["validation_result"]["anomalies"]
                     if a["check"] == "type_mismatch"]
        assert len(anomalies) == 1
        assert "abc" in anomalies[0]["detail"]
        assert "number" in anomalies[0]["detail"]

    def test_validator_node_type_mismatch_integer_invalid(
        self, base_validator_state, mock_t3_classification
    ):
        """
        Target type 'integer' with value 'xyz' produces type_mismatch anomaly.
        """
        # Arrange
        mock_mapping = Mock(spec=FieldMapping)
        mock_mapping.target_field = "quantity"
        mock_mapping.transformed_value = "xyz"

        state = base_validator_state.copy()
        state["interpreter_run_1"] = {"quantity": mock_mapping}
        state["target_schema"] = {"quantity": "integer"}
        state["field_classifications"] = {"quantity": mock_t3_classification}
        state["confidence_scores"] = {"quantity": 0.95}

        # Act
        result = validator_node(state)

        # Assert
        anomalies = [a for a in result["validation_result"]["anomalies"]
                     if a["check"] == "type_mismatch"]
        assert len(anomalies) == 1

    def test_validator_node_string_type_never_flagged(
        self, base_validator_state, mock_t3_classification
    ):
        """
        Target type 'string' with any value never produces type_mismatch anomaly.
        """
        # Arrange
        mock_mapping = Mock(spec=FieldMapping)
        mock_mapping.target_field = "text"
        mock_mapping.transformed_value = "any_value_123"

        state = base_validator_state.copy()
        state["interpreter_run_1"] = {"text": mock_mapping}
        state["target_schema"] = {"text": "string"}
        state["field_classifications"] = {"text": mock_t3_classification}
        state["confidence_scores"] = {"text": 0.95}

        # Act
        result = validator_node(state)

        # Assert
        anomalies = [a for a in result["validation_result"]["anomalies"]
                     if a["check"] == "type_mismatch"]
        assert len(anomalies) == 0

    def test_validator_node_type_mismatch_check_name(
        self, base_validator_state, mock_t3_classification
    ):
        """
        Verify type mismatch anomaly check name is exactly 'type_mismatch'.
        """
        # Arrange
        mock_mapping = Mock(spec=FieldMapping)
        mock_mapping.target_field = "count"
        mock_mapping.transformed_value = "abc"

        state = base_validator_state.copy()
        state["interpreter_run_1"] = {"count": mock_mapping}
        state["target_schema"] = {"count": "number"}
        state["field_classifications"] = {"count": mock_t3_classification}
        state["confidence_scores"] = {"count": 0.95}

        # Act
        result = validator_node(state)

        # Assert
        anomaly = result["validation_result"]["anomalies"][0]
        assert anomaly["check"] == "type_mismatch"

    # --- HOLD Early Exit ---

    def test_validator_node_hold_early_exit_no_validation(
        self, base_validator_state
    ):
        """
        state['decision'] == 'HOLD' causes early exit with no validation_result update.
        """
        # Arrange
        state = base_validator_state.copy()
        state["decision"] = "HOLD"
        state["validation_result"] = {"existing": "data"}

        # Act
        result = validator_node(state)

        # Assert - validation_result should NOT be updated
        assert result["validation_result"] == {"existing": "data"}

    def test_validator_node_hold_returns_unchanged_state(
        self, base_validator_state
    ):
        """
        HOLD decision returns state completely unchanged.
        """
        # Arrange
        state = base_validator_state.copy()
        state["decision"] = "HOLD"
        state["translated_payload"] = {"id": "test"}
        state_id_before = id(state)

        # Act
        result = validator_node(state)

        # Assert - state object is returned as-is
        assert result is state
        assert result["translated_payload"] == {"id": "test"}

    # --- Multiple Anomalies ---

    def test_validator_node_multiple_anomalies_one_field(
        self, base_validator_state, mock_t1_classification
    ):
        """
        One field failing multiple checks produces multiple anomaly entries.
        """
        # Arrange - field fails both target_field_not_in_schema AND confidence check
        mock_mapping = Mock(spec=FieldMapping)
        mock_mapping.target_field = "unknown_field"
        mock_mapping.transformed_value = "value"

        state = base_validator_state.copy()
        state["interpreter_run_1"] = {"weight_limit": mock_mapping}
        state["target_schema"] = {"id": "string"}  # unknown_field NOT in schema
        state["field_classifications"] = {"weight_limit": mock_t1_classification}
        state["confidence_scores"] = {"weight_limit": 0.99}  # Below threshold

        # Act
        result = validator_node(state)

        # Assert - should have at least 2 anomalies
        assert result["validation_result"]["anomaly_count"] >= 2
        checks = [a["check"] for a in result["validation_result"]["anomalies"]]
        assert "target_field_not_in_schema" in checks
        assert "confidence_below_threshold" in checks

    def test_validator_node_anomaly_count_matches_length(
        self, base_validator_state, mock_t3_classification
    ):
        """
        anomaly_count always equals len(anomalies).
        """
        # Arrange
        mock_mapping = Mock(spec=FieldMapping)
        mock_mapping.target_field = "unknown"
        mock_mapping.transformed_value = "abc"

        state = base_validator_state.copy()
        state["interpreter_run_1"] = {"field": mock_mapping}
        state["target_schema"] = {"id": "string"}
        state["field_classifications"] = {"field": mock_t3_classification}
        state["confidence_scores"] = {"field": 0.70}

        # Act
        result = validator_node(state)

        # Assert
        assert result["validation_result"]["anomaly_count"] == len(
            result["validation_result"]["anomalies"]
        )

    # --- Severity Mapping ---

    def test_validator_node_severity_t1_high(
        self, base_validator_state, mock_t1_classification
    ):
        """
        T1 field anomaly produces severity 'HIGH'.
        """
        # Arrange
        mock_mapping = Mock(spec=FieldMapping)
        mock_mapping.target_field = "unknown"
        mock_mapping.transformed_value = "value"

        state = base_validator_state.copy()
        state["interpreter_run_1"] = {"weight_limit": mock_mapping}
        state["target_schema"] = {"id": "string"}
        state["field_classifications"] = {"weight_limit": mock_t1_classification}
        state["confidence_scores"] = {"weight_limit": 1.0}

        # Act
        result = validator_node(state)

        # Assert
        anomaly = result["validation_result"]["anomalies"][0]
        assert anomaly["severity"] == "HIGH"

    def test_validator_node_severity_t2_medium(
        self, base_validator_state, mock_t2_classification
    ):
        """
        T2 field anomaly produces severity 'MEDIUM'.
        """
        # Arrange
        mock_mapping = Mock(spec=FieldMapping)
        mock_mapping.target_field = "unknown"
        mock_mapping.transformed_value = "value"

        state = base_validator_state.copy()
        state["interpreter_run_1"] = {"department": mock_mapping}
        state["target_schema"] = {"id": "string"}
        state["field_classifications"] = {"department": mock_t2_classification}
        state["confidence_scores"] = {"department": 0.95}

        # Act
        result = validator_node(state)

        # Assert
        anomaly = result["validation_result"]["anomalies"][0]
        assert anomaly["severity"] == "MEDIUM"

    def test_validator_node_severity_t3_low(
        self, base_validator_state, mock_t3_classification
    ):
        """
        T3 field anomaly produces severity 'LOW'.
        """
        # Arrange
        mock_mapping = Mock(spec=FieldMapping)
        mock_mapping.target_field = "unknown"
        mock_mapping.transformed_value = "value"

        state = base_validator_state.copy()
        state["interpreter_run_1"] = {"notes": mock_mapping}
        state["target_schema"] = {"id": "string"}
        state["field_classifications"] = {"notes": mock_t3_classification}
        state["confidence_scores"] = {"notes": 0.85}

        # Act
        result = validator_node(state)

        # Assert
        anomaly = result["validation_result"]["anomalies"][0]
        assert anomaly["severity"] == "LOW"

    def test_validator_node_severity_t4_low(
        self, base_validator_state, mock_t4_classification
    ):
        """
        T4 field anomaly produces severity 'LOW'.
        """
        # Arrange
        mock_mapping = Mock(spec=FieldMapping)
        mock_mapping.target_field = "unknown"
        mock_mapping.transformed_value = "value"

        state = base_validator_state.copy()
        state["interpreter_run_1"] = {"notes": mock_mapping}
        state["target_schema"] = {"id": "string"}
        state["field_classifications"] = {"notes": mock_t4_classification}
        state["confidence_scores"] = {"notes": 0.50}

        # Act
        result = validator_node(state)

        # Assert
        anomaly = result["validation_result"]["anomalies"][0]
        assert anomaly["severity"] == "LOW"

    # --- Validator Never Raises ---

    def test_validator_node_malformed_state_returns_system_anomaly(
        self, base_validator_state
    ):
        """
        Malformed state produces validation_result with system-level anomaly flag.
        """
        # Arrange - missing required key to trigger exception
        state = base_validator_state.copy()
        del state["interpreter_run_1"]  # Remove required key

        # Act
        result = validator_node(state)

        # Assert - should return system anomaly, not raise
        assert "validation_result" in result
        assert result["validation_result"]["anomaly_count"] == 1
        anomaly = result["validation_result"]["anomalies"][0]
        assert anomaly["field_name"] == "SYSTEM"
        assert anomaly["check"] == "validator_error"
        assert anomaly["severity"] == "HIGH"

    def test_validator_node_never_raises_exception(
        self, base_validator_state
    ):
        """
        Validator never raises exception, converts all errors to anomaly flags.
        """
        # Arrange - intentionally broken state
        state = base_validator_state.copy()
        state["confidence_scores"] = None  # Will cause error when iterating

        # Act - should NOT raise
        try:
            result = validator_node(state)
            exception_raised = False
        except Exception:
            exception_raised = True

        # Assert
        assert exception_raised is False

    # --- Edge Cases ---

    def test_validator_node_empty_interpreter_run_1(
        self, base_validator_state
    ):
        """
        Empty interpreter_run_1 produces checked_fields = 0 with no anomalies.
        """
        # Arrange
        state = base_validator_state.copy()
        state["interpreter_run_1"] = {}

        # Act
        result = validator_node(state)

        # Assert
        assert result["validation_result"]["checked_fields"] == 0
        assert result["validation_result"]["anomaly_count"] == 0
        assert result["validation_result"]["anomalies"] == []

    def test_validator_node_missing_classification_defaults_t4(
        self, base_validator_state
    ):
        """
        Field without classification defaults to tier 4 (LOW severity).
        """
        # Arrange
        mock_mapping = Mock(spec=FieldMapping)
        mock_mapping.target_field = "unknown"
        mock_mapping.transformed_value = "value"

        state = base_validator_state.copy()
        state["interpreter_run_1"] = {"mystery_field": mock_mapping}
        state["target_schema"] = {"id": "string"}
        state["field_classifications"] = {}  # No classification for mystery_field
        state["confidence_scores"] = {"mystery_field": 0.95}

        # Act
        result = validator_node(state)

        # Assert - should default to T4 = LOW severity
        if result["validation_result"]["anomaly_count"] > 0:
            anomaly = result["validation_result"]["anomalies"][0]
            assert anomaly["severity"] == "LOW"
