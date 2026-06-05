"""
NexBridge Core Constants

Defines immutable confidence thresholds for each tier.
These values are hardcoded and never configurable.
"""

# Confidence thresholds by tier — NEVER change these values
CONFIDENCE_THRESHOLDS: dict[int, float] = {
    1: 1.0,   # T1 Safety Critical — 100% confidence required
    2: 0.95,  # T2 Operationally Sensitive — 95% confidence required
    3: 0.80,  # T3 Business Important — 80% confidence required
    4: 0.0,   # T4 Informational — no threshold
}
