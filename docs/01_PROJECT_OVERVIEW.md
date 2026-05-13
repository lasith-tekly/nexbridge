# NexBridge - Project Overview

## What is NexBridge?

NexBridge is an open-source, AI-powered middleware framework that enables
safe, governed transformation between any two data protocols — XML, JSON,
REST, SOAP, and beyond.

Unlike traditional static mappers or ESB tools, NexBridge uses a
multi-agent orchestration pipeline where each field transformation is
understood semantically, classified by risk tier, and governed by
confidence thresholds before a payload is released.

---

## The Problem NexBridge Solves

Enterprise systems across every industry face the same fundamental problem:
legacy systems speak XML/SOAP while modern systems speak JSON/REST.
Bridging them today means static, brittle mappers that break on every
schema change and treat safety-critical fields the same as metadata.

```
WITHOUT NEXBRIDGE                WITH NEXBRIDGE
──────────────────               ──────────────────────────────
Static mapper                    AI-powered semantic interpretation
Breaks on schema change          Self-adapts with confidence scoring
No field sensitivity             4-tier risk classification
No audit trail                   Immutable transformation audit log
No escalation                    Human-in-the-loop for T1 fields
One-size-fits-all                Proportionate governance per tier
```

---

## Target Users

| User | Why They Need NexBridge |
|---|---|
| Enterprise Architects | Governed integration between legacy and modern systems |
| Platform Engineers | Reusable middleware infrastructure |
| Product Managers | Demonstrable AI governance framework |
| Open Source Community | Reference implementation for agentic middleware |

---

## Industry Applications

NexBridge is domain-agnostic. The same framework applies across:

```
Aviation        → FM XML Web Services ↔ Check-in REST APIs
Healthcare      → HL7 v2 ↔ FHIR JSON APIs
Banking         → SWIFT/ISO 20022 ↔ Fintech REST APIs
Logistics       → EDI ↔ Modern supply chain platforms
Government      → Legacy SOAP services ↔ Digital citizen APIs
Manufacturing   → Industrial IoT protocols ↔ ERP systems
```

---

## Key Differentiator

NexBridge is not just an API transformer. It is a
**governed transformation layer** where data sensitivity
is a first-class citizen.

The 4-tier classification system drives every processing decision:

```
TIER 1 — Safety Critical
  → Dual-agent verification
  → 100% confidence required
  → Human escalation gate
  → Immutable audit entry

TIER 2 — Operationally Sensitive
  → Single agent + validator
  → 95% confidence required
  → Anomaly flagging

TIER 3 — Business Important
  → Standard transformation
  → Error logging only

TIER 4 — Informational
  → Best effort pass-through
```

---

## Technology Stack

```
Core Engine         Python 3.11+
Agent Orchestration LangGraph (stateful multi-agent)
AI Integration      LangChain + Anthropic Claude API
API Layer           FastAPI
Data Validation     Pydantic
Demo UI             React 18 + TypeScript + Tailwind CSS
Package Registry    PyPI (pip install nexbridge)
Version Control     GitHub (github.com/lasith-tekly/nexbridge)
```

---

## System Components

```
nexbridge/
├── backend/
│   ├── core/
│   │   ├── orchestrator.py          ← Central control plane
│   │   ├── agents/
│   │   │   ├── interpreter.py       ← Semantic field interpreter
│   │   │   ├── validator.py         ← Schema + constraint validator
│   │   │   ├── translator.py        ← JSON payload builder
│   │   │   └── audit.py             ← Immutable audit logger
│   │   └── classification/
│   │       └── registry.py          ← Tier classification registry
│   ├── api/
│   │   └── main.py                  ← FastAPI entry point
│   └── tests/
├── frontend/
│   └── src/                         ← React demo UI
└── docs/                            ← All project documentation
```

---

## Project Phases

```
PHASE 1 — Core Engine (Weeks 1-3)
  Orchestrator + Interpreter + Translator
  End-to-end XML → JSON transformation
  Classification Registry

PHASE 2 — Safety Layer (Weeks 4-6)
  Validator Agent
  Tier-based confidence thresholds
  Dual-agent pattern for T1 fields
  Escalation pathways

PHASE 3 — Governance (Weeks 7-9)
  Audit Agent with immutable log
  Compliance reporting
  Full human escalation flow
  Accuracy benchmarking

PHASE 4 — Demo UI (Weeks 10-12)
  React interactive demo
  Real-time agent visualisation
  Tier classification display
  Public launch on GitHub + LinkedIn
```

---

## Open Source Goals

```
GitHub Stars       → 100+ in first 3 months
Contributors       → 5+ external contributors
pip installs       → Available as pip install nexbridge
Documentation      → Full docs site (GitHub Pages)
Community          → LinkedIn thought leadership series
```

---

## Key Design Principles

1. **Orchestrator as Control Plane**
   Only the orchestrator can release a payload.
   All other agents are advisory.

2. **Proportionate Governance**
   Safety-critical fields receive maximum scrutiny.
   Routine data flows efficiently.

3. **Domain Experts Own Classification**
   The tier registry is maintained by domain experts,
   not developers.

4. **Auditability as First-Class Output**
   Every transformation produces a structured,
   immutable audit log.

5. **Confidence Over Assumption**
   The system knows when it does not know.
   Ambiguity escalates — it never guesses.

6. **Reusable Infrastructure**
   The orchestrator pattern is platform infrastructure,
   not a point-to-point integration.

---

**Document Version:** 1.0
**Project:** NexBridge
**Maintained By:** Lasith Jayarathne (@TechLead)
**Last Updated:** March 2026
**Review Frequency:** After each phase completion
