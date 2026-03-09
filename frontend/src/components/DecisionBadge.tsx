import React, { useEffect, useState } from 'react'
import type { Decision } from '@/types/nexbridge.types'

interface DecisionBadgeProps {
  decision: Decision;
  reason: string;
  detail?: string;
  processingTimeMs?: number;
}

const DECISION_CONFIG = {
  GO: {
    container: 'bg-green-900 border-green-700',
    title: 'text-green-400',
    reason: 'text-green-300',
    detail: 'text-green-500',
    time: 'text-green-600',
    icon: '✓'
  },
  HOLD: {
    container: 'bg-red-900 border-red-700',
    title: 'text-red-400',
    reason: 'text-red-300',
    detail: 'text-red-500',
    time: 'text-red-600',
    icon: '⚠'
  },
  ESCALATE: {
    container: 'bg-amber-900 border-amber-700',
    title: 'text-amber-400',
    reason: 'text-amber-300',
    detail: 'text-amber-500',
    time: 'text-amber-600',
    icon: '⚡'
  }
}

export const DecisionBadge: React.FC<DecisionBadgeProps> = ({
  decision,
  reason,
  detail,
  processingTimeMs
}) => {
  const [isVisible, setIsVisible] = useState(false)
  const config = DECISION_CONFIG[decision]

  useEffect(() => {
    const timer = setTimeout(() => setIsVisible(true), 50)
    return () => clearTimeout(timer)
  }, [])

  const processingTimeSeconds = processingTimeMs
    ? (processingTimeMs / 1000).toFixed(1)
    : null

  return (
    <div
      className={`${config.container} border rounded-xl p-8 text-center transition-all duration-500 ${
        isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-2'
      }`}
    >
      <div className={`${config.title} text-4xl font-bold`}>
        {config.icon} {decision}
      </div>
      <p className={`${config.reason} text-lg mt-2`}>{reason}</p>
      {detail && <p className={`${config.detail} text-sm mt-1`}>{detail}</p>}
      {processingTimeSeconds && (
        <p className={`${config.time} text-xs mt-2`}>
          Processed in {processingTimeSeconds}s
        </p>
      )}
    </div>
  )
}
