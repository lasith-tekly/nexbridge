---
name: NexBridge Test Structure Patterns
description: Standard test organization and patterns for NexBridge agents
type: feedback
---

**Test Class Organization:**

Organize tests into classes by component under test:
- `TestInterpreterNode` - main agent node function
- `TestExtractFieldValueFromXml` - helper function tests
- `TestBuildTargetFieldsList` - helper function tests
- `TestBuildLlmPrompt` - helper function tests

**Test Naming Convention:**

`test_<component>_<scenario>_<expected_outcome>`

Examples:
- `test_interpreter_node_go_scenario_single_field`
- `test_extract_field_value_malformed_xml`
- `test_interpreter_node_llm_failure_raises_llm_error`

**Test Coverage Checklist:**

For agent nodes:
✅ Happy path with single field
✅ Happy path with multiple fields (3+)
✅ Boundary value testing (confidence 0.0, 1.0)
✅ LLM failure raises correct error type
✅ Invalid data raises ValueError
✅ Empty input returns empty output
✅ Missing XML fields handled gracefully
✅ State immutability (original state not mutated)

For helper functions:
✅ Basic happy path
✅ Nested structures
✅ Missing/empty data
✅ Malformed input
✅ Whitespace handling

**Why:** This structure makes tests easy to navigate, maintain, and ensures comprehensive coverage of all code paths including error conditions.

**How to apply:** Use this checklist when writing tests for any new agent. All items must be tested before committing.

---

**Parser/stdlib-only component checklist (XmlParser pattern):**

For components with no LLM dependency (pure Python/stdlib):
✅ Happy path with minimal valid input (2 fields)
✅ Happy path with multiple fields (5+)
✅ Empty root / self-closing root → empty dict/list
✅ Element with no text returns "" (not None) — `child.text or ""`
✅ Direct-children-only semantics (grandchild tags must NOT appear)
✅ Malformed XML raises ParseError (not raw ET.ParseError)
✅ ParseError carries input_format="xml" and a non-empty reason
✅ Empty string input raises ParseError
✅ Stdout logging verified with capsys for both success and zero-count cases
✅ Return type verified (dict vs list, str values)

**ParseError attribute trap:** The attribute is `self.input_format`, NOT `self.format`.
Accessing `err.format` will raise AttributeError. Always assert `err.input_format`.

**Virtualenv path:** `backend/venv/bin/activate` (NOT `venv/bin/activate` at repo root).
Run tests with: `source backend/venv/bin/activate && pytest backend/tests/test_xml_parser.py -v`

---

**JSON parser-specific checklist (JsonParser pattern):**

For JsonParser (json stdlib, no LLM dependency):
✅ Happy path flat object with 2 fields → correct dict[str, str]
✅ All returned values are str (assert isinstance for every value)
✅ int, float, bool true/false, null each coerced to correct str representation
✅ Nested object value present as top-level key (not flattened) — "city" not in result
✅ Empty object {} → empty dict / empty list
✅ Malformed JSON raises ParseError (not json.JSONDecodeError)
✅ ParseError carries input_format="json" and non-empty reason
✅ Root array, root string, root int each raise ParseError with reason="Expected JSON object at root"
✅ Empty string raises ParseError
✅ Stdout logging verified with capsys for 2-field and 0-field cases

**Boolean coercion gotcha:** Python str(True) == "True" and str(False) == "False".
Test inputs must be lowercase JSON (`true`/`false`); expected str values use Python capitalisation.

**Root non-object reason string:** The implementation hard-codes
`reason="Expected JSON object at root"` — test for exact match, not a substring.

---

**JsonTranslator-specific checklist (Task 3.00e pattern):**

For JsonTranslator (stdlib json + type-conversion, no LLM dependency):
✅ build() with dict mappings returns parseable JSON (json.loads succeeds)
✅ build() produces correct target_field keys and transformed_value values
✅ build() with SimpleNamespace (Pydantic-style) mappings behaves identically to dicts
✅ build({}, {}) returns exactly "{}"
✅ "number" and "float" schema types → value is Python float in parsed output
✅ "integer" and "int" schema types → value is Python int in parsed output
✅ "boolean"/"bool" + "true" → True; "false" → False; "True" (capital T) → True
✅ Unknown or missing schema type → value is str in parsed output
✅ Non-numeric string with "number" schema → graceful str fallback, no exception
✅ Non-numeric string with "integer" schema → graceful str fallback, no exception
✅ Missing "target_field" key → TranslationError with field_name = source key name
✅ Missing "transformed_value" key → TranslationError raised
✅ capsys: two-field input logs "[JSON_TRANSLATOR] Built JSON with 2 fields"
✅ capsys: empty input logs "[JSON_TRANSLATOR] Built JSON with 0 fields"
✅ monkeypatch json.dumps to raise ValueError → TranslationError with field_name="<payload>"
✅ Package import: from backend.core.translators import JsonTranslator succeeds
✅ "JsonTranslator" in backend.core.translators.__all__
✅ "XmlTranslator" still in backend.core.translators.__all__

**monkeypatch target for json.dumps:** `backend.core.translators.json_translator.json` (the module
reference inside json_translator.py). Use `monkeypatch.setattr(jt_module.json, "dumps", ...)`.

**Boolean coercion detail:** `_convert` uses `str(value).lower() == "true"`, so any casing of
"true" produces True and anything else (including "True") produces True correctly. "false", "False",
"0", "" all produce False.

---

**API schema checklist (schemas.py — Task 3.01 pattern):**

For Pydantic v2 API schemas with no LLM dependency:
✅ Valid construction for every format/tier boundary value (1, 4 for tiers; 0.0, 1.0 for thresholds)
✅ Invalid boundary values one step outside range (0, 5 for tier; -0.1, 1.1 for threshold)
✅ `field_validator` rejection tested with `pytest.raises(ValidationError)` and field name in error str
✅ Default values verified: `root_element="payload"`, `status="ok"`, `version="0.3.0"`, `translated_payload=None`
✅ Decision enum field: `isinstance(resp.decision, Decision)` AND `resp.decision == "GO"` (str enum)
✅ Empty-list validator: `ClassifyRequest(field_names=[])` raises, non-empty list passes
✅ Whitespace-only payload raises; surrounding-whitespace payload is accepted (strip check only)
✅ Nested model construction: `RegistryResponse.fields` accepts `dict[str, RegistryFieldInfo]`
✅ `ge=0` boundary for counter fields: 0 accepted, -1 raises

**Decision enum gotcha:** `Decision` is `class Decision(str, Enum)`.
`Decision.GO == "GO"` is True. `isinstance(Decision.GO, Decision)` is True.
Both assertions are worth writing to document both facts.

**_base_response helper pattern:** For schemas with many required fields, define a `_base_response`
helper method that returns a minimal valid kwargs dict with `**overrides` support. Keeps individual
tests short and focused on the one field being tested.

**Import path:** `from backend.api.schemas import TransformRequestSchema, ...` (not `TransformRequest`).

---

**FastAPI endpoint checklist (main.py — Task 3.08 pattern):**

For FastAPI routes tested with `TestClient` (no real LangGraph pipeline):
✅ `client = TestClient(app)` at module level — shared across all test classes
✅ Mock target for build_graph: `patch("backend.api.main.build_graph", return_value=_mock_graph(result))`
✅ `_mock_graph(result)` helper returns a `MagicMock` with `.invoke.return_value = result`
✅ GO result dict and HOLD result dict defined as module-level constants
✅ /health, /registry, /classify — no mock needed (real registry loaded from registry.json)
✅ /transform invalid source_format → 422 (Pydantic validator fires before pipeline)
✅ /transform empty/whitespace payload → 422 (Pydantic validator fires before pipeline)
✅ HOLD response: `translated_payload` must be None in the JSON body
✅ confidence_scores range: assert 0.0 <= score <= 1.0 for every entry
✅ processing_time_ms: assert >= 0
✅ /registry/analyse and /registry/export → 501 with "Phase 4" in detail

**Mock result dict structure** (must match what the real orchestrator writes to state):
```python
{
    "decision": "GO",               # str — Decision enum serialises to str in JSON
    "decision_reason": "...",
    "payload_tier": 3,
    "translated_payload": '{"id": "E-123"}',   # None for HOLD
    "confidence_scores": {"employee_id": 0.95},
    "validation_result": {"anomaly_count": 0},
    "audit_log": [],
}
```

**venv path reminder:** `source backend/venv/bin/activate` (NOT `venv/bin/activate`).

---

**Multi-registry support checklist (Task 3.20/4.01 pattern):**

For RegistryNotFoundError (exceptions.py):
✅ isinstance check against NexBridgeError (inheritance)
✅ raise-able as a standard exception
✅ registry_id attribute stored correctly
✅ available attribute stored (including empty list)
✅ __str__ includes registry_id and each available item
✅ __str__ shows "(none)" marker when available=[]
✅ default message includes registry_id
✅ custom message override is stored in .message

For ClassificationRegistry.load() classmethod:
✅ No REGISTRY_DIR → returns working ClassificationRegistry (same as ClassificationRegistry())
✅ No REGISTRY_DIR → isinstance ClassificationRegistry, classifies known T1 fields
✅ No REGISTRY_DIR → load(None) behaves identically to load()
✅ REGISTRY_DIR + file exists → loads domain/version from that file
✅ REGISTRY_DIR + file exists → classifies custom fields correctly
✅ REGISTRY_DIR → load("default") reads default.json
✅ REGISTRY_DIR → load(None) treats None as "default" and reads default.json
✅ REGISTRY_DIR + file missing → raises RegistryNotFoundError
✅ RegistryNotFoundError.registry_id == requested id
✅ RegistryNotFoundError.available lists existing files (not the missing one)
✅ empty REGISTRY_DIR → available == ["default"] (list_available_registries fallback)
✅ load(None) with no default.json → RegistryNotFoundError with registry_id="default"

For list_available_registries():
✅ No REGISTRY_DIR → returns ["default"]
✅ No REGISTRY_DIR → return type is list[str]
✅ REGISTRY_DIR with default.json + hr.json → ["default", "hr"] sorted
✅ Multiple files → sorted alphabetically
✅ Non-JSON files excluded from results
✅ .json extension stripped from IDs
✅ Empty REGISTRY_DIR → ["default"]
✅ Non-existent REGISTRY_DIR path → ["default"]

For RegistriesResponse schema:
✅ Constructs with list and count
✅ Empty list + count=0 accepted (ge=0 boundary)
✅ registries is list[str], count is int
✅ count=-1 raises ValidationError
✅ Missing registries or count fields raise ValidationError

For registry_id field on TransformRequestSchema and ClassifyRequest:
✅ Defaults to "default" when omitted
✅ Accepts "default", "hr", any string
✅ Existing validators still fire (source_format, field_names empty-list check)

For GET /registries endpoint:
✅ Returns 200
✅ Body has registries (list[str]) and count (int)
✅ count == len(registries)
✅ count >= 0
✅ Without REGISTRY_DIR → "default" in registries
✅ With REGISTRY_DIR containing files → lists those IDs, count matches
✅ With empty REGISTRY_DIR → ["default"], count=1

For GET /registry backward compat:
✅ No param → 200
✅ ?registry_id=default → 200, same body as no param
✅ Response has version, domain, field_count == len(fields)
✅ Unknown ID with REGISTRY_DIR set → 404, detail mentions registry_id
✅ Valid custom ID with file present → 200, correct domain/version

**monkeypatch patterns for env vars:**
- `monkeypatch.delenv("REGISTRY_DIR", raising=False)` to ensure env is unset
- `monkeypatch.setenv("REGISTRY_DIR", str(tmp_path))` to set a temp dir
- Always unset both REGISTRY_DIR and REGISTRY_PATH when testing no-env path

**_make_registry_json / _write_registry helpers:**
Define these module-level helpers in the test file for creating minimal valid
registry JSON files in tmp_path. Keeps test bodies short and focused.

---

**AuditAgent-specific checklist (audit.py — Task 3.09 pattern):**

For audit_node (no LLM dependency — pure Python state transformation):
✅ Single field in interpreter_run_1 → exactly one AuditEntry in audit_log
✅ Three fields → three AuditEntry objects, each isinstance-checked
✅ AuditEntry.field_name == source key from interpreter_run_1
✅ AuditEntry.agent == "audit" (hardcoded string, always)
✅ AuditEntry.decision matches state["decision"] — parametrize over GO/HOLD/ESCALATE
✅ AuditEntry.original_value == parsed_fields[field_name]
✅ AuditEntry.transformed_value == mapping["transformed_value"]
✅ AuditEntry.reasoning == mapping["reasoning"]
✅ AuditEntry.confidence == confidence_scores[field_name]
✅ AuditEntry.tier extracted via _get_tier_value from field_classifications
✅ confidence is None when field absent from confidence_scores
✅ original_value is "" when field absent from parsed_fields
✅ tier defaults to 4 when field absent from field_classifications
✅ Existing audit_log entries are preserved; first entry is `is prior_entry`
✅ Empty interpreter_run_1 → no new entries, existing log intact
✅ AuditEntry frozen: setting attribute raises TypeError or ValidationError
✅ timestamp is non-empty str
✅ Returned audit_log is a NEW list (`is not original_log`); original unchanged
✅ capsys: "[AUDIT] Written 2 audit entries decision=GO" for two-field run
✅ capsys: "[AUDIT] Written 0 audit entries decision=HOLD" for empty run_1

**_get_mapping_attr checklist:**
✅ Returns value from plain dict (test all three keys)
✅ Returns value from SimpleNamespace object (hasattr path)
✅ Raises KeyError for missing key on a plain dict

**_get_tier_value checklist:**
✅ Returns tier.value from SimpleNamespace(tier=SimpleNamespace(value=N)) — FieldClassification-style
✅ Returns int from dict {"tier": 2}
✅ Returns int(1) from dict {"tier": 1} — boundary check

**State builder pattern for audit tests:**
Use a `_base_state(**overrides)` helper that initialises all NexBridgeState keys to safe defaults.
Pass a `_mapping(target_field, transformed_value, reasoning)` helper for clean plain-dict mappings.
No need to import FieldMapping — plain dicts are sufficient and cleaner for these tests.

**Immutability test pattern:**
```python
with pytest.raises((TypeError, ValidationError)):
    entry.field_name = "tampered"  # type: ignore[misc]
```
Accept both TypeError (Pydantic v2 frozen) and ValidationError to be forward-compatible.

---

**RegistryAnalyser-specific checklist (Task 4.02 pattern):**

For FieldAnalysisResult (Pydantic model with tier/confidence ranges):
✅ Valid construction with all fields
✅ suggested_tier accepts 1, 2, 3, 4 (parametrize)
✅ suggested_tier=0 raises ValidationError with "suggested_tier" in error str
✅ suggested_tier=5 raises ValidationError with "suggested_tier" in error str
✅ confidence=0.0 and confidence=1.0 boundary accepted
✅ confidence=-0.01 and confidence=1.01 raise ValidationError with "confidence" in error str
✅ model_dump() returns exactly {"field_name", "suggested_tier", "suggested_label", "reasoning", "confidence"}
✅ T1-tier (safety-critical) field constructs correctly

For BatchAnalysisResult:
✅ Single FieldAnalysisResult in fields
✅ Multiple FieldAnalysisResult objects
✅ Empty fields list is valid (not a required-non-empty list)
✅ fields attribute is a list
✅ All items are FieldAnalysisResult instances

For analyse_fields():
✅ Returns list of plain dicts (model_dump output)
✅ Each dict has exactly the five required keys
✅ Multiple fields → correct count returned
✅ Values in result match what mock LLM returned
✅ source_format='json' accepted
✅ context kwarg accepted
✅ Empty field_names list → returns []
✅ context='' → prompt contains "general enterprise integration" (check via call_args[0][0] ChatPromptValue)
✅ Explicit context → prompt contains that value, NOT the default
✅ get_llm() called exactly once per invocation
✅ with_structured_output called with BatchAnalysisResult class
✅ Tier count log line matches returned results (capsys)
✅ Empty input logs T1=0 T2=0 T3=0 T4=0 (capsys)
✅ Log line shows "[REGISTRY_ANALYSER] Analysing N fields" (capsys)
✅ Any exception from get_llm → NexBridgeError raised
✅ NexBridgeError.message starts with "Registry analysis failed:"
✅ Exception from structured_llm call → NexBridgeError with same prefix

For POST /registry/analyse:
✅ Valid XML → 200, non-empty fields list
✅ field_count == len(fields) invariant
✅ source_format echoed back in response
✅ Valid JSON payload → 200
✅ source_format='json' echoed back
✅ field_count=0 when LLM returns no fields
✅ field_count == len(fields) invariant for 1, 2, 3 field counts
✅ context field accepted in request body (no 422)
✅ Malformed XML → 400
✅ Malformed XML detail is non-empty string
✅ NexBridgeError from analyse_fields → 500
✅ 500 detail contains "Registry analysis failed"
✅ source_format defaults to "xml" when omitted
✅ confidence values in [0.0, 1.0] for all fields
✅ suggested_tier values in [1, 4] for all fields

**Mock helpers pattern for registry_analyser tests:**
Define `_make_field_analysis_result(**overrides)` and `_mock_llm(batch_result)` at module level.
The _mock_llm helper sets `mock_structured_llm.return_value` (not `.invoke.return_value`).
See [[LLM Mocking Pattern for InterpreterAgent and RegistryAnalyser]] for full explanation.
