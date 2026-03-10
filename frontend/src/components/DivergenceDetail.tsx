import React from 'react'
import { TierBadge } from '@/components/TierBadge'
import { ConfidenceBar } from '@/components/ConfidenceBar'
import type { DivergenceDetail as DivergenceDetailType } from '@/types/nexbridge.types'

interface DivergenceDetailProps {
  divergence: DivergenceDetailType;
}

export const DivergenceDetail: React.FC<DivergenceDetailProps> = ({ divergence }) => {
  return (
    <div className="bg-red-950 border border-red-800 rounded-xl p-6">
      <div>
        <div className="flex items-center">
          <span className="text-red-400 text-lg mr-2">⚠</span>
          <h3 className="text-red-300 text-lg font-semibold">Divergence Detected</h3>
        </div>
        <p className="text-red-400 text-sm mt-1">
          Two independent interpreters produced different mappings for a T1 Safety Critical field
        </p>
      </div>

      <div className="mt-4 flex items-center">
        <span className="text-gray-500 text-sm mr-2">Field:</span>
        <span className="text-red-300 font-mono text-sm">{divergence.fieldName}</span>
        <div className="ml-2">
          <TierBadge tier={1} size="sm" showLabel={true} />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
        <div className="bg-gray-900 border border-gray-700 rounded-lg p-4">
          <h4 className="text-gray-400 text-xs uppercase tracking-wide mb-3">
            Interpreter — Run 1
          </h4>
          <div>
            <p className="text-gray-500 text-xs">Mapped to:</p>
            <p className="text-blue-300 font-mono text-sm font-medium mt-1">
              {divergence.run1.targetField}
            </p>
          </div>
          <div className="mt-3">
            <p className="text-gray-500 text-xs">Confidence:</p>
            <p className="text-gray-300 font-mono text-sm mt-1">
              {divergence.run1.confidence.toFixed(2)}
            </p>
          </div>
          <div className="mt-3">
            <ConfidenceBar
              confidence={divergence.run1.confidence}
              tier={1}
              showValue={false}
              showThreshold={true}
            />
          </div>
        </div>

        <div className="bg-gray-900 border border-gray-700 rounded-lg p-4">
          <h4 className="text-gray-400 text-xs uppercase tracking-wide mb-3">
            Interpreter — Run 2
          </h4>
          <div>
            <p className="text-gray-500 text-xs">Mapped to:</p>
            <p className="text-blue-300 font-mono text-sm font-medium mt-1">
              {divergence.run2.targetField}
            </p>
          </div>
          <div className="mt-3">
            <p className="text-gray-500 text-xs">Confidence:</p>
            <p className="text-gray-300 font-mono text-sm mt-1">
              {divergence.run2.confidence.toFixed(2)}
            </p>
          </div>
          <div className="mt-3">
            <ConfidenceBar
              confidence={divergence.run2.confidence}
              tier={1}
              showValue={false}
              showThreshold={true}
            />
          </div>
        </div>
      </div>

      <div className="mt-4 bg-red-900 border border-red-700 rounded-lg p-3 flex items-center gap-2">
        <span className="text-red-400">⚠</span>
        <p className="text-red-300 text-sm font-medium">
          Interpreters disagreed on a T1 Safety Critical field. Payload blocked pending human review.
        </p>
      </div>

      <div className="mt-4">
        <p className="text-gray-400 text-sm font-medium">What happens next:</p>
        <ul className="text-gray-500 text-sm mt-1 space-y-1">
          <li>• A human reviewer must inspect both mappings and confirm the correct target field</li>
          <li>• Once confirmed, the transformation can be retried with the verified mapping</li>
        </ul>
      </div>
    </div>
  )
}
