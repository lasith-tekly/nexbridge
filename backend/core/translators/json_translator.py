"""
json_translator — Build JSON strings from interpreter field mappings.

Part of the NexBridge transformation pipeline.
See docs/SOLUTION_AGENTS.md for full specification.
"""

import json
from typing import Any

from backend.core.exceptions import TranslationError


class JsonTranslator:
    """Builds JSON strings from interpreter FieldMapping results."""

    def build(
        self,
        field_mappings: dict,
        target_schema: dict
    ) -> str:
        """
        Build JSON string from field mappings.

        Reads target_field and transformed_value from each mapping,
        applies type conversion per target_schema, returns json.dumps output.
        Raises TranslationError if any field fails to build.
        """
        output: dict[str, Any] = {}

        for field_name, mapping in field_mappings.items():
            try:
                target_field = self._get_attr(mapping, "target_field")
                value = self._get_attr(mapping, "transformed_value")
                target_type = target_schema.get(target_field, "string")
                output[target_field] = self._convert(value, target_type)
            except (KeyError, AttributeError, TypeError) as e:
                raise TranslationError(
                    field_name=field_name,
                    reason=f"Failed to build JSON field for '{field_name}': {str(e)}"
                ) from e

        try:
            result = json.dumps(output)
        except (ValueError, OverflowError, TypeError) as e:
            raise TranslationError(
                field_name="<payload>",
                reason=f"JSON serialisation failed: {str(e)}"
            ) from e

        print(f"[JSON_TRANSLATOR] Built JSON with {len(output)} fields")
        return result

    def _convert(self, value: Any, target_type: str) -> Any:
        """Convert value to target_schema type with graceful str fallback."""
        if target_type in ("number", "float"):
            try:
                return float(value)
            except (ValueError, TypeError):
                return str(value)
        elif target_type in ("integer", "int"):
            try:
                return int(value)
            except (ValueError, TypeError):
                return str(value)
        elif target_type in ("boolean", "bool"):
            return str(value).lower() == "true"
        else:
            return str(value)

    def _get_attr(self, mapping: Any, attr: str) -> Any:
        """Safely read attribute from Pydantic FieldMapping or plain dict."""
        if hasattr(mapping, attr):
            return getattr(mapping, attr)
        return mapping[attr]
