import React from 'react'
import type { Scenario } from '@/types/nexbridge.types'

interface ConfigurePageProps {
  onNext: () => void;
  onBack: () => void;
  scenario: Scenario;
  setScenario: (scenario: Scenario) => void;
}

export const ConfigurePage: React.FC<ConfigurePageProps> = ({
  onNext,
  onBack,
  scenario,
  setScenario
}) => {
  return (
    <div className="min-h-[calc(100vh-120px)] px-4 py-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-white mb-8">Configure Demo</h1>

        <div className="bg-gray-900 rounded-lg border border-gray-800 p-8 mb-8">
          <h2 className="text-xl font-semibold text-white mb-4">Select Scenario</h2>
          <p className="text-gray-400 mb-6">
            Configure page content placeholder. This will allow scenario selection
            and XML/schema input.
          </p>

          <div className="flex gap-4 mb-6">
            <button
              onClick={() => setScenario('GO')}
              className={`flex-1 py-3 px-6 rounded-lg font-semibold transition-colors ${
                scenario === 'GO'
                  ? 'bg-green-600 text-white'
                  : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
              }`}
            >
              GO Scenario
            </button>
            <button
              onClick={() => setScenario('HOLD')}
              className={`flex-1 py-3 px-6 rounded-lg font-semibold transition-colors ${
                scenario === 'HOLD'
                  ? 'bg-red-600 text-white'
                  : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
              }`}
            >
              HOLD Scenario
            </button>
          </div>
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
            Run Pipeline →
          </button>
        </div>
      </div>
    </div>
  )
}
