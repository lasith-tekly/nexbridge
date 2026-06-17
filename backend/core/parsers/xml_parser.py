"""
xml_parser — Parse raw XML strings into flat field dicts for agents.

Part of the NexBridge transformation pipeline.
See docs/SOLUTION_AGENTS.md for full specification.
"""

import xml.etree.ElementTree as ET
from xml.etree.ElementTree import ParseError as _ETParseError

from backend.core.exceptions import ParseError


class XmlParser:
    """Converts raw XML payload strings into flat {tag: text} dicts."""

    def parse(self, raw_payload: str) -> dict[str, str]:
        """
        Parse raw XML string into flat field dict.

        Extracts all direct children of the root element.
        Returns {tag_name: text_value} for each child.
        Elements with no text return value "".

        Raises ParseError if XML is malformed.
        """
        root = self._parse_root(raw_payload)
        fields = {child.tag: child.text or "" for child in root}
        print(f"[XML_PARSER] Parsed {len(fields)} fields from XML")
        return fields

    def extract_field_names(self, raw_payload: str) -> list[str]:
        """
        Return list of field names only (no values).

        Used by classification_node for tier lookup.
        Raises ParseError if XML is malformed.
        """
        root = self._parse_root(raw_payload)
        names = [child.tag for child in root]
        print(f"[XML_PARSER] Extracted {len(names)} field names from XML")
        return names

    def _parse_root(self, raw_payload: str) -> ET.Element:
        """Parse raw XML and return root element, raising ParseError on failure."""
        try:
            return ET.fromstring(raw_payload)
        except _ETParseError as e:
            raise ParseError(
                input_format="xml",
                reason=str(e)
            ) from e
