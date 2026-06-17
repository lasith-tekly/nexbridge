"""
xml_translator — Build XML strings from interpreter field mappings.

Part of the NexBridge transformation pipeline.
See docs/SOLUTION_AGENTS.md for full specification.
"""

import xml.etree.ElementTree as ET
from typing import Any

from backend.core.exceptions import TranslationError

XML_DECLARATION = '<?xml version="1.0" encoding="UTF-8"?>'


class XmlTranslator:
    """Builds XML strings from interpreter FieldMapping results."""

    def build(
        self,
        field_mappings: dict,
        target_schema: dict,
        root_element: str = "payload"
    ) -> str:
        """
        Build XML string from field mappings.

        Iterates field_mappings, reads target_field and transformed_value
        from each mapping (Pydantic object or plain dict), and appends a
        child element to the root. Returns XML declaration + serialised tree.

        Raises TranslationError if any field fails to build.
        """
        root = ET.Element(root_element)

        for field_name, mapping in field_mappings.items():
            try:
                target_field = self._get_attr(mapping, "target_field")
                value = self._get_attr(mapping, "transformed_value")
                child = ET.SubElement(root, target_field)
                child.text = str(value)
            except (KeyError, AttributeError, TypeError) as e:
                raise TranslationError(
                    field_name=field_name,
                    reason=f"Failed to build XML element for '{field_name}': {str(e)}"
                ) from e

        n = len(field_mappings)
        xml_body = ET.tostring(root, encoding="unicode")
        print(f"[XML_TRANSLATOR] Built XML with {n} fields root_element={root_element}")
        return f"{XML_DECLARATION}\n{xml_body}"

    def _get_attr(self, mapping: Any, attr: str) -> Any:
        """Safely read attribute from Pydantic FieldMapping or plain dict."""
        if hasattr(mapping, attr):
            return getattr(mapping, attr)
        return mapping[attr]
