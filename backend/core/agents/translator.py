"""
NexBridge Translator Agent

Deterministic JSON builder. Constructs target JSON payload from
interpreter field mappings with type conversion. No LLM involved.

Part of the NexBridge transformation pipeline.
See docs/SOLUTION_AGENTS.md for full specification.
"""

from typing import Any

from backend.core.state import NexBridgeState
from backend.core.exceptions import TranslationError


def translator_node(state: NexBridgeState) -> NexBridgeState:
    """
    Builds target JSON payload from interpreter field mappings.
    Pure deterministic logic — no LLM involved.

    Reads:
        - state["decision"]: Check if HOLD (early exit)
        - state["interpreter_run_1"]: Field mappings from interpreter
        - state["target_schema"]: Target field types for conversion

    Writes:
        - state["translated_payload"]: Built JSON output (or None if HOLD)

    Args:
        state: Current NexBridgeState from LangGraph pipeline

    Returns:
        Updated state with translated_payload populated

    Raises:
        TranslationError: If critical build failure occurs
    """

    # Early exit if orchestrator already decided HOLD
    if state.get("decision") == "HOLD":
        print("[TRANSLATOR] Skipping — payload is HOLD")
        return {
            **state,
            "translated_payload": None,
        }

    interpreter_run_1 = state["interpreter_run_1"]
    target_schema = state["target_schema"]
    output = {}

    # Build target JSON from interpreter mappings
    for field_name, mapping in interpreter_run_1.items():
        try:
            # Access FieldMapping attributes
            target_field = mapping.target_field
            transformed_value = mapping.transformed_value

            # Get target type from schema
            target_type = target_schema.get(target_field, "string")

            # Convert value to target type
            converted_value = _convert_value_to_type(
                transformed_value,
                target_type,
                field_name
            )

            output[target_field] = converted_value

            # Log each field mapping
            print(
                f"[TRANSLATOR] field={field_name} → {target_field} "
                f"= {converted_value}"
            )

        except Exception as e:
            raise TranslationError(
                field_name=field_name,
                reason=f"Failed to build target field '{target_field}': {str(e)}"
            )

    print(f"[TRANSLATOR] Built payload with {len(output)} fields")

    return {
        **state,
        "translated_payload": output,
    }


def _convert_value_to_type(
    value: Any,
    target_type: str,
    field_name: str
) -> Any:
    """
    Convert value to target schema type.

    Args:
        value: Raw value from mapping
        target_type: Target type from schema ("number", "integer", "string", etc.)
        field_name: Source field name for error context

    Returns:
        Converted value (gracefully falls back to string on conversion failure)
    """
    if target_type in ("number", "float"):
        try:
            return float(value)
        except (ValueError, TypeError):
            # Keep as string if conversion fails
            return str(value)

    elif target_type in ("integer", "int"):
        try:
            return int(value)
        except (ValueError, TypeError):
            # Keep as string if conversion fails
            return str(value)

    else:
        # All other types: string, boolean, etc. — keep as-is
        return value
