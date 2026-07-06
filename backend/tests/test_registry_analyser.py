"""
Tests for registry_analyser.py (Task 4.02).

Covers:
  - FieldAnalysisResult  — Pydantic model constraints (tier, confidence ranges)
  - BatchAnalysisResult  — Pydantic model (list of FieldAnalysisResult, empty list)
  - analyse_fields()     — LLM-backed batch analysis with full mock isolation
  - POST /registry/analyse — FastAPI endpoint contract (200, 400, 500)

Mock strategy
-------------
The LangChain chain is built as ``_PROMPT | structured_llm`` where
``structured_llm = llm.with_structured_output(BatchAnalysisResult)``.
LangChain wraps the structured LLM in a RunnableLambda that **calls** it
directly (``structured_llm(messages)``), so the correct mock hook is
``mock_structured_llm.return_value = <BatchAnalysisResult>``,
NOT ``.invoke.return_value``.

Patch target: ``backend.core.agents.registry_analyser.get_llm``
"""

import pytest
from unittest.mock import MagicMock, patch, call
from pydantic import ValidationError
from fastapi.testclient import TestClient

from backend.core.agents.registry_analyser import (
    FieldAnalysisResult,
    BatchAnalysisResult,
    analyse_fields,
)
from backend.core.exceptions import NexBridgeError
from backend.api.main import app


# ── Module-level TestClient ────────────────────────────────────────────────────

client = TestClient(app)


# ── Shared helpers ─────────────────────────────────────────────────────────────

def _make_field_analysis_result(
    field_name: str = "employee_id",
    suggested_tier: int = 3,
    suggested_label: str = "Business Important",
    reasoning: str = "Employee IDs are correctable business identifiers.",
    confidence: float = 0.92,
) -> FieldAnalysisResult:
    """Return a valid FieldAnalysisResult with sensible defaults."""
    return FieldAnalysisResult(
        field_name=field_name,
        suggested_tier=suggested_tier,
        suggested_label=suggested_label,
        reasoning=reasoning,
        confidence=confidence,
    )


def _mock_llm(batch_result: BatchAnalysisResult) -> MagicMock:
    """
    Build a mock LLM whose chain.invoke() returns *batch_result*.

    The LangChain RunnableLambda calls ``structured_llm(messages)``
    so we set ``mock_structured_llm.return_value``.
    """
    mock_llm = MagicMock()
    mock_structured_llm = MagicMock()
    mock_structured_llm.return_value = batch_result
    mock_llm.with_structured_output.return_value = mock_structured_llm
    return mock_llm


# =============================================================================
# TestFieldAnalysisResult
# =============================================================================

class TestFieldAnalysisResult:
    """Pydantic model constraints for FieldAnalysisResult."""

    def test_valid_construction_all_fields(self):
        """Valid FieldAnalysisResult with all required fields constructs without error."""
        far = FieldAnalysisResult(
            field_name="weight_limit",
            suggested_tier=1,
            suggested_label="Safety Critical",
            reasoning="Weight limits can cause physical harm if wrong.",
            confidence=0.98,
        )
        assert far.field_name == "weight_limit"
        assert far.suggested_tier == 1
        assert far.suggested_label == "Safety Critical"
        assert far.reasoning == "Weight limits can cause physical harm if wrong."
        assert far.confidence == 0.98

    # --- suggested_tier boundary tests ---

    @pytest.mark.parametrize("tier", [1, 2, 3, 4])
    def test_suggested_tier_valid_range(self, tier: int):
        """suggested_tier accepts every value in the valid range 1–4."""
        far = _make_field_analysis_result(suggested_tier=tier)
        assert far.suggested_tier == tier

    def test_suggested_tier_minimum_boundary(self):
        """suggested_tier=1 (minimum) is accepted."""
        far = _make_field_analysis_result(suggested_tier=1)
        assert far.suggested_tier == 1

    def test_suggested_tier_maximum_boundary(self):
        """suggested_tier=4 (maximum) is accepted."""
        far = _make_field_analysis_result(suggested_tier=4)
        assert far.suggested_tier == 4

    def test_suggested_tier_below_minimum_raises(self):
        """suggested_tier=0 (below minimum) must raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            _make_field_analysis_result(suggested_tier=0)
        assert "suggested_tier" in str(exc_info.value)

    def test_suggested_tier_above_maximum_raises(self):
        """suggested_tier=5 (above maximum) must raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            _make_field_analysis_result(suggested_tier=5)
        assert "suggested_tier" in str(exc_info.value)

    def test_suggested_tier_negative_raises(self):
        """A negative suggested_tier must raise ValidationError."""
        with pytest.raises(ValidationError):
            _make_field_analysis_result(suggested_tier=-1)

    # --- confidence boundary tests ---

    def test_confidence_minimum_boundary(self):
        """confidence=0.0 (minimum) is accepted."""
        far = _make_field_analysis_result(confidence=0.0)
        assert far.confidence == 0.0

    def test_confidence_maximum_boundary(self):
        """confidence=1.0 (maximum) is accepted."""
        far = _make_field_analysis_result(confidence=1.0)
        assert far.confidence == 1.0

    @pytest.mark.parametrize("confidence", [0.0, 0.5, 0.95, 1.0])
    def test_confidence_valid_range(self, confidence: float):
        """confidence accepts values throughout [0.0, 1.0]."""
        far = _make_field_analysis_result(confidence=confidence)
        assert far.confidence == confidence

    def test_confidence_below_minimum_raises(self):
        """confidence=-0.01 (below minimum) must raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            _make_field_analysis_result(confidence=-0.01)
        assert "confidence" in str(exc_info.value)

    def test_confidence_above_maximum_raises(self):
        """confidence=1.01 (above maximum) must raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            _make_field_analysis_result(confidence=1.01)
        assert "confidence" in str(exc_info.value)

    def test_confidence_large_over_range_raises(self):
        """confidence=1.5 must raise ValidationError."""
        with pytest.raises(ValidationError):
            _make_field_analysis_result(confidence=1.5)

    def test_model_dump_contains_all_keys(self):
        """model_dump() must return all five required keys."""
        far = _make_field_analysis_result()
        dumped = far.model_dump()
        assert set(dumped.keys()) == {
            "field_name",
            "suggested_tier",
            "suggested_label",
            "reasoning",
            "confidence",
        }

    def test_all_tier_labels_accepted(self):
        """Any non-empty string is accepted as suggested_label."""
        for label in ["Safety Critical", "Operationally Sensitive", "Business Important", "Informational"]:
            far = _make_field_analysis_result(suggested_label=label)
            assert far.suggested_label == label

    def test_t1_tier_field_construction(self):
        """A T1-tier FieldAnalysisResult (safety-critical) constructs correctly."""
        far = FieldAnalysisResult(
            field_name="fuel_load",
            suggested_tier=1,
            suggested_label="Safety Critical",
            reasoning="Fuel load errors could cause catastrophic safety failures.",
            confidence=0.99,
        )
        assert far.suggested_tier == 1
        assert far.confidence == 0.99


# =============================================================================
# TestBatchAnalysisResult
# =============================================================================

class TestBatchAnalysisResult:
    """Pydantic model constraints for BatchAnalysisResult."""

    def test_valid_construction_with_single_field(self):
        """BatchAnalysisResult with one FieldAnalysisResult constructs correctly."""
        far = _make_field_analysis_result()
        batch = BatchAnalysisResult(fields=[far])
        assert len(batch.fields) == 1
        assert batch.fields[0].field_name == "employee_id"

    def test_valid_construction_with_multiple_fields(self):
        """BatchAnalysisResult with three FieldAnalysisResult objects is valid."""
        batch = BatchAnalysisResult(fields=[
            _make_field_analysis_result("employee_id", suggested_tier=3),
            _make_field_analysis_result("weight_limit", suggested_tier=1, suggested_label="Safety Critical", confidence=0.98),
            _make_field_analysis_result("department", suggested_tier=3),
        ])
        assert len(batch.fields) == 3

    def test_empty_fields_list_is_valid(self):
        """BatchAnalysisResult with an empty fields list is valid (no fields to analyse)."""
        batch = BatchAnalysisResult(fields=[])
        assert batch.fields == []
        assert len(batch.fields) == 0

    def test_fields_attribute_is_list(self):
        """The fields attribute must be a list type."""
        batch = BatchAnalysisResult(fields=[])
        assert isinstance(batch.fields, list)

    def test_each_field_is_field_analysis_result(self):
        """Every item in fields must be a FieldAnalysisResult instance."""
        batch = BatchAnalysisResult(fields=[
            _make_field_analysis_result("x"),
            _make_field_analysis_result("y"),
        ])
        for item in batch.fields:
            assert isinstance(item, FieldAnalysisResult)

    def test_batch_with_all_four_tiers(self):
        """BatchAnalysisResult can hold fields from all four tiers simultaneously."""
        batch = BatchAnalysisResult(fields=[
            _make_field_analysis_result("weight_limit", suggested_tier=1, suggested_label="Safety Critical"),
            _make_field_analysis_result("contract_type", suggested_tier=2, suggested_label="Operationally Sensitive"),
            _make_field_analysis_result("employee_id", suggested_tier=3, suggested_label="Business Important"),
            _make_field_analysis_result("notes", suggested_tier=4, suggested_label="Informational"),
        ])
        tiers = [f.suggested_tier for f in batch.fields]
        assert tiers == [1, 2, 3, 4]


# =============================================================================
# TestAnalyseFields
# =============================================================================

class TestAnalyseFields:
    """
    Tests for the analyse_fields() public function.

    All tests mock get_llm to prevent real API calls.
    The mock pattern uses mock_structured_llm.return_value (not .invoke.return_value)
    because the RunnableLambda in the LangChain pipeline calls the structured LLM
    directly rather than via .invoke().
    """

    # --- Happy path ---

    def test_analyse_fields_returns_list_of_dicts(self):
        """analyse_fields returns a plain list of dicts (not Pydantic objects)."""
        mock_result = BatchAnalysisResult(fields=[_make_field_analysis_result()])
        with patch("backend.core.agents.registry_analyser.get_llm", return_value=_mock_llm(mock_result)):
            result = analyse_fields(["employee_id"], source_format="xml")
        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], dict)

    def test_analyse_fields_single_field_returns_all_keys(self):
        """Each dict in the result must contain all five required keys."""
        mock_result = BatchAnalysisResult(fields=[_make_field_analysis_result("employee_id")])
        with patch("backend.core.agents.registry_analyser.get_llm", return_value=_mock_llm(mock_result)):
            result = analyse_fields(["employee_id"], source_format="xml")
        assert result[0].keys() == {"field_name", "suggested_tier", "suggested_label", "reasoning", "confidence"}

    def test_analyse_fields_multiple_fields_correct_count(self):
        """analyse_fields with three field names returns three result dicts."""
        mock_result = BatchAnalysisResult(fields=[
            _make_field_analysis_result("employee_id", suggested_tier=3),
            _make_field_analysis_result("weight_limit", suggested_tier=1, suggested_label="Safety Critical"),
            _make_field_analysis_result("department", suggested_tier=3),
        ])
        with patch("backend.core.agents.registry_analyser.get_llm", return_value=_mock_llm(mock_result)):
            result = analyse_fields(
                ["employee_id", "weight_limit", "department"],
                source_format="xml",
            )
        assert len(result) == 3

    def test_analyse_fields_result_values_match_mock(self):
        """The returned dict values must exactly match what the mock LLM returned."""
        mock_result = BatchAnalysisResult(fields=[
            FieldAnalysisResult(
                field_name="fuel_load",
                suggested_tier=1,
                suggested_label="Safety Critical",
                reasoning="Fuel load errors risk catastrophic failure.",
                confidence=0.97,
            )
        ])
        with patch("backend.core.agents.registry_analyser.get_llm", return_value=_mock_llm(mock_result)):
            result = analyse_fields(["fuel_load"], source_format="xml")
        assert result[0]["field_name"] == "fuel_load"
        assert result[0]["suggested_tier"] == 1
        assert result[0]["suggested_label"] == "Safety Critical"
        assert result[0]["reasoning"] == "Fuel load errors risk catastrophic failure."
        assert result[0]["confidence"] == 0.97

    def test_analyse_fields_json_source_format(self):
        """analyse_fields accepts source_format='json' without error."""
        mock_result = BatchAnalysisResult(fields=[_make_field_analysis_result("id")])
        with patch("backend.core.agents.registry_analyser.get_llm", return_value=_mock_llm(mock_result)):
            result = analyse_fields(["id"], source_format="json")
        assert len(result) == 1

    def test_analyse_fields_with_context_provided(self):
        """analyse_fields accepts a non-empty context string without error."""
        mock_result = BatchAnalysisResult(fields=[_make_field_analysis_result()])
        with patch("backend.core.agents.registry_analyser.get_llm", return_value=_mock_llm(mock_result)):
            result = analyse_fields(
                ["employee_id"],
                source_format="xml",
                context="aviation",
            )
        assert len(result) == 1

    # --- Empty input ---

    def test_analyse_fields_empty_list_returns_empty_list(self):
        """analyse_fields with an empty field_names list returns an empty list."""
        mock_result = BatchAnalysisResult(fields=[])
        with patch("backend.core.agents.registry_analyser.get_llm", return_value=_mock_llm(mock_result)):
            result = analyse_fields([], source_format="xml")
        assert result == []

    # --- context="" uses default prompt text ---

    def test_analyse_fields_empty_context_uses_default_prompt_text(self):
        """
        When context='', the prompt must include 'general enterprise integration'
        (the default context string). Verified by inspecting the args passed
        to the mock structured LLM.
        """
        mock_result = BatchAnalysisResult(fields=[])
        mock_llm_instance = MagicMock()
        mock_structured_llm = MagicMock()
        mock_structured_llm.return_value = mock_result
        mock_llm_instance.with_structured_output.return_value = mock_structured_llm

        with patch(
            "backend.core.agents.registry_analyser.get_llm",
            return_value=mock_llm_instance,
        ):
            analyse_fields([], source_format="xml", context="")

        # Inspect the ChatPromptValue passed to the structured LLM call
        call_args = mock_structured_llm.call_args
        assert call_args is not None, "mock_structured_llm was not called"
        prompt_value = call_args[0][0]
        rendered = str(prompt_value)
        assert "general enterprise integration" in rendered, (
            "Expected 'general enterprise integration' in prompt when context='', "
            f"got prompt: {rendered[:200]}"
        )

    def test_analyse_fields_explicit_context_not_replaced(self):
        """When context is non-empty the original value is used (not the default)."""
        mock_result = BatchAnalysisResult(fields=[])
        mock_llm_instance = MagicMock()
        mock_structured_llm = MagicMock()
        mock_structured_llm.return_value = mock_result
        mock_llm_instance.with_structured_output.return_value = mock_structured_llm

        with patch(
            "backend.core.agents.registry_analyser.get_llm",
            return_value=mock_llm_instance,
        ):
            analyse_fields([], source_format="xml", context="healthcare")

        call_args = mock_structured_llm.call_args
        prompt_value = call_args[0][0]
        rendered = str(prompt_value)
        assert "healthcare" in rendered
        assert "general enterprise integration" not in rendered

    # --- get_llm is called exactly once ---

    def test_analyse_fields_calls_get_llm_once(self):
        """get_llm must be called exactly once per analyse_fields invocation."""
        mock_result = BatchAnalysisResult(fields=[])
        mock_llm_instance = _mock_llm(mock_result)

        with patch(
            "backend.core.agents.registry_analyser.get_llm",
            return_value=mock_llm_instance,
        ) as mock_get_llm:
            analyse_fields([], source_format="xml")

        mock_get_llm.assert_called_once()

    # --- with_structured_output is called with the correct model ---

    def test_analyse_fields_uses_batch_analysis_result_schema(self):
        """get_llm().with_structured_output must be called with BatchAnalysisResult."""
        mock_result = BatchAnalysisResult(fields=[])
        mock_llm_instance = MagicMock()
        mock_structured_llm = MagicMock()
        mock_structured_llm.return_value = mock_result
        mock_llm_instance.with_structured_output.return_value = mock_structured_llm

        with patch(
            "backend.core.agents.registry_analyser.get_llm",
            return_value=mock_llm_instance,
        ):
            analyse_fields(["x"], source_format="xml")

        mock_llm_instance.with_structured_output.assert_called_once_with(BatchAnalysisResult)

    # --- Tier log counts match returned results ---

    def test_analyse_fields_tier_counts_match_returned_results(self, capsys):
        """
        The [REGISTRY_ANALYSER] log line must show tier counts that
        exactly match the fields returned by the mock LLM.
        """
        mock_result = BatchAnalysisResult(fields=[
            _make_field_analysis_result("weight_limit", suggested_tier=1, suggested_label="Safety Critical"),
            _make_field_analysis_result("contract_type", suggested_tier=2, suggested_label="Operationally Sensitive"),
            _make_field_analysis_result("employee_id", suggested_tier=3),
            _make_field_analysis_result("notes", suggested_tier=4, suggested_label="Informational"),
        ])
        with patch("backend.core.agents.registry_analyser.get_llm", return_value=_mock_llm(mock_result)):
            analyse_fields(
                ["weight_limit", "contract_type", "employee_id", "notes"],
                source_format="xml",
            )
        captured = capsys.readouterr()
        assert "T1=1" in captured.out
        assert "T2=1" in captured.out
        assert "T3=1" in captured.out
        assert "T4=1" in captured.out

    def test_analyse_fields_empty_list_logs_zero_tier_counts(self, capsys):
        """Empty input must log T1=0 T2=0 T3=0 T4=0."""
        mock_result = BatchAnalysisResult(fields=[])
        with patch("backend.core.agents.registry_analyser.get_llm", return_value=_mock_llm(mock_result)):
            analyse_fields([], source_format="xml")
        captured = capsys.readouterr()
        assert "T1=0" in captured.out
        assert "T2=0" in captured.out
        assert "T3=0" in captured.out
        assert "T4=0" in captured.out

    def test_analyse_fields_logs_field_count(self, capsys):
        """The initial log line must include the count of field_names passed in."""
        mock_result = BatchAnalysisResult(fields=[
            _make_field_analysis_result("a"),
            _make_field_analysis_result("b"),
        ])
        with patch("backend.core.agents.registry_analyser.get_llm", return_value=_mock_llm(mock_result)):
            analyse_fields(["a", "b"], source_format="xml")
        captured = capsys.readouterr()
        assert "[REGISTRY_ANALYSER] Analysing 2 fields" in captured.out

    # --- Error handling ---

    def test_analyse_fields_llm_exception_raises_nexbridge_error(self):
        """
        If get_llm() raises an exception analyse_fields must re-raise it
        as a NexBridgeError (not the original exception type).
        """
        mock_llm_instance = MagicMock()
        mock_llm_instance.with_structured_output.side_effect = RuntimeError("API timeout")

        with pytest.raises(NexBridgeError):
            with patch(
                "backend.core.agents.registry_analyser.get_llm",
                return_value=mock_llm_instance,
            ):
                analyse_fields(["x"], source_format="xml")

    def test_analyse_fields_llm_exception_message_prefix(self):
        """
        The NexBridgeError message must start with 'Registry analysis failed:'
        so callers can identify the error origin.
        """
        mock_llm_instance = MagicMock()
        mock_llm_instance.with_structured_output.side_effect = RuntimeError("timeout")

        with pytest.raises(NexBridgeError) as exc_info:
            with patch(
                "backend.core.agents.registry_analyser.get_llm",
                return_value=mock_llm_instance,
            ):
                analyse_fields(["x"], source_format="xml")

        assert exc_info.value.message.startswith("Registry analysis failed:")

    def test_analyse_fields_structured_llm_call_exception_raises_nexbridge_error(self):
        """
        If the structured LLM chain invocation raises an exception it must be
        wrapped in NexBridgeError with the 'Registry analysis failed:' prefix.
        """
        mock_llm_instance = MagicMock()
        mock_structured_llm = MagicMock()
        mock_structured_llm.side_effect = ValueError("Invalid structured output")
        mock_llm_instance.with_structured_output.return_value = mock_structured_llm

        with pytest.raises(NexBridgeError) as exc_info:
            with patch(
                "backend.core.agents.registry_analyser.get_llm",
                return_value=mock_llm_instance,
            ):
                analyse_fields(["x"], source_format="xml")

        assert exc_info.value.message.startswith("Registry analysis failed:")

    def test_analyse_fields_nexbridge_error_is_nexbridge_error_subclass(self):
        """The raised exception must be NexBridgeError or a subclass."""
        mock_llm_instance = MagicMock()
        mock_llm_instance.with_structured_output.side_effect = RuntimeError("error")

        with pytest.raises(NexBridgeError):
            with patch(
                "backend.core.agents.registry_analyser.get_llm",
                return_value=mock_llm_instance,
            ):
                analyse_fields(["x"], source_format="xml")


# =============================================================================
# TestAnalyseEndpoint
# =============================================================================

class TestAnalyseEndpoint:
    """
    Tests for POST /registry/analyse.

    Mocks analyse_fields() directly (via backend.api.main.analyse_fields)
    or mocks get_llm at the source (backend.core.agents.registry_analyser.get_llm).

    The two approaches are mixed: LLM-level mocking is used for happy-path
    tests (to exercise the real endpoint + agent code path); function-level
    mocking is used for error-injection scenarios.
    """

    # ── Shared test data ──────────────────────────────────────────────────────

    _XML_PAYLOAD = "<record><employee_id>E-123</employee_id><department>Ops</department></record>"
    _JSON_PAYLOAD = '{"employee_id": "E-123", "department": "Ops"}'
    _MALFORMED_XML = "<unclosed_tag"

    _MOCK_LLM_RESULT_TWO_FIELDS = BatchAnalysisResult(fields=[
        FieldAnalysisResult(
            field_name="employee_id",
            suggested_tier=3,
            suggested_label="Business Important",
            reasoning="Employee IDs are correctable.",
            confidence=0.92,
        ),
        FieldAnalysisResult(
            field_name="department",
            suggested_tier=3,
            suggested_label="Business Important",
            reasoning="Department is correctable context.",
            confidence=0.90,
        ),
    ])

    # ── Happy path — XML ──────────────────────────────────────────────────────

    def test_analyse_valid_xml_returns_200(self):
        """A valid XML payload must return HTTP 200."""
        with patch(
            "backend.core.agents.registry_analyser.get_llm",
            return_value=_mock_llm(self._MOCK_LLM_RESULT_TWO_FIELDS),
        ):
            response = client.post(
                "/registry/analyse",
                json={"payload": self._XML_PAYLOAD, "source_format": "xml"},
            )
        assert response.status_code == 200

    def test_analyse_valid_xml_response_has_fields(self):
        """Response body must contain a non-empty 'fields' list for a non-trivial payload."""
        with patch(
            "backend.core.agents.registry_analyser.get_llm",
            return_value=_mock_llm(self._MOCK_LLM_RESULT_TWO_FIELDS),
        ):
            response = client.post(
                "/registry/analyse",
                json={"payload": self._XML_PAYLOAD, "source_format": "xml"},
            )
        data = response.json()
        assert "fields" in data
        assert len(data["fields"]) == 2

    def test_analyse_valid_xml_field_count_matches_fields_len(self):
        """'field_count' in the response must equal len(fields)."""
        with patch(
            "backend.core.agents.registry_analyser.get_llm",
            return_value=_mock_llm(self._MOCK_LLM_RESULT_TWO_FIELDS),
        ):
            response = client.post(
                "/registry/analyse",
                json={"payload": self._XML_PAYLOAD, "source_format": "xml"},
            )
        data = response.json()
        assert data["field_count"] == len(data["fields"])

    def test_analyse_valid_xml_source_format_echoed(self):
        """'source_format' in the response must match the value sent in the request."""
        with patch(
            "backend.core.agents.registry_analyser.get_llm",
            return_value=_mock_llm(self._MOCK_LLM_RESULT_TWO_FIELDS),
        ):
            response = client.post(
                "/registry/analyse",
                json={"payload": self._XML_PAYLOAD, "source_format": "xml"},
            )
        assert response.json()["source_format"] == "xml"

    def test_analyse_each_field_has_required_keys(self):
        """Every item in the 'fields' list must contain all five required keys."""
        with patch(
            "backend.core.agents.registry_analyser.get_llm",
            return_value=_mock_llm(self._MOCK_LLM_RESULT_TWO_FIELDS),
        ):
            response = client.post(
                "/registry/analyse",
                json={"payload": self._XML_PAYLOAD, "source_format": "xml"},
            )
        for field in response.json()["fields"]:
            assert set(field.keys()) >= {
                "field_name",
                "suggested_tier",
                "suggested_label",
                "reasoning",
                "confidence",
            }, f"Field entry missing required keys: {field}"

    # ── Happy path — JSON ─────────────────────────────────────────────────────

    def test_analyse_valid_json_payload_returns_200(self):
        """A valid JSON payload with source_format='json' must return HTTP 200."""
        mock_result = BatchAnalysisResult(fields=[
            FieldAnalysisResult(
                field_name="employee_id",
                suggested_tier=3,
                suggested_label="Business Important",
                reasoning="Correctable identifier.",
                confidence=0.91,
            )
        ])
        with patch(
            "backend.core.agents.registry_analyser.get_llm",
            return_value=_mock_llm(mock_result),
        ):
            response = client.post(
                "/registry/analyse",
                json={"payload": self._JSON_PAYLOAD, "source_format": "json"},
            )
        assert response.status_code == 200

    def test_analyse_valid_json_source_format_echoed(self):
        """'source_format' must be 'json' when a JSON payload is submitted."""
        mock_result = BatchAnalysisResult(fields=[
            FieldAnalysisResult(
                field_name="employee_id",
                suggested_tier=3,
                suggested_label="Business Important",
                reasoning="Correctable identifier.",
                confidence=0.91,
            )
        ])
        with patch(
            "backend.core.agents.registry_analyser.get_llm",
            return_value=_mock_llm(mock_result),
        ):
            response = client.post(
                "/registry/analyse",
                json={"payload": self._JSON_PAYLOAD, "source_format": "json"},
            )
        assert response.json()["source_format"] == "json"

    # ── field_count integrity ─────────────────────────────────────────────────

    def test_analyse_field_count_is_zero_for_empty_result(self):
        """When the LLM returns no fields 'field_count' must be 0."""
        mock_result = BatchAnalysisResult(fields=[])
        # Use a payload with no child elements so the parser returns zero fields
        with patch(
            "backend.core.agents.registry_analyser.get_llm",
            return_value=_mock_llm(mock_result),
        ):
            response = client.post(
                "/registry/analyse",
                json={"payload": "<record/>", "source_format": "xml"},
            )
        assert response.status_code == 200
        data = response.json()
        assert data["field_count"] == 0
        assert data["fields"] == []

    def test_analyse_field_count_matches_len_fields_invariant(self):
        """field_count == len(fields) must hold for every valid response."""
        for field_count in [1, 2, 3]:
            mock_result = BatchAnalysisResult(fields=[
                _make_field_analysis_result(f"field_{i}") for i in range(field_count)
            ])
            payload = "<record>" + "".join(f"<field_{i}>v</field_{i}>" for i in range(field_count)) + "</record>"
            with patch(
                "backend.core.agents.registry_analyser.get_llm",
                return_value=_mock_llm(mock_result),
            ):
                response = client.post(
                    "/registry/analyse",
                    json={"payload": payload, "source_format": "xml"},
                )
            data = response.json()
            assert data["field_count"] == len(data["fields"]), (
                f"field_count={data['field_count']} != len(fields)={len(data['fields'])} "
                f"for {field_count}-field payload"
            )

    # ── context field ─────────────────────────────────────────────────────────

    def test_analyse_context_field_accepted_in_request(self):
        """
        A request body that includes 'context' must be accepted without
        validation error (context is an optional field on AnalyseRequest).
        """
        mock_result = BatchAnalysisResult(fields=[_make_field_analysis_result()])
        with patch(
            "backend.core.agents.registry_analyser.get_llm",
            return_value=_mock_llm(mock_result),
        ):
            response = client.post(
                "/registry/analyse",
                json={
                    "payload": self._XML_PAYLOAD,
                    "source_format": "xml",
                    "context": "aviation",
                },
            )
        assert response.status_code == 200

    # ── Error scenarios ───────────────────────────────────────────────────────

    def test_analyse_malformed_xml_returns_400(self):
        """Malformed XML in the payload must return HTTP 400."""
        response = client.post(
            "/registry/analyse",
            json={"payload": self._MALFORMED_XML, "source_format": "xml"},
        )
        assert response.status_code == 400

    def test_analyse_malformed_xml_detail_is_informative(self):
        """The 400 error detail for malformed XML must be non-empty."""
        response = client.post(
            "/registry/analyse",
            json={"payload": self._MALFORMED_XML, "source_format": "xml"},
        )
        detail = response.json().get("detail", "")
        assert isinstance(detail, str)
        assert len(detail) > 0

    def test_analyse_llm_failure_returns_500(self):
        """
        When analyse_fields raises a NexBridgeError the endpoint must
        return HTTP 500 (not 200, not 422, not 400).
        """
        with patch(
            "backend.api.main.analyse_fields",
            side_effect=NexBridgeError("Registry analysis failed: API timeout"),
        ):
            response = client.post(
                "/registry/analyse",
                json={"payload": self._XML_PAYLOAD, "source_format": "xml"},
            )
        assert response.status_code == 500

    def test_analyse_llm_failure_detail_echoes_message(self):
        """
        The 500 error detail must include the NexBridgeError message
        so callers can diagnose the failure.
        """
        with patch(
            "backend.api.main.analyse_fields",
            side_effect=NexBridgeError("Registry analysis failed: API timeout"),
        ):
            response = client.post(
                "/registry/analyse",
                json={"payload": self._XML_PAYLOAD, "source_format": "xml"},
            )
        detail = response.json()["detail"]
        assert "Registry analysis failed" in detail

    def test_analyse_source_format_default_is_xml(self):
        """
        When source_format is omitted from the request body the default
        must be 'xml' and the response must echo 'xml'.
        """
        mock_result = BatchAnalysisResult(fields=[_make_field_analysis_result()])
        with patch(
            "backend.core.agents.registry_analyser.get_llm",
            return_value=_mock_llm(mock_result),
        ):
            response = client.post(
                "/registry/analyse",
                json={"payload": self._XML_PAYLOAD},
            )
        assert response.status_code == 200
        assert response.json()["source_format"] == "xml"

    def test_analyse_confidence_values_in_valid_range(self):
        """
        Every confidence value returned in the 'fields' list must be
        in the range [0.0, 1.0].
        """
        mock_result = BatchAnalysisResult(fields=[
            _make_field_analysis_result("f1", confidence=0.0),
            _make_field_analysis_result("f2", confidence=0.5),
            _make_field_analysis_result("f3", confidence=1.0),
        ])
        payload = "<record><f1>a</f1><f2>b</f2><f3>c</f3></record>"
        with patch(
            "backend.core.agents.registry_analyser.get_llm",
            return_value=_mock_llm(mock_result),
        ):
            response = client.post(
                "/registry/analyse",
                json={"payload": payload, "source_format": "xml"},
            )
        for field in response.json()["fields"]:
            conf = field["confidence"]
            assert 0.0 <= conf <= 1.0, f"confidence={conf} out of range for field {field['field_name']}"

    def test_analyse_suggested_tier_values_in_valid_range(self):
        """
        Every suggested_tier value in the response must be in the range 1–4.
        """
        mock_result = BatchAnalysisResult(fields=[
            _make_field_analysis_result("weight_limit", suggested_tier=1, suggested_label="Safety Critical"),
            _make_field_analysis_result("notes", suggested_tier=4, suggested_label="Informational"),
        ])
        payload = "<record><weight_limit>250</weight_limit><notes>test</notes></record>"
        with patch(
            "backend.core.agents.registry_analyser.get_llm",
            return_value=_mock_llm(mock_result),
        ):
            response = client.post(
                "/registry/analyse",
                json={"payload": payload, "source_format": "xml"},
            )
        for field in response.json()["fields"]:
            assert 1 <= field["suggested_tier"] <= 4, (
                f"suggested_tier={field['suggested_tier']} out of range for {field['field_name']}"
            )
