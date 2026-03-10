import React from 'react'
import { TierBadge } from '@/components/TierBadge'
import { ConfidenceBar } from '@/components/ConfidenceBar'
import type { AgentStatus, FieldMapping, DivergenceDetail } from '@/types/nexbridge.types'

interface AgentCardProps {
  stepNumber: number;
  agentName: string;
  status: AgentStatus;
  subtitle?: string;
  fieldMappings?: FieldMapping[];
  isDivergence?: boolean;
  divergenceDetail?: DivergenceDetail;
}

export const AgentCard: React.FC<AgentCardProps> = ({
  stepNumber,
  agentName,
  status,
  subtitle,
  fieldMappings = [],
  isDivergence = false,
  divergenceDetail
}) => {
  const getBorderClass = () => {
    switch (status) {
      case 'idle':
        return 'border-gray-800'
      case 'running':
        return 'border-indigo-700 border-l-4 border-l-indigo-500'
      case 'complete':
        return 'border-gray-700'
      case 'hold':
        return 'border-red-700 border-l-4 border-l-red-500'
      case 'error':
        return 'border-red-700'
      default:
        return 'border-gray-800'
    }
  }

  const getOpacityClass = () => {
    return status === 'idle' ? 'opacity-60' : 'opacity-100'
  }

  const renderStatusIndicator = () => {
    switch (status) {
      case 'idle':
        return (
          <div className="flex items-center gap-2">
            <span className="text-gray-500">◌</span>
            <span className="text-gray-500 text-sm">Waiting</span>
          </div>
        )
      case 'running':
        return (
          <div className="flex items-center gap-2">
            <div className="relative w-3 h-3">
              <span className="absolute inset-0 w-3 h-3 rounded-full bg-indigo-500 animate-ping opacity-75"></span>
              <span className="absolute inset-0 w-3 h-3 rounded-full bg-indigo-500"></span>
            </div>
            <span className="text-indigo-400 text-sm">Running...</span>
          </div>
        )
      case 'complete':
        return (
          <div className="flex items-center gap-2">
            <span className="text-green-400">✓</span>
            <span className="text-green-400 text-sm">Complete</span>
          </div>
        )
      case 'hold':
        return (
          <div className="flex items-center gap-2">
            <span className="text-red-400">⚠</span>
            <span className="text-red-400 text-sm">Hold</span>
          </div>
        )
      case 'error':
        return (
          <div className="flex items-center gap-2">
            <span className="text-red-400">✗</span>
            <span className="text-red-400 text-sm">Error</span>
          </div>
        )
      default:
        return null
    }
  }

  const renderFieldMappings = () => {
    if (status !== 'complete' || fieldMappings.length === 0) return null

    return (
      <div className="mt-4 pt-4 border-t border-gray-800 space-y-2">
        {fieldMappings.map((mapping, index) => (
          <div key={index} className="flex items-center gap-3">
            <span className="text-gray-400 text-sm font-mono w-36 truncate">
              {mapping.field_name}
            </span>
            <TierBadge tier={mapping.tier} size="sm" showLabel={false} />
            <span className="text-gray-600 text-sm">→</span>
            <span className="text-blue-300 text-sm font-mono flex-1">
              {mapping.target_field}
            </span>
            <div className="flex-1">
              <ConfidenceBar
                confidence={mapping.confidence}
                tier={mapping.tier}
                showValue={true}
                showThreshold={true}
              />
            </div>
          </div>
        ))}
      </div>
    )
  }

  const renderDivergenceDetail = () => {
    if (!isDivergence || !divergenceDetail || status !== 'hold') return null

    return (
      <div className="mt-4 pt-4 border-t border-red-900">
        <div className="flex items-center gap-2 mb-2">
          <span className="text-gray-400 text-sm font-mono">
            {divergenceDetail.fieldName}
          </span>
          <TierBadge tier={1} size="sm" showLabel={false} />
        </div>

        <div className="bg-gray-800 rounded p-2 mt-2">
          <div className="flex items-center gap-2">
            <span className="text-gray-500 text-xs">Run 1 →</span>
            <span className="text-blue-300 text-sm font-mono">
              {divergenceDetail.run1.targetField}
            </span>
            <span className="text-gray-400 text-xs font-mono ml-auto">
              {divergenceDetail.run1.confidence.toFixed(2)}
            </span>
          </div>
        </div>

        <div className="bg-gray-800 rounded p-2 mt-1">
          <div className="flex items-center gap-2">
            <span className="text-gray-500 text-xs">Run 2 →</span>
            <span className="text-blue-300 text-sm font-mono">
              {divergenceDetail.run2.targetField}
            </span>
            <span className="text-gray-400 text-xs font-mono ml-auto">
              {divergenceDetail.run2.confidence.toFixed(2)}
            </span>
          </div>
        </div>

        <p className="text-red-400 text-sm mt-2 font-medium">
          ⚠ Outputs disagree — HOLD triggered
        </p>
      </div>
    )
  }

  const renderOrchestratorContent = () => {
    if (!agentName.includes('Orchestrator')) return null

    if (status === 'complete') {
      return (
        <div className="mt-4 pt-4 border-t border-gray-800">
          <p className="text-green-400 font-mono text-sm">Decision: GO</p>
        </div>
      )
    }

    if (status === 'hold') {
      return (
        <div className="mt-4 pt-4 border-t border-red-900">
          <p className="text-red-400 font-mono text-sm">Decision: HOLD</p>
          <p className="text-red-500 text-sm mt-1">
            Payload blocked — human review required
          </p>
        </div>
      )
    }

    return null
  }

  return (
    <div
      className={`bg-gray-900 border ${getBorderClass()} rounded-lg p-4 transition-all duration-300 ${getOpacityClass()}`}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center">
          <span className="text-gray-500 text-sm font-mono mr-3">
            {stepNumber.toString().padStart(2, '0')}
          </span>
          <span className="text-white font-medium">{agentName}</span>
          {subtitle && (
            <span className="text-xs text-red-400 bg-red-950 px-2 py-0.5 rounded ml-2">
              {subtitle}
            </span>
          )}
        </div>
        {renderStatusIndicator()}
      </div>

      {agentName.includes('Orchestrator')
        ? renderOrchestratorContent()
        : isDivergence
        ? renderDivergenceDetail()
        : renderFieldMappings()}
    </div>
  )
}
