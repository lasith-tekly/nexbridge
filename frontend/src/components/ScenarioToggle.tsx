import React from 'react'
import type { Scenario } from '@/types/nexbridge.types'

interface ScenarioToggleProps {
  scenario: Scenario;
  onChange: (scenario: Scenario) => void;
}

export const ScenarioToggle: React.FC<ScenarioToggleProps> = ({
  scenario,
  onChange
}) => {
  return (
    <div
      className="inline-flex bg-gray-900 border border-gray-800 rounded-xl p-1"
      role="tablist"
    >
      <button
        onClick={() => onChange('GO')}
        className={`rounded-lg px-6 py-2 font-medium transition-all duration-200 ${
          scenario === 'GO'
            ? 'bg-indigo-600 text-white'
            : 'bg-transparent text-gray-400 hover:text-gray-200'
        }`}
        role="tab"
        aria-selected={scenario === 'GO'}
      >
        ✓ GO — Safe transformation
      </button>
      <button
        onClick={() => onChange('HOLD')}
        className={`rounded-lg px-6 py-2 font-medium transition-all duration-200 ${
          scenario === 'HOLD'
            ? 'bg-red-600 text-white'
            : 'bg-transparent text-gray-400 hover:text-gray-200'
        }`}
        role="tab"
        aria-selected={scenario === 'HOLD'}
      >
        ⚠ HOLD — Risk scenario
      </button>
    </div>
  )
}
