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
from backend.core.format_registry import get_translator


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
    target_format = state.get("target_format", "json")

    translator = get_translator(target_format)

    if target_format == "xml":
        result = translator.build(
            field_mappings=interpreter_run_1,
            target_schema=target_schema,
            root_element=state.get("root_element", "payload"),
        )
    else:
        result = translator.build(
            field_mappings=interpreter_run_1,
            target_schema=target_schema,
        )

    print(f"[TRANSLATOR] Built payload with {len(interpreter_run_1)} fields")

    return {
        **state,
        "translated_payload": result,
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
