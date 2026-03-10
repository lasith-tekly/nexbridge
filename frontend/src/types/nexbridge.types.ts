export type Decision = 'GO' | 'HOLD' | 'ESCALATE';
export type AgentStatus = 'idle' | 'running' | 'complete' | 'hold' | 'error';
export type Tier = 1 | 2 | 3 | 4;
export type Scenario = 'GO' | 'HOLD';

export interface TransformResponse {
  status: Decision;
  transformed_payload: object | null;
  payload_tier: Tier;
  decision_reason: string;
  confidence_scores: Record<string, number>;
  audit_log: AuditEntry[];
  processing_time_ms: number;
}

export interface AuditEntry {
  timestamp: string;
  field_name: string;
  tier: Tier;
  original_value: string;
  transformed_value: unknown;
  confidence: number;
  agent: string;
  decision: string;
  reasoning: string;
}

export interface FieldMapping {
  field_name: string;
  target_field: string;
  transformed_value: unknown;
  confidence: number;
  tier: Tier;
}

export interface DivergenceDetail {
  fieldName: string;
  run1: {
    targetField: string;
    confidence: number;
  };
  run2: {
    targetField: string;
    confidence: number;
  };
}
