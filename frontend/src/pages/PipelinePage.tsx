import React from 'react'
import type { Scenario, TransformResponse } from '@/types/nexbridge.types'

interface PipelinePageProps {
  onNext: () => void;
  onBack: () => void;
  scenario: Scenario;
  transformResult: TransformResponse | null;
  setTransformResult: (result: TransformResponse | null) => void;
}

export const PipelinePage: React.FC<PipelinePageProps> = ({
  onNext,
  onBack,
  scenario,
  transformResult,
  setTransformResult
}) => {
  return (
    <div className="min-h-[calc(100vh-120px)] px-4 py-8">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-3xl font-bold text-white mb-8">Agent Pipeline</h1>

        <div className="bg-gray-900 rounded-lg border border-gray-800 p-8 mb-8">
          <p className="text-gray-400 mb-6">
            Pipeline page content placeholder. This will show the agent flow,
            real-time status updates, and confidence scores.
          </p>
          <p className="text-gray-500 text-sm">
            Scenario: <span className="text-white font-semibold">{scenario}</span>
          </p>
        </div>

        <div className="flex justify-between">
          <button
            onClick={onBack}
            className="bg-gray-800 hover:bg-gray-700 text-white font-semibold px-6 py-3 rounded-lg transition-colors"
          >
            ← Back
          </button>
          <button
            onClick={onNext}
            className="bg-indigo-600 hover:bg-indigo-700 text-white font-semibold px-6 py-3 rounded-lg transition-colors"
          >
            View Results →
          </button>
        </div>
      </div>
    </div>
  )
}
