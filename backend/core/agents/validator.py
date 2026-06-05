"""
NexBridge Validator Agent

Advisory anomaly detector. Checks field mappings against target schema
and flags issues. NEVER blocks pipeline — advisory only.

Part of the NexBridge transformation pipeline.
See docs/SOLUTION_AGENTS.md for full specification.
"""

from typing import Optional

from backend.core.state import NexBridgeState
from backend.core.constants import CONFIDENCE_THRESHOLDS
from backend.core.models import FieldMapping, FieldClassification


def _get_mapping_attr(mapping, attr: str):
    """
    Safely access mapping attribute from Pydantic object or dict.

    LangGraph serializes Pydantic models to dicts between nodes,
    so we must handle both forms.

    Args:
        mapping: Either FieldMapping Pydantic object or dict
        attr: Attribute name to access

    Returns:
        Value of the attribute/key
    """
    if hasattr(mapping, attr):
        return getattr(mapping, attr)
    return mapping[attr]


def validator_node(state: NexBridgeState) -> NexBridgeState:
    """
    Advisory anomaly detector. Checks field mappings against target schema
    and flags issues. NEVER blocks pipeline — advisory only.

    Reads:
        - state["decision"]: Check if HOLD (early exit)
        - state["interpreter_run_1"]: Field mappings to validate
        - state["target_schema"]: Schema to validate against
        - state["confidence_scores"]: Confidence per field
        - state["field_classifications"]: Tier per field

    Writes:
        - state["validation_result"]: Anomaly report with flags

    Args:
        state: Current NexBridgeState from LangGraph pipeline

    Returns:
        Updated state with validation_result populated

    Raises:
        Never raises — all errors converted to anomaly flags
    """

    # Early exit if orchestrator already decided HOLD
    if state.get("decision") == "HOLD":
        print("[VALIDATOR] Skipping — payload is HOLD")
        return state

    try:
        interpreter_run_1 = state["interpreter_run_1"]
        target_schema = state["target_schema"]
        confidence_scores = state["confidence_scores"]
        field_classifications = state["field_classifications"]

        anomalies = []
        checked_fields = 0

        # Validate each field mapping
        for field_name, mapping in interpreter_run_1.items():
            checked_fields += 1

            # Get tier for this field (from FieldClassification Pydantic object)
            classification = field_classifications.get(field_name)
            tier = classification.tier if classification else 4

            # Run all three checks
            checks = [
                _check_target_field_exists(field_name, mapping, target_schema, tier),
                _check_confidence_threshold(
                    field_name,
                    confidence_scores.get(field_name, 0.0),
                    tier
                ),
                _check_type_mismatch(field_name, mapping, target_schema, tier),
            ]

            # Collect non-None anomalies
            for anomaly in checks:
                if anomaly is not None:
                    anomalies.append(anomaly)
                    print(
                        f"[VALIDATOR] ANOMALY field={anomaly['field_name']} "
                        f"check={anomaly['check']} severity={anomaly['severity']}"
                    )

        print(
            f"[VALIDATOR] Checked {checked_fields} fields, "
            f"found {len(anomalies)} anomalies"
        )

        validation_result = {
            "anomalies": anomalies,
            "anomaly_count": len(anomalies),
            "checked_fields": checked_fields,
        }

        return {
            **state,
            "validation_result": validation_result,
        }

    except Exception as e:
        # Convert ANY error to anomaly flag — never block pipeline
        print(f"[VALIDATOR] ERROR during validation: {str(e)}")
        validation_result = {
            "anomalies": [{
                "field_name": "SYSTEM",
                "check": "validator_error",
                "severity": "HIGH",
                "detail": f"Validator error: {str(e)}"
            }],
            "anomaly_count": 1,
            "checked_fields": 0,
        }
        return {
            **state,
            "validation_result": validation_result,
        }


def _check_target_field_exists(
    field_name: str,
    mapping: FieldMapping,
    target_schema: dict,
    tier: int
) -> Optional[dict]:
    """
    Check if target_field exists in target_schema.

    Args:
        field_name: Source field name
        mapping: FieldMapping object from interpreter
        target_schema: Target schema dict
        tier: Classification tier (1-4)

    Returns:
        Anomaly dict if check fails, None otherwise
    """
    target_field = _get_mapping_attr(mapping, "target_field")
    if target_field not in target_schema:
        return {
            "field_name": field_name,
            "check": "target_field_not_in_schema",
            "severity": _get_severity(tier),
            "detail": (
                f"Target field '{target_field}' "
                f"not found in target schema"
            )
        }
    return None


def _check_confidence_threshold(
    field_name: str,
    confidence: float,
    tier: int
) -> Optional[dict]:
    """
    Check if confidence meets tier threshold.

    Args:
        field_name: Source field name
        confidence: Confidence score (0.0 to 1.0)
        tier: Classification tier (1-4)

    Returns:
        Anomaly dict if check fails, None otherwise
    """
    threshold = CONFIDENCE_THRESHOLDS[tier]
    if confidence < threshold:
        return {
            "field_name": field_name,
            "check": "confidence_below_threshold",
            "severity": _get_severity(tier),
            "detail": (
                f"Confidence {confidence:.2f} below "
                f"T{tier} threshold {threshold}"
            )
        }
    return None


def _check_type_mismatch(
    field_name: str,
    mapping: FieldMapping,
    target_schema: dict,
    tier: int
) -> Optional[dict]:
    """
    Check if value can be converted to target type.

    Args:
        field_name: Source field name
        mapping: FieldMapping object from interpreter
        target_schema: Target schema dict
        tier: Classification tier (1-4)

    Returns:
        Anomaly dict if check fails, None otherwise
    """
    target_field = _get_mapping_attr(mapping, "target_field")
    transformed_value = _get_mapping_attr(mapping, "transformed_value")
    target_type = target_schema.get(target_field)

    if target_type in ("number", "float", "integer", "int"):
        try:
            if target_type in ("number", "float"):
                float(transformed_value)
            else:
                int(transformed_value)
        except (ValueError, TypeError):
            return {
                "field_name": field_name,
                "check": "type_mismatch",
                "severity": _get_severity(tier),
                "detail": (
                    f"Value '{transformed_value}' cannot be "
                    f"converted to type '{target_type}'"
                )
            }
    return None


def _get_severity(tier: int) -> str:
    """
    Map tier to severity level.

    Args:
        tier: Classification tier (1-4)

    Returns:
        Severity level: "HIGH", "MEDIUM", or "LOW"
    """
    if tier == 1:
        return "HIGH"
    elif tier == 2:
        return "MEDIUM"
    else:  # T3 or T4
        return "LOW"
