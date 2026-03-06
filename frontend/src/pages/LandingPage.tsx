import React from 'react'
import { TIER_COLOURS } from '@/constants/tiers'

interface LandingPageProps {
  onNext: () => void;
}

export const LandingPage: React.FC<LandingPageProps> = ({ onNext }) => {
  return (
    <div className="min-h-[calc(100vh-120px)] bg-gray-950 py-12 px-4">
      <div className="max-w-3xl mx-auto">
        <div className="text-center mb-12">
          <h1 className="text-5xl font-bold text-white mb-4">NexBridge</h1>
          <p className="text-xl text-gray-400">
            Governed AI Transformation Between Enterprise Systems
          </p>
        </div>

        <div className="bg-gray-900 rounded-lg border border-gray-800 p-8 mb-10">
          <h2 className="text-2xl font-semibold text-white mb-4">The Problem</h2>
          <p className="text-gray-400 leading-relaxed mb-4">
            Your systems speak different languages. Legacy platforms send XML. Modern APIs expect JSON. Field names differ. Schemas drift. Traditional mappers treat a customer name the same as a safety-critical weight limit.
          </p>
          <p className="text-gray-400 leading-relaxed">
            NexBridge fixes this — with AI-powered field mapping that applies proportionate governance based on what each field actually means.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-10">
          <div className="bg-gray-900 rounded-lg border border-gray-800 p-6">
            <div className={`inline-block ${TIER_COLOURS[1].bg} ${TIER_COLOURS[1].text} bg-opacity-20 px-3 py-1 rounded-full text-sm font-semibold mb-4`}>
              T1
            </div>
            <h3 className="text-lg font-semibold text-white mb-3">Safety Critical</h3>
            <p className="text-gray-400 text-sm leading-relaxed">
              Dual AI verification with 100% confidence threshold. Any ambiguity triggers a HOLD.
            </p>
          </div>

          <div className="bg-gray-900 rounded-lg border border-gray-800 p-6">
            <div className={`inline-block ${TIER_COLOURS[2].bg} ${TIER_COLOURS[2].text} bg-opacity-20 px-3 py-1 rounded-full text-sm font-semibold mb-4`}>
              T2
            </div>
            <h3 className="text-lg font-semibold text-white mb-3">Operationally Sensitive</h3>
            <p className="text-gray-400 text-sm leading-relaxed">
              Single agent with validation. Anomalies flagged at 95% confidence threshold.
            </p>
          </div>

          <div className="bg-gray-900 rounded-lg border border-gray-800 p-6">
            <div className={`inline-block ${TIER_COLOURS[3].bg} ${TIER_COLOURS[3].text} bg-opacity-20 px-3 py-1 rounded-full text-sm font-semibold mb-4`}>
              T3
            </div>
            <h3 className="text-lg font-semibold text-white mb-3">Business Important</h3>
            <p className="text-gray-400 text-sm leading-relaxed">
              Standard governed transformation at 80% confidence threshold.
            </p>
          </div>
        </div>

        <div className="flex justify-center">
          <button
            onClick={onNext}
            className="bg-indigo-600 hover:bg-indigo-500 text-white font-semibold px-8 py-3 rounded-lg transition-colors"
          >
            See it in action →
          </button>
        </div>
      </div>
    </div>
  )
}
