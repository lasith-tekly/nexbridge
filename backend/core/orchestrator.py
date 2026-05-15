"""
NexBridge LangGraph Orchestrator

Builds the transformation pipeline graph and implements the orchestrator
decision node. Routes payloads through: classification → interpreter →
validator → translator → orchestrator → END.

Part of the NexBridge transformation pipeline.
See docs/SOLUTION_AGENTS.md for full specification.
"""

import xml.etree.ElementTree as ET
from langgraph.graph import StateGraph, END

from backend.core.state import NexBridgeState
from backend.core.constants import CONFIDENCE_THRESHOLDS
from backend.core.classification.registry import ClassificationRegistry
from backend.core.agents.interpreter import interpreter_node
from backend.core.agents.validator import validator_node
from backend.core.agents.translator import translator_node


def orchestrator_node(state: NexBridgeState) -> NexBridgeState:
    """
    Makes GO/HOLD decision based on confidence thresholds per tier.
    T1/T2 below threshold → HOLD immediately.
    T3/T4 below threshold → log warning, continue.

    Reads:
        - state["confidence_scores"]: Confidence per field
        - state["field_classifications"]: Tier per field
        - state["payload_tier"]: Overall payload tier

    Writes:
        - state["decision"]: "GO" or "HOLD"
        - state["decision_reason"]: Explanation
        - state["translated_payload"]: Set to None if HOLD

    Args:
        state: Current NexBridgeState from LangGraph pipeline

    Returns:
        Updated state with decision and decision_reason
    """

    confidence_scores = state["confidence_scores"]
    field_classifications = state["field_classifications"]
    payload_tier = state["payload_tier"]

    # Check each field against its tier threshold
    for field_name, confidence in confidence_scores.items():
        # Get tier from FieldClassification Pydantic object
        classification = field_classifications.get(field_name)
        if not classification:
            continue  # Skip if no classification

        tier = classification.tier.value  # Extract int from Tier enum
        threshold = CONFIDENCE_THRESHOLDS[tier]

        # Log check
        print(
            f"[ORCHESTRATOR] field={field_name} tier=T{tier} "
            f"conf={confidence:.2f} threshold={threshold}"
        )

        # T1 HOLD check
        if tier == 1 and confidence < CONFIDENCE_THRESHOLDS[1]:
            print(
                f"[ORCHESTRATOR] decision=HOLD "
                f"payload_tier=T{payload_tier}"
            )
            return {
                **state,
                "decision": "HOLD",
                "decision_reason": (
                    f"T1 field '{field_name}' confidence {confidence:.2f} "
                    f"below threshold {CONFIDENCE_THRESHOLDS[1]}"
                ),
                "translated_payload": None,
            }

        # T2 HOLD check
        if tier == 2 and confidence < CONFIDENCE_THRESHOLDS[2]:
            print(
                f"[ORCHESTRATOR] decision=HOLD "
                f"payload_tier=T{payload_tier}"
            )
            return {
                **state,
                "decision": "HOLD",
                "decision_reason": (
                    f"T2 field '{field_name}' confidence {confidence:.2f} "
                    f"below threshold {CONFIDENCE_THRESHOLDS[2]}"
                ),
                "translated_payload": None,
            }

        # T3/T4 warning only (do not HOLD)
        if tier in (3, 4) and confidence < threshold:
            print(
                f"[ORCHESTRATOR] WARNING field={field_name} "
                f"tier=T{tier} conf={confidence:.2f} below "
                f"threshold {threshold} (continuing)"
            )

    # All checks passed → GO
    print(f"[ORCHESTRATOR] decision=GO payload_tier=T{payload_tier}")
    return {
        **state,
        "decision": "GO",
        "decision_reason": "All fields passed confidence checks",
    }


def classification_node(state: NexBridgeState) -> NexBridgeState:
    """
    Classifies all fields in XML payload using ClassificationRegistry.

    Reads:
        - state["xml_payload"]: Raw XML string

    Writes:
        - state["field_classifications"]: Dict of FieldClassification objects
        - state["payload_tier"]: Highest risk tier (minimum tier number)

    Args:
        state: Current NexBridgeState from LangGraph pipeline

    Returns:
        Updated state with field_classifications and payload_tier
    """
    xml_payload = state["xml_payload"]

    # Extract field names from XML
    field_names = extract_field_names_from_xml(xml_payload)

    # Initialize registry
    registry = ClassificationRegistry()

    # Classify each field
    classifications = {}
    for field_name in field_names:
        classifications[field_name] = registry.classify(field_name)

    # Get payload tier (minimum tier = highest risk)
    payload_tier = registry.get_payload_tier(field_names)

    print(
        f"[CLASSIFICATION] {len(field_names)} fields, "
        f"payload_tier=T{payload_tier}"
    )

    return {
        **state,
        "field_classifications": classifications,
        "payload_tier": payload_tier,
    }


def extract_field_names_from_xml(xml: str) -> list[str]:
    """
    Extract all child element tag names from XML root.

    Args:
        xml: XML string

    Returns:
        List of field names (tag names)
    """
    try:
        root = ET.fromstring(xml)
        # Get all child element tag names
        field_names = [child.tag for child in root]
        return field_names
    except ET.ParseError as e:
        print(f"[CLASSIFICATION] XML parse error: {str(e)}")
        return []


def build_graph():
    """
    Build the NexBridge transformation pipeline graph.

    Flow: classification → interpreter → validator →
          translator → orchestrator → END

    Returns:
        Compiled LangGraph state graph ready for execution
    """
    # Initialize graph with state type
    graph = StateGraph(NexBridgeState)

    # Register all nodes
    graph.add_node("classification", classification_node)
    graph.add_node("interpreter", interpreter_node)
    graph.add_node("validator", validator_node)
    graph.add_node("translator", translator_node)
    graph.add_node("orchestrator", orchestrator_node)

    # Set entry point
    graph.set_entry_point("classification")

    # Add edges (linear flow for T2/T3 basic pipeline)
    graph.add_edge("classification", "interpreter")
    graph.add_edge("interpreter", "validator")
    graph.add_edge("validator", "translator")
    graph.add_edge("translator", "orchestrator")
    graph.add_edge("orchestrator", END)

    # Compile and return
    return graph.compile()
