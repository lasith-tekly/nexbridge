# NexBridge - Frontend Structure

## Overview

The NexBridge demo UI is a React + TypeScript application
built for a business audience. It demonstrates the real-world
problem NexBridge solves: two enterprise systems with different
schemas need to exchange data safely and intelligently.

System A (legacy) sends XML. System B (modern) expects JSON.
The field names differ. The schemas drift. Not all fields
carry the same risk. NexBridge bridges them with AI-powered,
governed transformation.

---

## The Business Scenario

```
SYSTEM A — Legacy Operations System      SYSTEM B — Modern Workforce Platform
────────────────────────────────────     ────────────────────────────────────
Sends XML payloads                       Expects JSON via REST API
Schema defined by old vendor             Schema defined by new vendor
Field names: <weight_limit>              Field names: "max_permitted_load"
                                         
               NEXBRIDGE sits between them
               ─────────────────────────
               Classifies every field by risk tier
               AI maps fields from A schema → B schema
               Governs proportionately to risk level
               Releases clean, trusted JSON to System B
               Logs every decision immutably
```

### GO Scenario — Standard Governed Transformation
```
XML Input (System A)                   JSON Output (System B)
────────────────────                   ─────────────────────
<record>                               {
  <employee_id>E-12345     T3   →        "id": "E-12345",
  <department>Operations   T3   →        "department_code": "OPS",
  <start_date>2024-03-01   T3   →        "start_date": "2024-03-01",
  <contract_type>FULL_TIME T2   →        "employment_type": "FULL_TIME",
  <office_location>London  T4   →        "location": "London"
</record>                              }
Result: GO — all fields above threshold, payload released
```

### HOLD Scenario — Safety Governance in Action
```
XML Input (System A)                   JSON Output (System B)
────────────────────                   ─────────────────────
<record>                               null — payload NOT released
  <employee_id>E-12345     T3
  <department>Operations   T3
  <weight_limit>250        T1   ← triggers dual-agent verification
  <equipment_class>HEAVY   T2       Run 1: maps to "max_permitted_load"
  <clearance_level>L3      T2       Run 2: maps to "weight_capacity"
</record>                             DIVERGENCE DETECTED → HOLD
Result: HOLD — T1 field interpreters disagreed, human review required
```

---

## Design Principles

```
1. Business audience first
   Language and visuals must be clear to a non-technical
   stakeholder without explanation

2. Pipeline is the visual hero
   The agent pipeline is the centrepiece of Step 3
   Inputs and outputs are secondary panels

3. Stepped flow
   4 stages — user never overwhelmed by full complexity at once
   Can go back but cannot skip forward

4. Two systems, one bridge
   Step 2 always shows BOTH schemas side by side
   This is the core business concept

5. Both stories in one demo
   GO: seamless governed transformation
   HOLD: safety governance catching a risk
   One toggle button switches between them

6. Dark theme
   Professional, high contrast
   Tier colours and decision badges must be immediately visible
```

---

## Visual Theme

```
Background:       bg-gray-950    (near black)
Surface:          bg-gray-900    (card backgrounds)
Surface raised:   bg-gray-800    (nested panels)
Border:           border-gray-800
Primary text:     text-white
Secondary text:   text-gray-400
Muted text:       text-gray-600
Accent:           indigo-500 / indigo-600  (buttons, active states)
```

---

## Tier Colour Constants

Always import from src/constants/tiers.ts — never hardcode.

```typescript
// src/constants/tiers.ts

export const TIER_COLOURS = {
  1: {
    bg:     'bg-red-500',
    text:   'text-red-400',
    border: 'border-red-500',
    label:  'Safety Critical',
    hex:    '#ef4444'
  },
  2: {
    bg:     'bg-amber-500',
    text:   'text-amber-400',
    border: 'border-amber-500',
    label:  'Operationally Sensitive',
    hex:    '#f59e0b'
  },
  3: {
    bg:     'bg-blue-500',
    text:   'text-blue-400',
    border: 'border-blue-500',
    label:  'Business Important',
    hex:    '#3b82f6'
  },
  4: {
    bg:     'bg-gray-500',
    text:   'text-gray-400',
    border: 'border-gray-500',
    label:  'Informational',
    hex:    '#6b7280'
  },
} as const

export const DECISION_COLOURS = {
  GO:       { bg: 'bg-green-500',  text: 'text-green-400',  border: 'border-green-500'  },
  HOLD:     { bg: 'bg-red-500',    text: 'text-red-400',    border: 'border-red-500'    },
  ESCALATE: { bg: 'bg-amber-500',  text: 'text-amber-400',  border: 'border-amber-500'  },
} as const
```

---

## The 4-Step Flow

```
┌───────────────────────────────────────────────────────────────┐
│  ① Landing    ② Configure + Run    ③ Pipeline    ④ Result    │
│  ─────────────────────────────────────────────────────────    │
│  Progress bar always visible at top                           │
│  Can go back but cannot skip forward                          │
└───────────────────────────────────────────────────────────────┘
```

---

## Step 1 — Landing Screen

**Purpose:** Tell the business story. Make the problem and solution
clear before any technical detail is shown.

**Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│              ◈  NEXBRIDGE                                   │
│    Governed AI Transformation Between Enterprise Systems    │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  The Problem                                        │   │
│  │                                                     │   │
│  │  Your systems speak different languages.            │   │
│  │  Legacy platforms send XML. Modern APIs expect      │   │
│  │  JSON. Field names differ. Schemas drift. And       │   │
│  │  traditional mappers treat a customer name the      │   │
│  │  same as a safety-critical weight limit.            │   │
│  │                                                     │   │
│  │  NexBridge fixes this — with AI-powered field       │   │
│  │  mapping that applies proportionate governance      │   │
│  │  based on what each field actually means.           │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌───────────┐   ┌───────────┐   ┌───────────┐             │
│  │ ● T1      │   │ ● T2      │   │ ● T3      │             │
│  │ Safety    │   │ Ops       │   │ Business  │             │
│  │ Critical  │   │ Sensitive │   │ Important │             │
│  │           │   │           │   │           │             │
│  │ Dual AI   │   │ Validated │   │ Standard  │             │
│  │ verified  │   │ + flagged │   │ transform │             │
│  │ 100% conf │   │ 95% conf  │   │ 80% conf  │             │
│  └───────────┘   └───────────┘   └───────────┘             │
│                                                             │
│                [ See it in action → ]                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Components:**
- Logo / name
- Problem statement paragraph (plain English)
- Three tier cards — T1 red, T2 amber, T3 blue
- Single CTA: "See it in action →"

---

## Step 2 — Configure + Run

**Purpose:** Show both system contracts side by side.
This is where the business concept becomes concrete —
two real systems, two different schemas, NexBridge between them.

**Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  Scenario:  [ ✓ GO — Safe transformation ]  [ HOLD — Risk ]│
│             (toggle between two pre-loaded scenarios)       │
│                                                             │
│  ┌─────────────────────────┐  ┌─────────────────────────┐  │
│  │  SYSTEM A               │  │  SYSTEM B               │  │
│  │  Legacy XML Payload     │  │  Target API Contract    │  │
│  │  ─────────────────────  │  │  ─────────────────────  │  │
│  │  <record>               │  │  {                      │  │
│  │    <employee_id>        │  │    "id": "string",      │  │
│  │      E-12345            │  │    "dept_code": "str",  │  │
│  │    <department>         │  │    "start_date": "str", │  │
│  │      Operations         │  │    "emp_type": "string",│  │
│  │    <start_date>         │  │    "location": "string" │  │
│  │      2024-03-01         │  │  }                      │  │
│  │    <contract_type>      │  │                         │  │
│  │      FULL_TIME          │  │  ← This is the JSON     │  │
│  │    <office_location>    │  │    contract System B    │  │
│  │      London             │  │    expects. Editable.   │  │
│  │  </record>              │  │                         │  │
│  │                         │  │                         │  │
│  │  ← Editable. Paste your │  │                         │  │
│  │    own XML to try it.   │  │                         │  │
│  └─────────────────────────┘  └─────────────────────────┘  │
│                                                             │
│  ℹ️  This payload contains only T2/T3 fields.              │
│     NexBridge will apply standard governed transformation.  │
│                                                             │
│                  [ Run Transformation → ]                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**HOLD scenario variant — context hint:**
```
  ⚠️  This payload contains weight_limit — a T1 Safety Critical field.
     NexBridge will apply dual-agent verification with 100% confidence
     threshold. Any ambiguity will trigger a HOLD.
```

**Scenario Toggle:**
- Two pill buttons side by side at the top
- Active scenario highlighted in indigo
- Switching pre-loads both XML and schema panels
- Context hint below updates automatically

---

## Step 3 — Pipeline (The Visual Hero)

**Purpose:** Show the agent pipeline executing in real time.
Every step is visible. The user understands what is happening
and why each agent exists.

**Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│  Payload Tier:  [ T1 — Safety Critical ]                    │
│  Processing weight_limit and 4 other fields...              │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  ① CLASSIFICATION                       ✓ Complete  │  │
│  │  ─────────────────────────────────────────────────── │  │
│  │  employee_id     [ T3 Business Important ]           │  │
│  │  department      [ T3 Business Important ]           │  │
│  │  weight_limit    [ T1 Safety Critical   ]  ← T1      │  │
│  │  equipment_class [ T2 Ops Sensitive     ]            │  │
│  │  clearance_level [ T2 Ops Sensitive     ]            │  │
│  └──────────────────────────────────────────────────────┘  │
│                           ↓                                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  ② INTERPRETER — Run 1                  ⟳ Running   │  │
│  │  Semantically mapping fields to target schema...     │  │
│  └──────────────────────────────────────────────────────┘  │
│                           ↓                                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  ③ INTERPRETER — Run 2 (T1 only)        ◌ Waiting   │  │
│  │  Independent verification for safety-critical fields │  │
│  └──────────────────────────────────────────────────────┘  │
│                           ↓                                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  ④ VALIDATOR                            ◌ Waiting   │  │
│  └──────────────────────────────────────────────────────┘  │
│                           ↓                                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  ⑤ TRANSLATOR                           ◌ Waiting   │  │
│  └──────────────────────────────────────────────────────┘  │
│                           ↓                                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  ⑥ ORCHESTRATOR DECISION                ◌ Waiting   │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Agent Card States:**
```
◌ Waiting    → gray,   muted, not started
⟳ Running   → indigo, animated pulse ring
✓ Complete  → green,  success
⚠ Hold      → red,    blocked
```

**Expanded Agent Card (after complete):**
```
┌──────────────────────────────────────────────────────────┐
│  ② INTERPRETER — Run 1                      ✓ Complete  │
│  ─────────────────────────────────────────────────────── │
│  employee_id    [T3] →  id                ████████▓  0.98│
│  department     [T3] →  dept_code         ███████░░  0.87│
│  weight_limit   [T1] →  max_permitted_load████████▓  0.95│
│  equipment_class[T2] →  equipment_type    ████████░  0.91│
│  clearance_level[T2] →  access_level      ███████▓░  0.96│
└──────────────────────────────────────────────────────────┘
```

**HOLD scenario — divergence display:**
```
┌──────────────────────────────────────────────────────────┐
│  ③ INTERPRETER — Run 2 (T1 only)            ⚠ Diverged  │
│  ─────────────────────────────────────────────────────── │
│  weight_limit   [T1]                                     │
│    Run 1 → max_permitted_load   0.95                     │
│    Run 2 → weight_capacity      0.91                     │
│    ⚠ Outputs disagree — HOLD triggered                   │
└──────────────────────────────────────────────────────────┘
```

---

## Step 4 — Result + Audit

**Purpose:** Show the outcome clearly. For GO — the governed
transformation. For HOLD — the safety governance in action.

**GO Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│              ┌──────────────────────────┐                  │
│              │   ✓  GO                  │                  │
│              │   Transformation complete│                  │
│              │   5 fields mapped        │                  │
│              │   Processed in 2.1s      │                  │
│              └──────────────────────────┘                  │
│                                                             │
│  ┌──────────────────────────┐  ┌──────────────────────┐   │
│  │  SYSTEM A — Original XML │  │  SYSTEM B — JSON Out │   │
│  │  ────────────────────    │  │  ─────────────────── │   │
│  │  <record>                │  │  {                   │   │
│  │    <employee_id>         │  │    "id": "E-12345",  │   │
│  │      E-12345             │  │    "dept_code": "OPS"│   │
│  │    <department>          │  │    "start_date":     │   │
│  │      Operations          │  │      "2024-03-01",   │   │
│  │    ...                   │  │    ...               │   │
│  │  </record>               │  │  }                   │   │
│  └──────────────────────────┘  └──────────────────────┘   │
│                                                             │
│  AUDIT LOG                                                  │
│  ──────────────────────────────────────────────────────    │
│  ▼  employee_id    T3  →  id              0.98  mapped     │
│  ▼  department     T3  →  dept_code       0.87  mapped     │
│  ▼  start_date     T3  →  start_date      0.99  mapped     │
│  ▼  contract_type  T2  →  emp_type        0.96  mapped     │
│  ▼  office_location T4 →  location        0.82  mapped     │
│  ▼  ORCHESTRATOR   T2  →  GO             —     released    │
│                                                             │
│  [ ← Back ]           [ Try HOLD scenario ]               │
└─────────────────────────────────────────────────────────────┘
```

**HOLD Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│              ┌──────────────────────────────┐              │
│              │   ⚠  HOLD                    │              │
│              │   Payload not released       │              │
│              │   T1 field: interpreter      │              │
│              │   outputs diverged           │              │
│              │   Human review required      │              │
│              └──────────────────────────────┘              │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  DIVERGENCE DETAIL                                   │  │
│  │  weight_limit  [T1 Safety Critical]                  │  │
│  │    Run 1 mapped to → max_permitted_load  (conf 0.95) │  │
│  │    Run 2 mapped to → weight_capacity     (conf 0.91) │  │
│  │    Interpreters disagreed — payload blocked          │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  AUDIT LOG                                                  │
│  ──────────────────────────────────────────────────────    │
│  ▼  employee_id    T3  →  id              0.98  mapped     │
│  ▼  weight_limit   T1  →  DIVERGED        —     HOLD       │
│  ▼  ORCHESTRATOR   T1  →  HOLD           —     blocked     │
│                                                             │
│  [ ← Back ]              [ Try GO scenario ]              │
└─────────────────────────────────────────────────────────────┘
```

---

## Component Hierarchy

```
App.tsx
│
├── ProgressBar.tsx              ← Steps 1/2/3/4 always at top
│
├── pages/
│   ├── LandingPage.tsx          ← Step 1
│   ├── ConfigurePage.tsx        ← Step 2
│   ├── PipelinePage.tsx         ← Step 3
│   └── ResultPage.tsx           ← Step 4
│
└── components/
    ├── ScenarioToggle.tsx       ← GO / HOLD toggle
    ├── TierBadge.tsx            ← T1/T2/T3/T4 colour badge
    ├── AgentCard.tsx            ← Pipeline agent card
    │   └── ConfidenceBar.tsx    ← Per-field confidence bar
    ├── DecisionBadge.tsx        ← GO / HOLD / ESCALATE
    ├── XmlViewer.tsx            ← Syntax-highlighted XML
    ├── JsonViewer.tsx           ← Syntax-highlighted JSON
    ├── DivergenceDetail.tsx     ← HOLD scenario detail card
    └── AuditLog.tsx             ← Audit entry list
```

---

## TypeScript Types

```typescript
// src/types/nexbridge.types.ts

export type Decision    = 'GO' | 'HOLD' | 'ESCALATE'
export type AgentStatus = 'idle' | 'running' | 'complete' | 'hold' | 'error'
export type Tier        = 1 | 2 | 3 | 4
export type Scenario    = 'GO' | 'HOLD'

export interface FieldClassification {
  field_name: string
  tier: Tier
  label: string
  confidence_threshold: number
}

export interface FieldMapping {
  field_name: string
  target_field: string
  transformed_value: unknown
  confidence: number
  reasoning: string
}

export interface DivergenceDetail {
  field_name: string
  tier: Tier
  run_1_target: string
  run_1_confidence: number
  run_2_target: string
  run_2_confidence: number
}

export interface AuditEntry {
  timestamp: string
  field_name: string
  tier: Tier
  original_value: string
  transformed_value: unknown
  confidence: number
  agent: string
  decision: string
  reasoning: string
}

export interface TransformResponse {
  status: Decision
  transformed_payload: object | null
  payload_tier: Tier
  decision_reason: string
  confidence_scores: Record<string, number>
  field_classifications: Record<string, FieldClassification>
  field_mappings: Record<string, FieldMapping>
  divergence?: DivergenceDetail
  audit_log: AuditEntry[]
  processing_time_ms: number
}
```

---

## Mock Scenarios — Pre-loaded Data

### GO Scenario
```typescript
// System A — XML payload (T2/T3 fields only)
const GO_XML = `<record>
  <employee_id>E-12345</employee_id>
  <department>Operations</department>
  <start_date>2024-03-01</start_date>
  <contract_type>FULL_TIME</contract_type>
  <office_location>London</office_location>
</record>`

// System B — Target API contract
const GO_SCHEMA = {
  "id": "string",
  "dept_code": "string",
  "start_date": "string",
  "emp_type": "string",
  "location": "string"
}
```

### HOLD Scenario
```typescript
// System A — XML payload (contains T1 field)
const HOLD_XML = `<record>
  <employee_id>E-12345</employee_id>
  <department>Operations</department>
  <weight_limit>250</weight_limit>
  <equipment_class>HEAVY</equipment_class>
  <clearance_level>L3</clearance_level>
</record>`

// System B — Target API contract
const HOLD_SCHEMA = {
  "id": "string",
  "dept_code": "string",
  "max_permitted_load": "number",
  "equipment_type": "string",
  "access_level": "string"
}
```

---

## Mock Agent Timings (Phase 1)

```typescript
// Simulated delays to show pipeline animation
const MOCK_TIMINGS = {
  classification:     400,   // ms
  interpreter_run_1:  900,
  interpreter_run_2:  900,   // T1 only
  comparison:         300,   // T1 only
  validation:         500,
  translation:        300,
  decision:           200,
}
```

---

## Phase 1 — Mock Data Strategy

The backend does not exist in Phase 1.
All components use mock data with simulated timing delays
to show the full animated pipeline flow.

The API service (nexbridgeApi.ts) returns mock responses in Phase 1.
In Phase 3 the same service is updated to call the real FastAPI backend.
No component code changes between Phase 1 and Phase 3.

---

## Locked Files — Never Modify Without @TechLead

```
src/constants/tiers.ts
src/types/nexbridge.types.ts
src/services/nexbridgeApi.ts
src/components/AgentCard.tsx   (after Phase 1 sign-off)
```

---

**Document Version:** 2.1
**Project:** NexBridge
**Maintained By:** Lasith Jayarathne (@TechLead)
**Last Updated:** March 2026
**Changes from v2.0:** Added business scenario context,
  updated Step 2 to show both system contracts side by side,
  output schema visible and editable, full mock data defined.
