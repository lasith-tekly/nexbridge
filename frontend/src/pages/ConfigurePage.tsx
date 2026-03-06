import React, { useState, useEffect } from 'react'
import type { Scenario } from '@/types/nexbridge.types'

interface ConfigurePageProps {
  onNext: () => void;
  onBack: () => void;
  scenario: Scenario;
  setScenario: (scenario: Scenario) => void;
}

const GO_XML = `<record>
  <employee_id>E-12345</employee_id>
  <department>Operations</department>
  <start_date>2024-03-01</start_date>
  <contract_type>FULL_TIME</contract_type>
  <office_location>London</office_location>
</record>`

const GO_SCHEMA = `{
  "id": "string",
  "dept_code": "string",
  "start_date": "string",
  "emp_type": "string",
  "location": "string"
}`

const HOLD_XML = `<record>
  <employee_id>E-12345</employee_id>
  <department>Operations</department>
  <weight_limit>250</weight_limit>
  <equipment_class>HEAVY</equipment_class>
  <clearance_level>L3</clearance_level>
</record>`

const HOLD_SCHEMA = `{
  "id": "string",
  "dept_code": "string",
  "max_permitted_load": "number",
  "equipment_type": "string",
  "access_level": "string"
}`

export const ConfigurePage: React.FC<ConfigurePageProps> = ({
  onNext,
  onBack,
  scenario,
  setScenario
}) => {
  const [xmlValue, setXmlValue] = useState<string>(GO_XML)
  const [schemaValue, setSchemaValue] = useState<string>(GO_SCHEMA)

  useEffect(() => {
    if (scenario === 'GO') {
      setXmlValue(GO_XML)
      setSchemaValue(GO_SCHEMA)
    } else {
      setXmlValue(HOLD_XML)
      setSchemaValue(HOLD_SCHEMA)
    }
  }, [scenario])

  return (
    <div className="min-h-[calc(100vh-120px)] bg-gray-950 px-4 py-8">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-3xl font-bold text-white mb-8">Configure Demo</h1>

        <div className="flex gap-4 mb-8">
          <button
            onClick={() => setScenario('GO')}
            className={`flex-1 py-3 px-6 rounded-lg font-semibold transition-colors ${
              scenario === 'GO'
                ? 'bg-indigo-600 text-white'
                : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
            }`}
          >
            ✓ GO — Safe transformation
          </button>
          <button
            onClick={() => setScenario('HOLD')}
            className={`flex-1 py-3 px-6 rounded-lg font-semibold transition-colors ${
              scenario === 'HOLD'
                ? 'bg-indigo-600 text-white'
                : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
            }`}
          >
            ⚠ HOLD — Risk scenario
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          <div>
            <h2 className="text-xl font-semibold text-white mb-2">System A</h2>
            <p className="text-gray-400 text-sm mb-4">Legacy XML Payload</p>
            <textarea
              value={xmlValue}
              onChange={(e) => setXmlValue(e.target.value)}
              className="w-full h-64 bg-gray-900 border border-gray-800 rounded-lg p-4 text-green-400 font-mono text-sm resize-none focus:outline-none focus:ring-2 focus:ring-indigo-500"
              spellCheck={false}
            />
          </div>

          <div>
            <h2 className="text-xl font-semibold text-white mb-2">System B</h2>
            <p className="text-gray-400 text-sm mb-4">Target API Contract</p>
            <textarea
              value={schemaValue}
              onChange={(e) => setSchemaValue(e.target.value)}
              className="w-full h-64 bg-gray-900 border border-gray-800 rounded-lg p-4 text-blue-400 font-mono text-sm resize-none focus:outline-none focus:ring-2 focus:ring-indigo-500"
              spellCheck={false}
            />
          </div>
        </div>

        {scenario === 'GO' ? (
          <div className="bg-gray-900 border border-gray-700 rounded-lg p-4 mb-8">
            <p className="text-gray-400 text-sm">
              <span className="text-blue-400 mr-2">ℹ️</span>
              This payload contains only T2/T3 fields. NexBridge will apply standard governed transformation.
            </p>
          </div>
        ) : (
          <div className="bg-amber-900 bg-opacity-20 border border-amber-700 rounded-lg p-4 mb-8">
            <p className="text-amber-200 text-sm">
              <span className="text-amber-400 mr-2">⚠️</span>
              This payload contains weight_limit — a T1 Safety Critical field. NexBridge will apply dual-agent verification with 100% confidence threshold. Any ambiguity will trigger a HOLD.
            </p>
          </div>
        )}

        <div className="flex justify-between">
          <button
            onClick={onBack}
            className="bg-gray-800 hover:bg-gray-700 text-white font-semibold px-6 py-3 rounded-lg transition-colors"
          >
            ← Back
          </button>
          <button
            onClick={onNext}
            className="bg-indigo-600 hover:bg-indigo-500 text-white font-semibold px-6 py-3 rounded-lg transition-colors"
          >
            Run Transformation →
          </button>
        </div>
      </div>
    </div>
  )
}
