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

export interface SystemAFieldInput {
  name: string;
  tier: number;
  threshold: number;
}

export interface ProposeMappingsRequest {
  domain: string;
  source_system: string;
  target_system: string;
  system_a_fields: SystemAFieldInput[];
  system_b_fields: string[];
}

export interface SystemBTierResult {
  tier: number;
  threshold: number;
  reasoning: string;
}

export interface MappingProposal {
  source_field: string;
  target_field: string;
  confidence: number;
  reasoning: string;
  source_tier: number;
  target_tier: number;
  tier_mismatch: boolean;
  effective_tier: number;
  effective_threshold: number;
}

export interface ProposeMappingsResponse {
  domain: string;
  source_system: string;
  target_system: string;
  system_b_tiers: Record<string, SystemBTierResult>;
  proposed_mappings: MappingProposal[];
  tier_mismatches: string[];
}

export interface ConfirmedMapping {
  sourceField: string;
  targetField: string;
  confidence: number;
  sourceTier: number;
  targetTier: number;
  effectiveTier: number;
  llmGenerated: boolean;
  confirmedAt: string;
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
