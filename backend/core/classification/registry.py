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
from backend.core.exceptions import ClassificationError, RegistryNotFoundError


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

    def __init__(self, _registry_path: Optional[Path] = None) -> None:
        """
        Load registry from the given path, REGISTRY_PATH env var, or bundled default.

        Args:
            _registry_path: Explicit path override (used by ClassificationRegistry.load()).
                            When None, falls back to REGISTRY_PATH env var or bundled file.

        Raises:
            FileNotFoundError: If the resolved registry file does not exist
            json.JSONDecodeError: If the registry file is malformed
        """
        if _registry_path is not None:
            registry_path = _registry_path
            print(f"[REGISTRY] Using registry: {registry_path}")
        else:
            # Check for REGISTRY_PATH environment variable
            custom_registry = os.getenv("REGISTRY_PATH")

            if custom_registry and Path(custom_registry).exists():
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
        self._approved_mappings: dict = registry_data.get("approved_mappings", {})

        # Log successful load
        field_count = len(self._fields)
        print(f"[REGISTRY] Loaded {field_count} fields")
        print(f"[REGISTRY] Version: {self._version}, Domain: {self._domain}")

    @classmethod
    def load(cls, registry_id: Optional[str] = None) -> "ClassificationRegistry":
        """
        Load a registry by ID from REGISTRY_DIR.

        Resolution order:
        1. If REGISTRY_DIR is set:
             load {REGISTRY_DIR}/{registry_id or 'default'}.json
             If the file does not exist: raise RegistryNotFoundError
        2. If REGISTRY_DIR is not set:
             fall through to __init__ default logic
             (respects REGISTRY_PATH env var, then bundled registry.json)

        Args:
            registry_id: Registry ID to load (e.g. "default", "hr", "aviation").
                         None is treated as "default".

        Returns:
            Loaded ClassificationRegistry instance

        Raises:
            RegistryNotFoundError: If REGISTRY_DIR is set but the file is not found
        """
        effective_id = registry_id or "default"
        registry_dir_env = os.getenv("REGISTRY_DIR")

        if registry_dir_env:
            registry_dir = Path(registry_dir_env)
            registry_path = registry_dir / f"{effective_id}.json"

            if not registry_path.exists():
                available = list_available_registries()
                print(
                    f"[REGISTRY] Registry '{effective_id}' not found in {registry_dir}. "
                    f"Available: {available}"
                )
                raise RegistryNotFoundError(
                    registry_id=effective_id,
                    available=available,
                )

            return cls(_registry_path=registry_path)

        # REGISTRY_DIR not set — use existing env var / bundled file logic
        return cls()

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

    def get_approved_mapping(self, source_field: str) -> dict | None:
        """
        Return the pre-approved mapping dict for a source field, or None.

        Returns None when:
        - The registry has no "approved_mappings" section
        - The field is not present in approved_mappings

        Returns dict with keys:
            target_field, confidence, approved_by, approved_at, llm_generated
        """
        return self._approved_mappings.get(source_field) or None

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


def list_available_registries() -> list[str]:
    """
    Return list of registry IDs available in REGISTRY_DIR.

    Strips the .json extension from each filename.
    Returns ["default"] if REGISTRY_DIR is not set or the directory is empty.

    Returns:
        Sorted list of registry ID strings (e.g. ["aviation", "default", "hr"])
    """
    registry_dir_env = os.getenv("REGISTRY_DIR")

    if not registry_dir_env:
        return ["default"]

    registry_dir = Path(registry_dir_env)

    if not registry_dir.exists() or not registry_dir.is_dir():
        return ["default"]

    ids = [
        p.stem
        for p in sorted(registry_dir.iterdir())
        if p.is_file() and p.suffix == ".json"
    ]

    return ids if ids else ["default"]
