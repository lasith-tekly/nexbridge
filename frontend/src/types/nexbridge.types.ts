export type Decision = 'GO' | 'HOLD' | 'ESCALATE';
export type AgentStatus = 'idle' | 'running' | 'complete' | 'hold' | 'error';
export type Tier = 1 | 2 | 3 | 4;
export type Scenario = 'GO' | 'HOLD';

export interface TransformResponse {
  decision: Decision;
  decision_reason: string;
  payload_tier: number;
  translated_payload: string | null;
  confidence_scores: Record<string, number>;
  anomaly_count: number;
  processing_time_ms: number;
  audit_log: AuditEntry[];
}

export interface RegistryFieldInfo {
  tier: number;
  label: string;
  threshold: number;
}

export interface ClassifyResponse {
  payload_tier: number;
  classifications: Record<string, RegistryFieldInfo>;
}

export interface AuditEntry {
  timestamp: string;
  field_name: string;
  tier: Tier;
  original_value: string;
  transformed_value: unknown;
  confidence: number | null;
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
