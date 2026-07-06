export interface AnalysedField {
  field_name: string
  suggested_tier: 1 | 2 | 3 | 4
  suggested_label: string
  reasoning: string
  confidence: number
}

export interface ConfirmedT1 {
  field_name: string
  confirmed_at: string
  final_tier: 1 | 2 | 3 | 4
}

export interface ReviewField {
  field_name: string
  tier: 1 | 2 | 3 | 4
  label: string
  threshold: number
  confirmed_individually: boolean
}

export interface ExportResult {
  filename: string
  content: string
  field_count: number
  t1_count: number
  registry_id: string
  saved_to_server: boolean
}
