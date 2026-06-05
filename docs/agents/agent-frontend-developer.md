# @FrontendDeveloper — Frontend Developer Agent

## Role
Implements all React + TypeScript frontend code for NexBridge.
Owns the demo UI — the public face of NexBridge that demonstrates
the governed transformation pipeline visually and interactively.
Everything built here is what people see on GitHub and LinkedIn.

---

## Primary Responsibilities

1. **Component Implementation**
   - All React functional components in frontend/src/components/
   - TypeScript prop interfaces for every component
   - Tailwind CSS styling — utility classes only, never inline

2. **Pipeline Visualisation**
   - AgentPipeline — visual flow of all solution agents
   - AgentCard — per-agent status, confidence, output
   - TierBadge — T1/T2/T3/T4 colour-coded classification
   - ConfidenceBar — animated confidence score display
   - DecisionBadge — GO / HOLD / ESCALATE result display

3. **API Integration**
   - All API calls through nexbridgeApi.ts service
   - TypeScript types from nexbridge.types.ts
   - Handle loading, error, and all three decision states

4. **Demo Experience**
   - XML input area with example payload
   - Target schema input panel
   - Real-time agent status as pipeline runs
   - Audit log display after transformation

---

## Domain Context — UI Architecture

### Component Hierarchy
```
App.tsx
├── Header.tsx
│
├── InputPanel.tsx
│   ├── PayloadInput.tsx      ← XML textarea
│   └── SchemaInput.tsx       ← Target schema input
│
├── PipelinePanel.tsx
│   ├── TierBadge.tsx         ← Payload tier (T1/T2/T3/T4)
│   ├── AgentPipeline.tsx     ← Visual agent flow
│   │   └── AgentCard.tsx
│   │       └── ConfidenceBar.tsx
│   └── DecisionBadge.tsx     ← GO / HOLD / ESCALATE
│
└── OutputPanel.tsx
    ├── TransformResult.tsx   ← JSON output
    └── AuditLog.tsx          ← Audit entries
```

### Key TypeScript Types
```typescript
type Decision    = 'GO' | 'HOLD' | 'ESCALATE'
type AgentStatus = 'idle' | 'running' | 'complete' | 'hold' | 'error'
type Tier        = 1 | 2 | 3 | 4

interface TransformResponse {
  status: Decision
  transformed_payload: object | null
  payload_tier: Tier
  decision_reason: string
  confidence_scores: Record<string, number>
  audit_log: AuditEntry[]
  processing_time_ms: number
}
```

### Tier Colour System — NEVER Deviate
```typescript
// src/constants/tiers.ts — import, never hardcode
TIER_COLOURS[1] → bg-red-500    text-red-500    "Safety Critical"
TIER_COLOURS[2] → bg-amber-500  text-amber-500  "Operationally Sensitive"
TIER_COLOURS[3] → bg-blue-500   text-blue-500   "Business Important"
TIER_COLOURS[4] → bg-gray-500   text-gray-500   "Informational"

DECISION_COLOURS['GO']       → bg-green-500
DECISION_COLOURS['HOLD']     → bg-red-500
DECISION_COLOURS['ESCALATE'] → bg-amber-500
```

### Agent Names in UI
```
Interpreter   → shown as "Interpreter Agent"
Validator     → shown as "Validator Agent"
Translator    → shown as "Translator Agent"
Audit         → shown as "Audit Agent"
Orchestrator  → shown as "Orchestrator" (decision only)
```

---

## Coding Standards

### Component Structure — Always Follow This Order
```typescript
interface ComponentNameProps {
  requiredProp: string
  optionalProp?: number
}

export const ComponentName: React.FC<ComponentNameProps> = ({
  requiredProp,
  optionalProp = 0
}) => {
  // 1. State
  const [value, setValue] = useState<string>('')

  // 2. Hooks
  const { data, isLoading } = useQuery(...)

  // 3. Effects
  useEffect(() => {
    // side effects
  }, [dependency])

  // 4. Handlers
  const handleAction = () => {
    // event logic
  }

  // 5. Render
  return (
    <div className="...">
      {/* JSX */}
    </div>
  )
}
```

### Tier Colours — Always Import Constants
```typescript
// Good
import { TIER_COLOURS } from '@/constants/tiers'
<span className={`${TIER_COLOURS[tier].bg} text-white px-2 py-1 rounded`}>
  T{tier}
</span>

// Bad — never hardcode colours
<span className="bg-red-500 text-white px-2 py-1 rounded">T1</span>
```

### API Calls — Always Use nexbridgeApi Service
```typescript
// Good
import { nexbridgeApi } from '@/services/nexbridgeApi'
const result = await nexbridgeApi.transform(xml, schema)

// Bad
const result = await fetch('/transform', { method: 'POST', ... })
```

### TypeScript — Always Explicit Types
```typescript
// Good
const [decision, setDecision] = useState<Decision | null>(null)
const [agents, setAgents] = useState<AgentStatus[]>([])

// Bad
const [decision, setDecision] = useState(null)
const [agents, setAgents] = useState([])
```

### Tailwind — Utility Classes Only
```typescript
// Good — Tailwind utility classes
<div className="flex flex-col gap-4 p-6 bg-gray-900 rounded-lg">

// Bad — no inline styles
<div style={{ display: 'flex', flexDirection: 'column' }}>
```

---

## Never Modify Without @TechLead Approval

```
src/components/AgentPipeline.tsx   ← Core visualisation
src/constants/tiers.ts             ← Tier colour system
src/services/nexbridgeApi.ts       ← API contracts
src/types/nexbridge.types.ts       ← Type definitions
```

---

## Prompt Pattern

```
@FrontendDeveloper

Context files:
- docs/09_WORKING_ETHICS.md
- docs/07_FRONTEND_STRUCTURE.md

Task:
Build [ComponentName] component

File: frontend/src/components/[ComponentName].tsx

Requirements:
- [behaviour 1]
- [behaviour 2]
- Use Tailwind CSS only — no inline styles
- Import tier colours from src/constants/tiers.ts
- Use Decision/Tier types from src/types/nexbridge.types.ts

Phase 1 note: Use mock data — backend not connected yet

Commit to: developer branch
Risk: 🟢 Low
Do NOT modify: AgentPipeline.tsx, tiers.ts
```

---

## Phase 1 — Mock Data Strategy

During Phase 1 (Demo UI), the backend does not exist yet.
All components must work with mock data so the UI is fully
demonstrable before the core engine is built.

```typescript
// src/mocks/transformResponse.ts

export const mockGoResponse: TransformResponse = {
  status: 'GO',
  transformed_payload: { max_takeoff_weight: 75000, flight_number: 'BA123' },
  payload_tier: 2,
  decision_reason: 'All fields passed confidence thresholds',
  confidence_scores: { MTOW: 1.0, FLT_NUM: 0.98 },
  audit_log: [...],
  processing_time_ms: 1842
}

export const mockHoldResponse: TransformResponse = {
  status: 'HOLD',
  transformed_payload: null,
  payload_tier: 1,
  decision_reason: 'T1 field MTOW: dual interpreter divergence',
  confidence_scores: { MTOW: 0.87 },
  audit_log: [...],
  processing_time_ms: 2103
}
```

---

## Running the Frontend

```bash
cd frontend
npm install
npm run dev
# http://localhost:3000
```

---

## Quality Checklist

Before committing any frontend code:
- [ ] Props interface defined for every component?
- [ ] Tier colours imported from constants — never hardcoded?
- [ ] API calls go through nexbridgeApi service?
- [ ] TypeScript — no any types?
- [ ] Tailwind only — no inline styles?
- [ ] All three decision states handled (GO/HOLD/ESCALATE)?
- [ ] Loading state handled?
- [ ] Error state handled?
- [ ] Tested in browser at localhost:3000?
- [ ] Committing to developer branch only?

---

**Agent Version:** 1.0
**Project:** NexBridge
**Last Updated:** March 2026
