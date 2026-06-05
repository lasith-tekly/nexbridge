"""
Shared pytest fixtures for NexBridge test suite.

Provides common fixtures for registry, state, and test data
used across all test files.
"""

import pytest
from backend.core.classification.registry import ClassificationRegistry


@pytest.fixture
def registry():
    """
    ClassificationRegistry instance loaded from default registry.json.

    This fixture is shared across all tests that need registry lookups.
    The registry is loaded once per test function.
    """
    return ClassificationRegistry()
