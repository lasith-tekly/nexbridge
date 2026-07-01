import type { TransformResponse, AuditEntry } from '@/types/nexbridge.types';

export const mockGoResponse: TransformResponse = {
  decision: 'GO',
  decision_reason: 'All fields passed confidence thresholds',
  payload_tier: 2,
  translated_payload: '{"max_takeoff_weight": 75000, "flight_number": "BA123"}',
  confidence_scores: {
    MTOW: 1.0,
    FLT_NUM: 0.98
  },
  anomaly_count: 0,
  processing_time_ms: 1842,
  audit_log: [
    {
      timestamp: '2026-03-06T14:20:00Z',
      field_name: 'MTOW',
      tier: 2,
      original_value: '75000',
      transformed_value: 75000,
      confidence: 1.0,
      agent: 'audit',
      decision: 'GO',
      reasoning: 'Field classified as Tier 2, confidence above threshold (0.95)'
    },
    {
      timestamp: '2026-03-06T14:20:01Z',
      field_name: 'FLT_NUM',
      tier: 2,
      original_value: 'BA123',
      transformed_value: 'BA123',
      confidence: 0.98,
      agent: 'audit',
      decision: 'GO',
      reasoning: 'Field classified as Tier 2, confidence above threshold (0.95)'
    }
  ] as AuditEntry[],
};

export const mockHoldResponse: TransformResponse = {
  decision: 'HOLD',
  decision_reason: 'T1 field MTOW: dual interpreter divergence detected',
  payload_tier: 1,
  translated_payload: null,
  confidence_scores: {
    MTOW: 0.87
  },
  anomaly_count: 1,
  processing_time_ms: 2103,
  audit_log: [
    {
      timestamp: '2026-03-06T14:20:00Z',
      field_name: 'MTOW',
      tier: 1,
      original_value: '75000',
      transformed_value: null,
      confidence: 0.87,
      agent: 'audit',
      decision: 'HOLD',
      reasoning: 'Tier 1 field: dual interpreter run detected divergence. Manual review required.'
    }
  ] as AuditEntry[],
};

export const mockEscalateResponse: TransformResponse = {
  decision: 'ESCALATE',
  decision_reason: 'Confidence below threshold for Tier 2 field',
  payload_tier: 2,
  translated_payload: null,
  confidence_scores: {
    DEPARTURE_TIME: 0.89
  },
  anomaly_count: 1,
  processing_time_ms: 1654,
  audit_log: [
    {
      timestamp: '2026-03-06T14:20:00Z',
      field_name: 'DEPARTURE_TIME',
      tier: 2,
      original_value: '14:30',
      transformed_value: null,
      confidence: 0.89,
      agent: 'audit',
      decision: 'ESCALATE',
      reasoning: 'Confidence 0.89 below Tier 2 threshold (0.95). Escalating for review.'
    }
  ] as AuditEntry[],
};
