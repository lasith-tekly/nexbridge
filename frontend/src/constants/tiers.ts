export const TIER_COLOURS = {
  1: {
    bg: 'bg-red-500',
    text: 'text-red-500',
    border: 'border-red-500',
    label: 'Safety Critical',
    hex: '#ef4444'
  },
  2: {
    bg: 'bg-amber-500',
    text: 'text-amber-500',
    border: 'border-amber-500',
    label: 'Operationally Sensitive',
    hex: '#f59e0b'
  },
  3: {
    bg: 'bg-blue-500',
    text: 'text-blue-500',
    border: 'border-blue-500',
    label: 'Business Important',
    hex: '#3b82f6'
  },
  4: {
    bg: 'bg-gray-500',
    text: 'text-gray-500',
    border: 'border-gray-500',
    label: 'Informational',
    hex: '#6b7280'
  },
} as const;

export const DECISION_COLOURS = {
  GO: { bg: 'bg-green-500', text: 'text-green-500' },
  HOLD: { bg: 'bg-red-500', text: 'text-red-500' },
  ESCALATE: { bg: 'bg-amber-500', text: 'text-amber-500' },
} as const;
