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
from backend.core.agents.interpreter import interpreter_node, interpreter_run_2_node
from backend.core.agents.validator import validator_node
from backend.core.agents.translator import translator_node


def orchestrator_node(state: NexBridgeState) -> NexBridgeState:
    """
    Makes GO/HOLD decision based on confidence thresholds per tier.
    T1/T2 below threshold → HOLD immediately.
    T3/T4 below threshold → log warning, continue.

    For T1 payloads, also checks divergence between interpreter Run 1 and Run 2.
    If target_field mappings differ, HOLD immediately.

    Reads:
        - state["confidence_scores"]: Confidence per field
        - state["field_classifications"]: Tier per field
        - state["payload_tier"]: Overall payload tier
        - state["interpreter_run_1"]: Run 1 field mappings (T1 only)
        - state["interpreter_run_2"]: Run 2 field mappings (T1 only)

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

    # T1 Divergence Check — dual-agent verification
    if payload_tier == 1:
        run_1 = state["interpreter_run_1"]
        run_2 = state.get("interpreter_run_2", {})

        print(f"[ORCHESTRATOR] T1 divergence check: comparing {len(run_1)} fields")

        for field_name, mapping_dict in run_1.items():
            if field_name in run_2:
                run1_target = mapping_dict["target_field"]
                run2_target = run_2[field_name]["target_field"]

                if run1_target != run2_target:
                    print(
                        f"[ORCHESTRATOR] T1 DIVERGENCE DETECTED "
                        f"field={field_name} Run1={run1_target} Run2={run2_target}"
                    )
                    return {
                        **state,
                        "decision": "HOLD",
                        "decision_reason": (
                            f"T1 field '{field_name}' diverged between interpreter runs: "
                            f"Run1={run1_target}, Run2={run2_target}"
                        ),
                        "translated_payload": None,
                    }

        print("[ORCHESTRATOR] T1 divergence check passed — both runs agree")

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
        - state["raw_payload"]: Raw input payload (XML or JSON string)

    Writes:
        - state["field_classifications"]: Dict of FieldClassification objects
        - state["payload_tier"]: Highest risk tier (minimum tier number)

    Args:
        state: Current NexBridgeState from LangGraph pipeline

    Returns:
        Updated state with field_classifications and payload_tier
    """
    raw_payload = state["raw_payload"]

    # Extract field names from XML
    field_names = extract_field_names_from_xml(raw_payload)

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


def route_after_interpreter_1(state: NexBridgeState) -> str:
    """
    Conditional routing after interpreter Run 1.
    T1 payloads must go through dual-agent verification (Run 2).
    T2/T3/T4 payloads skip Run 2 and go directly to validator.

    Reads:
        - state["payload_tier"]: Overall payload tier from classification

    Returns:
        Next node name: "interpreter_run_2" for T1, "validator" otherwise
    """
    payload_tier = state["payload_tier"]

    if payload_tier == 1:
        print("[ORCHESTRATOR] T1 payload detected → routing to Run 2")
        return "interpreter_run_2"
    else:
        print(f"[ORCHESTRATOR] T{payload_tier} payload → skipping Run 2")
        return "validator"


def build_graph():
    """
    Build the NexBridge transformation pipeline graph.

    Flow:
    - classification → interpreter_run_1 → [conditional routing]:
      - T1: interpreter_run_2 → validator → translator → orchestrator → END
      - T2/T3/T4: validator → translator → orchestrator → END

    Returns:
        Compiled LangGraph state graph ready for execution
    """
    # Initialize graph with state type
    graph = StateGraph(NexBridgeState)

    # Register all nodes
    graph.add_node("classification", classification_node)
    graph.add_node("interpreter_run_1", interpreter_node)
    graph.add_node("interpreter_run_2", interpreter_run_2_node)
    graph.add_node("validator", validator_node)
    graph.add_node("translator", translator_node)
    graph.add_node("orchestrator", orchestrator_node)

    # Set entry point
    graph.set_entry_point("classification")

    # Add edges
    graph.add_edge("classification", "interpreter_run_1")

    # Conditional routing after interpreter_run_1
    graph.add_conditional_edges(
        "interpreter_run_1",
        route_after_interpreter_1,
        {
            "interpreter_run_2": "interpreter_run_2",
            "validator": "validator",
        }
    )

    # Linear edges after Run 2
    graph.add_edge("interpreter_run_2", "validator")
    graph.add_edge("validator", "translator")
    graph.add_edge("translator", "orchestrator")
    graph.add_edge("orchestrator", END)

    # Compile and return
    return graph.compile()
