# NexBridge - Solution Agents Technical Specification

## Overview

This document is the deep technical specification for every
runtime agent in the NexBridge pipeline. It covers implementation
design, LangChain/LangGraph patterns, prompt templates, confidence
scoring, state contracts, and error behaviour.

This is the primary reference for @BackendDeveloper when
implementing each agent.

---

## Agent Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                   NEXBRIDGE PIPELINE                        │
│                                                             │
│  XML Input                                                  │
│      │                                                      │
│      ▼                                                      │
│  ┌─────────────────────────────────────────────────────┐   │
│  │           CLASSIFICATION REGISTRY                   │   │
│  │   registry.py — maps every field to T1/T2/T3/T4    │   │
│  └──────────────────────┬──────────────────────────────┘   │
│                         │                                   │
│      ┌──────────────────▼──────────────────┐               │
│      │         ORCHESTRATOR                │               │
│      │  Controls pipeline via LangGraph    │               │
│      │  Makes all GO/HOLD/ESCALATE calls   │               │
│      └──┬──────────────┬───────────────────┘               │
│         │              │                                    │
│  ┌──────▼──────┐ ┌─────▼──────┐                            │
│  │ INTERPRETER │ │ INTERPRETER│  ← T1 only (dual run)      │
│  │   (Run 1)   │ │  (Run 2)   │                            │
│  └──────┬──────┘ └─────┬──────┘                            │
│         └──────┬────────┘                                   │
│                │                                            │
│         ┌──────▼──────┐                                     │
│         │  VALIDATOR  │                                     │
│         └──────┬──────┘                                     │
│                │                                            │
│         ┌──────▼──────┐                                     │
│         │ TRANSLATOR  │                                     │
│         └──────┬──────┘                                     │
│                │                                            │
│         ┌──────▼──────┐                                     │
│         │    AUDIT    │                                     │
│         └──────┬──────┘                                     │
│                │                                            │
│         ┌──────▼──────┐                                     │
│         │ORCHESTRATOR │  ← Final decision                   │
│         │  DECISION   │                                     │
│         └─────────────┘                                     │
└─────────────────────────────────────────────────────────────┘
```

---

## Shared State — NexBridgeState

All agents read from and write to a single shared state object.
No agent communicates directly with another agent.
All inter-agent communication happens through this state.

```python
# backend/core/models.py

from typing import TypedDict, Literal, Optional
from pydantic import BaseModel, Field
from enum import IntEnum

class FieldTier(IntEnum):
    SAFETY_CRITICAL = 1
    OPERATIONALLY_SENSITIVE = 2
    BUSINESS_IMPORTANT = 3
    INFORMATIONAL = 4

class FieldClassification(BaseModel):
    field_name: str
    tier: FieldTier
    label: str
    confidence_threshold: float

class FieldMapping(BaseModel):
    field_name: str
    target_field: str
    transformed_value: object
    confidence: float
    reasoning: str

class ValidationResult(BaseModel):
    field_name: str
    valid: bool
    anomaly: bool
    severity: Optional[Literal["LOW", "MEDIUM", "HIGH"]]
    detail: str

class AuditEntry(BaseModel):
    timestamp: str
    field_name: str
    tier: int
    original_value: str
    transformed_value: object
    confidence: float
    agent: str
    decision: str
    reasoning: str

class NexBridgeState(TypedDict):
    # Input
    raw_xml: str
    target_schema: dict

    # Classification
    field_classifications: dict[str, FieldClassification]
    payload_tier: int

    # Interpreter outputs
    interpreter_run_1: dict[str, FieldMapping]
    interpreter_run_2: dict[str, FieldMapping]   # T1 only
    interpreter_agreed: dict[str, FieldMapping]  # merged after comparison

    # Validation
    validation_results: dict[str, ValidationResult]
    anomalies: list[dict]

    # Translation
    translated_payload: dict

    # Audit
    audit_log: list[AuditEntry]

    # Orchestrator decision
    decision: Literal["GO", "HOLD", "ESCALATE"]
    decision_reason: str
    confidence_scores: dict[str, float]

    # Error tracking
    pipeline_errors: list[str]
```

---

## Agent 1 — Classification Registry

```
File:   backend/core/classification/registry.py
Config: backend/core/classification/registry.json
Status: Phase 1 — implement first
```

### Purpose
Maps every XML field name to its risk tier before
any AI processing begins. This is deterministic —
no LLM involved. The registry is loaded at startup
and cached in memory for the life of the process.

### Implementation Design

```python
# backend/core/classification/registry.py

import json
from pathlib import Path
from functools import lru_cache
from core.models import FieldClassification, FieldTier

THRESHOLDS = {
    FieldTier.SAFETY_CRITICAL:         1.0,
    FieldTier.OPERATIONALLY_SENSITIVE: 0.95,
    FieldTier.BUSINESS_IMPORTANT:      0.80,
    FieldTier.INFORMATIONAL:           0.0,
}

TIER_LABELS = {
    1: "Safety Critical",
    2: "Operationally Sensitive",
    3: "Business Important",
    4: "Informational",
}

class ClassificationRegistry:
    def __init__(self, registry_path: str = None):
        """
        Loads and caches the field classification registry.

        Args:
            registry_path: Path to registry.json.
                           Defaults to core/classification/registry.json
        """
        self._registry: dict[str, int] = {}
        self._load(registry_path)

    def _load(self, path: str = None) -> None:
        default = Path(__file__).parent / "registry.json"
        target = Path(path) if path else default
        with open(target) as f:
            data = json.load(f)
        self._registry = {
            k: v["tier"] for k, v in data["fields"].items()
        }
        print(f"[REGISTRY] Loaded {len(self._registry)} fields")

    def classify(self, field_name: str) -> FieldClassification:
        """
        Returns the FieldClassification for a given XML field name.
        Unknown fields default to Tier 4.
        """
        tier_value = self._registry.get(field_name, 4)
        tier = FieldTier(tier_value)
        return FieldClassification(
            field_name=field_name,
            tier=tier,
            label=TIER_LABELS[tier_value],
            confidence_threshold=THRESHOLDS[tier],
        )

    def classify_payload(
        self, field_names: list[str]
    ) -> tuple[dict[str, FieldClassification], int]:
        """
        Classifies all fields in a payload.
        Returns classifications dict and the highest tier found.
        """
        classifications = {
            f: self.classify(f) for f in field_names
        }
        payload_tier = min(c.tier for c in classifications.values())
        print(f"[REGISTRY] Payload tier={payload_tier}")
        return classifications, payload_tier
```

### registry.json Structure
```json
{
  "version": "1.0",
  "domain": "aviation",
  "fields": {
    "MTOW":     { "tier": 1, "label": "Max Takeoff Weight" },
    "ZFW":      { "tier": 1, "label": "Zero Fuel Weight" },
    "FLT_NUM":  { "tier": 2, "label": "Flight Number" },
    "PAX_NAME": { "tier": 3, "label": "Passenger Name" },
    "TIMESTAMP":{ "tier": 4, "label": "Message Timestamp" }
  },
  "default_tier": 4
}
```

### State Write
```python
state["field_classifications"] = classifications
state["payload_tier"] = payload_tier
```

---

## Agent 2 — Interpreter Agent

```
File:   backend/core/agents/interpreter.py
Status: Phase 1 — core agent
```

### Purpose
Uses Claude API via LangChain to semantically understand
each XML field and map it to the correct target JSON field.
Returns a confidence score representing certainty of the mapping.

### LangChain Implementation

```python
# backend/core/agents/interpreter.py

from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from core.models import NexBridgeState, FieldMapping

INTERPRETER_PROMPT = """
You are a data transformation expert specialising in aviation
system integration. Your task is to map a single XML field
to the most appropriate field in the target JSON schema.

XML Field Name: {field_name}
XML Field Value: {field_value}
Field Tier: T{tier} — {tier_label}
Domain Context: {domain_context}

Target JSON Schema:
{target_schema}

Instructions:
1. Understand the semantic meaning of the XML field
2. Identify the best matching field in the target schema
3. Transform the value to match the target field's type
4. Return a confidence score between 0.0 and 1.0
5. Explain your reasoning clearly

Return ONLY a JSON object in this exact format:
{{
  "field_name": "{field_name}",
  "target_field": "<best matching field from target schema>",
  "transformed_value": <appropriately typed value>,
  "confidence": <float between 0.0 and 1.0>,
  "reasoning": "<why you chose this mapping>"
}}
"""

class InterpreterAgent:
    def __init__(self):
        self.llm = ChatAnthropic(
            model="claude-sonnet-4-20250514",
            temperature=0,       # Deterministic for consistency
            max_tokens=1000,
        )
        self.prompt = ChatPromptTemplate.from_template(
            INTERPRETER_PROMPT
        )
        self.parser = PydanticOutputParser(pydantic_object=FieldMapping)

    def interpret_field(
        self,
        field_name: str,
        field_value: str,
        tier: int,
        tier_label: str,
        target_schema: dict,
        domain_context: str = "aviation operations",
    ) -> FieldMapping:
        """
        Maps a single XML field to the target JSON schema.

        Args:
            field_name:     XML field name (e.g. "MTOW")
            field_value:    Raw XML value (e.g. "75000")
            tier:           Classification tier (1-4)
            tier_label:     Human readable tier label
            target_schema:  Target JSON schema dict
            domain_context: Domain hint for the LLM

        Returns:
            FieldMapping with target field, value, confidence,
            and reasoning
        """
        print(f"[INTERPRETER] Processing field={field_name} tier=T{tier}")

        chain = self.prompt | self.llm | self.parser
        result = chain.invoke({
            "field_name": field_name,
            "field_value": field_value,
            "tier": tier,
            "tier_label": tier_label,
            "domain_context": domain_context,
            "target_schema": str(target_schema),
        })

        print(
            f"[INTERPRETER] field={field_name} "
            f"→ {result.target_field} "
            f"confidence={result.confidence:.2f}"
        )
        return result

    def interpret_payload(
        self,
        state: NexBridgeState,
        run_number: int = 1,
    ) -> dict[str, FieldMapping]:
        """
        Interprets all fields in the payload.
        run_number=1 or 2 for T1 dual-agent runs.
        """
        from xml.etree import ElementTree as ET
        root = ET.fromstring(state["raw_xml"])
        fields = {child.tag: child.text for child in root}

        mappings = {}
        for field_name, field_value in fields.items():
            classification = state["field_classifications"][field_name]
            mapping = self.interpret_field(
                field_name=field_name,
                field_value=str(field_value),
                tier=classification.tier,
                tier_label=classification.label,
                target_schema=state["target_schema"],
            )
            mappings[field_name] = mapping

        print(f"[INTERPRETER] Run {run_number} complete — {len(mappings)} fields")
        return mappings
```

### Confidence Scoring Design

```
1.0   Agent is certain. Exact match in target schema.
      Value type is unambiguous.

0.95  Agent is highly confident. Clear semantic match.
      Minor type coercion applied.

0.80  Agent is reasonably confident. Likely match
      but some ambiguity in naming.

0.60  Agent found a match but is uncertain.
      Multiple possible target fields.

< 0.5 Agent cannot confidently map this field.
      Will trigger HOLD for T1/T2.
```

### State Write
```python
# Run 1 (all tiers) or Run 2 (T1 only)
state["interpreter_run_1"] = mappings   # or run_2
state["confidence_scores"] = {
    k: v.confidence for k, v in mappings.items()
}
```

### Error and Retry Behaviour
```
Claude API timeout    → Retry once after 3 seconds
                        If fails again → set confidence = 0.0
                        Orchestrator will HOLD on T1/T2

Malformed JSON output → LangChain parser retries with
                        more explicit format instruction
                        If fails → raise AgentProcessingError

Empty response        → raise AgentProcessingError immediately
                        Do not retry
```

---

## Agent 3 — Validator Agent

```
File:   backend/core/agents/validator.py
Status: Phase 2
```

### Purpose
Advisory agent that checks each transformed field against
the target schema constraints. Does NOT block the pipeline
directly — it flags anomalies and the orchestrator decides
the action based on tier.

### Implementation Design

```python
# backend/core/agents/validator.py

from core.models import NexBridgeState, ValidationResult, FieldMapping

class ValidatorAgent:
    def validate_field(
        self,
        field_name: str,
        mapping: FieldMapping,
        target_schema: dict,
        tier: int,
    ) -> ValidationResult:
        """
        Validates a single mapped field against target schema.
        Advisory only — does not raise exceptions.
        """
        print(f"[VALIDATOR] Checking field={field_name} tier=T{tier}")

        expected_type = target_schema.get(mapping.target_field)
        anomaly = False
        severity = None
        detail = "OK"

        # Type check
        if expected_type == "number":
            try:
                float(str(mapping.transformed_value))
            except ValueError:
                anomaly = True
                severity = "HIGH" if tier <= 2 else "MEDIUM"
                detail = f"Expected number, got {type(mapping.transformed_value)}"

        # Required field check
        if mapping.target_field not in target_schema:
            anomaly = True
            severity = "LOW"
            detail = f"Target field {mapping.target_field} not in schema"

        # Confidence check
        classification = None  # passed in from state
        threshold = {1: 1.0, 2: 0.95, 3: 0.80, 4: 0.0}.get(tier, 0.0)
        if mapping.confidence < threshold:
            anomaly = True
            severity = "HIGH" if tier == 1 else "MEDIUM"
            detail = (
                f"Confidence {mapping.confidence:.2f} "
                f"below threshold {threshold}"
            )

        print(
            f"[VALIDATOR] field={field_name} "
            f"valid={not anomaly} anomaly={anomaly} severity={severity}"
        )

        return ValidationResult(
            field_name=field_name,
            valid=not anomaly,
            anomaly=anomaly,
            severity=severity,
            detail=detail,
        )

    def validate_payload(
        self, state: NexBridgeState
    ) -> tuple[dict[str, ValidationResult], list[dict]]:
        """
        Validates all fields in the agreed interpreter output.
        Returns results dict and list of anomalies found.
        """
        results = {}
        anomalies = []

        for field_name, mapping in state["interpreter_agreed"].items():
            tier = state["field_classifications"][field_name].tier
            result = self.validate_field(
                field_name, mapping,
                state["target_schema"], tier
            )
            results[field_name] = result
            if result.anomaly:
                anomalies.append({
                    "field": field_name,
                    "severity": result.severity,
                    "detail": result.detail,
                })

        print(f"[VALIDATOR] Complete — {len(anomalies)} anomalies found")
        return results, anomalies
```

### Anomaly Severity Rules
```
HIGH    → T1 or T2 field: wrong type, missing, or
          confidence below threshold
          Orchestrator will HOLD

MEDIUM  → T3 field issue, or T2 minor concern
          Orchestrator attaches flag but may proceed

LOW     → T4 field issue, metadata concern
          Logged only, never blocks
```

### State Write
```python
state["validation_results"] = results
state["anomalies"] = anomalies
```

---

## Agent 4 — Translator Agent

```
File:   backend/core/agents/translator.py
Status: Phase 1
```

### Purpose
Takes the agreed, validated field mappings and constructs
the final target JSON payload. Deterministic — no LLM.
Applies naming conventions and handles optional/required fields.

### Implementation Design

```python
# backend/core/agents/translator.py

from core.models import NexBridgeState

class TranslatorAgent:
    def translate(self, state: NexBridgeState) -> dict:
        """
        Builds the target JSON payload from agreed mappings.

        Takes interpreter_agreed mappings and constructs
        a clean JSON object matching the target schema.

        Returns:
            Translated payload as dict
        """
        print("[TRANSLATOR] Building target JSON payload")

        payload = {}
        missing_required = []
        omitted = []

        for field_name, mapping in state["interpreter_agreed"].items():
            if mapping.target_field in state["target_schema"]:
                payload[mapping.target_field] = mapping.transformed_value
                print(
                    f"[TRANSLATOR] Mapped {field_name} "
                    f"→ {mapping.target_field} "
                    f"= {mapping.transformed_value}"
                )
            else:
                omitted.append(field_name)
                print(f"[TRANSLATOR] Omitted {field_name} — not in schema")

        # Check required fields
        for required_field in state["target_schema"]:
            if required_field not in payload:
                missing_required.append(required_field)
                print(f"[TRANSLATOR] Missing required field: {required_field}")

        print(
            f"[TRANSLATOR] Complete — "
            f"{len(payload)} fields mapped, "
            f"{len(missing_required)} missing, "
            f"{len(omitted)} omitted"
        )
        return payload
```

### State Write
```python
state["translated_payload"] = payload
```

---

## Agent 5 — Audit Agent

```
File:   backend/core/agents/audit.py
Status: Phase 3
```

### Purpose
Creates an immutable, structured audit log entry for every
field transformation and every orchestrator decision.
Audit entries are append-only — never modified, never deleted.

### Implementation Design

```python
# backend/core/agents/audit.py

from datetime import datetime, timezone
from core.models import NexBridgeState, AuditEntry

class AuditAgent:
    def log_transformation(
        self, state: NexBridgeState
    ) -> list[AuditEntry]:
        """
        Creates audit entries for all field transformations.
        Must be called AFTER translator and BEFORE decision.
        """
        print("[AUDIT] Writing transformation audit log")
        entries = []

        for field_name, mapping in state["interpreter_agreed"].items():
            classification = state["field_classifications"][field_name]
            validation = state["validation_results"].get(field_name)

            entry = AuditEntry(
                timestamp=datetime.now(timezone.utc).isoformat(),
                field_name=field_name,
                tier=classification.tier,
                original_value=self._extract_original(
                    field_name, state["raw_xml"]
                ),
                transformed_value=mapping.transformed_value,
                confidence=mapping.confidence,
                agent="interpreter",
                decision="mapped" if not validation or validation.valid
                         else "flagged",
                reasoning=mapping.reasoning,
            )
            entries.append(entry)
            print(
                f"[AUDIT] Logged field={field_name} "
                f"tier=T{classification.tier} "
                f"confidence={mapping.confidence:.2f}"
            )

        return entries

    def log_decision(
        self,
        state: NexBridgeState,
        decision: str,
        reason: str,
    ) -> AuditEntry:
        """
        Creates a single audit entry for the orchestrator decision.
        """
        entry = AuditEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            field_name="__PAYLOAD__",
            tier=state["payload_tier"],
            original_value="<full payload>",
            transformed_value=state.get("translated_payload"),
            confidence=min(state["confidence_scores"].values())
                       if state["confidence_scores"] else 0.0,
            agent="orchestrator",
            decision=decision,
            reasoning=reason,
        )
        print(f"[AUDIT] Logged orchestrator decision={decision}")
        return entry

    def _extract_original(self, field_name: str, raw_xml: str) -> str:
        """Extracts original value from raw XML for audit record."""
        from xml.etree import ElementTree as ET
        try:
            root = ET.fromstring(raw_xml)
            element = root.find(field_name)
            return element.text if element is not None else ""
        except Exception:
            return ""
```

### Immutability Rules
```
RULE 1: AuditEntry objects are frozen Pydantic models
        model_config = ConfigDict(frozen=True)

RULE 2: audit_log in state is append-only
        Never pop, never replace, only append

RULE 3: No API endpoint exists to delete audit entries

RULE 4: All T1 fields MUST have an audit entry
        Pipeline fails if T1 entry is missing
```

### State Write
```python
state["audit_log"] = field_entries + [decision_entry]
```

---

## Agent 6 — Orchestrator

```
File:   backend/core/orchestrator.py
Status: Phase 1 (basic) → Phase 2 (T1 dual-agent)
LOCKED: After Phase 2 completion
```

### Purpose
The central control plane. Builds and runs the LangGraph
state machine. Enforces all governance rules. The only
agent that can release a payload.

### LangGraph Graph Definition

```python
# backend/core/orchestrator.py

from langgraph.graph import StateGraph, END
from core.models import NexBridgeState
from core.classification.registry import ClassificationRegistry
from core.agents.interpreter import InterpreterAgent
from core.agents.validator import ValidatorAgent
from core.agents.translator import TranslatorAgent
from core.agents.audit import AuditAgent

T1_THRESHOLD = 1.0   # HARDCODED — never change
T2_THRESHOLD = 0.95  # HARDCODED — never change

class NexBridgeOrchestrator:
    def __init__(self):
        self.registry = ClassificationRegistry()
        self.interpreter = InterpreterAgent()
        self.validator = ValidatorAgent()
        self.translator = TranslatorAgent()
        self.audit = AuditAgent()
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        graph = StateGraph(NexBridgeState)

        # Register nodes
        graph.add_node("classify",       self._classify)
        graph.add_node("interpret",      self._interpret)
        graph.add_node("dual_interpret", self._dual_interpret)
        graph.add_node("compare",        self._compare)
        graph.add_node("validate",       self._validate)
        graph.add_node("translate",      self._translate)
        graph.add_node("audit",          self._audit)
        graph.add_node("decide",         self._decide)

        # Entry point
        graph.set_entry_point("classify")

        # Routing after classify
        graph.add_conditional_edges(
            "classify",
            self._route_by_tier,
            {
                "t1": "dual_interpret",
                "standard": "interpret",
            }
        )

        # Standard path
        graph.add_edge("interpret",      "validate")

        # T1 path
        graph.add_edge("dual_interpret", "compare")
        graph.add_conditional_edges(
            "compare",
            self._route_after_compare,
            {
                "agreed":   "validate",
                "diverged": "decide",    # HOLD immediately
            }
        )

        # Shared path after validation
        graph.add_edge("validate",  "translate")
        graph.add_edge("translate", "audit")
        graph.add_edge("audit",     "decide")
        graph.add_edge("decide",    END)

        return graph.compile()

    def _route_by_tier(self, state: NexBridgeState) -> str:
        return "t1" if state["payload_tier"] == 1 else "standard"

    def _route_after_compare(self, state: NexBridgeState) -> str:
        return "agreed" if state.get("interpreter_agreed") else "diverged"

    def _classify(self, state: NexBridgeState) -> NexBridgeState:
        from xml.etree import ElementTree as ET
        root = ET.fromstring(state["raw_xml"])
        field_names = [child.tag for child in root]
        classifications, payload_tier = self.registry.classify_payload(
            field_names
        )
        return {
            **state,
            "field_classifications": classifications,
            "payload_tier": payload_tier,
        }

    def _interpret(self, state: NexBridgeState) -> NexBridgeState:
        mappings = self.interpreter.interpret_payload(state, run_number=1)
        return {
            **state,
            "interpreter_run_1": mappings,
            "interpreter_agreed": mappings,
            "confidence_scores": {
                k: v.confidence for k, v in mappings.items()
            },
        }

    def _dual_interpret(self, state: NexBridgeState) -> NexBridgeState:
        print("[ORCHESTRATOR] T1 payload — running dual interpreter")
        run_1 = self.interpreter.interpret_payload(state, run_number=1)
        run_2 = self.interpreter.interpret_payload(state, run_number=2)
        return {**state, "interpreter_run_1": run_1, "interpreter_run_2": run_2}

    def _compare(self, state: NexBridgeState) -> NexBridgeState:
        run_1 = state["interpreter_run_1"]
        run_2 = state["interpreter_run_2"]
        agreed = {}

        for field_name in run_1:
            m1 = run_1[field_name]
            m2 = run_2.get(field_name)
            if m2 and m1.target_field == m2.target_field:
                agreed[field_name] = m1
            else:
                print(
                    f"[ORCHESTRATOR] DIVERGENCE field={field_name} "
                    f"run1={m1.target_field} "
                    f"run2={m2.target_field if m2 else 'missing'}"
                )

        return {**state, "interpreter_agreed": agreed if agreed else {}}

    def _validate(self, state: NexBridgeState) -> NexBridgeState:
        results, anomalies = self.validator.validate_payload(state)
        return {**state, "validation_results": results, "anomalies": anomalies}

    def _translate(self, state: NexBridgeState) -> NexBridgeState:
        payload = self.translator.translate(state)
        return {**state, "translated_payload": payload}

    def _audit(self, state: NexBridgeState) -> NexBridgeState:
        entries = self.audit.log_transformation(state)
        return {**state, "audit_log": entries}

    def _decide(self, state: NexBridgeState) -> NexBridgeState:
        tier = state["payload_tier"]
        scores = state.get("confidence_scores", {})

        # T1 divergence check
        if tier == 1 and not state.get("interpreter_agreed"):
            decision = "HOLD"
            reason = "T1 dual-agent divergence — interpreters disagreed"
            print(f"[ORCHESTRATOR] Decision=HOLD reason={reason}")
            entry = self.audit.log_decision(state, decision, reason)
            return {
                **state,
                "decision": decision,
                "decision_reason": reason,
                "audit_log": state.get("audit_log", []) + [entry],
            }

        # Confidence threshold check
        threshold = T1_THRESHOLD if tier == 1 else T2_THRESHOLD if tier == 2 else 0.0
        for field, score in scores.items():
            if score < threshold:
                decision = "HOLD"
                reason = (
                    f"T{tier} field {field}: confidence {score:.2f} "
                    f"below threshold {threshold}"
                )
                print(f"[ORCHESTRATOR] Decision=HOLD reason={reason}")
                entry = self.audit.log_decision(state, decision, reason)
                return {
                    **state,
                    "decision": decision,
                    "decision_reason": reason,
                    "audit_log": state.get("audit_log", []) + [entry],
                }

        # T2 anomaly check
        high_anomalies = [
            a for a in state.get("anomalies", [])
            if a["severity"] == "HIGH"
        ]
        if high_anomalies:
            decision = "ESCALATE"
            reason = f"HIGH anomalies detected: {high_anomalies}"
            print(f"[ORCHESTRATOR] Decision=ESCALATE reason={reason}")
            entry = self.audit.log_decision(state, decision, reason)
            return {
                **state,
                "decision": decision,
                "decision_reason": reason,
                "audit_log": state.get("audit_log", []) + [entry],
            }

        # All checks passed
        decision = "GO"
        reason = "All fields passed confidence thresholds and validation"
        print(f"[ORCHESTRATOR] Decision=GO")
        entry = self.audit.log_decision(state, decision, reason)
        return {
            **state,
            "decision": decision,
            "decision_reason": reason,
            "audit_log": state.get("audit_log", []) + [entry],
        }

    def run(self, xml_payload: str, target_schema: dict) -> NexBridgeState:
        """
        Entry point. Runs the full NexBridge pipeline.
        Returns the final state with decision and audit log.
        """
        print("[ORCHESTRATOR] Pipeline started")
        initial_state: NexBridgeState = {
            "raw_xml": xml_payload,
            "target_schema": target_schema,
            "field_classifications": {},
            "payload_tier": 4,
            "interpreter_run_1": {},
            "interpreter_run_2": {},
            "interpreter_agreed": {},
            "validation_results": {},
            "anomalies": [],
            "translated_payload": {},
            "audit_log": [],
            "decision": "HOLD",
            "decision_reason": "",
            "confidence_scores": {},
            "pipeline_errors": [],
        }
        result = self.graph.invoke(initial_state)
        print(f"[ORCHESTRATOR] Pipeline complete decision={result['decision']}")
        return result
```

---

## Error Handling Across All Agents

```python
# backend/core/exceptions.py

class NexBridgeError(Exception):
    """Base exception for all NexBridge errors"""

class AgentProcessingError(NexBridgeError):
    """Raised when an agent fails to process a field"""
    def __init__(self, agent: str, detail: str):
        self.agent = agent
        self.detail = detail
        super().__init__(f"[{agent.upper()}] {detail}")

class ConfidenceThresholdError(NexBridgeError):
    """Raised when confidence is below tier threshold"""
    def __init__(self, field: str, tier: int,
                 confidence: float, threshold: float):
        self.field = field
        self.tier = tier
        self.confidence = confidence
        self.threshold = threshold
        super().__init__(
            f"Field {field} (T{tier}): "
            f"confidence {confidence:.2f} < {threshold}"
        )

class OrchestratorHoldError(NexBridgeError):
    """Raised when orchestrator issues a HOLD"""
    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(f"HOLD: {reason}")
```

### Global Error Behaviour
```
Agent error on T4 field    → Log and skip field, continue
Agent error on T3 field    → Log anomaly, continue
Agent error on T2 field    → ESCALATE
Agent error on T1 field    → HOLD immediately
Claude API unavailable     → HOLD all T1/T2, T3/T4 may continue
Registry not loaded        → Fail fast at startup, do not start API
```

---

**Document Version:** 1.0
**Project:** NexBridge
**Maintained By:** Lasith Jayarathne (@TechLead)
**Last Updated:** March 2026
**Reference for:** @BackendDeveloper implementing all solution agents
