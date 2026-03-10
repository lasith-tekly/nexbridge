import React from 'react'
import { TierBadge } from '@/components/TierBadge'
import type { AuditEntry } from '@/types/nexbridge.types'

interface AuditLogProps {
  entries: AuditEntry[];
}

export const AuditLog: React.FC<AuditLogProps> = ({ entries }) => {
  const isHoldRow = (decision: string) => {
    return decision === 'HOLD' || decision === 'blocked' || decision === 'diverged'
  }

  const isOrchestratorRow = (fieldName: string) => {
    return fieldName === 'ORCHESTRATOR'
  }

  const renderEntry = (entry: AuditEntry, index: number) => {
    const isHold = isHoldRow(entry.decision)
    const isOrchestrator = isOrchestratorRow(entry.field_name)

    const rowBgClass = isOrchestrator
      ? 'bg-gray-800'
      : isHold
      ? 'bg-red-950 hover:bg-red-900'
      : 'bg-transparent hover:bg-gray-800'

    const fieldNameClass = isHold
      ? 'text-red-300 text-sm font-mono'
      : 'text-gray-300 text-sm font-mono'

    const mappedToClass = isHold
      ? 'text-red-400 text-sm font-mono'
      : 'text-blue-300 text-sm font-mono'

    const confidenceClass = isHold
      ? 'text-red-500 text-xs font-mono'
      : 'text-gray-400 text-xs font-mono'

    const decisionClass = isHold
      ? 'text-red-400 text-xs font-bold'
      : 'text-green-400 text-xs'

    return (
      <div
        key={index}
        className={`px-4 py-3 border-t border-gray-800 grid grid-cols-12 items-center gap-2 transition-colors duration-150 ${rowBgClass}`}
      >
        <span className={`col-span-3 ${fieldNameClass}`}>
          {entry.field_name}
        </span>
        <div className="col-span-1">
          <TierBadge tier={entry.tier} size="sm" showLabel={false} />
        </div>
        <span className={`col-span-3 ${mappedToClass}`}>
          {String(entry.transformed_value)}
        </span>
        <span className={`col-span-2 ${confidenceClass}`}>
          {entry.confidence !== null ? entry.confidence.toFixed(2) : '—'}
        </span>
        <span className={`col-span-2 ${decisionClass}`}>
          {entry.decision}
        </span>
        <span className="col-span-1 text-gray-500 text-xs">
          {entry.agent}
        </span>
      </div>
    )
  }

  return (
    <div>
      <div className="mb-3">
        <h2 className="text-lg font-semibold text-white inline">Audit Log</h2>
        <span className="text-xs text-gray-500 ml-3 inline">
          Immutable transformation record
        </span>
      </div>

      <div className="bg-gray-900 border border-gray-800 rounded-lg overflow-hidden">
        <div className="bg-gray-800 px-4 py-2 grid grid-cols-12 gap-2">
          <span className="col-span-3 text-xs text-gray-500 uppercase">Field</span>
          <span className="col-span-1 text-xs text-gray-500 uppercase">Tier</span>
          <span className="col-span-3 text-xs text-gray-500 uppercase">Mapped To</span>
          <span className="col-span-2 text-xs text-gray-500 uppercase">Confidence</span>
          <span className="col-span-2 text-xs text-gray-500 uppercase">Decision</span>
          <span className="col-span-1 text-xs text-gray-500 uppercase">Agent</span>
        </div>

        {entries.length === 0 ? (
          <div className="text-gray-500 text-sm text-center py-8">
            No audit entries yet
          </div>
        ) : (
          entries.map((entry, index) => renderEntry(entry, index))
        )}
      </div>
    </div>
  )
}
