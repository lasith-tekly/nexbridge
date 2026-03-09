import React from 'react'
import { DecisionBadge } from '@/components/DecisionBadge'
import type { Scenario } from '@/types/nexbridge.types'

interface ResultPageProps {
  onBack: () => void;
  onRestart: () => void;
  scenario: Scenario;
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

const GO_JSON = `{
  "id": "E-12345",
  "dept_code": "OPS",
  "start_date": "2024-03-01",
  "emp_type": "FULL_TIME",
  "location": "London"
}`

export const ResultPage: React.FC<ResultPageProps> = ({
  onBack,
  onRestart,
  scenario
}) => {
  return (
    <div className="min-h-[calc(100vh-120px)] bg-gray-950 px-4 py-8">
      <div className="max-w-6xl mx-auto">
        {scenario === 'GO' ? (
          <DecisionBadge
            decision="GO"
            reason="Transformation complete — payload released"
            detail="5 fields mapped"
            processingTimeMs={2100}
          />
        ) : (
          <DecisionBadge
            decision="HOLD"
            reason="Payload not released — human review required"
            detail="T1 field: dual interpreter outputs diverged"
          />
        )}
        <div className="mb-8" />

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          <div>
            <h2 className="text-xl font-semibold text-white mb-4">
              System A — Original XML
            </h2>
            <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
              <pre className="text-green-400 font-mono text-sm whitespace-pre-wrap">
                {scenario === 'GO' ? GO_XML : HOLD_XML}
              </pre>
            </div>
          </div>

          <div>
            <h2 className="text-xl font-semibold text-white mb-4">
              System B — Transformed JSON
            </h2>
            {scenario === 'GO' ? (
              <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
                <pre className="text-blue-400 font-mono text-sm whitespace-pre-wrap">
                  {GO_JSON}
                </pre>
              </div>
            ) : (
              <div className="bg-gray-900 border border-red-800 rounded-lg p-4 text-center">
                <p className="text-red-400 font-semibold mb-2">
                  — Payload not released —
                </p>
                <p className="text-gray-500 text-sm">
                  NexBridge blocked this transformation. Human review required before retry.
                </p>
              </div>
            )}
          </div>
        </div>

        <div className="mb-8">
          <h2 className="text-xl font-semibold text-white mb-4">Audit Log</h2>
          <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
            <div className="font-mono text-sm text-gray-400 space-y-2">
              <div>▼ employee_id    T3  →  id            0.98  mapped</div>
              <div>▼ department     T3  →  dept_code     0.87  mapped</div>
              {scenario === 'GO' ? (
                <>
                  <div>▼ start_date     T3  →  start_date    0.95  mapped</div>
                  <div>▼ ORCHESTRATOR   T2  →  GO            —     released</div>
                </>
              ) : (
                <>
                  <div>▼ weight_limit   T1  →  blocked       0.87  diverged</div>
                  <div>▼ ORCHESTRATOR   T1  →  HOLD          —     blocked</div>
                </>
              )}
            </div>
          </div>
        </div>

        <div className="flex justify-between">
          <button
            onClick={onBack}
            className="bg-gray-800 hover:bg-gray-700 text-white font-semibold px-6 py-3 rounded-lg transition-colors"
          >
            ← Try another scenario
          </button>
          <button
            onClick={onRestart}
            className="bg-indigo-600 hover:bg-indigo-500 text-white font-semibold px-6 py-3 rounded-lg transition-colors"
          >
            Start over
          </button>
        </div>
      </div>
    </div>
  )
}
