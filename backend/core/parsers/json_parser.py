"""
json_parser — Parse raw JSON strings into flat field dicts for agents.

Part of the NexBridge transformation pipeline.
See docs/SOLUTION_AGENTS.md for full specification.
"""

import json
from typing import Any

from backend.core.exceptions import ParseError


class JsonParser:
    """Converts raw JSON payload strings into flat {key: str} dicts."""

    def parse(self, raw_payload: str) -> dict[str, str]:
        """
        Parse raw JSON string into flat field dict.

        Extracts top-level keys only. All values converted to str.
        Raises ParseError if JSON is malformed or root is not an object.
        """
        obj = self._parse_object(raw_payload)
        fields = {k: str(v) for k, v in obj.items()}
        print(f"[JSON_PARSER] Parsed {len(fields)} fields from JSON")
        return fields

    def extract_field_names(self, raw_payload: str) -> list[str]:
        """
        Return list of top-level key names only.

        Used by classification_node for tier lookup.
        Raises ParseError if JSON is malformed or root is not an object.
        """
        obj = self._parse_object(raw_payload)
        names = list(obj.keys())
        print(f"[JSON_PARSER] Extracted {len(names)} field names from JSON")
        return names

    def _parse_object(self, raw_payload: str) -> dict[str, Any]:
        """Parse raw JSON, validate root is a dict, raise ParseError on failure."""
        try:
            data = json.loads(raw_payload)
        except json.JSONDecodeError as e:
            raise ParseError(
                input_format="json",
                reason=str(e)
            ) from e

        if not isinstance(data, dict):
            raise ParseError(
                input_format="json",
                reason="Expected JSON object at root"
            )

        return data
