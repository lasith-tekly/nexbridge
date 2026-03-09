import React from 'react'
import { TIER_COLOURS } from '@/constants/tiers'
import type { Tier } from '@/types/nexbridge.types'

interface TierBadgeProps {
  tier: Tier;
  showLabel?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

export const TierBadge: React.FC<TierBadgeProps> = ({
  tier,
  showLabel = false,
  size = 'md'
}) => {
  const sizeClasses = {
    sm: 'text-xs px-1.5 py-0.5',
    md: 'text-sm px-2 py-0.5',
    lg: 'text-base px-3 py-1'
  }

  const tierConfig = TIER_COLOURS[tier]
  const displayText = showLabel ? `T${tier} ${tierConfig.label}` : `T${tier}`

  return (
    <span
      className={`inline-block rounded-full ${tierConfig.bg} text-white font-bold ${sizeClasses[size]}`}
    >
      {displayText}
    </span>
  )
}
