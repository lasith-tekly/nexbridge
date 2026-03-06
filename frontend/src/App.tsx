import React, { useState } from 'react'
import { ProgressBar } from '@/components/ProgressBar'
import { LandingPage } from '@/pages/LandingPage'
import { ConfigurePage } from '@/pages/ConfigurePage'
import { PipelinePage } from '@/pages/PipelinePage'
import { ResultPage } from '@/pages/ResultPage'
import type { Scenario, TransformResponse } from '@/types/nexbridge.types'

const App: React.FC = () => {
  const [currentStep, setCurrentStep] = useState<number>(1)
  const [scenario, setScenario] = useState<Scenario>('GO')
  const [transformResult, setTransformResult] = useState<TransformResponse | null>(null)

  const handleNext = () => {
    if (currentStep < 4) {
      setCurrentStep(currentStep + 1)
    }
  }

  const handleBack = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1)
    }
  }

  const renderPage = () => {
    switch (currentStep) {
      case 1:
        return <LandingPage onNext={handleNext} onBack={handleBack} />
      case 2:
        return (
          <ConfigurePage
            onNext={handleNext}
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
            transformResult={transformResult}
            setTransformResult={setTransformResult}
          />
        )
      case 4:
        return (
          <ResultPage
            onNext={handleNext}
            onBack={handleBack}
            transformResult={transformResult}
          />
        )
      default:
        return <LandingPage onNext={handleNext} onBack={handleBack} />
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
