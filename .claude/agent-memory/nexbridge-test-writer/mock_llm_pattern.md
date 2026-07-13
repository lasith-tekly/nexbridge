---
name: LLM Mocking Pattern for InterpreterAgent and RegistryAnalyser
description: Reusable patterns for mocking get_llm() and structured output — IMPORTANT: call vs invoke difference
type: feedback
---

## CRITICAL: .return_value vs .invoke.return_value

LangChain chains built with `_PROMPT | structured_llm` wrap the structured LLM in a
`RunnableLambda` that **calls** it directly (`structured_llm(messages)`), NOT via `.invoke()`.

**For registry_analyser.py and any agent using `_PROMPT | structured_llm`:**
```python
mock_structured_llm.return_value = mock_result   # __call__, NOT .invoke.return_value
```

**For interpreter.py (direct `.invoke()` on the chain — different pattern):**
```python
mock_structured_llm.invoke.return_value = mock_result
```

Verify which path is in use by checking whether the code does `chain.invoke(...)` or
`structured_llm(...)` directly. When in doubt, test empirically.

---

## Pattern A — InterpreterAgent (uses chain.invoke, but chain calls structured_llm directly)

When mocking the InterpreterAgent's LLM calls, use this pattern:

```python
# Create mock FieldMapping with all required attributes
mock_field_mapping = Mock(spec=FieldMapping)
mock_field_mapping.field_name = "field_name"
mock_field_mapping.target_field = "target_field"
mock_field_mapping.transformed_value = "value"
mock_field_mapping.confidence = 0.98
mock_field_mapping.reasoning = "reasoning"
mock_field_mapping.tier = Tier.T3
mock_field_mapping.model_dump.return_value = {
    "field_name": "field_name",
    "target_field": "target_field",
    "transformed_value": "value",
    "confidence": 0.98,
    "reasoning": "reasoning",
    "tier": 3,
}

# Create mock LLM chain
mock_llm = MagicMock()
mock_structured_llm = MagicMock()
mock_structured_llm.invoke.return_value = mock_field_mapping
mock_llm.with_structured_output.return_value = mock_structured_llm

# Patch get_llm
mocker.patch("backend.core.agents.interpreter.get_llm", return_value=mock_llm)
```

**Why:** The interpreter_node prints log messages that access result.target_field and result.confidence, so the mock must have these attributes defined (not just in model_dump).

**How to apply:** Use Pattern A for interpreter_node tests. Use Pattern B (below) for registry_analyser tests.

---

## Pattern B — RegistryAnalyser (uses _PROMPT | structured_llm; structured_llm is called directly)

```python
from backend.core.agents.registry_analyser import BatchAnalysisResult, FieldAnalysisResult

mock_result = BatchAnalysisResult(fields=[
    FieldAnalysisResult(
        field_name="employee_id",
        suggested_tier=3,
        suggested_label="Business Important",
        reasoning="Correctable identifier.",
        confidence=0.92,
    )
])

mock_llm = MagicMock()
mock_structured_llm = MagicMock()
mock_structured_llm.return_value = mock_result    # __call__, NOT .invoke.return_value
mock_llm.with_structured_output.return_value = mock_structured_llm

with patch("backend.core.agents.registry_analyser.get_llm", return_value=mock_llm):
    result = analyse_fields(["employee_id"], source_format="xml")
```

To inspect what was passed to the structured LLM (e.g., to check prompt content):
```python
call_args = mock_structured_llm.call_args
prompt_value = call_args[0][0]   # ChatPromptValue
rendered = str(prompt_value)     # contains full message text
assert "general enterprise integration" in rendered
```

**Why:** LangChain `_PROMPT | mock_structured_llm` creates a RunnableSequence with a
RunnableLambda step. The lambda calls `mock_structured_llm(messages)` not `.invoke()`.
Setting `.return_value` captures the `__call__` path; `.invoke.return_value` is ignored.

**How to apply:** Use Pattern B for any agent whose chain is built as `prompt | llm`.
