"""
audit — Immutable audit log writer for the NexBridge pipeline.

Writes one AuditEntry per field after the orchestrator decision.
Entries are frozen Pydantic models — append-only, never modified.

Part of the NexBridge transformation pipeline.
See docs/SOLUTION_AGENTS.md for full specification.
"""

from datetime import datetime, timezone
from typing import Any

from backend.core.state import NexBridgeState
from backend.core.models import AuditEntry


def _get_mapping_attr(mapping: Any, attr: str) -> Any:
    """Safely read attribute from Pydantic FieldMapping or plain dict."""
    if hasattr(mapping, attr):
        return getattr(mapping, attr)
    return mapping[attr]


def _get_tier_value(classification: Any) -> int:
    """Extract integer tier value from FieldClassification object or dict."""
    if hasattr(classification, "tier"):
        tier = classification.tier
        return tier.value if hasattr(tier, "value") else int(tier)
    return int(classification["tier"])


def audit_node(state: NexBridgeState) -> NexBridgeState:
    """
    Writes an immutable AuditEntry for each field in interpreter_run_1.

    Reads:  state["interpreter_run_1"]
            state["field_classifications"]
            state["confidence_scores"]
            state["parsed_fields"]
            state["decision"]
            state["decision_reason"]
    Writes: state["audit_log"]
    """
    interpreter_run_1 = state.get("interpreter_run_1", {})
    field_classifications = state.get("field_classifications", {})
    confidence_scores = state.get("confidence_scores", {})
    parsed_fields = state.get("parsed_fields", {})
    decision = state.get("decision", "")
    decision_reason = state.get("decision_reason", "")

    existing_log = list(state.get("audit_log", []))
    new_entries = []

    timestamp = datetime.now(timezone.utc).isoformat()

    for field_name, mapping in interpreter_run_1.items():
        transformed_value = _get_mapping_attr(mapping, "transformed_value")
        reasoning = _get_mapping_attr(mapping, "reasoning")

        original_value = str(parsed_fields.get(field_name, ""))

        classification = field_classifications.get(field_name)
        tier = _get_tier_value(classification) if classification else 4

        confidence = confidence_scores.get(field_name)

        entry = AuditEntry(
            timestamp=timestamp,
            field_name=field_name,
            tier=tier,
            original_value=original_value,
            transformed_value=transformed_value,
            confidence=confidence,
            agent="audit",
            decision=decision,
            reasoning=reasoning,
        )
        new_entries.append(entry)

    n = len(new_entries)
    print(f"[AUDIT] Written {n} audit entries decision={decision}")

    return {
        **state,
        "audit_log": existing_log + new_entries,
    }
