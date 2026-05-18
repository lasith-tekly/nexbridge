"""
Tests for Orchestrator

The Orchestrator is the single governance gate in NexBridge. These tests
validate the decision logic (GO/HOLD), classification, and XML parsing.
Safety-critical tests are marked with @pytest.mark.safety.
"""

import pytest
from unittest.mock import Mock
from backend.core.orchestrator import (
    orchestrator_node,
    classification_node,
    extract_field_names_from_xml,
)
from backend.core.state import NexBridgeState
from backend.core.models import FieldClassification, Tier
from backend.core.constants import CONFIDENCE_THRESHOLDS


# --- Fixtures ---

@pytest.fixture
def mock_t1_classification():
    """FieldClassification mock for T1 field."""
    classification = Mock(spec=FieldClassification)
    classification.tier = Mock()
    classification.tier.value = 1
    classification.confidence_threshold = 1.0
    classification.label = "Safety Critical"
    return classification


@pytest.fixture
def mock_t2_classification():
    """FieldClassification mock for T2 field."""
    classification = Mock(spec=FieldClassification)
    classification.tier = Mock()
    classification.tier.value = 2
    classification.confidence_threshold = 0.95
    classification.label = "Operationally Sensitive"
    return classification


@pytest.fixture
def mock_t3_classification():
    """FieldClassification mock for T3 field."""
    classification = Mock(spec=FieldClassification)
    classification.tier = Mock()
    classification.tier.value = 3
    classification.confidence_threshold = 0.80
    classification.label = "Business Important"
    return classification


@pytest.fixture
def mock_t4_classification():
    """FieldClassification mock for T4 field."""
    classification = Mock(spec=FieldClassification)
    classification.tier = Mock()
    classification.tier.value = 4
    classification.confidence_threshold = 0.0
    classification.label = "Informational"
    return classification


@pytest.fixture
def base_orchestrator_state():
    """Minimal state for orchestrator tests."""
    return {
        "xml_payload": "<record></record>",
        "target_schema": {"id": "string"},
        "field_classifications": {},
        "payload_tier": 3,
        "interpreter_run_1": {},
        "interpreter_run_2": {},
        "validation_result": {},
        "translated_payload": {"id": "test-value"},
        "decision": None,
        "decision_reason": None,
        "confidence_scores": {},
        "audit_log": [],
        "processing_start_ms": 0,
    }


# --- Test Classes ---

class TestOrchestratorNode:
    """Test suite for orchestrator_node decision logic."""

    # --- GO Scenarios ---

    def test_orchestrator_node_all_t3_above_threshold_go(
        self, base_orchestrator_state, mock_t3_classification
    ):
        """
        T3 field with confidence above threshold (0.80) produces GO decision.
        """
        # Arrange
        state = base_orchestrator_state.copy()
        state["field_classifications"] = {"employee_id": mock_t3_classification}
        state["confidence_scores"] = {"employee_id": 0.85}
        state["payload_tier"] = 3

        # Act
        result = orchestrator_node(state)

        # Assert
        assert result["decision"] == "GO"
        assert result["decision_reason"] == "All fields passed confidence checks"
        assert result["translated_payload"] == {"id": "test-value"}

    def test_orchestrator_node_t2_exactly_at_threshold_go(
        self, base_orchestrator_state, mock_t2_classification
    ):
        """
        T2 field with confidence exactly at threshold (0.95) produces GO.
        """
        # Arrange
        state = base_orchestrator_state.copy()
        state["field_classifications"] = {"department": mock_t2_classification}
        state["confidence_scores"] = {"department": 0.95}
        state["payload_tier"] = 2

        # Act
        result = orchestrator_node(state)

        # Assert
        assert result["decision"] == "GO"
        assert result["translated_payload"] == {"id": "test-value"}

    @pytest.mark.safety
    def test_orchestrator_node_t1_exactly_at_threshold_go(
        self, base_orchestrator_state, mock_t1_classification
    ):
        """
        SAFETY TEST: T1 field with confidence exactly 1.0 MUST produce GO.
        This test must never be skipped or marked xfail.
        """
        # Arrange
        state = base_orchestrator_state.copy()
        state["field_classifications"] = {"weight_limit": mock_t1_classification}
        state["confidence_scores"] = {"weight_limit": 1.0}
        state["payload_tier"] = 1

        # Act
        result = orchestrator_node(state)

        # Assert
        assert result["decision"] == "GO"
        assert result["translated_payload"] == {"id": "test-value"}

    def test_orchestrator_node_t4_any_confidence_go(
        self, base_orchestrator_state, mock_t4_classification
    ):
        """
        T4 field with any confidence (even 0.10) produces GO.
        T4 has no threshold check.
        """
        # Arrange
        state = base_orchestrator_state.copy()
        state["field_classifications"] = {"notes": mock_t4_classification}
        state["confidence_scores"] = {"notes": 0.10}
        state["payload_tier"] = 4

        # Act
        result = orchestrator_node(state)

        # Assert
        assert result["decision"] == "GO"
        assert result["translated_payload"] == {"id": "test-value"}

    def test_orchestrator_node_empty_confidence_scores_go(
        self, base_orchestrator_state
    ):
        """
        Empty confidence_scores produces GO (no fields to check).
        """
        # Arrange
        state = base_orchestrator_state.copy()
        state["confidence_scores"] = {}
        state["field_classifications"] = {}

        # Act
        result = orchestrator_node(state)

        # Assert
        assert result["decision"] == "GO"
        assert result["decision_reason"] == "All fields passed confidence checks"

    def test_orchestrator_node_multiple_t3_above_threshold_go(
        self, base_orchestrator_state, mock_t3_classification
    ):
        """
        Multiple T3 fields all above threshold produce GO.
        """
        # Arrange
        state = base_orchestrator_state.copy()
        state["field_classifications"] = {
            "field_1": mock_t3_classification,
            "field_2": mock_t3_classification,
            "field_3": mock_t3_classification,
        }
        state["confidence_scores"] = {
            "field_1": 0.85,
            "field_2": 0.90,
            "field_3": 0.82,
        }
        state["payload_tier"] = 3

        # Act
        result = orchestrator_node(state)

        # Assert
        assert result["decision"] == "GO"

    # --- HOLD Scenarios ---

    @pytest.mark.safety
    def test_orchestrator_node_t1_below_threshold_hold(
        self, base_orchestrator_state, mock_t1_classification
    ):
        """
        SAFETY TEST: T1 field with confidence 0.99 (below 1.0) MUST produce HOLD.
        This test must never be skipped or marked xfail.
        """
        # Arrange
        state = base_orchestrator_state.copy()
        state["field_classifications"] = {"weight_limit": mock_t1_classification}
        state["confidence_scores"] = {"weight_limit": 0.99}
        state["payload_tier"] = 1

        # Act
        result = orchestrator_node(state)

        # Assert
        assert result["decision"] == "HOLD"
        assert "weight_limit" in result["decision_reason"]
        assert "0.99" in result["decision_reason"]

    @pytest.mark.safety
    def test_orchestrator_node_t1_zero_confidence_hold(
        self, base_orchestrator_state, mock_t1_classification
    ):
        """
        SAFETY TEST: T1 field with confidence 0.0 MUST produce HOLD.
        This test must never be skipped or marked xfail.
        """
        # Arrange
        state = base_orchestrator_state.copy()
        state["field_classifications"] = {"weight_limit": mock_t1_classification}
        state["confidence_scores"] = {"weight_limit": 0.0}
        state["payload_tier"] = 1

        # Act
        result = orchestrator_node(state)

        # Assert
        assert result["decision"] == "HOLD"
        assert "weight_limit" in result["decision_reason"]

    def test_orchestrator_node_t2_below_threshold_hold(
        self, base_orchestrator_state, mock_t2_classification
    ):
        """
        T2 field with confidence 0.94 (below 0.95) produces HOLD.
        """
        # Arrange
        state = base_orchestrator_state.copy()
        state["field_classifications"] = {"department": mock_t2_classification}
        state["confidence_scores"] = {"department": 0.94}
        state["payload_tier"] = 2

        # Act
        result = orchestrator_node(state)

        # Assert
        assert result["decision"] == "HOLD"
        assert "department" in result["decision_reason"]
        assert "0.94" in result["decision_reason"]

    def test_orchestrator_node_t2_zero_confidence_hold(
        self, base_orchestrator_state, mock_t2_classification
    ):
        """
        T2 field with confidence 0.0 produces HOLD.
        """
        # Arrange
        state = base_orchestrator_state.copy()
        state["field_classifications"] = {"department": mock_t2_classification}
        state["confidence_scores"] = {"department": 0.0}
        state["payload_tier"] = 2

        # Act
        result = orchestrator_node(state)

        # Assert
        assert result["decision"] == "HOLD"

    def test_orchestrator_node_mixed_t3_below_t2_above_go(
        self, base_orchestrator_state, mock_t2_classification, mock_t3_classification
    ):
        """
        T3 below threshold + T2 above threshold produces GO.
        Verifies T3 below threshold does NOT cause HOLD.
        """
        # Arrange
        state = base_orchestrator_state.copy()
        state["field_classifications"] = {
            "notes": mock_t3_classification,
            "department": mock_t2_classification,
        }
        state["confidence_scores"] = {
            "notes": 0.50,  # Below T3 threshold (0.80)
            "department": 0.95,  # At T2 threshold
        }
        state["payload_tier"] = 2

        # Act
        result = orchestrator_node(state)

        # Assert
        assert result["decision"] == "GO"
        assert result["translated_payload"] == {"id": "test-value"}

    # --- State Verification ---

    @pytest.mark.safety
    def test_orchestrator_node_hold_sets_translated_payload_none(
        self, base_orchestrator_state, mock_t1_classification
    ):
        """
        SAFETY TEST: HOLD decision MUST set translated_payload to None.
        This test must never be skipped or marked xfail.
        """
        # Arrange
        state = base_orchestrator_state.copy()
        state["field_classifications"] = {"weight_limit": mock_t1_classification}
        state["confidence_scores"] = {"weight_limit": 0.99}
        state["translated_payload"] = {"id": "test-value"}  # Pre-populated

        # Act
        result = orchestrator_node(state)

        # Assert
        assert result["decision"] == "HOLD"
        assert result["translated_payload"] is None

    def test_orchestrator_node_go_preserves_translated_payload(
        self, base_orchestrator_state, mock_t3_classification
    ):
        """
        GO decision preserves translated_payload from input state.
        """
        # Arrange
        state = base_orchestrator_state.copy()
        state["field_classifications"] = {"employee_id": mock_t3_classification}
        state["confidence_scores"] = {"employee_id": 0.85}
        state["translated_payload"] = {"id": "test-value", "dept": "OPS"}

        # Act
        result = orchestrator_node(state)

        # Assert
        assert result["decision"] == "GO"
        assert result["translated_payload"] == {"id": "test-value", "dept": "OPS"}

    def test_orchestrator_node_decision_reason_always_set(
        self, base_orchestrator_state, mock_t1_classification, mock_t3_classification
    ):
        """
        Both GO and HOLD decisions have non-empty decision_reason.
        """
        # GO scenario
        state_go = base_orchestrator_state.copy()
        state_go["field_classifications"] = {"employee_id": mock_t3_classification}
        state_go["confidence_scores"] = {"employee_id": 0.85}

        result_go = orchestrator_node(state_go)
        assert result_go["decision_reason"] != ""
        assert result_go["decision_reason"] is not None

        # HOLD scenario
        state_hold = base_orchestrator_state.copy()
        state_hold["field_classifications"] = {"weight_limit": mock_t1_classification}
        state_hold["confidence_scores"] = {"weight_limit": 0.99}

        result_hold = orchestrator_node(state_hold)
        assert result_hold["decision_reason"] != ""
        assert result_hold["decision_reason"] is not None

    def test_orchestrator_node_decision_always_go_or_hold(
        self, base_orchestrator_state, mock_t1_classification, mock_t3_classification
    ):
        """
        Decision is always exactly 'GO' or 'HOLD', never None.
        """
        # GO scenario
        state_go = base_orchestrator_state.copy()
        state_go["field_classifications"] = {"employee_id": mock_t3_classification}
        state_go["confidence_scores"] = {"employee_id": 0.85}

        result_go = orchestrator_node(state_go)
        assert result_go["decision"] in ["GO", "HOLD"]
        assert result_go["decision"] == "GO"

        # HOLD scenario
        state_hold = base_orchestrator_state.copy()
        state_hold["field_classifications"] = {"weight_limit": mock_t1_classification}
        state_hold["confidence_scores"] = {"weight_limit": 0.99}

        result_hold = orchestrator_node(state_hold)
        assert result_hold["decision"] in ["GO", "HOLD"]
        assert result_hold["decision"] == "HOLD"


class TestClassificationNode:
    """Test suite for classification_node."""

    def test_classification_node_go_xml_extracts_fields(self):
        """
        Standard GO XML payload extracts correct field names.
        """
        # Arrange
        state: NexBridgeState = {
            "xml_payload": """<record>
                <employee_id>E-12345</employee_id>
                <department>Operations</department>
                <start_date>2024-03-01</start_date>
            </record>""",
            "target_schema": {},
            "field_classifications": {},
            "payload_tier": 4,
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

        # Act
        result = classification_node(state)

        # Assert
        assert "field_classifications" in result
        assert len(result["field_classifications"]) == 3
        assert "employee_id" in result["field_classifications"]
        assert "department" in result["field_classifications"]
        assert "start_date" in result["field_classifications"]

    def test_classification_node_field_classifications_stored(self):
        """
        Field classifications are stored as FieldClassification objects.
        """
        # Arrange
        state: NexBridgeState = {
            "xml_payload": "<record><employee_id>E-12345</employee_id></record>",
            "target_schema": {},
            "field_classifications": {},
            "payload_tier": 4,
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

        # Act
        result = classification_node(state)

        # Assert
        classification = result["field_classifications"]["employee_id"]
        assert hasattr(classification, "tier")
        assert hasattr(classification, "confidence_threshold")
        assert hasattr(classification, "label")

    def test_classification_node_payload_tier_minimum(self):
        """
        Mixed tier XML produces payload_tier as minimum (highest risk).
        """
        # Arrange - registry has employee_id as T3, notes as T4
        state: NexBridgeState = {
            "xml_payload": """<record>
                <employee_id>E-12345</employee_id>
                <notes>Test note</notes>
            </record>""",
            "target_schema": {},
            "field_classifications": {},
            "payload_tier": 4,
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

        # Act
        result = classification_node(state)

        # Assert - minimum tier (highest risk)
        assert result["payload_tier"] <= 4

    def test_classification_node_t1_field_sets_payload_tier_1(self):
        """
        XML with T1 field (weight_limit) sets payload_tier to 1.
        """
        # Arrange - registry has weight_limit as T1
        state: NexBridgeState = {
            "xml_payload": """<record>
                <weight_limit>250</weight_limit>
                <notes>Test</notes>
            </record>""",
            "target_schema": {},
            "field_classifications": {},
            "payload_tier": 4,
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

        # Act
        result = classification_node(state)

        # Assert
        assert result["payload_tier"] == 1

    def test_classification_node_unknown_fields_default_t4(self):
        """
        Unknown field names are classified as T4 (Informational).
        """
        # Arrange - unknown_field_xyz not in registry
        state: NexBridgeState = {
            "xml_payload": "<record><unknown_field_xyz>value</unknown_field_xyz></record>",
            "target_schema": {},
            "field_classifications": {},
            "payload_tier": 4,
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

        # Act
        result = classification_node(state)

        # Assert
        classification = result["field_classifications"]["unknown_field_xyz"]
        assert classification.tier.value == 4


class TestExtractFieldNamesFromXml:
    """Test suite for extract_field_names_from_xml helper."""

    def test_extract_field_names_standard_xml(self):
        """
        Standard XML with 3 fields returns 3 field names.
        """
        # Arrange
        xml = """<record>
            <employee_id>E-12345</employee_id>
            <department>Operations</department>
            <start_date>2024-03-01</start_date>
        </record>"""

        # Act
        result = extract_field_names_from_xml(xml)

        # Assert
        assert len(result) == 3
        assert "employee_id" in result
        assert "department" in result
        assert "start_date" in result

    def test_extract_field_names_nested_xml_only_direct_children(self):
        """
        Nested XML extracts only direct children, not grandchildren.
        """
        # Arrange
        xml = """<record>
            <employee>
                <id>E-12345</id>
                <name>John Doe</name>
            </employee>
            <department>Operations</department>
        </record>"""

        # Act
        result = extract_field_names_from_xml(xml)

        # Assert
        assert len(result) == 2
        assert "employee" in result
        assert "department" in result
        # Grandchildren NOT extracted
        assert "id" not in result
        assert "name" not in result

    def test_extract_field_names_malformed_xml_returns_empty(self):
        """
        Malformed XML returns empty list without crashing.
        """
        # Arrange
        xml = "<record><unclosed>value"

        # Act
        result = extract_field_names_from_xml(xml)

        # Assert
        assert result == []

    def test_extract_field_names_empty_xml_returns_empty(self):
        """
        Empty/minimal XML returns empty list.
        """
        # Arrange
        xml = "<record></record>"

        # Act
        result = extract_field_names_from_xml(xml)

        # Assert
        assert result == []

    def test_extract_field_names_preserves_tag_order(self):
        """
        Field order in XML is preserved in returned list.
        """
        # Arrange
        xml = """<record>
            <field_a>A</field_a>
            <field_b>B</field_b>
            <field_c>C</field_c>
        </record>"""

        # Act
        result = extract_field_names_from_xml(xml)

        # Assert
        assert result == ["field_a", "field_b", "field_c"]


class TestConfidenceThresholds:
    """Test suite for CONFIDENCE_THRESHOLDS constants."""

    @pytest.mark.safety
    def test_confidence_thresholds_t1_is_exactly_1_0(self):
        """
        SAFETY TEST: T1 threshold MUST be exactly 1.0.
        This value must never change. This test must never be skipped.
        """
        assert CONFIDENCE_THRESHOLDS[1] == 1.0

    @pytest.mark.safety
    def test_confidence_thresholds_t2_is_exactly_0_95(self):
        """
        SAFETY TEST: T2 threshold MUST be exactly 0.95.
        This value must never change. This test must never be skipped.
        """
        assert CONFIDENCE_THRESHOLDS[2] == 0.95

    def test_confidence_thresholds_t3_is_0_80(self):
        """
        T3 threshold is 0.80.
        """
        assert CONFIDENCE_THRESHOLDS[3] == 0.80

    def test_confidence_thresholds_t4_is_0_0(self):
        """
        T4 threshold is 0.0 (no threshold check).
        """
        assert CONFIDENCE_THRESHOLDS[4] == 0.0
