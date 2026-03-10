import React, { useState, useEffect, useRef } from 'react'
import { AgentCard } from '@/components/AgentCard'
import type { Scenario, AgentStatus, FieldMapping, DivergenceDetail } from '@/types/nexbridge.types'

interface PipelinePageProps {
  onNext: () => void;
  onBack: () => void;
  scenario: Scenario;
}

interface AgentStep {
  id: number;
  agentName: string;
  subtitle?: string;
  durationMs: number;
}

const AGENT_STEPS: AgentStep[] = [
  { id: 1, agentName: 'Classification', durationMs: 500 },
  { id: 2, agentName: 'Interpreter — Run 1', durationMs: 800 },
  { id: 3, agentName: 'Interpreter — Run 2', subtitle: 'T1 only', durationMs: 800 },
  { id: 4, agentName: 'Validator', durationMs: 400 },
  { id: 5, agentName: 'Translator', durationMs: 300 },
  { id: 6, agentName: 'Orchestrator Decision', durationMs: 300 },
]

const GO_FIELD_MAPPINGS: FieldMapping[] = [
  { field_name: 'employee_id', target_field: 'id', transformed_value: 'E-12345', confidence: 0.98, tier: 3 },
  { field_name: 'department', target_field: 'dept_code', transformed_value: 'OPS', confidence: 0.87, tier: 3 },
  { field_name: 'start_date', target_field: 'start_date', transformed_value: '2024-03-01', confidence: 0.99, tier: 3 },
  { field_name: 'contract_type', target_field: 'emp_type', transformed_value: 'FULL_TIME', confidence: 0.96, tier: 2 },
  { field_name: 'office_location', target_field: 'location', transformed_value: 'London', confidence: 0.82, tier: 4 },
]

const HOLD_FIELD_MAPPINGS: FieldMapping[] = [
  { field_name: 'employee_id', target_field: 'id', transformed_value: 'E-12345', confidence: 0.98, tier: 3 },
  { field_name: 'department', target_field: 'dept_code', transformed_value: 'OPS', confidence: 0.87, tier: 3 },
  { field_name: 'weight_limit', target_field: 'max_permitted_load', transformed_value: 250, confidence: 0.95, tier: 1 },
  { field_name: 'equipment_class', target_field: 'equipment_type', transformed_value: 'HEAVY', confidence: 0.91, tier: 2 },
  { field_name: 'clearance_level', target_field: 'access_level', transformed_value: 'L3', confidence: 0.94, tier: 2 },
]

const DIVERGENCE_DETAIL: DivergenceDetail = {
  fieldName: 'weight_limit',
  run1: {
    targetField: 'max_permitted_load',
    confidence: 0.95,
  },
  run2: {
    targetField: 'weight_capacity',
    confidence: 0.91,
  },
}

interface CompletionBannerProps {
  scenario: Scenario
  onNext: () => void
}

const CompletionBanner: React.FC<CompletionBannerProps> = ({ scenario, onNext }) => {
  if (scenario === 'GO') {
    return (
      <div className="bg-green-950 border border-green-800 rounded-lg p-5 mt-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <span className="text-green-400 text-xl mr-3">✓</span>
            <span className="text-green-300 text-sm font-medium">
              Pipeline complete — all fields governed successfully
            </span>
          </div>
          <button
            onClick={onNext}
            className="bg-green-600 hover:bg-green-500 text-white px-6 py-2.5 rounded-lg font-medium transition-colors"
          >
            View Results →
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-red-950 border border-red-800 rounded-lg p-5 mt-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center">
          <span className="text-red-400 text-xl mr-3">⚠</span>
          <span className="text-red-300 text-sm font-medium">
            Pipeline blocked — T1 field requires human review
          </span>
        </div>
        <button
          onClick={onNext}
          className="bg-red-600 hover:bg-red-500 text-white px-6 py-2.5 rounded-lg font-medium transition-colors"
        >
          View Results →
        </button>
      </div>
    </div>
  )
}

export const PipelinePage: React.FC<PipelinePageProps> = ({
  onNext,
  onBack,
  scenario
}) => {
  const [agentStatuses, setAgentStatuses] = useState<Record<number, AgentStatus>>({
    1: 'idle',
    2: 'idle',
    3: 'idle',
    4: 'idle',
    5: 'idle',
    6: 'idle',
  })
  const [isComplete, setIsComplete] = useState(false)
  const hasStarted = useRef(false)

  useEffect(() => {
    if (hasStarted.current) return
    hasStarted.current = true

    const stepsToRun = scenario === 'GO'
      ? AGENT_STEPS.filter(s => s.id !== 3)
      : AGENT_STEPS.filter(s => s.id !== 4 && s.id !== 5)

    let cumulativeDelay = 0
    const timers: ReturnType<typeof setTimeout>[] = []

    for (const step of stepsToRun) {
      const runDelay = cumulativeDelay
      const isHoldStep = scenario === 'HOLD' && step.id === 3
      const isOrchestratorHold = scenario === 'HOLD' && step.id === 6

      timers.push(setTimeout(() => {
        setAgentStatuses(prev => ({...prev, [step.id]: 'running'}))
      }, runDelay))

      cumulativeDelay += step.durationMs

      const completeDelay = cumulativeDelay
      const finalStatus: AgentStatus = (isHoldStep || isOrchestratorHold)
        ? 'hold'
        : 'complete'

      timers.push(setTimeout(() => {
        setAgentStatuses(prev => ({...prev, [step.id]: finalStatus}))
      }, completeDelay))
    }

    timers.push(setTimeout(() => {
      setIsComplete(true)
    }, cumulativeDelay))

    return () => {
      // Only clear timers if hasStarted was NOT set
      // (i.e. first StrictMode unmount before sequence starts)
      // Do NOT reset hasStarted — sequence must not restart
    }
  }, [])

  const getFieldMappings = (stepId: number): FieldMapping[] | undefined => {
    if (stepId === 2) {
      return scenario === 'GO' ? GO_FIELD_MAPPINGS : HOLD_FIELD_MAPPINGS
    }
    return undefined
  }

  const getDivergenceDetail = (stepId: number): DivergenceDetail | undefined => {
    if (stepId === 3 && scenario === 'HOLD') {
      return DIVERGENCE_DETAIL
    }
    return undefined
  }

  const isRunning = Object.values(agentStatuses).some(status => status === 'running')

  return (
    <div className="min-h-[calc(100vh-120px)] bg-gray-950 px-4 py-8">
      <div className="max-w-3xl mx-auto">
        <h1 className="text-2xl font-bold text-white">Pipeline</h1>
        <p className="text-gray-400 text-sm mt-1">
          {scenario === 'GO'
            ? 'Processing 5 fields through governed transformation pipeline...'
            : 'Processing 5 fields — T1 Safety Critical field detected...'}
        </p>

        <div className="mt-6">
          {scenario === 'GO' ? (
            <div className="bg-blue-950 border border-blue-800 rounded-lg p-3">
              <p className="text-blue-300 text-sm font-medium">
                Payload Tier: T2 — Operationally Sensitive
              </p>
            </div>
          ) : (
            <div className="bg-red-950 border border-red-800 rounded-lg p-3">
              <p className="text-red-300 text-sm font-medium">
                Payload Tier: T1 — Safety Critical
              </p>
            </div>
          )}
        </div>

        <div className="mt-6">
          {AGENT_STEPS.map((step, index) => (
            <div key={step.id}>
              <AgentCard
                stepNumber={step.id}
                agentName={step.agentName}
                status={agentStatuses[step.id]}
                subtitle={step.subtitle}
                fieldMappings={getFieldMappings(step.id)}
                isDivergence={step.id === 3 && scenario === 'HOLD'}
                divergenceDetail={getDivergenceDetail(step.id)}
              />
              {index < AGENT_STEPS.length - 1 && (
                <div className="w-0.5 h-4 bg-gray-800 mx-auto"></div>
              )}
            </div>
          ))}
          {isComplete && <CompletionBanner scenario={scenario} onNext={onNext} />}
        </div>

        <div className="flex justify-start mt-6">
          <button
            onClick={onBack}
            disabled={isRunning}
            className={`px-6 py-3 rounded-lg transition-colors ${
              isRunning
                ? 'bg-gray-800 text-gray-600 cursor-not-allowed'
                : 'bg-gray-800 hover:bg-gray-700 text-white'
            }`}
          >
            ← Back
          </button>
        </div>
      </div>
    </div>
  )
}
