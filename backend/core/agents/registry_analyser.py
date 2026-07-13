"""
Registry Analyser Agent — LLM-powered batch field classification suggester.

Analyses field names from uploaded payloads and suggests tier classifications
with reasoning. Used by the POST /registry/analyse endpoint.

Part of the NexBridge transformation pipeline.
See docs/SOLUTION_AGENTS.md for full specification.
"""

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from backend.core.llm import get_llm
from backend.core.exceptions import NexBridgeError, LLMError


# ── Internal structured output models ─────────────────────────────────────────

class FieldAnalysisResult(BaseModel):
    """LLM-suggested classification for a single field."""
    field_name: str
    suggested_tier: int = Field(..., ge=1, le=4)
    suggested_label: str
    reasoning: str
    confidence: float = Field(..., ge=0.0, le=1.0)


class BatchAnalysisResult(BaseModel):
    """LLM output for a batch of fields."""
    fields: list[FieldAnalysisResult]


# ── Prompt ────────────────────────────────────────────────────────────────────

_SYSTEM_PROMPT = """You are a data governance expert helping organisations classify \
fields in their enterprise integration payloads.

Classify each field into one of four tiers:

T1 Safety Critical (tier=1):
  Errors could cause physical harm, safety incidents, or regulatory violations.
  Examples: weight limits, fuel loads, medication dosages, account numbers,
  dangerous goods indicators.

T2 Operationally Sensitive (tier=2):
  Errors cause operational disruption or compliance gaps.
  Examples: contract types, equipment classes, access levels, certification status.

T3 Business Important (tier=3):
  Errors are significant but correctable.
  Examples: employee IDs, departments, start dates, flight numbers.

T4 Informational (tier=4):
  Low-impact metadata or display fields.
  Examples: notes, timestamps, gate numbers, preferred names, internal IDs.

Return your analysis as structured JSON.
Be conservative — when in doubt, classify higher (more restrictive)."""

_USER_TEMPLATE = """Source format: {source_format}
Domain context: {context}

Classify these {field_count} fields:
{field_list}"""

_PROMPT = ChatPromptTemplate.from_messages([
    ("system", _SYSTEM_PROMPT),
    ("human", _USER_TEMPLATE),
])


# ── Public interface ───────────────────────────────────────────────────────────

def analyse_fields(
    field_names: list[str],
    source_format: str = "xml",
    context: str = "",
) -> list[dict]:
    """
    Batch LLM analysis of field names.

    Issues a single LLM call for all fields and returns one tier suggestion
    per field with reasoning and confidence score.

    Args:
        field_names: List of field names to classify
        source_format: Input format hint ("xml" or "json")
        context: Optional domain hint (e.g. "aviation", "healthcare")

    Returns:
        List of dicts matching the AnalysedField schema keys:
        field_name, suggested_tier, suggested_label, reasoning, confidence

    Raises:
        NexBridgeError: If the LLM call fails or returns unusable output
    """
    print(f"[REGISTRY_ANALYSER] Analysing {len(field_names)} fields")

    try:
        llm = get_llm()
        structured_llm = llm.with_structured_output(BatchAnalysisResult)
        chain = _PROMPT | structured_llm

        result: BatchAnalysisResult = chain.invoke({
            "source_format": source_format,
            "context": context or "general enterprise integration",
            "field_count": len(field_names),
            "field_list": "\n".join(f"- {name}" for name in field_names),
        })

    except Exception as e:
        raise LLMError(
            provider="registry_analyser",
            reason=str(e),
            message=f"Registry analysis failed: {e}",
        ) from e

    # Tally tier distribution for structured logging
    tier_counts = {1: 0, 2: 0, 3: 0, 4: 0}
    for f in result.fields:
        tier_counts[f.suggested_tier] += 1

    print(
        f"[REGISTRY_ANALYSER] Analysis complete: "
        f"T1={tier_counts[1]} T2={tier_counts[2]} "
        f"T3={tier_counts[3]} T4={tier_counts[4]}"
    )

    return [f.model_dump() for f in result.fields]
