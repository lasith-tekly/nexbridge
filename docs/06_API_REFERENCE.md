# NexBridge - API Reference

## Overview

NexBridge exposes a REST API via FastAPI. All endpoints
accept and return JSON. The API runs on port 8000 by default.

Base URL: `http://localhost:8000`

---

## Endpoints

---

### POST /transform

Transform an XML payload to JSON using the NexBridge pipeline.

**Request Body:**
```json
{
  "xml_payload": "<flight><MTOW>75000</MTOW><FLT_NUM>BA123</FLT_NUM></flight>",
  "target_schema": {
    "max_takeoff_weight": "number",
    "flight_number": "string"
  },
  "options": {
    "strict_mode": true,
    "include_audit": true
  }
}
```

**Fields:**
| Field | Type | Required | Description |
|---|---|---|---|
| xml_payload | string | Yes | Well-formed XML string |
| target_schema | object | Yes | Target JSON field map |
| options.strict_mode | boolean | No | Default true. Blocks on any anomaly |
| options.include_audit | boolean | No | Default true. Includes audit log |

**Response — GO:**
```json
{
  "status": "GO",
  "transformed_payload": {
    "max_takeoff_weight": 75000,
    "flight_number": "BA123"
  },
  "payload_tier": 1,
  "decision_reason": "All T1 fields passed dual-agent verification at 1.0 confidence",
  "confidence_scores": {
    "MTOW": 1.0,
    "FLT_NUM": 0.98
  },
  "audit_log": [
    {
      "timestamp": "2026-03-05T10:23:11Z",
      "field_name": "MTOW",
      "tier": 1,
      "original_value": "75000",
      "transformed_value": 75000,
      "confidence": 1.0,
      "agent": "interpreter",
      "decision": "mapped",
      "reasoning": "MTOW maps directly to max_takeoff_weight as numeric value"
    }
  ],
  "processing_time_ms": 1842
}
```

**Response — HOLD:**
```json
{
  "status": "HOLD",
  "transformed_payload": null,
  "payload_tier": 1,
  "decision_reason": "T1 field MTOW: dual interpreter divergence detected",
  "field_trace": {
    "MTOW": {
      "run_1": { "target_field": "max_takeoff_weight", "value": 75000 },
      "run_2": { "target_field": "mtow_kg", "value": 75000 },
      "diverged": true
    }
  },
  "audit_log": [ ... ],
  "processing_time_ms": 2103
}
```

**Response — ESCALATE:**
```json
{
  "status": "ESCALATE",
  "transformed_payload": null,
  "payload_tier": 1,
  "decision_reason": "T1 field MTOW: confidence 0.87 below required threshold 1.0",
  "confidence_scores": {
    "MTOW": 0.87
  },
  "audit_log": [ ... ],
  "processing_time_ms": 1654
}
```

**Error Responses:**
```json
{ "status": 400, "detail": "Invalid XML: unclosed tag at line 3" }
{ "status": 422, "detail": "target_schema is required" }
{ "status": 500, "detail": "Agent processing error: interpreter timeout" }
```

---

### GET /registry

Returns the current classification registry.

**Response:**
```json
{
  "version": "1.0",
  "domain": "aviation",
  "total_fields": 25,
  "fields": [
    {
      "field_name": "MTOW",
      "tier": 1,
      "label": "Max Takeoff Weight",
      "description": "Maximum certified takeoff weight"
    },
    {
      "field_name": "FLT_NUM",
      "tier": 2,
      "label": "Flight Number",
      "description": "IATA flight identifier"
    }
  ]
}
```

---

### GET /health

Returns API and agent health status.

**Response:**
```json
{
  "status": "healthy",
  "registry_loaded": true,
  "agent_count": 4,
  "agents": {
    "interpreter": "ready",
    "validator": "ready",
    "translator": "ready",
    "audit": "ready"
  },
  "anthropic_api": "connected",
  "version": "0.1.0"
}
```

---

### POST /classify

Classify a list of field names without running transformation.
Useful for testing registry mappings.

**Request Body:**
```json
{
  "fields": ["MTOW", "FLT_NUM", "PAX_NAME", "UNKNOWN_FIELD"]
}
```

**Response:**
```json
{
  "classifications": [
    { "field_name": "MTOW",          "tier": 1, "label": "Safety Critical" },
    { "field_name": "FLT_NUM",       "tier": 2, "label": "Operationally Sensitive" },
    { "field_name": "PAX_NAME",      "tier": 3, "label": "Business Important" },
    { "field_name": "UNKNOWN_FIELD", "tier": 4, "label": "Informational (default)" }
  ],
  "payload_tier": 1
}
```

---

## Running the API

```bash
cd backend
source venv/bin/activate
uvicorn api.main:app --reload --port 8000
```

API docs available at: `http://localhost:8000/docs`

---

## Error Handling Standards

All errors follow this structure:
```json
{
  "status": 400 | 422 | 500,
  "detail": "Human readable error message",
  "field": "field_name if field-specific",
  "code": "ERROR_CODE"
}
```

Error codes:
```
INVALID_XML           XML payload is malformed
MISSING_SCHEMA        target_schema not provided
REGISTRY_NOT_LOADED   Classification registry failed to load
AGENT_TIMEOUT         Agent did not respond in time
T1_DIVERGENCE         T1 dual-agent outputs diverged
T1_CONFIDENCE_FAIL    T1 confidence below 1.0
API_KEY_MISSING       ANTHROPIC_API_KEY not in environment
```

---

**Document Version:** 1.0
**Project:** NexBridge
**Maintained By:** Lasith Jayarathne (@TechLead)
**Last Updated:** March 2026
