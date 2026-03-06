import React, { useEffect } from 'react'
import type { Scenario } from '@/types/nexbridge.types'

interface PipelinePageProps {
  onNext: () => void;
  onBack: () => void;
  scenario: Scenario;
}

const agentSteps = [
  { number: 1, name: 'Classification', t1Only: false },
  { number: 2, name: 'Interpreter — Run 1', t1Only: false },
  { number: 3, name: 'Interpreter — Run 2', t1Only: true },
  { number: 4, name: 'Validator', t1Only: false },
  { number: 5, name: 'Translator', t1Only: false },
  { number: 6, name: 'Orchestrator Decision', t1Only: false },
]

export const PipelinePage: React.FC<PipelinePageProps> = ({
  onNext,
  onBack,
  scenario
}) => {
  useEffect(() => {
    const timer = setTimeout(() => {
      onNext()
    }, 4000)

    return () => clearTimeout(timer)
  }, [onNext])

  return (
    <div className="min-h-[calc(100vh-120px)] bg-gray-950 px-4 py-8">
      <div className="max-w-3xl mx-auto">
        <h1 className="text-3xl font-bold text-white mb-2">Pipeline</h1>
        <p className="text-gray-400 mb-6">
          {scenario === 'GO'
            ? 'Processing 5 fields through governed transformation pipeline...'
            : 'Processing 5 fields — T1 Safety Critical field detected...'}
        </p>

        {scenario === 'GO' ? (
          <div className="bg-blue-900 border border-blue-700 rounded-lg p-4 mb-8">
            <p className="text-blue-300 font-semibold">
              Payload Tier: T2 — Operationally Sensitive
            </p>
          </div>
        ) : (
          <div className="bg-red-900 border border-red-700 rounded-lg p-4 mb-8">
            <p className="text-red-300 font-semibold">
              Payload Tier: T1 — Safety Critical
            </p>
          </div>
        )}

        <div className="space-y-4 mb-8">
          {agentSteps.map((step, index) => (
            <div key={step.number}>
              <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <span className="text-white font-semibold">
                      {step.number}. {step.name}
                    </span>
                    {step.t1Only && (
                      <span className="text-red-400 text-xs font-semibold">
                        T1 only
                      </span>
                    )}
                  </div>
                  <span className="text-gray-500 text-sm">◌ Waiting</span>
                </div>
              </div>
              {index < agentSteps.length - 1 && (
                <div className="h-4 flex justify-center">
                  <div className="w-0.5 h-full bg-gray-700"></div>
                </div>
              )}
            </div>
          ))}
        </div>

        <div className="flex justify-start">
          <button
            onClick={onBack}
            className="bg-gray-800 hover:bg-gray-700 text-white font-semibold px-6 py-3 rounded-lg transition-colors"
          >
            ← Back
          </button>
        </div>
      </div>
    </div>
  )
}
