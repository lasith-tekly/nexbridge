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
    """

    # Input — set by FastAPI layer, never modified by agents
    xml_payload: str
    target_schema: dict

    # Classification — written by registry node
    field_classifications: dict
    payload_tier: int  # 1, 2, 3, or 4

    # Interpretation — written by interpreter node(s)
    interpreter_run_1: dict  # All fields
    interpreter_run_2: dict  # T1 fields only (dual-agent verification)

    # Validation — written by validator node
    validation_result: dict

    # Translation — written by translator node
    translated_payload: Optional[dict]  # None if decision is HOLD

    # Decision — written by orchestrator node
    decision: Optional[str]  # "GO", "HOLD", or "ESCALATE"
    decision_reason: Optional[str]

    # Confidence tracking
    confidence_scores: dict  # field_name -> confidence score

    # Audit — written by audit node (append-only)
    audit_log: list

    # Performance tracking
    processing_start_ms: int
