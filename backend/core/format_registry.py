"""
format_registry — Factory functions for parser and translator adapters.

Part of the NexBridge transformation pipeline.
See docs/SOLUTION_AGENTS.md for full specification.
"""

from backend.core.parsers import XmlParser, JsonParser
from backend.core.translators import XmlTranslator, JsonTranslator


def get_parser(source_format: str):
    """
    Return the appropriate parser adapter for the given source format.

    Raises ValueError for unsupported formats.
    """
    if source_format == "xml":
        return XmlParser()
    elif source_format == "json":
        return JsonParser()
    else:
        raise ValueError(
            f"Unsupported source_format: {source_format}. "
            f"Supported: xml, json"
        )


def get_translator(target_format: str):
    """
    Return the appropriate translator adapter for the given target format.

    Raises ValueError for unsupported formats.
    """
    if target_format == "xml":
        return XmlTranslator()
    elif target_format == "json":
        return JsonTranslator()
    else:
        raise ValueError(
            f"Unsupported target_format: {target_format}. "
            f"Supported: xml, json"
        )
