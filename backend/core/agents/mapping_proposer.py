"""
Mapping Proposer Agent — LLM-powered semantic field mapping between two systems.

Classifies System B fields into tiers and proposes semantic mappings from
System A fields to System B fields in a single LLM call.

Part of the NexBridge transformation pipeline.
See docs/SOLUTION_AGENTS.md for full specification.
"""

import json

from backend.core.llm import get_llm
from backend.core.constants import CONFIDENCE_THRESHOLDS
from backend.core.exceptions import NexBridgeError

# ── Prompt templates ──────────────────────────────────────────────────────────

_SYSTEM_PROMPT = (
    "You are a data integration expert classifying fields and proposing semantic "
    "mappings between enterprise systems. "
    "Respond ONLY with valid JSON — no preamble, no markdown fences."
)

_USER_TEMPLATE = """\
Domain: {domain}
Source system: {source_system}  Target system: {target_system}

=== TASK 1: Classify each System B field ===
Tier definitions:
  T1 Safety Critical (tier=1): affects physical safety, life-critical systems
  T2 Operationally Sensitive (tier=2): disrupts operations if wrong
  T3 Business Important (tier=3): causes business issues if wrong
  T4 Informational (tier=4): low-risk metadata

System B fields to classify:
{system_b_list}

=== TASK 2: Propose semantic mappings ===
For each System A field, find the best matching System B field that represents
the same real-world concept, even if named differently. Confidence is 0.0–1.0.

System A fields (with known tier):
{system_a_list}

Return this EXACT JSON shape and nothing else:
{{
  "system_b_tiers": {{
    "<field_name>": {{"tier": <int 1-4>, "reasoning": "<str>"}}
  }},
  "proposed_mappings": [
    {{
      "source_field": "<str>",
      "target_field": "<str>",
      "confidence": <float 0.0-1.0>,
      "reasoning": "<str>"
    }}
  ]
}}"""


# ── Public interface ───────────────────────────────────────────────────────────

def propose_mappings(
    domain: str,
    source_system: str,
    target_system: str,
    system_a_fields: list[dict],
    system_b_fields: list[str],
) -> dict:
    """
    Single LLM call that classifies System B fields and proposes semantic mappings.

    Calculates effective_tier as min(source_tier, target_tier) — lowest number
    is most restrictive (T1=highest risk, T4=lowest risk).

    Args:
        domain: Integration domain context (e.g. "flight-ops")
        source_system: Name of System A (e.g. "FMS")
        target_system: Name of System B (e.g. "GSP")
        system_a_fields: List of dicts with keys name, tier, threshold
        system_b_fields: List of field name strings from System B

    Returns:
        Dict with keys: system_b_tiers, proposed_mappings, tier_mismatches

    Raises:
        NexBridgeError: If the LLM call fails or returns non-JSON output
    """
    print(
        f"[MAPPING_PROPOSER] Proposing mappings: "
        f"{len(system_a_fields)} System A fields → {len(system_b_fields)} System B fields"
    )

    system_b_list = "\n".join(f"- {name}" for name in system_b_fields)
    system_a_list = "\n".join(
        f"- {f['name']} (T{f['tier']})" for f in system_a_fields
    )

    user_message = _USER_TEMPLATE.format(
        domain=domain,
        source_system=source_system,
        target_system=target_system,
        system_b_list=system_b_list,
        system_a_list=system_a_list,
    )

    try:
        llm = get_llm()
        response = llm.invoke([
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "human", "content": user_message},
        ])
        raw = response.content if hasattr(response, "content") else str(response)
    except Exception as e:
        raise NexBridgeError(f"Mapping proposer LLM call failed: {e}") from e

    try:
        llm_result = json.loads(raw)
    except json.JSONDecodeError as e:
        raise NexBridgeError(
            f"Mapping proposer returned non-JSON output: {e}. Raw: {raw[:200]}"
        ) from e

    system_b_tiers: dict[str, dict] = llm_result.get("system_b_tiers", {})
    raw_mappings: list[dict] = llm_result.get("proposed_mappings", [])

    # Build a lookup from System A field name → source_tier
    source_tier_lookup = {f["name"]: int(f["tier"]) for f in system_a_fields}

    # Enrich each mapping with tier calculations (Python, not LLM)
    enriched_mappings = []
    tier_mismatches: list[str] = []

    for m in raw_mappings:
        source_field = m["source_field"]
        target_field = m["target_field"]
        source_tier = source_tier_lookup.get(source_field, 4)
        target_tier_entry = system_b_tiers.get(target_field, {})
        target_tier = int(target_tier_entry.get("tier", 4))

        # Highest risk wins — lowest tier number is most restrictive
        effective_tier = min(source_tier, target_tier)
        tier_mismatch = source_tier != target_tier

        if tier_mismatch:
            tier_mismatches.append(source_field)

        enriched_mappings.append({
            "source_field": source_field,
            "target_field": target_field,
            "confidence": float(m.get("confidence", 0.0)),
            "reasoning": m.get("reasoning", ""),
            "source_tier": source_tier,
            "target_tier": target_tier,
            "tier_mismatch": tier_mismatch,
            "effective_tier": effective_tier,
            "effective_threshold": CONFIDENCE_THRESHOLDS[effective_tier],
        })

    # Attach threshold to each System B tier result
    enriched_b_tiers = {}
    for field_name, entry in system_b_tiers.items():
        tier = int(entry.get("tier", 4))
        enriched_b_tiers[field_name] = {
            "tier": tier,
            "threshold": CONFIDENCE_THRESHOLDS[tier],
            "reasoning": entry.get("reasoning", ""),
        }

    t1_count = sum(1 for v in enriched_b_tiers.values() if v["tier"] == 1)
    t4_count = sum(1 for v in enriched_b_tiers.values() if v["tier"] == 4)
    print(
        f"[MAPPING_PROPOSER] System B classification complete: "
        f"T1={t1_count} "
        f"T2={sum(1 for v in enriched_b_tiers.values() if v['tier'] == 2)} "
        f"T3={sum(1 for v in enriched_b_tiers.values() if v['tier'] == 3)} "
        f"T4={t4_count}"
    )
    print(
        f"[MAPPING_PROPOSER] Mappings: {len(enriched_mappings)} proposals, "
        f"{len(tier_mismatches)} tier mismatches"
    )

    return {
        "system_b_tiers": enriched_b_tiers,
        "proposed_mappings": enriched_mappings,
        "tier_mismatches": tier_mismatches,
    }
