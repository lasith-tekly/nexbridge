# Skill — pytest for NexBridge Agents

## When To Use This Skill

Load this file before writing any pytest test
for NexBridge backend agents, models, or the orchestrator.

---

## Test File Naming

```
backend/tests/
├── conftest.py              ← shared fixtures
├── test_models.py           ← Pydantic model tests
├── test_registry.py         ← ClassificationRegistry tests
├── test_interpreter.py      ← InterpreterAgent tests
├── test_translator.py       ← TranslatorAgent tests
├── test_validator.py        ← ValidatorAgent tests
├── test_orchestrator.py     ← Full pipeline + T1 safety tests
└── test_audit.py            ← AuditAgent tests
```

---

## conftest.py — Standard Fixtures

```python
# backend/tests/conftest.py
import pytest
from backend.core.state import NexBridgeState

@pytest.fixture
def go_xml_payload() -> str:
    return """<record>
    <employee_id>E-12345</employee_id>
    <department>Operations</department>
    <start_date>2024-03-01</start_date>
    <contract_type>FULL_TIME</contract_type>
    <office_location>London</office_location>
</record>"""

@pytest.fixture
def hold_xml_payload() -> str:
    return """<record>
    <employee_id>E-12345</employee_id>
    <department>Operations</department>
    <weight_limit>250</weight_limit>
    <equipment_class>HEAVY</equipment_class>
    <clearance_level>L3</clearance_level>
</record>"""

@pytest.fixture
def go_target_schema() -> dict:
    return {
        "id": "string",
        "dept_code": "string",
        "start_date": "string",
        "emp_type": "string",
        "location": "string",
    }

@pytest.fixture
def hold_target_schema() -> dict:
    return {
        "id": "string",
        "dept_code": "string",
        "max_permitted_load": "number",
        "equipment_type": "string",
        "access_level": "string",
    }

@pytest.fixture
def base_state(go_xml_payload, go_target_schema) -> NexBridgeState:
    """Minimal valid state for GO scenario testing."""
    return NexBridgeState(
        xml_payload=go_xml_payload,
        target_schema=go_target_schema,
        field_classifications={},
        payload_tier=3,
        interpreter_run_1={},
        interpreter_run_2={},
        validation_result={},
        translated_payload=None,
        decision=None,
        decision_reason=None,
        confidence_scores={},
        audit_log=[],
        processing_start_ms=0,
    )

@pytest.fixture
def t1_state(hold_xml_payload, hold_target_schema) -> NexBridgeState:
    """Minimal valid state for T1/HOLD scenario testing."""
    return NexBridgeState(
        xml_payload=hold_xml_payload,
        target_schema=hold_target_schema,
        field_classifications={},
        payload_tier=1,
        interpreter_run_1={},
        interpreter_run_2={},
        validation_result={},
        translated_payload=None,
        decision=None,
        decision_reason=None,
        confidence_scores={},
        audit_log=[],
        processing_start_ms=0,
    )
```

---

## Standard Test Patterns

### Model Tests
```python
def test_field_classification_is_immutable():
    fc = FieldClassification(
        field_name="weight_limit",
        tier=Tier.T1,
        confidence_threshold=1.0,
        label="Safety Critical",
    )
    with pytest.raises(Exception):
        fc.tier = Tier.T2  # must raise — frozen model


def test_confidence_out_of_range_raises():
    with pytest.raises(ValueError):
        FieldMapping(
            field_name="test",
            target_field="test_out",
            transformed_value="x",
            confidence=1.5,  # invalid
            reasoning="test",
            tier=Tier.T3,
        )
```

### Agent Node Tests
```python
def test_classification_node_identifies_t1(t1_state):
    """Classification must identify weight_limit as T1."""
    result = classification_node(t1_state)

    assert result["payload_tier"] == 1
    assert "weight_limit" in result["field_classifications"]
    assert result["field_classifications"]["weight_limit"].tier == Tier.T1


def test_classification_node_go_scenario(base_state):
    """GO scenario payload must not contain T1 fields."""
    result = classification_node(base_state)

    tiers = [fc.tier for fc in result["field_classifications"].values()]
    assert Tier.T1 not in tiers
    assert result["payload_tier"] >= 2
```

### Orchestrator Safety Tests
```python
def test_orchestrator_holds_on_t1_divergence(t1_state):
    """
    CRITICAL SAFETY TEST.
    T1 field with diverging interpreter outputs MUST produce HOLD.
    This test must never be skipped or marked xfail.
    """
    # Set up diverging interpreter outputs
    state = {
        **t1_state,
        "interpreter_run_1": {
            "weight_limit": FieldMapping(
                field_name="weight_limit",
                target_field="max_permitted_load",
                transformed_value=250,
                confidence=0.95,
                reasoning="run 1 mapping",
                tier=Tier.T1,
            )
        },
        "interpreter_run_2": {
            "weight_limit": FieldMapping(
                field_name="weight_limit",
                target_field="weight_capacity",  # different!
                transformed_value=250,
                confidence=0.91,
                reasoning="run 2 mapping",
                tier=Tier.T1,
            )
        },
        "confidence_scores": {"weight_limit": 0.95},
    }

    result = orchestrator_node(state)

    assert result["decision"] == Decision.HOLD
    assert result["translated_payload"] is None
    assert "diverged" in result["decision_reason"].lower()


def test_orchestrator_holds_on_low_confidence(t1_state):
    """T1 field with confidence < 1.0 MUST produce HOLD."""
    state = {
        **t1_state,
        "confidence_scores": {"weight_limit": 0.95},  # below T1 threshold
    }
    result = orchestrator_node(state)
    assert result["decision"] == Decision.HOLD


def test_t1_threshold_is_exactly_1_0():
    """Confirm T1 threshold constant is exactly 1.0 — never lower."""
    from backend.core.constants import CONFIDENCE_THRESHOLDS
    assert CONFIDENCE_THRESHOLDS[1] == 1.0
```

---

## Test Coverage Requirements

Every agent must have tests covering:

```
Classification:   T1 detection, T2/T3/T4 correct tier assignment,
                  payload_tier inheritance rule (T1 field = T1 payload)

Interpreter:      Field mapping output shape, confidence in range,
                  reasoning is non-empty string

Translator:       Output matches target schema keys,
                  HOLD state produces None translated_payload

Orchestrator:     GO scenario passes, HOLD on T1 divergence,
                  HOLD on low confidence, audit_log populated

Audit:            Entry is immutable after creation,
                  timestamp is present, all required fields present
```

---

## Running Tests

```bash
# All tests
pytest tests/ -v

# Single file
pytest tests/test_orchestrator.py -v

# Single test
pytest tests/test_orchestrator.py::test_orchestrator_holds_on_t1_divergence -v

# Safety tests only (mark them)
pytest tests/ -v -m "safety"
```

---

## NexBridge Test Rules

```
✅ T1 safety tests must NEVER be skipped
✅ T1 safety tests must NEVER be marked xfail
✅ Every agent node must have a test for GO and HOLD
✅ Confidence threshold constants must be tested
✅ AuditEntry immutability must be tested
❌ Never mock the T1 threshold value in tests
❌ Never test with confidence values outside 0.0-1.0
```
