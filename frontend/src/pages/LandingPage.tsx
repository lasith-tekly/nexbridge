import React from 'react'

interface LandingPageProps {
  onNext: () => void;
  onBack: () => void;
}

export const LandingPage: React.FC<LandingPageProps> = ({ onNext }) => {
  return (
    <div className="min-h-[calc(100vh-120px)] flex items-center justify-center px-4">
      <div className="max-w-4xl w-full">
        <div className="text-center mb-12">
          <h1 className="text-5xl font-bold text-white mb-4">NexBridge</h1>
          <p className="text-xl text-gray-400">
            Governed AI Transformation for Any Protocol
          </p>
        </div>

        <div className="bg-gray-900 rounded-lg border border-gray-800 p-8 mb-8">
          <h2 className="text-2xl font-semibold text-white mb-4">The Problem</h2>
          <p className="text-gray-300 leading-relaxed">
            Landing page content placeholder. This will explain the business problem,
            the solution, and the tier-based governance approach.
          </p>
        </div>

        <div className="flex justify-center">
          <button
            onClick={onNext}
            className="bg-indigo-600 hover:bg-indigo-700 text-white font-semibold px-8 py-3 rounded-lg transition-colors"
          >
            Try Demo →
          </button>
        </div>
      </div>
    </div>
  )
}
