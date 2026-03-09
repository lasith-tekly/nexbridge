import React, { useState, useEffect } from 'react'
import { TierBadge } from '@/components/TierBadge'
import { TIER_COLOURS } from '@/constants/tiers'

interface LandingPageProps {
  onNext: () => void;
}

export const LandingPage: React.FC<LandingPageProps> = ({ onNext }) => {
  const [showHero, setShowHero] = useState(false)
  const [showProblem, setShowProblem] = useState(false)
  const [showTiers, setShowTiers] = useState(false)
  const [showCTA, setShowCTA] = useState(false)

  useEffect(() => {
    setShowHero(true)
    const problemTimer = setTimeout(() => setShowProblem(true), 100)
    const tiersTimer = setTimeout(() => setShowTiers(true), 200)
    const ctaTimer = setTimeout(() => setShowCTA(true), 300)

    return () => {
      clearTimeout(problemTimer)
      clearTimeout(tiersTimer)
      clearTimeout(ctaTimer)
    }
  }, [])

  return (
    <div className="min-h-[calc(100vh-120px)] bg-gray-950 px-6 py-16">
      <div className="max-w-3xl mx-auto">
        <div
          className={`text-center transition-opacity duration-500 ${
            showHero ? 'opacity-100' : 'opacity-0'
          }`}
        >
          <div className="text-indigo-500 text-3xl mb-3">◈</div>
          <h1 className="text-5xl font-bold text-white tracking-tight">NexBridge</h1>
          <p className="text-xl text-gray-400 mt-3">
            Governed AI Transformation Between Enterprise Systems
          </p>
        </div>

        <div
          className={`bg-gray-900 border border-gray-800 rounded-xl p-8 mt-10 text-left transition-opacity duration-500 ${
            showProblem ? 'opacity-100' : 'opacity-0'
          }`}
        >
          <h2 className="text-xl font-semibold text-white mb-4">The Problem</h2>
          <p className="text-gray-400 leading-relaxed">
            Your systems speak different languages. Legacy platforms send XML. Modern APIs expect JSON. Field names differ. Schemas drift. Traditional mappers treat a customer name the same as a safety-critical weight limit.
          </p>
          <p className="text-gray-400 leading-relaxed mt-3">
            NexBridge fixes this — with AI-powered field mapping that applies proportionate governance based on what each field actually means.
          </p>
        </div>

        <div
          className={`grid grid-cols-1 md:grid-cols-3 gap-6 mt-8 transition-opacity duration-500 ${
            showTiers ? 'opacity-100' : 'opacity-0'
          }`}
        >
          <div className={`bg-gray-900 border ${TIER_COLOURS[1].border} rounded-xl p-6 text-left`}>
            <TierBadge tier={1} size="lg" showLabel={false} />
            <h3 className="font-semibold text-white mt-4">Safety Critical</h3>
            <p className="text-gray-400 text-sm mt-2 leading-relaxed">
              Dual AI verification with 100% confidence threshold. Any ambiguity triggers a HOLD and requires human review before the payload is released.
            </p>
            <p className={`text-xs font-mono mt-4 ${TIER_COLOURS[1].text}`}>
              threshold: 1.00
            </p>
          </div>

          <div className={`bg-gray-900 border ${TIER_COLOURS[2].border} rounded-xl p-6 text-left`}>
            <TierBadge tier={2} size="lg" showLabel={false} />
            <h3 className="font-semibold text-white mt-4">Operationally Sensitive</h3>
            <p className="text-gray-400 text-sm mt-2 leading-relaxed">
              Single agent with schema validation. Anomalies are flagged and attached to the payload at 95% confidence threshold.
            </p>
            <p className={`text-xs font-mono mt-4 ${TIER_COLOURS[2].text}`}>
              threshold: 0.95
            </p>
          </div>

          <div className={`bg-gray-900 border ${TIER_COLOURS[3].border} rounded-xl p-6 text-left`}>
            <TierBadge tier={3} size="lg" showLabel={false} />
            <h3 className="font-semibold text-white mt-4">Business Important</h3>
            <p className="text-gray-400 text-sm mt-2 leading-relaxed">
              Standard governed transformation. Anomalies are logged but do not block the pipeline at 80% confidence threshold.
            </p>
            <p className={`text-xs font-mono mt-4 ${TIER_COLOURS[3].text}`}>
              threshold: 0.80
            </p>
          </div>
        </div>

        <div
          className={`mt-12 text-center transition-opacity duration-500 ${
            showCTA ? 'opacity-100' : 'opacity-0'
          }`}
        >
          <p className="text-gray-500 text-sm mb-4">
            See how NexBridge governs a real transformation
          </p>
          <button
            onClick={onNext}
            className="bg-indigo-600 hover:bg-indigo-500 text-white px-10 py-4 rounded-xl text-lg font-medium transition-colors duration-200"
          >
            See it in action →
          </button>
        </div>
      </div>
    </div>
  )
}
