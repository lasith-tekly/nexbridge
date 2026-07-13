"""
NexBridge LangGraph State

Defines the TypedDict structure used by all LangGraph nodes.
This is the shared state that flows through the entire pipeline.
"""

from typing import TypedDict, Optional


class NexBridgeState(TypedDict):
    """
    Shared state for the NexBridge LangGraph pipeline.

    All agent nodes read from and write to this state.
    Each agent owns specific fields and should never modify
    fields owned by other agents.

    Key fields:
    - raw_payload: Original payload string (XML or JSON)
    - source_format: Input format ("xml" or "json")
    - target_format: Desired output format ("xml" or "json")
    - translated_payload: Serialized output string (XML or JSON), None if HOLD
    """

    # Input — set by FastAPI layer, never modified by agents
    raw_payload: str          # Original payload (XML or JSON string)
    source_format: str        # "xml" or "json"
    target_format: str        # "xml" or "json"
    target_schema: dict       # Target schema definition

    # Classification — written by classification_node
    field_classifications: dict
    payload_tier: int  # 1, 2, 3, or 4
    parsed_fields: dict  # {field_name: str_value} from parser adapter

    # XML output config — set by FastAPI layer (XML target only)
    root_element: Optional[str]  # XML root tag, defaults to "payload"

    # Interpretation — written by interpreter node(s)
    interpreter_run_1: dict  # All fields
    interpreter_run_2: dict  # T1 fields only (dual-agent verification)

    # Validation — written by validator node
    validation_result: dict

    # Translation — written by translator node
    translated_payload: Optional[str]  # Serialized output (XML or JSON string), None if HOLD

    # Decision — written by orchestrator node
    decision: Optional[str]  # "GO", "HOLD", or "ESCALATE"
    decision_reason: Optional[str]

    # Confidence tracking
    confidence_scores: dict  # field_name -> confidence score

    # Audit — written by audit node (append-only)
    audit_log: list

    # Performance tracking
    processing_start_ms: int

    # Registry selection — set by FastAPI layer, used by classification_node
    registry_id: Optional[str]  # Registry ID to use; None falls back to default
