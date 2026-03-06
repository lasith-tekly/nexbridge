import React from 'react'
import type { TransformResponse } from '@/types/nexbridge.types'

interface ResultPageProps {
  onNext: () => void;
  onBack: () => void;
  transformResult: TransformResponse | null;
}

export const ResultPage: React.FC<ResultPageProps> = ({
  onBack,
  transformResult
}) => {
  return (
    <div className="min-h-[calc(100vh-120px)] px-4 py-8">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-3xl font-bold text-white mb-8">Transformation Result</h1>

        <div className="bg-gray-900 rounded-lg border border-gray-800 p-8 mb-8">
          <p className="text-gray-400 mb-6">
            Result page content placeholder. This will show the final decision,
            transformed JSON, and audit log.
          </p>
          {transformResult && (
            <p className="text-gray-500 text-sm">
              Decision: <span className="text-white font-semibold">{transformResult.status}</span>
            </p>
          )}
        </div>

        <div className="flex justify-between">
          <button
            onClick={onBack}
            className="bg-gray-800 hover:bg-gray-700 text-white font-semibold px-6 py-3 rounded-lg transition-colors"
          >
            ← Back to Pipeline
          </button>
          <button
            onClick={() => window.location.reload()}
            className="bg-indigo-600 hover:bg-indigo-700 text-white font-semibold px-6 py-3 rounded-lg transition-colors"
          >
            Start Over
          </button>
        </div>
      </div>
    </div>
  )
}
