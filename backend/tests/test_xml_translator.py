"""
Tests for XmlTranslator

XmlTranslator is a stdlib-only component that builds XML strings from
interpreter FieldMapping results. It accepts either plain dicts or
Pydantic-style objects (accessed via getattr/key) and serialises them
to a well-formed XML document prefixed by an XML declaration.

These tests validate:
- Correct XML declaration prefix on all outputs
- Correct root element tag (default and custom)
- Correct child element tags and text content
- Pydantic-style object mappings via SimpleNamespace
- Empty field_mappings produce a valid empty root element
- Integer (non-string) values are str-coerced in XML text
- Multiple fields all appear as child elements
- TranslationError raised when a mapping is missing a required key
- Stdout logging for both non-empty and empty mapping cases
- TranslationError exception class attributes and inheritance
"""

import pytest
from types import SimpleNamespace

from backend.core.translators.xml_translator import XmlTranslator
from backend.core.exceptions import TranslationError, NexBridgeError

XML_DECLARATION = '<?xml version="1.0" encoding="UTF-8"?>'


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def translator() -> XmlTranslator:
    """Shared XmlTranslator instance for all tests."""
    return XmlTranslator()


@pytest.fixture
def two_dict_mappings() -> dict:
    """Two plain-dict field mappings for a standard GO scenario."""
    return {
        "employee_id": {"target_field": "id", "transformed_value": "E-12345"},
        "department":  {"target_field": "dept_code", "transformed_value": "OPS"},
    }


@pytest.fixture
def two_object_mappings() -> dict:
    """Two SimpleNamespace field mappings (Pydantic-style attribute access)."""
    return {
        "employee_id": SimpleNamespace(target_field="id", transformed_value="E-12345"),
        "department":  SimpleNamespace(target_field="dept_code", transformed_value="OPS"),
    }


# ---------------------------------------------------------------------------
# TestXmlTranslatorBuild — build() method
# ---------------------------------------------------------------------------

class TestXmlTranslatorBuild:
    """Tests for XmlTranslator.build()."""

    # --- XML declaration ---

    def test_build_dict_mappings_returns_string_starting_with_xml_declaration(
        self, translator, two_dict_mappings
    ):
        """
        build() with dict mappings must return a string that starts with the
        standard XML 1.0 UTF-8 declaration line followed by a newline.
        """
        result = translator.build(two_dict_mappings, {})

        assert isinstance(result, str)
        assert result.startswith(f"{XML_DECLARATION}\n")

    # --- Root element tag ---

    def test_build_dict_mappings_includes_correct_root_element_tag(
        self, translator, two_dict_mappings
    ):
        """
        build() with the default root_element must wrap children in a
        <payload>...</payload> tag in the serialised output.
        """
        result = translator.build(two_dict_mappings, {})

        assert "<payload>" in result
        assert "</payload>" in result

    # --- Child element tags and text ---

    def test_build_dict_mappings_includes_correct_child_tags_and_text(
        self, translator, two_dict_mappings
    ):
        """
        build() must produce child elements whose tag names come from
        target_field and whose text content comes from transformed_value.
        """
        result = translator.build(two_dict_mappings, {})

        assert "<id>E-12345</id>" in result
        assert "<dept_code>OPS</dept_code>" in result

    # --- Pydantic-style object mappings ---

    def test_build_object_mappings_works_correctly(
        self, translator, two_object_mappings
    ):
        """
        build() must handle Pydantic-style objects (attribute access via
        getattr) identically to plain dicts. SimpleNamespace simulates the
        .target_field / .transformed_value interface.
        """
        result = translator.build(two_object_mappings, {})

        assert result.startswith(f"{XML_DECLARATION}\n")
        assert "<id>E-12345</id>" in result
        assert "<dept_code>OPS</dept_code>" in result

    # --- Empty mappings ---

    def test_build_empty_field_mappings_returns_xml_declaration_and_empty_root(
        self, translator
    ):
        """
        build() with an empty field_mappings dict must still return a valid
        string starting with the XML declaration, followed by an empty root.
        The result must NOT be None or an empty string.
        """
        result = translator.build({}, {})

        assert isinstance(result, str)
        assert result.startswith(f"{XML_DECLARATION}\n")
        # Empty root element — either <payload /> or <payload></payload>
        xml_body = result[len(XML_DECLARATION) + 1:]  # strip declaration + \n
        assert "payload" in xml_body

    # --- Default root_element ---

    def test_build_default_root_element_uses_payload_tag(
        self, translator, two_dict_mappings
    ):
        """
        When root_element is not supplied, build() must default to 'payload'
        as the root tag name.
        """
        result = translator.build(two_dict_mappings, {})

        assert "<payload>" in result or "<payload/>" in result

    # --- Custom root_element ---

    def test_build_custom_root_element_uses_that_tag(
        self, translator, two_dict_mappings
    ):
        """
        When root_element='record' is passed, build() must use <record> as
        the XML root tag instead of <payload>.
        """
        result = translator.build(two_dict_mappings, {}, root_element="record")

        assert "<record>" in result
        assert "</record>" in result
        assert "<payload>" not in result

    # --- Integer coercion ---

    def test_build_integer_value_is_str_coerced_in_xml_text(self, translator):
        """
        An integer transformed_value must be serialised as its string
        representation in the XML text node (not left as int or omitted).
        """
        mappings = {
            "weight_limit": {"target_field": "max_load", "transformed_value": 250}
        }

        result = translator.build(mappings, {})

        assert "<max_load>250</max_load>" in result

    # --- Multiple fields ---

    def test_build_multiple_fields_all_appear_as_children(self, translator):
        """
        build() with five fields must produce five child elements, each
        present in the output exactly once with the correct tag and text.
        """
        mappings = {
            "employee_id":    {"target_field": "id",        "transformed_value": "E-12345"},
            "department":     {"target_field": "dept_code", "transformed_value": "OPS"},
            "start_date":     {"target_field": "hire_date", "transformed_value": "2024-03-01"},
            "contract_type":  {"target_field": "emp_type",  "transformed_value": "FULL_TIME"},
            "office_location":{"target_field": "location",  "transformed_value": "London"},
        }

        result = translator.build(mappings, {})

        assert "<id>E-12345</id>" in result
        assert "<dept_code>OPS</dept_code>" in result
        assert "<hire_date>2024-03-01</hire_date>" in result
        assert "<emp_type>FULL_TIME</emp_type>" in result
        assert "<location>London</location>" in result

    # --- TranslationError on missing required key ---

    def test_build_raises_translation_error_when_target_field_missing(
        self, translator
    ):
        """
        build() must raise TranslationError when a dict mapping is missing
        the required 'target_field' key. The error must not propagate as a
        raw KeyError or AttributeError.
        """
        bad_mappings = {
            "employee_id": {"transformed_value": "E-12345"}  # no target_field
        }

        with pytest.raises(TranslationError):
            translator.build(bad_mappings, {})

    def test_build_translation_error_carries_field_name(self, translator):
        """
        The TranslationError raised for a missing key must carry the
        originating field_name so callers can identify which field failed.
        """
        bad_mappings = {
            "employee_id": {"transformed_value": "E-12345"}  # no target_field
        }

        with pytest.raises(TranslationError) as exc_info:
            translator.build(bad_mappings, {})

        assert exc_info.value.field_name == "employee_id"

    def test_build_translation_error_carries_non_empty_reason(self, translator):
        """TranslationError raised for a bad mapping must carry a non-empty reason."""
        bad_mappings = {
            "employee_id": {"transformed_value": "E-12345"}
        }

        with pytest.raises(TranslationError) as exc_info:
            translator.build(bad_mappings, {})

        assert exc_info.value.reason
        assert isinstance(exc_info.value.reason, str)

    # --- Stdout logging ---

    def test_build_logs_two_fields_with_default_root_element(
        self, translator, two_dict_mappings, capsys
    ):
        """
        build() with two fields and root_element='payload' (default) must
        print exactly:
            [XML_TRANSLATOR] Built XML with 2 fields root_element=payload
        """
        translator.build(two_dict_mappings, {})
        captured = capsys.readouterr()

        assert "[XML_TRANSLATOR] Built XML with 2 fields root_element=payload" in captured.out

    def test_build_logs_zero_fields_for_empty_mappings(self, translator, capsys):
        """
        build() with empty field_mappings must log:
            [XML_TRANSLATOR] Built XML with 0 fields root_element=payload
        """
        translator.build({}, {})
        captured = capsys.readouterr()

        assert "[XML_TRANSLATOR] Built XML with 0 fields root_element=payload" in captured.out

    def test_build_logs_correct_root_element_for_custom_root(
        self, translator, two_dict_mappings, capsys
    ):
        """
        build() with root_element='record' must log:
            [XML_TRANSLATOR] Built XML with 2 fields root_element=record
        """
        translator.build(two_dict_mappings, {}, root_element="record")
        captured = capsys.readouterr()

        assert "[XML_TRANSLATOR] Built XML with 2 fields root_element=record" in captured.out

    # --- target_schema is accepted but ignored ---

    def test_build_accepts_non_empty_target_schema_without_error(
        self, translator, two_dict_mappings
    ):
        """
        build() must accept a non-empty target_schema without raising any
        error; schema is ignored (unlike the JSON translator_node).
        The output is identical to passing an empty dict.
        """
        schema = {"id": "string", "dept_code": "string"}

        result_with_schema = translator.build(two_dict_mappings, schema)
        result_empty_schema = translator.build(two_dict_mappings, {})

        assert result_with_schema == result_empty_schema

    # --- Return type ---

    def test_build_always_returns_str(self, translator, two_dict_mappings):
        """build() return type must always be str."""
        result = translator.build(two_dict_mappings, {})
        assert isinstance(result, str)

    # --- Source field names must NOT appear as XML tags ---

    def test_build_source_field_names_not_in_output(
        self, translator, two_dict_mappings
    ):
        """
        The source field names (dict keys) must NOT appear as XML element tags
        in the output. Only target_field names should be used as tags.
        """
        result = translator.build(two_dict_mappings, {})

        assert "<employee_id>" not in result
        assert "<department>" not in result


# ---------------------------------------------------------------------------
# TestTranslationError — TranslationError exception class
# ---------------------------------------------------------------------------

class TestTranslationError:
    """Tests for the TranslationError exception class in backend.core.exceptions."""

    def test_translation_error_is_instance_of_nexbridge_error(self):
        """TranslationError must inherit from NexBridgeError."""
        err = TranslationError(field_name="weight_limit", reason="bad value")
        assert isinstance(err, NexBridgeError)

    def test_translation_error_is_instance_of_exception(self):
        """TranslationError must also be a standard Python Exception."""
        err = TranslationError(field_name="weight_limit", reason="bad value")
        assert isinstance(err, Exception)

    def test_translation_error_stores_field_name(self):
        """TranslationError must store field_name as self.field_name."""
        err = TranslationError(field_name="weight_limit", reason="missing key")
        assert err.field_name == "weight_limit"

    def test_translation_error_stores_reason(self):
        """TranslationError must store reason as self.reason."""
        err = TranslationError(field_name="weight_limit", reason="missing key")
        assert err.reason == "missing key"

    def test_translation_error_str_format(self):
        """
        TranslationError.__str__() must return the format:
            [TRANSLATION ERROR] field=<field_name> reason=<reason>
        """
        err = TranslationError(field_name="max_load", reason="KeyError: target_field")
        result = str(err)
        assert result == "[TRANSLATION ERROR] field=max_load reason=KeyError: target_field"

    def test_translation_error_str_starts_with_translation_error_tag(self):
        """TranslationError.__str__() must start with '[TRANSLATION ERROR]'."""
        err = TranslationError(field_name="f", reason="r")
        assert str(err).startswith("[TRANSLATION ERROR]")

    def test_translation_error_can_be_raised_and_caught(self):
        """TranslationError must be raise-able and catch-able."""
        with pytest.raises(TranslationError) as exc_info:
            raise TranslationError(field_name="dept", reason="missing target_field")
        assert exc_info.value.field_name == "dept"
        assert exc_info.value.reason == "missing target_field"

    def test_translation_error_can_be_caught_as_nexbridge_error(self):
        """TranslationError must be catch-able as NexBridgeError (Liskov substitution)."""
        with pytest.raises(NexBridgeError):
            raise TranslationError(field_name="x", reason="y")

    def test_translation_error_default_message_contains_field_and_reason(self):
        """Auto-generated default message must mention both field_name and reason."""
        err = TranslationError(field_name="weight_limit", reason="missing key")
        assert "weight_limit" in err.message
        assert "missing key" in err.message
