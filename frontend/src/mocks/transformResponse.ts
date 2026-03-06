import type { TransformResponse, AuditEntry } from '@/types/nexbridge.types';

export const mockGoResponse: TransformResponse = {
  status: 'GO',
  transformed_payload: {
    max_takeoff_weight: 75000,
    flight_number: 'BA123'
  },
  payload_tier: 2,
  decision_reason: 'All fields passed confidence thresholds',
  confidence_scores: {
    MTOW: 1.0,
    FLT_NUM: 0.98
  },
  audit_log: [
    {
      timestamp: '2026-03-06T14:20:00Z',
      field_name: 'MTOW',
      tier: 2,
      original_value: '75000',
      transformed_value: 75000,
      confidence: 1.0,
      agent: 'Interpreter',
      decision: 'PASS',
      reasoning: 'Field classified as Tier 2, confidence above threshold (0.95)'
    },
    {
      timestamp: '2026-03-06T14:20:01Z',
      field_name: 'FLT_NUM',
      tier: 2,
      original_value: 'BA123',
      transformed_value: 'BA123',
      confidence: 0.98,
      agent: 'Interpreter',
      decision: 'PASS',
      reasoning: 'Field classified as Tier 2, confidence above threshold (0.95)'
    }
  ] as AuditEntry[],
  processing_time_ms: 1842
};

export const mockHoldResponse: TransformResponse = {
  status: 'HOLD',
  transformed_payload: null,
  payload_tier: 1,
  decision_reason: 'T1 field MTOW: dual interpreter divergence detected',
  confidence_scores: {
    MTOW: 0.87
  },
  audit_log: [
    {
      timestamp: '2026-03-06T14:20:00Z',
      field_name: 'MTOW',
      tier: 1,
      original_value: '75000',
      transformed_value: null,
      confidence: 0.87,
      agent: 'Interpreter',
      decision: 'HOLD',
      reasoning: 'Tier 1 field: dual interpreter run detected divergence. Manual review required.'
    }
  ] as AuditEntry[],
  processing_time_ms: 2103
};

export const mockEscalateResponse: TransformResponse = {
  status: 'ESCALATE',
  transformed_payload: null,
  payload_tier: 2,
  decision_reason: 'Confidence below threshold for Tier 2 field',
  confidence_scores: {
    DEPARTURE_TIME: 0.89
  },
  audit_log: [
    {
      timestamp: '2026-03-06T14:20:00Z',
      field_name: 'DEPARTURE_TIME',
      tier: 2,
      original_value: '14:30',
      transformed_value: null,
      confidence: 0.89,
      agent: 'Interpreter',
      decision: 'ESCALATE',
      reasoning: 'Confidence 0.89 below Tier 2 threshold (0.95). Escalating for review.'
    }
  ] as AuditEntry[],
  processing_time_ms: 1654
};
