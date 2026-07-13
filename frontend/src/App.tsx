import React, { useState, useCallback } from 'react'
import { ProgressBar } from '@/components/ProgressBar'
import { LandingPage } from '@/pages/LandingPage'
import { ConfigurePage } from '@/pages/ConfigurePage'
import { PipelinePage } from '@/pages/PipelinePage'
import { ResultPage } from '@/pages/ResultPage'
import { RegistryBuilderPage } from '@/pages/RegistryBuilderPage'
import type { Scenario, TransformResponse } from '@/types/nexbridge.types'

type View = 'pipeline' | 'registry-builder'

const App: React.FC = () => {
  const [view, setView] = useState<View>('pipeline')
  const [currentStep, setCurrentStep] = useState<number>(1)
  const [scenario, setScenario] = useState<Scenario>('GO')
  const [payload, setPayload] = useState<string>('')
  const [sourceFormat, setSourceFormat] = useState<string>('xml')
  const [targetFormat, setTargetFormat] = useState<string>('json')
  const [targetSchema, setTargetSchema] = useState<Record<string, string>>({})
  const [transformResult, setTransformResult] = useState<TransformResponse | null>(null)

  const handleNext = useCallback(() => {
    setCurrentStep(prev => prev < 4 ? prev + 1 : prev)
  }, [])

  const handleConfigureNext = useCallback((
    p: string,
    sf: string,
    tf: string,
    schema: Record<string, string>
  ) => {
    setPayload(p)
    setSourceFormat(sf)
    setTargetFormat(tf)
    setTargetSchema(schema)
    setCurrentStep(prev => prev < 4 ? prev + 1 : prev)
  }, [])

  const handleBack = useCallback(() => {
    setCurrentStep(prev => prev > 1 ? prev - 1 : prev)
  }, [])

  const handleRestart = useCallback(() => {
    setCurrentStep(1)
    setScenario('GO')
    setTransformResult(null)
  }, [])

  const renderPage = () => {
    switch (currentStep) {
      case 1:
        return <LandingPage onNext={handleNext} />
      case 2:
        return (
          <ConfigurePage
            onNext={handleConfigureNext}
            onBack={handleBack}
            scenario={scenario}
            setScenario={setScenario}
          />
        )
      case 3:
        return (
          <PipelinePage
            onNext={handleNext}
            onBack={handleBack}
            scenario={scenario}
            payload={payload}
            sourceFormat={sourceFormat}
            targetFormat={targetFormat}
            targetSchema={targetSchema}
            onComplete={setTransformResult}
          />
        )
      case 4:
        return (
          <ResultPage
            onBack={handleBack}
            onRestart={handleRestart}
            scenario={scenario}
            transformResult={transformResult}
          />
        )
      default:
        return <LandingPage onNext={handleNext} />
    }
  }

  if (view === 'registry-builder') {
    return (
      <div className="min-h-screen bg-[#080c18] text-white">
        <div className="flex items-center justify-between px-6 py-4 border-b border-[#1e2d45]">
          <span className="text-lg font-bold text-white">◈ NexBridge</span>
          <button
            onClick={() => setView('pipeline')}
            className="text-sm text-[#64748b] hover:text-white transition-colors"
          >
            ← Back to Pipeline Demo
          </button>
        </div>
        <RegistryBuilderPage />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <div className="flex items-center justify-between px-6 py-4">
        <div className="flex-1" />
        <button
          onClick={() => setView('registry-builder')}
          className="text-sm text-indigo-400 hover:text-indigo-300 border border-indigo-800 hover:border-indigo-500 px-3 py-1.5 rounded-lg transition-colors"
        >
          🗂️ Registry Builder
        </button>
      </div>
      <ProgressBar currentStep={currentStep} />
      {renderPage()}
    </div>
  )
}

export default App
