import React, { useState, useEffect } from 'react'
import { ScenarioToggle } from '@/components/ScenarioToggle'
import { XmlViewer } from '@/components/XmlViewer'
import { JsonViewer } from '@/components/JsonViewer'
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
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-white">Configure Demo</h1>
          <p className="text-gray-400 mt-2">
            Load a scenario or paste your own XML payload and target schema
          </p>
        </div>

        <div className="mb-6">
          <ScenarioToggle scenario={scenario} onChange={setScenario} />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6">
          <div>
            <div className="mb-4">
              <h2 className="text-lg font-semibold text-white">System A</h2>
              <p className="text-sm text-gray-400 mt-1">Legacy XML Payload</p>
            </div>
            <XmlViewer
              content={xmlValue}
              editable={true}
              onChange={(val) => setXmlValue(val)}
              highlightFields={scenario === 'HOLD' ? ['weight_limit'] : []}
            />
          </div>

          <div>
            <div className="mb-4">
              <h2 className="text-lg font-semibold text-white">System B</h2>
              <p className="text-sm text-gray-400 mt-1">Target API Contract</p>
            </div>
            <JsonViewer
              content={schemaValue}
              editable={true}
              onChange={(val) => setSchemaValue(val)}
            />
          </div>
        </div>

        {scenario === 'GO' ? (
          <div className="bg-gray-900 border border-gray-700 rounded-lg p-4 mt-4 flex items-start gap-3">
            <span className="text-xl">ℹ️</span>
            <p className="text-gray-400 text-sm">
              This payload contains only T2/T3 fields. NexBridge will apply standard governed transformation.
            </p>
          </div>
        ) : (
          <div className="bg-amber-950 border border-amber-800 rounded-lg p-4 mt-4 flex items-start gap-3">
            <span className="text-xl">⚠️</span>
            <p className="text-amber-300 text-sm">
              This payload contains weight_limit — a T1 Safety Critical field. NexBridge will apply dual-agent verification with 100% confidence threshold. Any ambiguity will trigger a HOLD.
            </p>
          </div>
        )}

        <div className="flex justify-between mt-6">
          <button
            onClick={onBack}
            className="bg-gray-800 hover:bg-gray-700 text-white px-6 py-3 rounded-lg transition-colors"
          >
            ← Back
          </button>
          <button
            onClick={onNext}
            className="bg-indigo-600 hover:bg-indigo-500 text-white px-6 py-3 rounded-lg font-medium transition-colors"
          >
            Run Transformation →
          </button>
        </div>
      </div>
    </div>
  )
}
