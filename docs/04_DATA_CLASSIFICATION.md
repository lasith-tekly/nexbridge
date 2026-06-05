# NexBridge - Data Classification Framework

## Overview

The Classification Framework is the heart of NexBridge's governance model.
Every field in a payload is assigned a tier before any transformation occurs.
The tier determines the processing protocol — proportionate governance
rather than one-size-fits-all treatment.

---

## The Four Tiers

### Tier 1 — Safety Critical
```
Confidence threshold:  1.0 (100%) — no exceptions
Processing:            Dual-agent verification mandatory
Escalation:            Human gate before release
Audit:                 Immutable full-trace log entry
Payload rule:          ANY T1 field = entire payload is T1
```

### Tier 2 — Operationally Sensitive
```
Confidence threshold:  0.95 (95%)
Processing:            Single agent + validator
Escalation:            Anomaly flag attached to payload
Audit:                 Structured log entry
```

### Tier 3 — Business Important
```
Confidence threshold:  0.80 (80%)
Processing:            Standard transformation
Escalation:            Log on error only
Audit:                 Error log only
```

### Tier 4 — Informational
```
Confidence threshold:  0.0 (best effort)
Processing:            Pass-through
Escalation:            None
Audit:                 None required
```

---

## Classification Registry — Aviation Example

The registry below demonstrates how FM fields map to tiers.
This is the reference example. Domain experts configure
their own registry for each deployment.

### Tier 1 — Safety Critical Fields
```json
{
  "MTOW":           { "tier": 1, "label": "Max Takeoff Weight" },
  "ZFW":            { "tier": 1, "label": "Zero Fuel Weight" },
  "FUEL_LOAD":      { "tier": 1, "label": "Fuel Load" },
  "CG_LIMIT_FWD":   { "tier": 1, "label": "CG Forward Limit" },
  "CG_LIMIT_AFT":   { "tier": 1, "label": "CG Aft Limit" },
  "PAX_COUNT":      { "tier": 1, "label": "Passenger Count" },
  "ACFT_TYPE":      { "tier": 1, "label": "Aircraft Type" },
  "DG_INDICATOR":   { "tier": 1, "label": "Dangerous Goods" },
  "STRUCT_LIMIT":   { "tier": 1, "label": "Structural Load Limit" }
}
```

### Tier 2 — Operationally Sensitive Fields
```json
{
  "FLT_NUM":        { "tier": 2, "label": "Flight Number" },
  "DEP_APT":        { "tier": 2, "label": "Departure Airport" },
  "ARR_APT":        { "tier": 2, "label": "Arrival Airport" },
  "GATE":           { "tier": 2, "label": "Departure Gate" },
  "ACFT_REG":       { "tier": 2, "label": "Aircraft Registration" },
  "CREW_ID":        { "tier": 2, "label": "Crew Identifier" },
  "STD":            { "tier": 2, "label": "Scheduled Departure" },
  "STA":            { "tier": 2, "label": "Scheduled Arrival" },
  "TURNAROUND":     { "tier": 2, "label": "Turnaround Status" }
}
```

### Tier 3 — Business Important Fields
```json
{
  "PAX_NAME":       { "tier": 3, "label": "Passenger Name" },
  "SEAT_NO":        { "tier": 3, "label": "Seat Number" },
  "MEAL_PREF":      { "tier": 3, "label": "Meal Preference" },
  "LOYALTY_NUM":    { "tier": 3, "label": "Loyalty Number" },
  "BAG_COUNT":      { "tier": 3, "label": "Baggage Count" },
  "SPECIAL_ASST":   { "tier": 3, "label": "Special Assistance" },
  "SSR_CODE":       { "tier": 3, "label": "Special Service Request" }
}
```

### Tier 4 — Informational Fields
```json
{
  "INT_REF":        { "tier": 4, "label": "Internal Reference" },
  "TIMESTAMP":      { "tier": 4, "label": "Message Timestamp" },
  "OP_COMMENT":     { "tier": 4, "label": "Operator Comment" },
  "SEQ_NUM":        { "tier": 4, "label": "Sequence Number" },
  "SYS_META":       { "tier": 4, "label": "System Metadata" }
}
```

---

## Payload Inheritance Rule

```
RULE: If a payload contains ANY Tier 1 field,
      the ENTIRE payload is processed under Tier 1 protocol.

EXAMPLE:
  Payload fields: MTOW (T1), FLT_NUM (T2), PAX_NAME (T3)
  Payload tier:   T1
  Protocol:       Dual-agent, 100% confidence, human gate

REASON:
  A payload containing safety-critical data cannot be
  partially governed. All fields must receive maximum
  scrutiny to ensure payload integrity.
```

---

## Registry Configuration Format

The registry lives in `backend/core/classification/registry.json`.
Domain experts edit this file directly — no code changes required.

```json
{
  "version": "1.0",
  "domain": "aviation",
  "fields": {
    "FIELD_NAME": {
      "tier": 1,
      "label": "Human readable name",
      "description": "What this field represents",
      "examples": ["value1", "value2"]
    }
  },
  "default_tier": 4
}
```

---

## How to Add a New Field

1. Identify the correct tier based on operational impact
2. Open `backend/core/classification/registry.json`
3. Add the field entry with tier, label, description
4. For T1 fields → get @TechLead approval first
5. Update this document with the new field
6. Restart the API to reload the registry

---

## Tier Decision Guide

Use this guide when classifying a new field:

```
QUESTION 1: Could a wrong value cause physical harm or unsafe operation?
  YES → Tier 1

QUESTION 2: Could a wrong value disrupt a flight or operational process?
  YES → Tier 2

QUESTION 3: Could a wrong value affect a passenger or business outcome?
  YES → Tier 3

QUESTION 4: Is this reference, metadata, or logging data?
  YES → Tier 4
```

---

**Document Version:** 1.0
**Project:** NexBridge
**Maintained By:** Lasith Jayarathne (@TechLead)
**Last Updated:** March 2026
