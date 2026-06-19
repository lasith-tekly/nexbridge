import React, { useState, useEffect } from 'react'
import { DecisionBadge } from '@/components/DecisionBadge'
import { DivergenceDetail } from '@/components/DivergenceDetail'
import { XmlViewer } from '@/components/XmlViewer'
import { JsonViewer } from '@/components/JsonViewer'
import { AuditLog } from '@/components/AuditLog'
import type { Scenario, AuditEntry, DivergenceDetail as DivergenceDetailType, TransformResponse } from '@/types/nexbridge.types'

interface ResultPageProps {
  onBack: () => void;
  onRestart: () => void;
  scenario: Scenario;
  transformResult: TransformResponse | null;
}

const GO_XML = `<record>
  <employee_id>E-12345</employee_id>
  <department>Operations</department>
  <start_date>2024-03-01</start_date>
  <contract_type>FULL_TIME</contract_type>
  <office_location>London</office_location>
</record>`

const HOLD_XML = `<record>
  <employee_id>E-12345</employee_id>
  <department>Operations</department>
  <weight_limit>250</weight_limit>
  <equipment_class>HEAVY</equipment_class>
  <clearance_level>L3</clearance_level>
</record>`

const GO_JSON = {
  id: 'E-12345',
  dept_code: 'OPS',
  start_date: '2024-03-01',
  emp_type: 'FULL_TIME',
  location: 'London'
}

const GO_AUDIT_ENTRIES: AuditEntry[] = [
  {
    timestamp: '2024-03-10T10:30:01.123Z',
    field_name: 'employee_id',
    tier: 3,
    original_value: 'E-12345',
    transformed_value: 'E-12345',
    confidence: 0.98,
    agent: 'Interpreter',
    decision: 'mapped',
    reasoning: 'Direct field match with high confidence'
  },
  {
    timestamp: '2024-03-10T10:30:01.234Z',
    field_name: 'department',
    tier: 3,
    original_value: 'Operations',
    transformed_value: 'OPS',
    confidence: 0.87,
    agent: 'Interpreter',
    decision: 'mapped',
    reasoning: 'Standard department code mapping'
  },
  {
    timestamp: '2024-03-10T10:30:01.345Z',
    field_name: 'start_date',
    tier: 3,
    original_value: '2024-03-01',
    transformed_value: '2024-03-01',
    confidence: 0.99,
    agent: 'Interpreter',
    decision: 'mapped',
    reasoning: 'ISO date format preserved'
  },
  {
    timestamp: '2024-03-10T10:30:01.456Z',
    field_name: 'contract_type',
    tier: 2,
    original_value: 'FULL_TIME',
    transformed_value: 'FULL_TIME',
    confidence: 0.96,
    agent: 'Interpreter',
    decision: 'mapped',
    reasoning: 'Employment type standardized'
  },
  {
    timestamp: '2024-03-10T10:30:01.567Z',
    field_name: 'office_location',
    tier: 4,
    original_value: 'London',
    transformed_value: 'London',
    confidence: 0.82,
    agent: 'Interpreter',
    decision: 'mapped',
    reasoning: 'Location field mapped'
  },
  {
    timestamp: '2024-03-10T10:30:02.100Z',
    field_name: 'ORCHESTRATOR',
    tier: 2,
    original_value: '—',
    transformed_value: 'GO',
    confidence: null,
    agent: 'Orchestrator',
    decision: 'released',
    reasoning: 'All fields within confidence thresholds'
  }
]

const HOLD_AUDIT_ENTRIES: AuditEntry[] = [
  {
    timestamp: '2024-03-10T10:30:01.123Z',
    field_name: 'employee_id',
    tier: 3,
    original_value: 'E-12345',
    transformed_value: 'E-12345',
    confidence: 0.98,
    agent: 'Interpreter',
    decision: 'mapped',
    reasoning: 'Direct field match with high confidence'
  },
  {
    timestamp: '2024-03-10T10:30:01.234Z',
    field_name: 'department',
    tier: 3,
    original_value: 'Operations',
    transformed_value: 'OPS',
    confidence: 0.87,
    agent: 'Interpreter',
    decision: 'mapped',
    reasoning: 'Standard department code mapping'
  },
  {
    timestamp: '2024-03-10T10:30:01.345Z',
    field_name: 'weight_limit',
    tier: 1,
    original_value: '250',
    transformed_value: 'DIVERGED',
    confidence: null,
    agent: 'Interpreter',
    decision: 'diverged',
    reasoning: 'T1 dual-agent outputs disagreed'
  },
  {
    timestamp: '2024-03-10T10:30:02.100Z',
    field_name: 'ORCHESTRATOR',
    tier: 1,
    original_value: '—',
    transformed_value: 'HOLD',
    confidence: null,
    agent: 'Orchestrator',
    decision: 'blocked',
    reasoning: 'T1 field divergence detected'
  }
]

const DIVERGENCE_DETAIL: DivergenceDetailType = {
  fieldName: 'weight_limit',
  run1: {
    targetField: 'max_permitted_load',
    confidence: 0.95
  },
  run2: {
    targetField: 'weight_capacity',
    confidence: 0.91
  }
}

export const ResultPage: React.FC<ResultPageProps> = ({
  onBack,
  onRestart,
  scenario,
  transformResult,
}) => {
  const [showContent, setShowContent] = useState(false)

  useEffect(() => {
    setShowContent(true)
  }, [])

  const decision = transformResult?.decision ?? (scenario === 'GO' ? 'GO' : 'HOLD')
  const decisionReason = transformResult?.decision_reason ?? (
    scenario === 'GO'
      ? 'Transformation complete — payload released'
      : 'Payload not released — human review required'
  )
  const fieldCount = transformResult
    ? Object.keys(transformResult.confidence_scores).length
    : 5
  const processingTimeMs = transformResult?.processing_time_ms ?? 2100
  const auditEntries = transformResult?.audit_log?.length
    ? transformResult.audit_log
    : (scenario === 'GO' ? GO_AUDIT_ENTRIES : HOLD_AUDIT_ENTRIES)

  const outputContent = (() => {
    if (!transformResult?.translated_payload) return null
    try {
      return JSON.parse(transformResult.translated_payload)
    } catch {
      return transformResult.translated_payload
    }
  })()

  const isHold = decision === 'HOLD'

  return (
    <div className="min-h-[calc(100vh-120px)] bg-gray-950 px-6 py-10">
      <div
        className={`max-w-5xl mx-auto transition-opacity duration-400 ${
          showContent ? 'opacity-100' : 'opacity-0'
        }`}
      >
        <DecisionBadge
          decision={decision}
          reason={decisionReason}
          detail={isHold
            ? 'T1 field: dual interpreter outputs diverged'
            : `${fieldCount} fields mapped successfully`
          }
          processingTimeMs={processingTimeMs}
        />

        {isHold && (
          <div className="mt-6">
            <DivergenceDetail divergence={DIVERGENCE_DETAIL} />
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6">
          <div>
            <h2 className="text-base font-semibold text-white mb-3">
              System A — Original XML
            </h2>
            <XmlViewer
              content={scenario === 'GO' ? GO_XML : HOLD_XML}
              editable={false}
              highlightFields={scenario === 'HOLD' ? ['weight_limit'] : []}
            />
          </div>

          <div>
            <h2 className="text-base font-semibold text-white mb-3">
              System B — Transformed Output
            </h2>
            {!isHold && outputContent ? (
              <JsonViewer content={outputContent} editable={false} />
            ) : !isHold ? (
              <JsonViewer content={GO_JSON} editable={false} />
            ) : (
              <div className="bg-gray-900 border border-red-900 rounded-lg p-6 h-full flex flex-col items-center justify-center">
                <div className="text-2xl text-center">⛔</div>
                <p className="text-red-400 text-center font-medium mt-3">
                  — Payload not released —
                </p>
                <p className="text-gray-500 text-sm text-center mt-2">
                  NexBridge blocked this transformation. Human review required before retry.
                </p>
              </div>
            )}
          </div>
        </div>

        <div className="mt-6">
          <AuditLog entries={auditEntries} />
        </div>

        <div className="flex justify-between mt-8">
          <button
            onClick={onBack}
            className="bg-gray-800 hover:bg-gray-700 text-white px-6 py-3 rounded-lg transition-colors"
          >
            ← Try another scenario
          </button>
          <button
            onClick={onRestart}
            className="bg-indigo-600 hover:bg-indigo-500 text-white px-6 py-3 rounded-lg font-medium transition-colors"
          >
            Start over
          </button>
        </div>
      </div>
    </div>
  )
}
