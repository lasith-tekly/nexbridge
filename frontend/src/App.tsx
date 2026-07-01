import React, { useState, useCallback } from 'react'
import { ProgressBar } from '@/components/ProgressBar'
import { LandingPage } from '@/pages/LandingPage'
import { ConfigurePage } from '@/pages/ConfigurePage'
import { PipelinePage } from '@/pages/PipelinePage'
import { ResultPage } from '@/pages/ResultPage'
import type { Scenario, TransformResponse } from '@/types/nexbridge.types'

const App: React.FC = () => {
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

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <ProgressBar currentStep={currentStep} />
      {renderPage()}
    </div>
  )
}

export default App
