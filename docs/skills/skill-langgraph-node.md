# Skill — LangGraph Agent Node

## When To Use This Skill

Load this file before writing any LangGraph node,
conditional edge, or graph compilation code in NexBridge.

---

## NexBridgeState Shape

Every node receives and returns NexBridgeState.
Never add fields to state without updating the TypedDict.

```python
from typing import TypedDict, Optional
from backend.core.models import (
    FieldClassification,
    FieldMapping,
    AuditEntry,
    Decision,
)

class NexBridgeState(TypedDict):
    xml_payload:           str
    target_schema:         dict
    field_classifications: dict[str, FieldClassification]
    payload_tier:          int                      # 1, 2, 3, or 4
    interpreter_run_1:     dict[str, FieldMapping]
    interpreter_run_2:     dict[str, FieldMapping]  # T1 only
    validation_result:     dict
    translated_payload:    Optional[dict]           # None if HOLD
    decision:              Optional[Decision]        # GO/HOLD/ESCALATE
    decision_reason:       Optional[str]
    confidence_scores:     dict[str, float]
    audit_log:             list[AuditEntry]
    processing_start_ms:   int
```

---

## Standard Node Pattern

```python
from langgraph.graph import StateGraph
from backend.core.state import NexBridgeState

def my_agent_node(state: NexBridgeState) -> NexBridgeState:
    """
    One-line description of what this node does.

    Reads:  state fields this node consumes
    Writes: state fields this node produces
    """

    # 1. Read what you need from state
    xml_payload = state["xml_payload"]

    # 2. Do the work
    result = do_something(xml_payload)

    # 3. Write ONLY what this node owns back to state
    # Never overwrite fields owned by another agent
    return {
        **state,
        "field_classifications": result,
    }
```

**Rules:**
- Every node must return the full state with `**state`
- Never mutate state in place — always return a new dict
- Never write to fields owned by another node
- Node names must match the agent they represent

---

## Conditional Edge Pattern

```python
def route_after_classification(state: NexBridgeState) -> str:
    """
    Returns the name of the next node to execute.
    Must return a string matching a registered node name.
    """
    payload_tier = state["payload_tier"]

    if payload_tier == 1:
        return "interpreter_run_1"  # will also run run_2
    else:
        return "interpreter_run_1"  # skips run_2 later
```

---

## Graph Compilation Pattern

```python
from langgraph.graph import StateGraph, END
from backend.core.state import NexBridgeState

def build_graph() -> StateGraph:
    graph = StateGraph(NexBridgeState)

    # Register nodes
    graph.add_node("classification",    classification_node)
    graph.add_node("interpreter_run_1", interpreter_run_1_node)
    graph.add_node("interpreter_run_2", interpreter_run_2_node)
    graph.add_node("validator",         validator_node)
    graph.add_node("translator",        translator_node)
    graph.add_node("orchestrator",      orchestrator_node)
    graph.add_node("audit",             audit_node)

    # Entry point
    graph.set_entry_point("classification")

    # Standard edges
    graph.add_edge("classification",    "interpreter_run_1")
    graph.add_edge("validator",         "translator")
    graph.add_edge("translator",        "orchestrator")
    graph.add_edge("orchestrator",      "audit")
    graph.add_edge("audit",             END)

    # Conditional edge — T1 needs run_2, others skip it
    graph.add_conditional_edges(
        "interpreter_run_1",
        route_after_interpreter_1,
        {
            "interpreter_run_2": "interpreter_run_2",
            "validator":         "validator",
        }
    )

    graph.add_edge("interpreter_run_2", "validator")

    return graph.compile()
```

---

## Orchestrator Decision Pattern

```python
def orchestrator_node(state: NexBridgeState) -> NexBridgeState:
    payload_tier   = state["payload_tier"]
    run_1          = state["interpreter_run_1"]
    run_2          = state["interpreter_run_2"]
    confidence     = state["confidence_scores"]

    # T1 divergence check
    if payload_tier == 1:
        for field, mapping in run_1.items():
            if field in run_2:
                if mapping.target_field != run_2[field].target_field:
                    return {
                        **state,
                        "decision": "HOLD",
                        "decision_reason": (
                            f"T1 field '{field}' diverged between "
                            f"interpreter runs"
                        ),
                        "translated_payload": None,
                    }

    # Confidence threshold check
    thresholds = {1: 1.0, 2: 0.95, 3: 0.80, 4: 0.0}
    threshold  = thresholds[payload_tier]

    for field, score in confidence.items():
        if score < threshold:
            return {
                **state,
                "decision": "HOLD",
                "decision_reason": (
                    f"Field '{field}' confidence {score:.2f} "
                    f"below T{payload_tier} threshold {threshold}"
                ),
                "translated_payload": None,
            }

    return {
        **state,
        "decision": "GO",
        "decision_reason": "All fields passed confidence checks",
    }
```

---

## NexBridge-Specific Rules

```
✅ Orchestrator is the ONLY node that sets decision to GO
✅ Any node can set decision to HOLD (safety override)
✅ T1 threshold = 1.0 — hardcoded, never a parameter
✅ T2 threshold = 0.95 — hardcoded, never a parameter
✅ interpreter_run_2 only executes when payload_tier == 1
✅ translated_payload must be None when decision is HOLD
✅ audit_log entries are append-only — never remove
```
