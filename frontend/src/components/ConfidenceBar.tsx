import React from 'react'
import type { Tier } from '@/types/nexbridge.types'

interface ConfidenceBarProps {
  confidence: number;
  tier: Tier;
  showValue?: boolean;
  showThreshold?: boolean;
}

const TIER_THRESHOLDS: Record<Tier, number> = {
  1: 1.0,
  2: 0.95,
  3: 0.80,
  4: 0.0
}

export const ConfidenceBar: React.FC<ConfidenceBarProps> = ({
  confidence,
  tier,
  showValue = true,
  showThreshold = true
}) => {
  const threshold = TIER_THRESHOLDS[tier]
  const meetsThreshold = confidence >= threshold
  const fillColor = meetsThreshold ? 'bg-green-500' : 'bg-red-500'
  const textColor = meetsThreshold ? 'text-green-500' : 'text-red-500'
  const fillWidth = `${Math.min(confidence * 100, 100)}%`
  const thresholdPosition = `${threshold * 100}%`

  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 relative bg-gray-700 rounded-full h-2">
        <div
          className={`${fillColor} h-full rounded-full transition-all duration-500`}
          style={{ width: fillWidth }}
        />
        {showThreshold && threshold > 0 && (
          <div
            className="absolute w-0.5 h-3 bg-white opacity-60 -top-0.5"
            style={{ left: thresholdPosition }}
          />
        )}
      </div>
      {showValue && (
        <span className={`w-10 text-right text-xs font-mono ${textColor}`}>
          {confidence.toFixed(2)}
        </span>
      )}
    </div>
  )
}
