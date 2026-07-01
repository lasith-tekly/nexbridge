"""
Tests for JsonTranslator (Task 3.00e)

JsonTranslator is a stdlib-only component that builds JSON strings from
interpreter FieldMapping results. It accepts either plain dicts or
Pydantic-style objects (accessed via getattr/key), applies type conversion
per the target_schema, and returns json.dumps output.

These tests validate:
- build() returns valid, parseable JSON for both dict and object mappings
- Correct key-value pairs are present in the JSON output
- Type conversion for "number"/"float", "integer"/"int", "boolean"/"bool", and unknown types
- Fallback to str when numeric conversion is not possible
- TranslationError raised on missing required mapping keys
- TranslationError raised when json.dumps fails (monkeypatched)
- Stdout logging for non-empty and empty field counts
- Package-level import and __all__ membership
"""

import json
import pytest
from types import SimpleNamespace

from backend.core.translators.json_translator import JsonTranslator
from backend.core.exceptions import TranslationError, NexBridgeError


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def translator() -> JsonTranslator:
    """Shared JsonTranslator instance for all tests."""
    return JsonTranslator()


@pytest.fixture
def two_dict_mappings() -> dict:
    """Two plain-dict field mappings for a standard GO scenario."""
    return {
        "employee_id": {"target_field": "id",        "transformed_value": "E-12345"},
        "department":  {"target_field": "dept_code", "transformed_value": "OPS"},
    }


@pytest.fixture
def two_object_mappings() -> dict:
    """Two SimpleNamespace field mappings (Pydantic-style attribute access)."""
    return {
        "employee_id": SimpleNamespace(target_field="id",        transformed_value="E-12345"),
        "department":  SimpleNamespace(target_field="dept_code", transformed_value="OPS"),
    }


@pytest.fixture
def two_field_schema() -> dict:
    """Target schema for the two-field GO scenario."""
    return {
        "id":        "string",
        "dept_code": "string",
    }


# ---------------------------------------------------------------------------
# TestJsonTranslatorBuild — build() method
# ---------------------------------------------------------------------------

class TestJsonTranslatorBuild:
    """Tests for JsonTranslator.build()."""

    # --- Basic return type and parseability ---

    def test_build_dict_mappings_returns_valid_json_string(
        self, translator, two_dict_mappings, two_field_schema
    ):
        """
        build() with plain-dict mappings must return a str that can be
        parsed by json.loads without raising any exception.
        """
        result = translator.build(two_dict_mappings, two_field_schema)

        assert isinstance(result, str)
        parsed = json.loads(result)  # must not raise
        assert isinstance(parsed, dict)

    def test_build_dict_mappings_produces_correct_key_value_pairs(
        self, translator, two_dict_mappings, two_field_schema
    ):
        """
        build() must produce JSON whose keys are the target_field values and
        whose values are the (type-converted) transformed_value values.
        """
        result = translator.build(two_dict_mappings, two_field_schema)
        parsed = json.loads(result)

        assert parsed["id"] == "E-12345"
        assert parsed["dept_code"] == "OPS"

    # --- SimpleNamespace (Pydantic-style) object mappings ---

    def test_build_object_mappings_works_correctly(
        self, translator, two_object_mappings, two_field_schema
    ):
        """
        build() must handle SimpleNamespace (attribute-access) mappings the
        same way as plain dicts. Output must parse to an identical structure.
        """
        result = translator.build(two_object_mappings, two_field_schema)
        parsed = json.loads(result)

        assert parsed["id"] == "E-12345"
        assert parsed["dept_code"] == "OPS"

    # --- Empty mappings ---

    def test_build_empty_field_mappings_returns_empty_json_object(
        self, translator
    ):
        """
        build() with an empty field_mappings dict must return the exact
        string '{}', which is the json.dumps representation of an empty dict.
        """
        result = translator.build({}, {})

        assert result == "{}"

    # --- Type conversion: number / float ---

    def test_build_number_type_converts_value_to_float(self, translator):
        """
        A target_schema type of "number" must coerce the transformed_value
        to a Python float in the resulting JSON.
        """
        mappings = {"weight_limit": {"target_field": "max_load", "transformed_value": "250"}}
        schema   = {"max_load": "number"}

        result = translator.build(mappings, schema)
        parsed = json.loads(result)

        assert isinstance(parsed["max_load"], float)
        assert parsed["max_load"] == 250.0

    def test_build_float_alias_type_converts_value_to_float(self, translator):
        """
        A target_schema type of "float" (alias for "number") must also produce
        a Python float in the JSON output.
        """
        mappings = {"price": {"target_field": "unit_price", "transformed_value": "9.99"}}
        schema   = {"unit_price": "float"}

        result = translator.build(mappings, schema)
        parsed = json.loads(result)

        assert isinstance(parsed["unit_price"], float)
        assert parsed["unit_price"] == 9.99

    # --- Type conversion: integer / int ---

    def test_build_integer_type_converts_value_to_int(self, translator):
        """
        A target_schema type of "integer" must coerce the transformed_value
        to a Python int in the resulting JSON.
        """
        mappings = {"head_count": {"target_field": "num_employees", "transformed_value": "42"}}
        schema   = {"num_employees": "integer"}

        result = translator.build(mappings, schema)
        parsed = json.loads(result)

        assert isinstance(parsed["num_employees"], int)
        assert parsed["num_employees"] == 42

    def test_build_int_alias_type_converts_value_to_int(self, translator):
        """
        A target_schema type of "int" (alias for "integer") must also produce
        a Python int in the JSON output.
        """
        mappings = {"qty": {"target_field": "quantity", "transformed_value": "7"}}
        schema   = {"quantity": "int"}

        result = translator.build(mappings, schema)
        parsed = json.loads(result)

        assert isinstance(parsed["quantity"], int)
        assert parsed["quantity"] == 7

    # --- Type conversion: boolean / bool ---

    def test_build_boolean_type_value_true_string_returns_true(self, translator):
        """
        A target_schema type of "boolean" with transformed_value "true"
        (lowercase) must produce Python True in the JSON output.
        """
        mappings = {"active": {"target_field": "is_active", "transformed_value": "true"}}
        schema   = {"is_active": "boolean"}

        result = translator.build(mappings, schema)
        parsed = json.loads(result)

        assert parsed["is_active"] is True

    def test_build_boolean_type_value_false_string_returns_false(self, translator):
        """
        A target_schema type of "boolean" with transformed_value "false"
        must produce Python False in the JSON output.
        """
        mappings = {"active": {"target_field": "is_active", "transformed_value": "false"}}
        schema   = {"is_active": "boolean"}

        result = translator.build(mappings, schema)
        parsed = json.loads(result)

        assert parsed["is_active"] is False

    def test_build_boolean_type_value_true_capitalised_returns_true(self, translator):
        """
        A target_schema type of "boolean" with transformed_value "True"
        (capital T, as produced by Python str(True)) must also produce
        Python True.  The conversion uses str(value).lower() == "true".
        """
        mappings = {"active": {"target_field": "is_active", "transformed_value": "True"}}
        schema   = {"is_active": "boolean"}

        result = translator.build(mappings, schema)
        parsed = json.loads(result)

        assert parsed["is_active"] is True

    def test_build_bool_alias_type_works_same_as_boolean(self, translator):
        """
        A target_schema type of "bool" (alias for "boolean") must behave
        identically to "boolean".
        """
        mappings = {"flag": {"target_field": "enabled", "transformed_value": "true"}}
        schema   = {"enabled": "bool"}

        result = translator.build(mappings, schema)
        parsed = json.loads(result)

        assert parsed["enabled"] is True

    # --- Type conversion: unknown / missing type → str ---

    def test_build_unknown_target_schema_type_returns_str(self, translator):
        """
        When target_schema maps a field to an unrecognised type (e.g. "date"),
        build() must fall back to returning a str value in the JSON.
        """
        mappings = {"start_date": {"target_field": "hire_date", "transformed_value": "2024-03-01"}}
        schema   = {"hire_date": "date"}

        result = translator.build(mappings, schema)
        parsed = json.loads(result)

        assert isinstance(parsed["hire_date"], str)
        assert parsed["hire_date"] == "2024-03-01"

    def test_build_missing_target_schema_entry_returns_str(self, translator):
        """
        When a target field has no entry in target_schema, build() must fall
        back to "string" type and return a str in the JSON.
        """
        mappings = {"location": {"target_field": "office", "transformed_value": "London"}}
        schema   = {}  # no entry for "office"

        result = translator.build(mappings, schema)
        parsed = json.loads(result)

        assert isinstance(parsed["office"], str)
        assert parsed["office"] == "London"

    # --- Numeric conversion fallbacks ---

    def test_build_number_type_non_numeric_string_falls_back_to_str(self, translator):
        """
        When target_schema type is "number" but the value cannot be coerced
        to float, build() must fall back to returning a str rather than raising.
        """
        mappings = {"salary": {"target_field": "pay_rate", "transformed_value": "n/a"}}
        schema   = {"pay_rate": "number"}

        result = translator.build(mappings, schema)
        parsed = json.loads(result)

        assert isinstance(parsed["pay_rate"], str)
        assert parsed["pay_rate"] == "n/a"

    def test_build_integer_type_non_numeric_string_falls_back_to_str(self, translator):
        """
        When target_schema type is "integer" but the value cannot be coerced
        to int, build() must fall back to returning a str rather than raising.
        """
        mappings = {"count": {"target_field": "total", "transformed_value": "unknown"}}
        schema   = {"total": "integer"}

        result = translator.build(mappings, schema)
        parsed = json.loads(result)

        assert isinstance(parsed["total"], str)
        assert parsed["total"] == "unknown"

    # --- TranslationError on missing required keys ---

    def test_build_raises_translation_error_when_target_field_key_missing(
        self, translator
    ):
        """
        build() must raise TranslationError (not a raw KeyError) when a dict
        mapping is missing the required 'target_field' key.
        """
        bad_mappings = {
            "employee_id": {"transformed_value": "E-12345"}  # no target_field
        }

        with pytest.raises(TranslationError) as exc_info:
            translator.build(bad_mappings, {})

        assert exc_info.value.field_name == "employee_id"

    def test_build_raises_translation_error_when_transformed_value_key_missing(
        self, translator
    ):
        """
        build() must raise TranslationError (not a raw KeyError) when a dict
        mapping is missing the required 'transformed_value' key.
        """
        bad_mappings = {
            "employee_id": {"target_field": "id"}  # no transformed_value
        }

        with pytest.raises(TranslationError):
            translator.build(bad_mappings, {})

    # --- Stdout logging ---

    def test_build_logs_two_fields_for_two_field_input(
        self, translator, two_dict_mappings, two_field_schema, capsys
    ):
        """
        build() with two field mappings must print exactly:
            [JSON_TRANSLATOR] Built JSON with 2 fields
        """
        translator.build(two_dict_mappings, two_field_schema)
        captured = capsys.readouterr()

        assert "[JSON_TRANSLATOR] Built JSON with 2 fields" in captured.out

    def test_build_logs_zero_fields_for_empty_input(self, translator, capsys):
        """
        build() with empty field_mappings must print exactly:
            [JSON_TRANSLATOR] Built JSON with 0 fields
        """
        translator.build({}, {})
        captured = capsys.readouterr()

        assert "[JSON_TRANSLATOR] Built JSON with 0 fields" in captured.out

    # --- json.dumps serialisation failure ---

    def test_build_raises_translation_error_on_json_serialisation_failure(
        self, translator, monkeypatch
    ):
        """
        If json.dumps raises a ValueError (simulated by monkeypatching), build()
        must wrap it in a TranslationError with field_name='<payload>'.
        This validates the catch-block around json.dumps in the implementation.
        """
        import backend.core.translators.json_translator as jt_module

        def _bad_dumps(obj, **kwargs):
            raise ValueError("simulated serialisation failure")

        monkeypatch.setattr(jt_module.json, "dumps", _bad_dumps)

        mappings = {"field": {"target_field": "f", "transformed_value": "v"}}

        with pytest.raises(TranslationError) as exc_info:
            translator.build(mappings, {})

        assert exc_info.value.field_name == "<payload>"


# ---------------------------------------------------------------------------
# TestJsonTranslatorInit — package import and __all__
# ---------------------------------------------------------------------------

class TestJsonTranslatorInit:
    """Tests for the backend.core.translators package-level exports."""

    def test_json_translator_import_from_package_succeeds(self):
        """
        'from backend.core.translators import JsonTranslator' must succeed
        and the imported name must be the JsonTranslator class.
        """
        from backend.core.translators import JsonTranslator as JT
        assert JT is JsonTranslator

    def test_json_translator_in_package_all(self):
        """
        "JsonTranslator" must appear in backend.core.translators.__all__
        so it is part of the public API surface.
        """
        import backend.core.translators as translators_pkg
        assert "JsonTranslator" in translators_pkg.__all__

    def test_xml_translator_still_in_package_all(self):
        """
        Adding JsonTranslator must not remove XmlTranslator from __all__.
        Both must coexist as public exports.
        """
        import backend.core.translators as translators_pkg
        assert "XmlTranslator" in translators_pkg.__all__
