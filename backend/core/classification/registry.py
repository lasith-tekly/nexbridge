"""
Classification Registry

Loads and queries the field classification registry.
Maps field names to risk tiers with confidence thresholds.

Part of the NexBridge transformation pipeline.
See docs/04_DATA_CLASSIFICATION.md for tier definitions.
"""

import json
import os
from pathlib import Path
from typing import Optional

from backend.core.models import FieldClassification, Tier
from backend.core.constants import CONFIDENCE_THRESHOLDS
from backend.core.exceptions import ClassificationError


# Tier label mapping
TIER_LABELS = {
    1: "Safety Critical",
    2: "Operationally Sensitive",
    3: "Business Important",
    4: "Informational",
}


class ClassificationRegistry:
    """
    Classification registry for field-to-tier lookup.

    Loads registry.json on initialization and caches in memory.
    Provides methods to classify individual fields, determine
    payload tier, and list fields by tier.
    """

    def __init__(self) -> None:
        """
        Load registry.json from the same directory.
        Cache in memory and log field count.

        Raises:
            FileNotFoundError: If registry.json does not exist
            json.JSONDecodeError: If registry.json is malformed
        """
        # Check for REGISTRY_PATH environment variable
        custom_registry = os.getenv("REGISTRY_PATH")

        if custom_registry and Path(custom_registry).exists():
            # Use custom registry from environment
            registry_path = Path(custom_registry)
            print(f"[REGISTRY] Using custom registry: {registry_path}")
        else:
            # Default: registry.json in the same directory as this file
            registry_path = Path(__file__).parent / "registry.json"
            print(f"[REGISTRY] Using default registry: {registry_path}")

        if not registry_path.exists():
            raise FileNotFoundError(
                f"Registry file not found: {registry_path}"
            )

        # Load and parse JSON
        with open(registry_path, "r", encoding="utf-8") as f:
            registry_data = json.load(f)

        # Cache registry data
        self._fields: dict = registry_data.get("fields", {})
        self._default_tier: int = registry_data.get("default_tier", 4)
        self._version: str = registry_data.get("version", "unknown")
        self._domain: str = registry_data.get("domain", "unknown")

        # Log successful load
        field_count = len(self._fields)
        print(f"[REGISTRY] Loaded {field_count} fields")
        print(f"[REGISTRY] Version: {self._version}, Domain: {self._domain}")

    def classify(self, field_name: str) -> FieldClassification:
        """
        Classify a field by name.

        Args:
            field_name: The field name to classify

        Returns:
            FieldClassification with tier, label, threshold

        Note:
            Unknown fields default to Tier 4 (Informational).
            This ensures the pipeline never fails on unknown fields.
        """
        # Lookup field in registry
        if field_name in self._fields:
            field_data = self._fields[field_name]
            tier = field_data["tier"]
            label = field_data["label"]
            threshold = field_data["threshold"]
        else:
            # Default to T4 for unknown fields
            tier = self._default_tier
            label = TIER_LABELS[tier]
            threshold = CONFIDENCE_THRESHOLDS[tier]
            print(
                f"[REGISTRY] Unknown field '{field_name}' "
                f"defaulted to Tier {tier}"
            )

        # Return as FieldClassification (frozen Pydantic model)
        return FieldClassification(
            field_name=field_name,
            tier=Tier(tier),
            confidence_threshold=threshold,
            label=label,
        )

    def get_payload_tier(self, field_names: list[str]) -> int:
        """
        Get the highest risk tier across all fields.

        The payload tier is determined by the MINIMUM tier number
        (since T1=1 is highest risk, T4=4 is lowest risk).

        Args:
            field_names: List of field names in the payload

        Returns:
            Minimum tier number (1 = highest risk, 4 = lowest)

        Example:
            >>> fields = ["weight_limit", "employee_id", "notes"]
            >>> registry.get_payload_tier(fields)
            1  # because weight_limit is T1
        """
        if not field_names:
            return self._default_tier

        # Classify each field and extract tier values
        tiers = [self.classify(field).tier.value for field in field_names]

        # Return minimum (highest risk)
        payload_tier = min(tiers)

        print(
            f"[REGISTRY] Payload tier: T{payload_tier} "
            f"(from {len(field_names)} fields)"
        )

        return payload_tier

    def list_all_fields(self) -> dict:
        """Return a copy of all registered fields as a plain dict."""
        return dict(self._fields)

    def get_version(self) -> str:
        """Return the registry version string."""
        return self._version

    def get_domain(self) -> str:
        """Return the registry domain string."""
        return self._domain

    def list_fields_by_tier(self, tier: int) -> list[str]:
        """
        List all field names for a given tier.

        Args:
            tier: Tier number (1, 2, 3, or 4)

        Returns:
            List of field names classified at that tier

        Example:
            >>> registry.list_fields_by_tier(1)
            ['weight_limit', 'max_load', 'safety_rating', ...]
        """
        return [
            field_name
            for field_name, field_data in self._fields.items()
            if field_data["tier"] == tier
        ]
