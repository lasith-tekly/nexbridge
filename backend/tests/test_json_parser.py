"""
Tests for JsonParser

JsonParser is a stdlib-only component that converts raw JSON strings into
flat {key: str} dicts for use by downstream NexBridge agents.  All values
are coerced to str at parse time, regardless of the original JSON type.

These tests validate:
- Correct field extraction from a valid flat JSON object
- Value coercion to str for int, float, bool, and null
- Top-level-only semantics (nested object values not flattened into keys)
- ParseError raised on malformed JSON (not json.JSONDecodeError)
- ParseError raised when root is not a JSON object (array, string, int)
- extract_field_names() returns key names only, without values
- Stdout logging for both public methods, verified with capsys
"""

import pytest

from backend.core.parsers.json_parser import JsonParser
from backend.core.exceptions import ParseError


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def parser() -> JsonParser:
    """Shared JsonParser instance for all tests."""
    return JsonParser()


# ---------------------------------------------------------------------------
# TestJsonParserParse — parse() method
# ---------------------------------------------------------------------------

class TestJsonParserParse:
    """Tests for JsonParser.parse()."""

    def test_parse_valid_flat_object_returns_correct_dict(self, parser):
        """
        parse() with a valid flat JSON object returns a dict mapping every
        top-level key to its string value.
        """
        raw = '{"employee_id": "E-123", "department": "Eng"}'

        result = parser.parse(raw)

        assert result == {"employee_id": "E-123", "department": "Eng"}

    def test_parse_all_returned_values_are_str(self, parser):
        """
        Every value in the returned dict must be of type str, regardless of
        the original JSON type (string, int, float, bool, null).
        """
        raw = '{"name": "Alice", "age": 30, "score": 9.5, "active": true, "alias": null}'

        result = parser.parse(raw)

        for v in result.values():
            assert isinstance(v, str), f"Expected str, got {type(v)} for value {v!r}"

    def test_parse_integer_value_coerced_to_str(self, parser):
        """Integer JSON values must be coerced to their str representation."""
        raw = '{"age": 30}'

        result = parser.parse(raw)

        assert result == {"age": "30"}

    def test_parse_float_value_coerced_to_str(self, parser):
        """Float JSON values must be coerced to their str representation."""
        raw = '{"score": 9.75}'

        result = parser.parse(raw)

        assert result == {"score": "9.75"}

    def test_parse_boolean_true_coerced_to_str(self, parser):
        """JSON true must be coerced to 'True' (Python str(True))."""
        raw = '{"active": true}'

        result = parser.parse(raw)

        assert result == {"active": "True"}

    def test_parse_boolean_false_coerced_to_str(self, parser):
        """JSON false must be coerced to 'False' (Python str(False))."""
        raw = '{"active": false}'

        result = parser.parse(raw)

        assert result == {"active": "False"}

    def test_parse_null_value_coerced_to_str(self, parser):
        """JSON null must be coerced to 'None' (Python str(None))."""
        raw = '{"val": null}'

        result = parser.parse(raw)

        assert result == {"val": "None"}

    def test_parse_nested_object_value_not_flattened(self, parser):
        """
        A nested object value must NOT be flattened into the result keys.
        Only the top-level key is present; nested keys do not appear at the
        top level.
        """
        raw = '{"id": "E-123", "address": {"city": "London", "postcode": "EC1A"}}'

        result = parser.parse(raw)

        assert "id" in result
        assert "address" in result
        assert "city" not in result
        assert "postcode" not in result

    def test_parse_empty_object_returns_empty_dict(self, parser):
        """An empty JSON object {} must return an empty dict."""
        raw = '{}'

        result = parser.parse(raw)

        assert result == {}

    def test_parse_malformed_json_raises_parse_error(self, parser):
        """
        Malformed JSON must raise ParseError, not the stdlib json.JSONDecodeError
        that json.loads would raise directly.
        """
        with pytest.raises(ParseError):
            parser.parse("{not: valid json}")

    def test_parse_malformed_json_parse_error_has_json_format(self, parser):
        """ParseError raised by parse() must carry input_format='json'."""
        with pytest.raises(ParseError) as exc_info:
            parser.parse("{bad json")
        assert exc_info.value.input_format == "json"

    def test_parse_malformed_json_parse_error_has_non_empty_reason(self, parser):
        """ParseError raised by parse() must carry a non-empty reason string."""
        with pytest.raises(ParseError) as exc_info:
            parser.parse("not json at all")
        assert exc_info.value.reason
        assert isinstance(exc_info.value.reason, str)

    def test_parse_root_array_raises_parse_error_with_expected_reason(self, parser):
        """Root JSON array must raise ParseError with reason='Expected JSON object at root'."""
        with pytest.raises(ParseError) as exc_info:
            parser.parse('[1, 2, 3]')
        assert exc_info.value.reason == "Expected JSON object at root"

    def test_parse_root_string_raises_parse_error_with_expected_reason(self, parser):
        """Root JSON string must raise ParseError with reason='Expected JSON object at root'."""
        with pytest.raises(ParseError) as exc_info:
            parser.parse('"just a string"')
        assert exc_info.value.reason == "Expected JSON object at root"

    def test_parse_root_integer_raises_parse_error_with_expected_reason(self, parser):
        """Root JSON integer must raise ParseError with reason='Expected JSON object at root'."""
        with pytest.raises(ParseError) as exc_info:
            parser.parse('42')
        assert exc_info.value.reason == "Expected JSON object at root"

    def test_parse_empty_string_raises_parse_error(self, parser):
        """Completely empty input must raise ParseError."""
        with pytest.raises(ParseError):
            parser.parse("")

    def test_parse_logs_field_count_to_stdout(self, parser, capsys):
        """
        parse() must print "[JSON_PARSER] Parsed {n} fields from JSON" to stdout
        where {n} matches the number of top-level keys found.
        """
        raw = '{"id": "E-123", "dept": "Eng"}'

        parser.parse(raw)
        captured = capsys.readouterr()

        assert "[JSON_PARSER] Parsed 2 fields from JSON" in captured.out

    def test_parse_logs_zero_fields_for_empty_object(self, parser, capsys):
        """parse() on an empty object must log '0 fields'."""
        parser.parse('{}')
        captured = capsys.readouterr()
        assert "[JSON_PARSER] Parsed 0 fields from JSON" in captured.out


# ---------------------------------------------------------------------------
# TestJsonParserExtractFieldNames — extract_field_names() method
# ---------------------------------------------------------------------------

class TestJsonParserExtractFieldNames:
    """Tests for JsonParser.extract_field_names()."""

    def test_extract_field_names_returns_list_of_top_level_key_names(self, parser):
        """
        extract_field_names() must return a list[str] containing only the
        top-level key names of the JSON object, with no values included.
        """
        raw = '{"id": "E-123", "dept": "Eng"}'

        result = parser.extract_field_names(raw)

        assert result == ["id", "dept"]

    def test_extract_field_names_values_not_included_in_result(self, parser):
        """Returned list must contain only key names, not any of the values."""
        raw = '{"id": "E-123", "dept": "Eng"}'

        result = parser.extract_field_names(raw)

        assert "E-123" not in result
        assert "Eng" not in result

    def test_extract_field_names_empty_object_returns_empty_list(self, parser):
        """Empty JSON object must return an empty list."""
        raw = '{}'

        result = parser.extract_field_names(raw)

        assert result == []

    def test_extract_field_names_only_top_level_keys_not_nested(self, parser):
        """
        extract_field_names() must return only top-level key names.
        Keys nested inside a child object must not appear in the result.
        """
        raw = '{"id": "E-123", "address": {"city": "London", "postcode": "EC1A"}}'

        result = parser.extract_field_names(raw)

        assert "id" in result
        assert "address" in result
        assert "city" not in result
        assert "postcode" not in result

    def test_extract_field_names_malformed_json_raises_parse_error(self, parser):
        """Malformed JSON must raise ParseError, not a raw json.JSONDecodeError."""
        with pytest.raises(ParseError):
            parser.extract_field_names("{not valid}")

    def test_extract_field_names_parse_error_has_json_format(self, parser):
        """ParseError raised by extract_field_names() must carry input_format='json'."""
        with pytest.raises(ParseError) as exc_info:
            parser.extract_field_names("{bad json")
        assert exc_info.value.input_format == "json"

    def test_extract_field_names_root_array_raises_parse_error(self, parser):
        """Root JSON array must raise ParseError with reason='Expected JSON object at root'."""
        with pytest.raises(ParseError) as exc_info:
            parser.extract_field_names('[1, 2, 3]')
        assert exc_info.value.reason == "Expected JSON object at root"

    def test_extract_field_names_empty_string_raises_parse_error(self, parser):
        """Empty input string must raise ParseError."""
        with pytest.raises(ParseError):
            parser.extract_field_names("")

    def test_extract_field_names_logs_count_to_stdout(self, parser, capsys):
        """
        extract_field_names() must print
        "[JSON_PARSER] Extracted {n} field names from JSON" to stdout
        where {n} is the number of top-level keys found.
        """
        raw = '{"id": "E-123", "dept": "Eng"}'

        parser.extract_field_names(raw)
        captured = capsys.readouterr()

        assert "[JSON_PARSER] Extracted 2 field names from JSON" in captured.out

    def test_extract_field_names_logs_zero_for_empty_object(self, parser, capsys):
        """extract_field_names() on an empty object must log '0 field names'."""
        parser.extract_field_names('{}')
        captured = capsys.readouterr()
        assert "[JSON_PARSER] Extracted 0 field names from JSON" in captured.out
