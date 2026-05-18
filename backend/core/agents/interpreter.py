"""
NexBridge Interpreter Agent

The AI brain of the transformation pipeline. Uses an LLM to semantically
map XML fields to target JSON schema fields with confidence scoring.

Part of the NexBridge transformation pipeline.
See docs/SOLUTION_AGENTS.md for full specification.
"""

import os
import xml.etree.ElementTree as ET
from typing import Any

from backend.core.state import NexBridgeState
from backend.core.models import FieldMapping, Tier
from backend.core.llm import get_llm
from backend.core.exceptions import LLMError


def _run_interpretation(
    xml_payload: str,
    target_schema: dict,
    field_classifications: dict,
    provider_name: str
) -> dict[str, FieldMapping]:
    """
    Private helper that runs LLM-powered semantic field mapping.
    Returns FieldMapping objects (not dicts).

    Args:
        xml_payload: Raw XML string
        target_schema: Flat dict of target field names
        field_classifications: Registry classification results
        provider_name: LLM provider name for error handling

    Returns:
        Dict mapping field_name -> FieldMapping object (not dict)

    Raises:
        LLMError: If LLM call fails or returns invalid output
        ValueError: If confidence score is outside [0.0, 1.0] range
    """
    # Build LLM with structured output
    llm = get_llm()
    structured_llm = llm.with_structured_output(FieldMapping)

    mappings = {}

    # Process each classified field
    for field_name, classification in field_classifications.items():
        # Extract field value from XML
        field_value = _extract_field_value_from_xml(xml_payload, field_name)

        # Handle both dict and object access
        # (tests may pass dicts, production passes FieldClassification objects)
        if isinstance(classification, dict):
            tier_enum = classification["tier"]
            tier_value = tier_enum.value if hasattr(tier_enum, "value") else tier_enum
            tier_label = classification["label"]
        else:
            tier_value = classification.tier.value
            tier_label = classification.label

        # Build LLM prompt
        prompt = _build_llm_prompt(
            field_name=field_name,
            field_value=field_value,
            tier=tier_value,
            tier_label=tier_label,
            target_schema=target_schema
        )

        # Call LLM with structured output
        try:
            result: FieldMapping = structured_llm.invoke(prompt)
        except Exception as e:
            raise LLMError(
                provider=provider_name,
                reason=str(e)
            ) from e

        # Validate confidence range
        if not (0.0 <= result.confidence <= 1.0):
            raise ValueError(
                f"Invalid confidence {result.confidence} for field '{field_name}'. "
                f"Must be in range [0.0, 1.0]"
            )

        # Store FieldMapping object (not dict)
        mappings[field_name] = result

    return mappings


def interpreter_node(state: NexBridgeState) -> NexBridgeState:
    """
    LangGraph node that maps source XML fields to target JSON schema
    using LLM-powered semantic field mapping (Run 1).

    Reads:
        - state["xml_payload"]: Raw XML string
        - state["target_schema"]: Flat dict of target field names
        - state["field_classifications"]: Registry classification results

    Writes:
        - state["interpreter_run_1"]: Dict mapping field_name -> FieldMapping dict
        - state["confidence_scores"]: Dict mapping field_name -> confidence float

    Args:
        state: Current NexBridgeState from LangGraph pipeline

    Returns:
        Updated state with interpreter_run_1 and confidence_scores populated

    Raises:
        LLMError: If LLM call fails or returns invalid output
        ValueError: If confidence score is outside [0.0, 1.0] range
    """

    xml_payload = state["xml_payload"]
    target_schema = state["target_schema"]
    field_classifications = state["field_classifications"]

    # Get provider name for error handling
    provider_name = os.getenv("LLM_PROVIDER", "anthropic")

    # Run interpretation
    mappings = _run_interpretation(
        xml_payload=xml_payload,
        target_schema=target_schema,
        field_classifications=field_classifications,
        provider_name=provider_name
    )

    # Extract confidence_scores using attribute access (not dict key access)
    confidence_scores = {
        field_name: mapping.confidence
        for field_name, mapping in mappings.items()
    }

    # Convert FieldMapping objects to dicts for state storage
    interpreter_run_1 = {
        field_name: mapping.model_dump()
        for field_name, mapping in mappings.items()
    }

    # Log mappings
    for field_name, mapping in mappings.items():
        print(
            f"[INTERPRETER RUN 1] field={field_name} → {mapping.target_field} "
            f"conf={mapping.confidence:.2f}"
        )

    # Return updated state
    return {
        **state,
        "interpreter_run_1": interpreter_run_1,
        "confidence_scores": confidence_scores,
    }


def interpreter_run_2_node(state: NexBridgeState) -> NexBridgeState:
    """
    LangGraph node for T1 dual-agent verification (Run 2).
    Completely independent from Run 1 — never reads interpreter_run_1.

    Reads:
        - state["xml_payload"]: Raw XML string
        - state["target_schema"]: Flat dict of target field names
        - state["field_classifications"]: Registry classification results

    Writes:
        - state["interpreter_run_2"]: Dict mapping field_name -> FieldMapping dict

    Args:
        state: Current NexBridgeState from LangGraph pipeline

    Returns:
        Updated state with interpreter_run_2 populated

    Raises:
        LLMError: If LLM call fails or returns invalid output
        ValueError: If confidence score is outside [0.0, 1.0] range
    """

    xml_payload = state["xml_payload"]
    target_schema = state["target_schema"]
    field_classifications = state["field_classifications"]

    # Get provider name for error handling
    provider_name = os.getenv("LLM_PROVIDER", "anthropic")

    # Run interpretation (completely independent)
    mappings = _run_interpretation(
        xml_payload=xml_payload,
        target_schema=target_schema,
        field_classifications=field_classifications,
        provider_name=provider_name
    )

    # Convert FieldMapping objects to dicts for state storage
    interpreter_run_2 = {
        field_name: mapping.model_dump()
        for field_name, mapping in mappings.items()
    }

    # Log mappings
    for field_name, mapping in mappings.items():
        print(
            f"[INTERPRETER RUN 2] field={field_name} → {mapping.target_field} "
            f"conf={mapping.confidence:.2f}"
        )

    # Return updated state
    return {
        **state,
        "interpreter_run_2": interpreter_run_2,
    }


def _extract_field_value_from_xml(xml_payload: str, field_name: str) -> str:
    """
    Extract the value of a field from XML payload using ElementTree.

    Args:
        xml_payload: Raw XML string
        field_name: Name of the field to extract

    Returns:
        Field value as string, or empty string if not found

    Raises:
        None — returns empty string on parse errors or missing fields
    """
    try:
        root = ET.fromstring(xml_payload)
        element = root.find(f".//{field_name}")
        if element is not None and element.text is not None:
            return element.text.strip()
        return ""
    except ET.ParseError:
        # Malformed XML — return empty string
        return ""


def _build_target_fields_list(target_schema: dict) -> str:
    """
    Build a formatted string listing all target schema fields.

    Args:
        target_schema: Flat dict of target field names and types

    Returns:
        Formatted string with one field per line: "- field_name (type)"
    """
    lines = []
    for field_name, field_type in target_schema.items():
        lines.append(f"- {field_name} ({field_type})")
    return "\n".join(lines)


def _build_llm_prompt(
    field_name: str,
    field_value: str,
    tier: int,
    tier_label: str,
    target_schema: dict
) -> str:
    """
    Build the LLM prompt for semantic field mapping.

    Args:
        field_name: Source field name from XML
        field_value: Source field value from XML
        tier: Classification tier (1-4)
        tier_label: Human-readable tier label
        target_schema: Flat dict of target field names and types

    Returns:
        Complete prompt string for LLM
    """
    target_fields_list = _build_target_fields_list(target_schema)

    return f"""You are a semantic field mapper for NexBridge.

SOURCE FIELD:
- Name: {field_name}
- Value: {field_value}
- Classification Tier: T{tier} ({tier_label})

AVAILABLE TARGET SCHEMA FIELDS:
{target_fields_list}

Your task is to:
1. Identify which target field best matches the semantic meaning of the source field
2. Transform the value to the target format if needed
3. Assign a confidence score using these rules:

CONFIDENCE SCORING RULES:
- 0.95-1.0: Perfect semantic match (e.g., "customer_id" → "customerId")
- 0.80-0.95: Good match with minor differences (e.g., "dept_code" → "departmentCode")
- 0.60-0.80: Uncertain match (field names differ but meaning might align)
- Below 0.60: Poor match (semantic mismatch or ambiguous)

Respond with:
- field_name: The original source field name
- target_field: The best matching target field name
- transformed_value: The value in target format
- confidence: Confidence score (0.0 to 1.0)
- reasoning: Brief explanation for your choice
- tier: {tier}
"""
