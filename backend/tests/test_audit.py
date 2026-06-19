"""
Tests for the AuditAgent (Task 3.09).

Covers:
  - audit_node: all state field reads/writes, append-only guarantee,
    immutability, stdout logging
  - _get_mapping_attr: dict and object attribute access, KeyError on missing
  - _get_tier_value: FieldClassification-style objects and plain dicts
"""

import types
from typing import Any

import pytest
from pydantic import ValidationError

from backend.core.agents.audit import audit_node, _get_mapping_attr, _get_tier_value
from backend.core.models import AuditEntry


# ---------------------------------------------------------------------------
# Helpers — build minimal state dicts for audit_node
# ---------------------------------------------------------------------------

def _base_state(**overrides) -> dict:
    """Return a minimal NexBridgeState-compatible dict for audit_node tests."""
    state: dict[str, Any] = {
        # Required NexBridgeState keys (audit_node uses .get() so defaults apply)
        "raw_payload": "<record/>",
        "source_format": "xml",
        "target_format": "json",
        "target_schema": {},
        "field_classifications": {},
        "payload_tier": 3,
        "parsed_fields": {},
        "root_element": None,
        "interpreter_run_1": {},
        "interpreter_run_2": {},
        "validation_result": {},
        "translated_payload": None,
        "decision": "GO",
        "decision_reason": "All fields passed validation",
        "confidence_scores": {},
        "audit_log": [],
        "processing_start_ms": 0,
    }
    state.update(overrides)
    return state


def _mapping(target_field: str = "target_id",
             transformed_value: Any = "E-123",
             reasoning: str = "Direct match") -> dict:
    """Return a plain-dict field mapping (as produced by the interpreter)."""
    return {
        "target_field": target_field,
        "transformed_value": transformed_value,
        "reasoning": reasoning,
    }


# ---------------------------------------------------------------------------
# TestAuditNode
# ---------------------------------------------------------------------------

class TestAuditNode:
    """Tests for audit_node — the primary entry-point of the AuditAgent."""

    # ------------------------------------------------------------------
    # 1. Single field → single AuditEntry produced
    # ------------------------------------------------------------------
    def test_audit_node_single_field_produces_one_entry(self):
        """audit_node with one field in interpreter_run_1 produces exactly one AuditEntry."""
        state = _base_state(
            interpreter_run_1={"employee_id": _mapping()},
            parsed_fields={"employee_id": "E-12345"},
            confidence_scores={"employee_id": 0.97},
        )
        result = audit_node(state)

        assert len(result["audit_log"]) == 1
        assert isinstance(result["audit_log"][0], AuditEntry)

    # ------------------------------------------------------------------
    # 2. Three fields → three AuditEntry objects
    # ------------------------------------------------------------------
    def test_audit_node_three_fields_produces_three_entries(self):
        """audit_node with three fields in interpreter_run_1 produces three AuditEntry objects."""
        state = _base_state(
            interpreter_run_1={
                "employee_id": _mapping("id", "E-001", "Direct"),
                "department": _mapping("dept_code", "OPS", "Abbreviation"),
                "start_date": _mapping("start_date", "2024-03-01", "Pass-through"),
            },
        )
        result = audit_node(state)

        assert len(result["audit_log"]) == 3
        for entry in result["audit_log"]:
            assert isinstance(entry, AuditEntry)

    # ------------------------------------------------------------------
    # 3. field_name matches source key
    # ------------------------------------------------------------------
    def test_audit_node_entry_field_name_matches_source_key(self):
        """Each AuditEntry.field_name must equal the key from interpreter_run_1."""
        state = _base_state(
            interpreter_run_1={
                "employee_id": _mapping(),
                "department": _mapping("dept_code", "OPS", "Abbreviation"),
            },
        )
        result = audit_node(state)

        field_names = {e.field_name for e in result["audit_log"]}
        assert field_names == {"employee_id", "department"}

    # ------------------------------------------------------------------
    # 4. agent field is always "audit"
    # ------------------------------------------------------------------
    def test_audit_node_entry_agent_is_audit(self):
        """Every AuditEntry produced by audit_node must have agent='audit'."""
        state = _base_state(
            interpreter_run_1={"employee_id": _mapping()},
        )
        result = audit_node(state)

        for entry in result["audit_log"]:
            assert entry.agent == "audit"

    # ------------------------------------------------------------------
    # 5. decision matches state["decision"]
    # ------------------------------------------------------------------
    @pytest.mark.parametrize("decision", ["GO", "HOLD", "ESCALATE"])
    def test_audit_node_entry_decision_matches_state(self, decision: str):
        """AuditEntry.decision must equal the decision value from state."""
        state = _base_state(
            interpreter_run_1={"employee_id": _mapping()},
            decision=decision,
        )
        result = audit_node(state)

        assert result["audit_log"][0].decision == decision

    # ------------------------------------------------------------------
    # 6. original_value sourced from parsed_fields
    # ------------------------------------------------------------------
    def test_audit_node_entry_original_value_from_parsed_fields(self):
        """AuditEntry.original_value must equal parsed_fields[field_name]."""
        state = _base_state(
            interpreter_run_1={"employee_id": _mapping()},
            parsed_fields={"employee_id": "E-99999"},
        )
        result = audit_node(state)

        assert result["audit_log"][0].original_value == "E-99999"

    # ------------------------------------------------------------------
    # 7. transformed_value sourced from mapping
    # ------------------------------------------------------------------
    def test_audit_node_entry_transformed_value_from_mapping(self):
        """AuditEntry.transformed_value must equal the mapping's transformed_value."""
        state = _base_state(
            interpreter_run_1={"employee_id": _mapping(transformed_value="EMP-007")},
        )
        result = audit_node(state)

        assert result["audit_log"][0].transformed_value == "EMP-007"

    # ------------------------------------------------------------------
    # 8. reasoning sourced from mapping
    # ------------------------------------------------------------------
    def test_audit_node_entry_reasoning_from_mapping(self):
        """AuditEntry.reasoning must equal the mapping's reasoning string."""
        state = _base_state(
            interpreter_run_1={"employee_id": _mapping(reasoning="Semantic match on employee ID")},
        )
        result = audit_node(state)

        assert result["audit_log"][0].reasoning == "Semantic match on employee ID"

    # ------------------------------------------------------------------
    # 9. confidence sourced from confidence_scores
    # ------------------------------------------------------------------
    def test_audit_node_entry_confidence_from_confidence_scores(self):
        """AuditEntry.confidence must equal confidence_scores[field_name]."""
        state = _base_state(
            interpreter_run_1={"employee_id": _mapping()},
            confidence_scores={"employee_id": 0.88},
        )
        result = audit_node(state)

        assert result["audit_log"][0].confidence == pytest.approx(0.88)

    # ------------------------------------------------------------------
    # 10. tier sourced from field_classifications
    # ------------------------------------------------------------------
    def test_audit_node_entry_tier_from_field_classifications(self):
        """AuditEntry.tier must be extracted from field_classifications."""
        # Use a SimpleNamespace that mirrors FieldClassification
        tier_obj = types.SimpleNamespace(value=2)
        classification = types.SimpleNamespace(tier=tier_obj)

        state = _base_state(
            interpreter_run_1={"employee_id": _mapping()},
            field_classifications={"employee_id": classification},
        )
        result = audit_node(state)

        assert result["audit_log"][0].tier == 2

    # ------------------------------------------------------------------
    # 11. confidence is None when field not in confidence_scores
    # ------------------------------------------------------------------
    def test_audit_node_entry_confidence_none_when_missing(self):
        """AuditEntry.confidence must be None when field is absent from confidence_scores."""
        state = _base_state(
            interpreter_run_1={"employee_id": _mapping()},
            confidence_scores={},  # no entry for employee_id
        )
        result = audit_node(state)

        assert result["audit_log"][0].confidence is None

    # ------------------------------------------------------------------
    # 12. original_value is "" when field not in parsed_fields
    # ------------------------------------------------------------------
    def test_audit_node_entry_original_value_empty_string_when_missing(self):
        """AuditEntry.original_value must be '' when field is absent from parsed_fields."""
        state = _base_state(
            interpreter_run_1={"employee_id": _mapping()},
            parsed_fields={},  # no entry for employee_id
        )
        result = audit_node(state)

        assert result["audit_log"][0].original_value == ""

    # ------------------------------------------------------------------
    # 13. tier defaults to 4 when field not in field_classifications
    # ------------------------------------------------------------------
    def test_audit_node_entry_tier_defaults_to_4_when_missing(self):
        """AuditEntry.tier must default to 4 (Informational) when field has no classification."""
        state = _base_state(
            interpreter_run_1={"unknown_field": _mapping()},
            field_classifications={},  # no entry for unknown_field
        )
        result = audit_node(state)

        assert result["audit_log"][0].tier == 4

    # ------------------------------------------------------------------
    # 14. Existing audit_log entries are preserved (append-only)
    # ------------------------------------------------------------------
    def test_audit_node_preserves_existing_audit_log(self):
        """audit_node must append to audit_log — never overwrite existing entries."""
        prior_entry = AuditEntry(
            timestamp="2024-01-01T00:00:00+00:00",
            field_name="prior_field",
            tier=3,
            original_value="old_val",
            transformed_value="new_val",
            confidence=0.99,
            agent="audit",
            decision="GO",
            reasoning="Prior run",
        )
        state = _base_state(
            interpreter_run_1={"employee_id": _mapping()},
            audit_log=[prior_entry],
        )
        result = audit_node(state)

        assert len(result["audit_log"]) == 2
        assert result["audit_log"][0] is prior_entry

    # ------------------------------------------------------------------
    # 15. Empty interpreter_run_1 — no new entries, existing log preserved
    # ------------------------------------------------------------------
    def test_audit_node_empty_run1_preserves_existing_log(self):
        """audit_node with empty interpreter_run_1 must not add entries but must keep existing."""
        prior_entry = AuditEntry(
            timestamp="2024-01-01T00:00:00+00:00",
            field_name="prior_field",
            tier=3,
            original_value="old_val",
            transformed_value="new_val",
            confidence=None,
            agent="audit",
            decision="HOLD",
            reasoning="Prior run",
        )
        state = _base_state(
            interpreter_run_1={},
            audit_log=[prior_entry],
        )
        result = audit_node(state)

        assert len(result["audit_log"]) == 1
        assert result["audit_log"][0] is prior_entry

    # ------------------------------------------------------------------
    # 16. AuditEntry is immutable — setting an attribute raises an exception
    # ------------------------------------------------------------------
    def test_audit_entry_is_immutable(self):
        """AuditEntry must be frozen — attribute assignment must raise TypeError or ValidationError."""
        entry = AuditEntry(
            timestamp="2024-01-01T00:00:00+00:00",
            field_name="employee_id",
            tier=3,
            original_value="E-123",
            transformed_value="EMP-123",
            confidence=0.95,
            agent="audit",
            decision="GO",
            reasoning="Direct match",
        )
        with pytest.raises((TypeError, ValidationError)):
            entry.field_name = "tampered"  # type: ignore[misc]

    # ------------------------------------------------------------------
    # 17. timestamp is a non-empty string
    # ------------------------------------------------------------------
    def test_audit_node_entry_timestamp_is_nonempty_string(self):
        """AuditEntry.timestamp must be a non-empty string (ISO 8601 expected)."""
        state = _base_state(
            interpreter_run_1={"employee_id": _mapping()},
        )
        result = audit_node(state)

        ts = result["audit_log"][0].timestamp
        assert isinstance(ts, str)
        assert len(ts) > 0

    # ------------------------------------------------------------------
    # 18. audit_log in returned state is a new list (state immutability)
    # ------------------------------------------------------------------
    def test_audit_node_returns_new_list_not_original(self):
        """audit_node must return a new audit_log list, not mutate the original."""
        original_log: list = []
        state = _base_state(
            interpreter_run_1={"employee_id": _mapping()},
            audit_log=original_log,
        )
        result = audit_node(state)

        # The returned log is a different object from the input list
        assert result["audit_log"] is not original_log
        # The original list must be unchanged
        assert len(original_log) == 0

    # ------------------------------------------------------------------
    # 19. capsys: logs "[AUDIT] Written 2 audit entries decision=GO"
    # ------------------------------------------------------------------
    def test_audit_node_logs_written_count_for_two_entries(self, capsys):
        """audit_node must print '[AUDIT] Written 2 audit entries decision=GO'."""
        state = _base_state(
            interpreter_run_1={
                "employee_id": _mapping("id", "E-001", "Direct"),
                "department": _mapping("dept_code", "OPS", "Abbreviation"),
            },
            decision="GO",
        )
        audit_node(state)

        captured = capsys.readouterr()
        assert "[AUDIT] Written 2 audit entries decision=GO" in captured.out

    # ------------------------------------------------------------------
    # 20. capsys: logs "[AUDIT] Written 0 audit entries decision=HOLD" for empty run_1
    # ------------------------------------------------------------------
    def test_audit_node_logs_zero_entries_for_empty_run1(self, capsys):
        """audit_node must print '[AUDIT] Written 0 audit entries decision=HOLD' when run_1 is empty."""
        state = _base_state(
            interpreter_run_1={},
            decision="HOLD",
        )
        audit_node(state)

        captured = capsys.readouterr()
        assert "[AUDIT] Written 0 audit entries decision=HOLD" in captured.out


# ---------------------------------------------------------------------------
# TestGetMappingAttr
# ---------------------------------------------------------------------------

class TestGetMappingAttr:
    """Tests for _get_mapping_attr — reads an attribute from a dict or object."""

    # ------------------------------------------------------------------
    # 21. Returns correct value from plain dict
    # ------------------------------------------------------------------
    def test_get_mapping_attr_returns_value_from_dict(self):
        """_get_mapping_attr must return the correct value when mapping is a plain dict."""
        mapping = {"target_field": "id", "transformed_value": "E-001", "reasoning": "x"}
        assert _get_mapping_attr(mapping, "target_field") == "id"
        assert _get_mapping_attr(mapping, "transformed_value") == "E-001"
        assert _get_mapping_attr(mapping, "reasoning") == "x"

    # ------------------------------------------------------------------
    # 22. Returns correct value from object with attribute (SimpleNamespace)
    # ------------------------------------------------------------------
    def test_get_mapping_attr_returns_value_from_object(self):
        """_get_mapping_attr must return the correct value when mapping is an object."""
        mapping = types.SimpleNamespace(
            target_field="dept_code",
            transformed_value="OPS",
            reasoning="Abbreviation mapping",
        )
        assert _get_mapping_attr(mapping, "target_field") == "dept_code"
        assert _get_mapping_attr(mapping, "transformed_value") == "OPS"
        assert _get_mapping_attr(mapping, "reasoning") == "Abbreviation mapping"

    # ------------------------------------------------------------------
    # 23. Raises KeyError for missing dict key
    # ------------------------------------------------------------------
    def test_get_mapping_attr_raises_keyerror_for_missing_dict_key(self):
        """_get_mapping_attr must raise KeyError when attr is absent from a plain dict."""
        mapping = {"target_field": "id"}
        with pytest.raises(KeyError):
            _get_mapping_attr(mapping, "nonexistent_attr")


# ---------------------------------------------------------------------------
# TestGetTierValue
# ---------------------------------------------------------------------------

class TestGetTierValue:
    """Tests for _get_tier_value — extracts integer tier from various classification types."""

    # ------------------------------------------------------------------
    # 24. Returns tier.value from FieldClassification-like object
    # ------------------------------------------------------------------
    def test_get_tier_value_from_classification_object(self):
        """_get_tier_value must call .tier.value when classification is an object with a tier attr."""
        tier_obj = types.SimpleNamespace(value=3)
        classification = types.SimpleNamespace(tier=tier_obj)

        assert _get_tier_value(classification) == 3

    # ------------------------------------------------------------------
    # 25. Returns int from plain dict {"tier": 2}
    # ------------------------------------------------------------------
    def test_get_tier_value_from_dict_tier_2(self):
        """_get_tier_value must extract the integer tier from a plain dict."""
        classification = {"tier": 2}
        result = _get_tier_value(classification)
        assert result == 2
        assert isinstance(result, int)

    # ------------------------------------------------------------------
    # 26. Returns int(1) from dict {"tier": 1}
    # ------------------------------------------------------------------
    def test_get_tier_value_from_dict_tier_1(self):
        """_get_tier_value must return int(1) for a T1 plain-dict classification."""
        classification = {"tier": 1}
        result = _get_tier_value(classification)
        assert result == 1
        assert isinstance(result, int)
