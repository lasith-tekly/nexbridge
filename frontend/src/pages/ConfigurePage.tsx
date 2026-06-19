import React, { useState, useEffect } from 'react'
import { ScenarioToggle } from '@/components/ScenarioToggle'
import { XmlViewer } from '@/components/XmlViewer'
import { JsonViewer } from '@/components/JsonViewer'
import type { Scenario } from '@/types/nexbridge.types'

interface ConfigurePageProps {
  onNext: (
    payload: string,
    sourceFormat: string,
    targetFormat: string,
    schema: Record<string, string>
  ) => void;
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
  const [sourceFormat, setSourceFormat] = useState<string>('xml')
  const [targetFormat, setTargetFormat] = useState<string>('json')
  const [schemaError, setSchemaError] = useState<string>('')

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

        <div className="flex gap-4 mb-4">
          <div>
            <label className="block text-sm text-gray-400 mb-1">Source Format</label>
            <select
              value={sourceFormat}
              onChange={e => setSourceFormat(e.target.value)}
              className="bg-gray-800 border border-gray-700 text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-indigo-500"
            >
              <option value="xml">XML</option>
              <option value="json">JSON</option>
            </select>
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1">Target Format</label>
            <select
              value={targetFormat}
              onChange={e => setTargetFormat(e.target.value)}
              className="bg-gray-800 border border-gray-700 text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-indigo-500"
            >
              <option value="json">JSON</option>
              <option value="xml">XML</option>
            </select>
          </div>
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
          <div className="flex flex-col items-end gap-2">
            {schemaError && (
              <p className="text-red-400 text-sm">{schemaError}</p>
            )}
            <button
              onClick={() => {
                try {
                  const parsedSchema = JSON.parse(schemaValue) as Record<string, string>
                  setSchemaError('')
                  onNext(xmlValue, sourceFormat, targetFormat, parsedSchema)
                } catch {
                  setSchemaError('Target schema is not valid JSON')
                }
              }}
              className="bg-indigo-600 hover:bg-indigo-500 text-white px-6 py-3 rounded-lg font-medium transition-colors"
            >
              Run Transformation →
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
