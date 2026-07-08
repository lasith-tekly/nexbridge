# NexBridge

**AI-governed middleware for legacy-to-modern integration**

![Python 3.11](https://img.shields.io/badge/python-3.11-blue)
![Tests](https://img.shields.io/badge/tests-600%20passing-brightgreen)
![License: MIT](https://img.shields.io/badge/license-MIT-green)
![LangGraph](https://img.shields.io/badge/LangGraph-1.0-purple)

---

## What is NexBridge?

Unlike MuleSoft or IBM App Connect, NexBridge uses AI to map fields by semantic meaning rather than brittle hand-coded rules — and applies risk-proportionate governance based on what each field actually represents. It bridges legacy enterprise systems (XML/SOAP) with modern REST APIs (JSON/REST) without requiring a dedicated integration engineer to maintain static transformation logic. Safety-critical fields like weight limits or medication dosages get dual-agent AI verification and explicit human confirmation before any payload is released. Everything else — T3 business fields, T4 metadata — flows automatically with zero manual overhead.

---

## The Problem

Enterprise integration breaks in predictable, expensive ways:

- Legacy platforms speak XML/SOAP; modern APIs expect JSON/REST — and neither side is changing
- Schema changes on either system silently break static field-mapping rules overnight
- IT teams end up owning thousands of lines of brittle mapping configuration with no semantic understanding
- There is no traceability: who approved this mapping, when, and why?

---

## The NexBridge Approach

### Four-Tier Risk Classification

Every field in every payload is classified into one of four tiers. The tier determines how much governance overhead is applied — not a uniform tax on every field, but proportionate to actual risk.

| Tier | Description | Confidence Threshold | Governance |
|------|-------------|---------------------|------------|
| T1 | Safety Critical | 1.00 (100%) | Dual-agent AI verification + explicit human confirmation |
| T2 | Operationally Sensitive | 0.95 (95%) | Single-agent with anomaly flagging |
| T3 | Business Important | 0.80 (80%) | Automatic mapping, anomalies logged |
| T4 | Informational | 0.0 | Automatic, no threshold |

A single T1 field in a payload elevates the entire payload to T1. The orchestrator is the only entity that can release a payload — and it will not do so if any T1 field fails its confidence check or dual-agent agreement.

### The Registry Builder

Domain experts don't write YAML. Instead, they upload sample payloads from both systems into the Registry Builder UI. The AI proposes tier classifications for every field and semantic mappings between the two systems. The expert reviews and confirms — once. After that, all known fields bypass the LLM entirely at runtime: pre-approved mappings are served directly from the registry at zero inference cost. The LLM is only called for fields the registry has never seen.

---

## Architecture

```
[XML / JSON Payload]
        │
        ▼
    [Parser]
        │
        ▼
 [Tier Classifier]  (ClassificationRegistry)
        │
        ▼
   [Interpreter]
        │
        ▼
 [Registry lookup]
   ↙           ↘
[Pre-approved]  [LLM mapping]     (T1: runs twice, independently)
   ↘           ↙
  [Validator]
        │
        ▼
  [Orchestrator]
        │
        ▼
 GO / HOLD / ESCALATE
        │
        ▼
  [JSON / XML Output]  +  Immutable Audit Log
```

The orchestrator is the sole decision authority. It reads confidence scores and tier classifications, applies the thresholds, and either releases the payload or issues a HOLD. It never delegates this decision.

---

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- [Ollama](https://ollama.ai) (for local, free LLM) **or** an Anthropic API key

### Installation

```bash
git clone https://github.com/lasith-tekly/nexbridge
cd nexbridge
cp .env.example .env        # add your API key, or set LLM_PROVIDER=ollama
pip install -r backend/requirements.txt
cd frontend && npm install
```

### Running

```bash
# Terminal 1 — Backend API
uvicorn backend.api.main:app --reload --port 8000

# Terminal 2 — Frontend
cd frontend && npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

---

## The AirNova Example

AirNova Airlines needs to connect their Flight Management System (FMS, XML) to their Ground Support Platform (GSP, JSON) for weight and flight data. Two fields illustrate everything NexBridge does.

**`weight_limit → max_permitted_load` (T1 Safety Critical)**

The FMS sends aircraft maximum take-off weight as `weight_limit`. The GSP expects `max_permitted_load`. A wrong value here can ground a flight or, worse, authorise an overloaded aircraft. This field is classified T1.

In the Registry Builder, NexBridge's AI proposes the mapping with 0.98 confidence. Sarah Okonkwo, AirNova's Safety Compliance Officer, reviews the proposal on the Confirm T1 screen — she sees the field name, sample value, AI reasoning, and confidence score. She clicks: *"I confirm weight_limit is T1 Safety Critical."* That confirmation is timestamped, attributed to Sarah, and written permanently to the registry.

From that point forward, every payload containing `weight_limit` runs two independent interpreter passes (the dual-agent guarantee), both returning the registry result without calling the LLM. The orchestrator compares the two results, sees agreement, checks the 1.0 confidence threshold, and releases the payload.

**`flight_number → flight_code` (T3 Business Important)**

Classified T3. No human confirmation required. Accepted in bulk during Registry Builder onboarding and mapped automatically at runtime. If confidence drops below 0.80, an anomaly is logged — but the pipeline does not stop.

**A live GO response after onboarding:**

```json
{
  "decision": "GO",
  "payload_tier": 1,
  "translated_payload": {
    "max_permitted_load": 352000,
    "flight_code": "ANV-2047"
  },
  "confidence_scores": {
    "weight_limit": 0.98,
    "flight_number": 0.95
  },
  "processing_time_ms": 12,
  "audit_log": [...]
}
```

`processing_time_ms: 12` — because both fields were pre-approved. No LLM calls were made.

---

## Registry Builder

The Registry Builder is a 7-screen browser-based workflow at [http://localhost:3000](http://localhost:3000). Domain experts upload sample payloads from both systems, the AI classifies every field and proposes semantic A→B mappings, and experts review and confirm — including an individual confirmation screen for every T1 field. Once approved, the registry is exported as a versioned JSON file and placed in `./registries/`.

**T1 safety rule: bulk-accept is blocked by design.** Every T1 field requires an individual, named, timestamped confirmation. This is enforced in both the UI and the export endpoint — a T1 field without `confirmed_individually: true` is rejected with HTTP 400.

---

## Configuration

Copy `.env.example` to `.env` and set the following:

| Variable | Description | Default |
|----------|-------------|---------|
| `LLM_PROVIDER` | `anthropic` or `ollama` | `anthropic` |
| `ANTHROPIC_API_KEY` | API key for Claude (Anthropic provider only) | — |
| `ANTHROPIC_MODEL` | Claude model ID | `claude-sonnet-4-20250514` |
| `OLLAMA_MODEL` | Ollama model name | `llama3.2` |
| `REGISTRY_DIR` | Path to folder containing registry JSON files | `./registries` |

To run entirely locally with no API costs:

```bash
# Install Ollama and pull a model
ollama pull llama3.2

# Set in .env
LLM_PROVIDER=ollama
OLLAMA_MODEL=llama3.2
```

---

## Running Tests

```bash
pytest backend/tests/ -v
```

**600 tests passing.** The suite covers tier classification, the full LangGraph pipeline, T1 dual-agent verification and divergence detection, all API endpoints, the Registry Builder export, and the hybrid pre-approved/LLM interpreter path.

---

## Contributing

Pull requests are welcome. The `docs/` directory contains the full architecture reference, data classification rules (`04_DATA_CLASSIFICATION.md`), API reference (`06_API_REFERENCE.md`), and agent registry (`08_AGENT_REGISTRY.md`). Before contributing changes to T1 confidence thresholds, dual-agent verification logic, or the orchestrator decision node, read `08_AGENT_REGISTRY.md` — these components have a change impact matrix and require @TechLead review. Everything else follows standard GitHub flow: fork, branch off `developer`, open a PR.

---

## License

MIT © Lasith Jayarathne
