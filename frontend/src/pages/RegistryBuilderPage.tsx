import React, { useState, useRef } from 'react'
import type {
  AnalysedField,
  ConfirmedT1,
  ReviewField,
  ExportResult,
} from '@/types/registryBuilder.types'

// ── Constants ──────────────────────────────────────────────────────────────────

const TIER_LABELS: Record<1 | 2 | 3 | 4, string> = {
  1: 'Safety Critical',
  2: 'Operationally Sensitive',
  3: 'Business Important',
  4: 'Informational',
}

const TIER_DEFAULTS: Record<1 | 2 | 3 | 4, number> = {
  1: 1.0,
  2: 0.95,
  3: 0.80,
  4: 0.0,
}

const TIER_THRESHOLD_BOUNDS: Record<1 | 2 | 3 | 4, { min: number; max: number }> = {
  1: { min: 1.0, max: 1.0 },
  2: { min: 0.95, max: 1.0 },
  3: { min: 0.50, max: 0.95 },
  4: { min: 0.0, max: 0.0 },
}

const TIER_TEXT: Record<1 | 2 | 3 | 4, string> = {
  1: 'text-[#ef4444]',
  2: 'text-[#f59e0b]',
  3: 'text-[#3b82f6]',
  4: 'text-[#64748b]',
}

const TIER_BORDER: Record<1 | 2 | 3 | 4, string> = {
  1: 'border-[#ef4444]',
  2: 'border-[#f59e0b]',
  3: 'border-[#3b82f6]',
  4: 'border-[#64748b]',
}

const TIER_BG: Record<1 | 2 | 3 | 4, string> = {
  1: 'bg-[#ef4444]',
  2: 'bg-[#f59e0b]',
  3: 'bg-[#3b82f6]',
  4: 'bg-[#64748b]',
}

const STEP_LABELS = ['Extract', 'Analyse', 'Confirm T1', 'Review', 'Export']

type Format = 'xml' | 'json'
type Step = 1 | 2 | 3 | 4 | 5 | 6

// ── Sub-components ─────────────────────────────────────────────────────────────

const Stepper: React.FC<{ step: Step; integrationName: string; fieldCount: number }> = ({
  step,
  integrationName,
  fieldCount,
}) => {
  if (step === 1) return null
  const currentIndex = step - 2 // steps 2-6 map to indices 0-4

  return (
    <div className="flex items-center justify-between mb-8 px-2">
      <div className="flex items-center gap-2">
        {STEP_LABELS.map((label, i) => (
          <React.Fragment key={label}>
            <div className="flex items-center gap-1.5">
              <div
                className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0 ${
                  i < currentIndex
                    ? 'bg-[#06b6d4] text-white'
                    : i === currentIndex
                    ? 'border-2 border-[#06b6d4] text-[#06b6d4]'
                    : 'border-2 border-[#1e2d45] text-[#64748b]'
                }`}
              >
                {i < currentIndex ? '✓' : i + 1}
              </div>
              <span
                className={`text-xs font-medium hidden sm:block ${
                  i <= currentIndex ? 'text-white' : 'text-[#64748b]'
                }`}
              >
                {label}
              </span>
            </div>
            {i < STEP_LABELS.length - 1 && (
              <div
                className={`h-px w-8 flex-shrink-0 ${
                  i < currentIndex ? 'bg-[#06b6d4]' : 'bg-[#1e2d45]'
                }`}
              />
            )}
          </React.Fragment>
        ))}
      </div>

      {step > 1 && step < 6 && integrationName && (
        <div className="flex items-center gap-1.5 text-sm text-[#06b6d4] bg-[#0f1724] border border-[#1e2d45] rounded-full px-3 py-1">
          <span className="w-2 h-2 rounded-full bg-[#06b6d4] flex-shrink-0" />
          <span className="font-medium">{integrationName}</span>
          {fieldCount > 0 && (
            <span className="text-[#64748b]">| {fieldCount} fields</span>
          )}
        </div>
      )}
    </div>
  )
}

const TierPill: React.FC<{ tier: 1 | 2 | 3 | 4; small?: boolean }> = ({ tier, small }) => (
  <span
    className={`inline-flex items-center rounded-full font-bold text-white ${TIER_BG[tier]} ${
      small ? 'text-xs px-2 py-0.5' : 'text-sm px-2.5 py-0.5'
    }`}
  >
    T{tier}
  </span>
)

const SmallConfidenceBar: React.FC<{ confidence: number; tier: 1 | 2 | 3 | 4 }> = ({
  confidence,
  tier,
}) => {
  const pct = Math.min(confidence * 100, 100)
  const color =
    tier === 1
      ? 'bg-[#ef4444]'
      : tier === 2
      ? 'bg-[#f59e0b]'
      : tier === 3
      ? 'bg-[#3b82f6]'
      : 'bg-[#64748b]'

  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 bg-[#1e2d45] rounded-full h-1.5">
        <div className={`${color} h-full rounded-full`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs font-mono text-[#64748b] w-8 text-right">
        {confidence.toFixed(2)}
      </span>
    </div>
  )
}

// ── Helpers ────────────────────────────────────────────────────────────────────

function extractFieldsFromXml(content: string): string[] {
  try {
    const parser = new DOMParser()
    const doc = parser.parseFromString(content, 'text/xml')
    const root = doc.documentElement
    return Array.from(root.children).map((el) => el.tagName)
  } catch {
    return []
  }
}

function extractFieldsFromJson(content: string): string[] {
  try {
    const obj = JSON.parse(content)
    const names = new Set<string>()
    const walk = (val: unknown) => {
      if (val && typeof val === 'object' && !Array.isArray(val)) {
        for (const [k, v] of Object.entries(val as Record<string, unknown>)) {
          names.add(k)
          walk(v)
        }
      } else if (Array.isArray(val)) {
        for (const item of val) walk(item)
      }
    }
    walk(obj)
    return Array.from(names)
  } catch {
    return []
  }
}

function buildReviewField(
  f: AnalysedField,
  confirmedT1s: ConfirmedT1[]
): ReviewField {
  const confirmed = confirmedT1s.find((c) => c.field_name === f.field_name)
  const tier = (confirmed ? confirmed.final_tier : f.suggested_tier) as 1 | 2 | 3 | 4
  return {
    field_name: f.field_name,
    tier,
    label: TIER_LABELS[tier],
    threshold: TIER_DEFAULTS[tier],
    confirmed_individually: tier === 1,
  }
}

// ── Main component ─────────────────────────────────────────────────────────────

export const RegistryBuilderPage: React.FC = () => {
  const [step, setStep] = useState<Step>(1)
  const [integrationName, setIntegrationName] = useState('')
  const [sourceFormat, setSourceFormat] = useState<Format>('xml')
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([])
  const [fileContents, setFileContents] = useState<Record<string, string>>({})
  const [extractedFields, setExtractedFields] = useState<string[]>([])
  const [analysisResults, setAnalysisResults] = useState<AnalysedField[]>([])
  const [confirmedT1Fields, setConfirmedT1Fields] = useState<ConfirmedT1[]>([])
  const [allFields, setAllFields] = useState<ReviewField[]>([])
  const [exportResult, setExportResult] = useState<ExportResult | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const [manualField, setManualField] = useState('')
  const [analyseFilter, setAnalyseFilter] = useState<'All' | 'T1' | 'T2' | 'T3' | 'T4'>('All')
  const [acceptedNonT1, setAcceptedNonT1] = useState<Set<string>>(new Set())
  const [overrideField, setOverrideField] = useState<string | null>(null)
  const [t1Index, setT1Index] = useState(0)
  const [reclassifyField, setReclassifyField] = useState<string | null>(null)
  const [editingReviewField, setEditingReviewField] = useState<string | null>(null)
  const [editingT1Field, setEditingT1Field] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  // Derived
  const t1Fields = analysisResults.filter((f) => f.suggested_tier === 1)
  const nonT1Fields = analysisResults.filter((f) => f.suggested_tier !== 1)
  const allNonT1Accepted =
    nonT1Fields.length > 0 &&
    nonT1Fields.every((f) => acceptedNonT1.has(f.field_name))
  const currentT1 = t1Fields[t1Index] ?? null

  // ── Handlers ────────────────────────────────────────────────────────────────

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files ?? [])
    setUploadedFiles(files)
    setError('')
    const contents: Record<string, string> = {}
    let completed = 0
    files.forEach((file) => {
      const reader = new FileReader()
      reader.onload = (ev) => {
        contents[file.name] = ev.target?.result as string
        completed++
        if (completed === files.length) {
          setFileContents({ ...contents })
        }
      }
      reader.onerror = () => {
        completed++
        setError(`Failed to read file: ${file.name}`)
        setUploadedFiles((prev) => prev.filter((f) => f.name !== file.name))
        if (completed === files.length) {
          setFileContents({ ...contents })
        }
      }
      reader.readAsText(file)
    })
  }

  const handleExtract = () => {
    if (!integrationName.trim()) {
      setError('Integration name is required.')
      return
    }
    if (uploadedFiles.length === 0) {
      setError('Please upload at least one file.')
      return
    }
    setError('')
    const allNames = new Set<string>()
    for (const content of Object.values(fileContents)) {
      const names =
        sourceFormat === 'xml'
          ? extractFieldsFromXml(content)
          : extractFieldsFromJson(content)
      names.forEach((n) => allNames.add(n))
    }
    setExtractedFields(Array.from(allNames))
    setStep(2)
  }

  const handleAddManualField = () => {
    const name = manualField.trim()
    if (name && !extractedFields.includes(name)) {
      setExtractedFields((prev) => [...prev, name])
    }
    setManualField('')
  }

  const handleAnalyse = async () => {
    setIsLoading(true)
    setError('')
    try {
      const firstContent = Object.values(fileContents)[0] ?? ''
      const res = await fetch('http://localhost:8000/registry/analyse', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          payload: firstContent,
          source_format: sourceFormat,
          context: integrationName,
        }),
      })
      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail ?? 'Analysis failed')
      }
      const data = await res.json()
      setAnalysisResults(data.fields)
      setAcceptedNonT1(new Set())
      setStep(3)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Analysis failed')
    } finally {
      setIsLoading(false)
    }
  }

  const handleAcceptField = (fieldName: string) => {
    setAcceptedNonT1((prev) => new Set([...prev, fieldName]))
  }

  const handleAcceptAllNonT1 = () => {
    const names = nonT1Fields.map((f) => f.field_name)
    setAcceptedNonT1(new Set(names))
  }

  const handleOverrideTier = (fieldName: string, newTier: 1 | 2 | 3 | 4) => {
    setAnalysisResults((prev) =>
      prev.map((f) =>
        f.field_name === fieldName
          ? { ...f, suggested_tier: newTier, suggested_label: TIER_LABELS[newTier] }
          : f
      )
    )
    setOverrideField(null)
    if (newTier !== 1) {
      setAcceptedNonT1((prev) => new Set([...prev, fieldName]))
    }
  }

  const handleProceedToT1 = () => {
    if (t1Fields.length === 0) {
      const fields = analysisResults.map((f) => buildReviewField(f, []))
      setAllFields(fields)
      setStep(5)
    } else {
      setT1Index(0)
      setStep(4)
    }
  }

  const handleConfirmT1 = () => {
    if (!currentT1) return
    const entry: ConfirmedT1 = {
      field_name: currentT1.field_name,
      confirmed_at: new Date().toISOString(),
      final_tier: 1,
    }
    const updated = [...confirmedT1Fields, entry]
    setConfirmedT1Fields(updated)
    if (t1Index + 1 < t1Fields.length) {
      setT1Index(t1Index + 1)
    } else {
      const fields = analysisResults.map((f) => buildReviewField(f, updated))
      setAllFields(fields)
      setStep(5)
    }
  }

  const handleReclassifyT1 = (fieldName: string, newTier: 2 | 3 | 4) => {
    setAnalysisResults((prev) =>
      prev.map((f) =>
        f.field_name === fieldName
          ? { ...f, suggested_tier: newTier, suggested_label: TIER_LABELS[newTier] }
          : f
      )
    )
    setReclassifyField(null)
    setAcceptedNonT1((prev) => new Set([...prev, fieldName]))
    if (t1Index + 1 < t1Fields.length) {
      setT1Index(t1Index + 1)
    } else {
      const fields = analysisResults.map((f) => buildReviewField(f, confirmedT1Fields))
      setAllFields(fields)
      setStep(5)
    }
  }

  const handleUpdateReviewField = (
    fieldName: string,
    newTier: 1 | 2 | 3 | 4,
    newThreshold: number
  ) => {
    if (newTier === 1) {
      // Changing to T1 requires going back through confirmation
      setAnalysisResults((prev) =>
        prev.map((f) =>
          f.field_name === fieldName
            ? { ...f, suggested_tier: 1, suggested_label: TIER_LABELS[1] }
            : f
        )
      )
      setConfirmedT1Fields([])
      setAcceptedNonT1(new Set())
      setT1Index(0)
      setEditingT1Field(null)
      setEditingReviewField(null)
      setStep(4)
      return
    }
    setAllFields((prev) =>
      prev.map((f) =>
        f.field_name === fieldName
          ? {
              ...f,
              tier: newTier,
              label: TIER_LABELS[newTier],
              threshold: newThreshold,
              confirmed_individually: false,
            }
          : f
      )
    )
    setEditingReviewField(null)
    setEditingT1Field(null)
  }

  const handleExport = async () => {
    setIsLoading(true)
    setError('')
    try {
      const res = await fetch('http://localhost:8000/registry/export', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          fields: allFields,
          integration_name: integrationName,
          domain: integrationName,
        }),
      })
      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail ?? 'Export failed')
      }
      const data: ExportResult = await res.json()
      setExportResult(data)
      setStep(6)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Export failed')
    } finally {
      setIsLoading(false)
    }
  }

  const handleDownload = () => {
    if (!exportResult) return
    const blob = new Blob([exportResult.content], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = exportResult.filename
    a.click()
    URL.revokeObjectURL(url)
  }

  const handleReset = () => {
    setStep(1)
    setIntegrationName('')
    setSourceFormat('xml')
    setUploadedFiles([])
    setFileContents({})
    setExtractedFields([])
    setAnalysisResults([])
    setConfirmedT1Fields([])
    setAllFields([])
    setExportResult(null)
    setError('')
    setAcceptedNonT1(new Set())
    setAnalyseFilter('All')
    setT1Index(0)
  }

  // ── Render helpers ───────────────────────────────────────────────────────────

  const renderStep1 = () => (
    <div className="max-w-xl mx-auto">
      <div className="text-center mb-10">
        <div className="text-4xl mb-3">🗂️</div>
        <h1 className="text-3xl font-bold text-white">Registry Builder</h1>
        <p className="text-[#64748b] mt-2">
          Upload sample payloads to generate an AI-classified field registry
        </p>
      </div>

      <div className="space-y-5">
        <div>
          <label className="block text-sm font-medium text-[#94a3b8] mb-1.5">
            Integration Name
          </label>
          <input
            type="text"
            value={integrationName}
            onChange={(e) => setIntegrationName(e.target.value)}
            placeholder="e.g. flight-ops, hr-system, patient-records"
            className="w-full bg-[#0f1724] border border-[#1e2d45] rounded-lg px-4 py-3 text-white placeholder-[#334155] focus:outline-none focus:border-[#06b6d4] transition-colors"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-[#94a3b8] mb-1.5">
            Source Format
          </label>
          <div className="flex gap-2">
            {(['xml', 'json'] as Format[]).map((fmt) => (
              <button
                key={fmt}
                onClick={() => setSourceFormat(fmt)}
                className={`flex-1 py-2.5 rounded-lg font-medium text-sm transition-colors ${
                  sourceFormat === fmt
                    ? 'bg-[#06b6d4] text-white'
                    : 'bg-[#0f1724] border border-[#1e2d45] text-[#64748b] hover:border-[#06b6d4] hover:text-white'
                }`}
              >
                {fmt.toUpperCase()}
              </button>
            ))}
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-[#94a3b8] mb-1.5">
            Upload Sample Files
          </label>
          <div
            onClick={() => fileInputRef.current?.click()}
            className="w-full bg-[#0f1724] border-2 border-dashed border-[#1e2d45] rounded-lg px-4 py-8 text-center cursor-pointer hover:border-[#06b6d4] transition-colors"
          >
            <div className="text-3xl mb-2">📂</div>
            <p className="text-[#64748b] text-sm">
              Click to upload .xml or .json files
            </p>
            <p className="text-[#334155] text-xs mt-1">Multiple files supported</p>
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept=".xml,.json"
              onChange={handleFileChange}
              className="hidden"
            />
          </div>
          {uploadedFiles.length > 0 && (
            <ul className="mt-2 space-y-1">
              {uploadedFiles.map((f) => (
                <li key={f.name} className="text-xs text-[#06b6d4] flex items-center gap-1.5">
                  <span>✓</span> {f.name}
                </li>
              ))}
            </ul>
          )}
        </div>

        {error && <p className="text-[#ef4444] text-sm">{error}</p>}

        <button
          onClick={handleExtract}
          disabled={!integrationName.trim() || uploadedFiles.length === 0}
          className="w-full bg-[#06b6d4] hover:bg-cyan-400 disabled:opacity-40 disabled:cursor-not-allowed text-white font-semibold py-3 rounded-lg transition-colors"
        >
          Extract Fields →
        </button>
      </div>
    </div>
  )

  const renderStep2 = () => (
    <div className="max-w-2xl mx-auto">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-white">Extracted Fields</h2>
        <p className="text-[#64748b] text-sm mt-1">
          {extractedFields.length} fields found in {uploadedFiles.length} file
          {uploadedFiles.length !== 1 ? 's' : ''} · {sourceFormat.toUpperCase()}
        </p>
      </div>

      <div className="grid grid-cols-2 gap-2 mb-6">
        {extractedFields.map((name) => (
          <div
            key={name}
            className="bg-[#0f1724] border border-[#1e2d45] rounded-lg px-3 py-2 font-mono text-sm text-white"
          >
            {name}
          </div>
        ))}
      </div>

      <div className="flex gap-2 mb-6">
        <input
          type="text"
          value={manualField}
          onChange={(e) => setManualField(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleAddManualField()}
          placeholder="Add field manually..."
          className="flex-1 bg-[#0f1724] border border-[#1e2d45] rounded-lg px-3 py-2 text-sm text-white placeholder-[#334155] focus:outline-none focus:border-[#06b6d4]"
        />
        <button
          onClick={handleAddManualField}
          className="bg-[#0f1724] border border-[#1e2d45] hover:border-[#06b6d4] text-[#06b6d4] px-4 py-2 rounded-lg text-sm font-medium transition-colors"
        >
          + Add
        </button>
      </div>

      {error && <p className="text-[#ef4444] text-sm mb-4">{error}</p>}

      <button
        onClick={handleAnalyse}
        disabled={isLoading || extractedFields.length === 0}
        className="w-full bg-[#06b6d4] hover:bg-cyan-400 disabled:opacity-40 disabled:cursor-not-allowed text-white font-semibold py-3 rounded-lg transition-colors flex items-center justify-center gap-2"
      >
        {isLoading ? (
          <>
            <span className="animate-spin">⟳</span> Analysing with AI…
          </>
        ) : (
          'Analyse with AI →'
        )}
      </button>
    </div>
  )

  const renderStep3 = () => {
    const filterTabs = ['All', 'T1', 'T2', 'T3', 'T4'] as const
    const filterTierMap: Record<'T1' | 'T2' | 'T3' | 'T4', 1 | 2 | 3 | 4> = { T1: 1, T2: 2, T3: 3, T4: 4 }
    const filtered =
      analyseFilter === 'All'
        ? analysisResults
        : analysisResults.filter((f) => f.suggested_tier === filterTierMap[analyseFilter])

    const counts = {
      All: analysisResults.length,
      T1: analysisResults.filter((f) => f.suggested_tier === 1).length,
      T2: analysisResults.filter((f) => f.suggested_tier === 2).length,
      T3: analysisResults.filter((f) => f.suggested_tier === 3).length,
      T4: analysisResults.filter((f) => f.suggested_tier === 4).length,
    }

    return (
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-2xl font-bold text-white">AI Analysis Results</h2>
            <p className="text-[#64748b] text-sm mt-1">
              Review and accept tier classifications
            </p>
          </div>
          <button
            onClick={handleAcceptAllNonT1}
            className="bg-[#0f1724] border border-[#1e2d45] hover:border-[#06b6d4] text-[#06b6d4] px-4 py-2 rounded-lg text-sm font-medium transition-colors"
          >
            Accept All T2–T4
          </button>
        </div>

        <div className="flex gap-1 mb-4">
          {filterTabs.map((tab) => (
            <button
              key={tab}
              onClick={() => setAnalyseFilter(tab)}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                analyseFilter === tab
                  ? 'bg-[#06b6d4] text-white'
                  : 'bg-[#0f1724] text-[#64748b] hover:text-white border border-[#1e2d45]'
              }`}
            >
              {tab} <span className="opacity-70">({counts[tab]})</span>
            </button>
          ))}
        </div>

        <div className="bg-[#0f1724] border border-[#1e2d45] rounded-xl overflow-hidden mb-4">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[#1e2d45]">
                <th className="text-left px-4 py-3 text-[#64748b] font-medium">Field</th>
                <th className="text-left px-4 py-3 text-[#64748b] font-medium">Tier</th>
                <th className="text-left px-4 py-3 text-[#64748b] font-medium">Confidence</th>
                <th className="text-left px-4 py-3 text-[#64748b] font-medium">Reasoning</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody>
              {filtered.map((f) => {
                const isT1 = f.suggested_tier === 1
                const tier = f.suggested_tier as 1 | 2 | 3 | 4
                const accepted = acceptedNonT1.has(f.field_name)

                return (
                  <tr
                    key={f.field_name}
                    className={`border-b border-[#1e2d45] last:border-0 ${
                      isT1 ? 'border-l-2 border-l-[#ef4444]' : ''
                    }`}
                  >
                    <td className="px-4 py-3">
                      <span className="font-mono text-white">{f.field_name}</span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-1.5">
                        <TierPill tier={tier} small />
                        {isT1 && <span className="text-[#ef4444] text-xs">⚠️</span>}
                      </div>
                    </td>
                    <td className="px-4 py-3 w-32">
                      <SmallConfidenceBar confidence={f.confidence} tier={tier} />
                    </td>
                    <td className="px-4 py-3 text-[#64748b] text-xs max-w-xs">
                      {f.reasoning}
                    </td>
                    <td className="px-4 py-3 text-right">
                      {isT1 ? (
                        <span className="text-xs text-[#ef4444] font-medium">
                          Confirm individually →
                        </span>
                      ) : (
                        <div className="flex items-center gap-2 justify-end">
                          {overrideField === f.field_name ? (
                            <select
                              autoFocus
                              onChange={(e) =>
                                handleOverrideTier(
                                  f.field_name,
                                  parseInt(e.target.value) as 1 | 2 | 3 | 4
                                )
                              }
                              onBlur={() => setOverrideField(null)}
                              className="bg-[#080c18] border border-[#1e2d45] text-white text-xs rounded px-2 py-1"
                              defaultValue={tier}
                            >
                              {([1, 2, 3, 4] as const).map((t) => (
                                <option key={t} value={t}>
                                  T{t} — {TIER_LABELS[t]}
                                </option>
                              ))}
                            </select>
                          ) : (
                            <>
                              <button
                                onClick={() => setOverrideField(f.field_name)}
                                className="text-[#64748b] hover:text-white text-sm"
                                title="Override tier"
                              >
                                ✏️
                              </button>
                              <button
                                onClick={() => handleAcceptField(f.field_name)}
                                disabled={accepted}
                                className={`text-xs px-3 py-1 rounded-lg font-medium transition-colors ${
                                  accepted
                                    ? 'bg-green-900 text-green-400 cursor-default'
                                    : 'bg-[#0f1724] border border-[#1e2d45] hover:border-[#06b6d4] text-[#06b6d4]'
                                }`}
                              >
                                {accepted ? '✓ Accepted' : 'Accept'}
                              </button>
                            </>
                          )}
                        </div>
                      )}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>

        {t1Fields.length > 0 && (
          <div className="bg-[#1a0f0f] border border-[#ef4444] border-opacity-40 rounded-lg px-4 py-3 mb-4 flex items-center gap-2 text-sm text-[#ef4444]">
            ⚠️ {t1Fields.length} T1 field{t1Fields.length !== 1 ? 's' : ''} require individual confirmation
          </div>
        )}

        <div className="flex justify-end">
          <button
            onClick={handleProceedToT1}
            disabled={!allNonT1Accepted && nonT1Fields.length > 0}
            className="bg-[#06b6d4] hover:bg-cyan-400 disabled:opacity-40 disabled:cursor-not-allowed text-white font-semibold px-6 py-3 rounded-lg transition-colors"
          >
            {t1Fields.length > 0
              ? `Confirm ${t1Fields.length} T1 field${t1Fields.length !== 1 ? 's' : ''} →`
              : 'Proceed to Review →'}
          </button>
        </div>
      </div>
    )
  }

  const renderStep4 = () => {
    if (!currentT1) return null
    const firstFile = uploadedFiles[0]?.name ?? ''
    const firstContent = Object.values(fileContents)[0] ?? ''
    let sampleValue = ''
    try {
      if (sourceFormat === 'xml') {
        const parser = new DOMParser()
        const doc = parser.parseFromString(firstContent, 'application/xml')
        const el = doc.querySelector(currentT1.field_name)
        sampleValue = el?.textContent ?? ''
      } else {
        const obj = JSON.parse(firstContent)
        sampleValue = String(obj[currentT1.field_name] ?? '')
      }
    } catch {
      sampleValue = ''
    }

    return (
      <div className="max-w-xl mx-auto">
        <div className="bg-[#1a0a0a] border border-[#ef4444] border-opacity-50 rounded-xl p-4 mb-6 flex items-center gap-3 text-sm text-[#ef4444]">
          <span className="text-lg">⚠️</span>
          <div>
            <p className="font-semibold">T1 Safety Critical — Individual Confirmation Required</p>
            <p className="opacity-80 text-xs mt-0.5">
              Field {t1Index + 1} of {t1Fields.length}
            </p>
          </div>
        </div>

        <div className="flex gap-1.5 mb-6">
          {t1Fields.map((_, i) => (
            <div
              key={i}
              className={`h-1.5 flex-1 rounded-full ${
                i < t1Index
                  ? 'bg-[#06b6d4]'
                  : i === t1Index
                  ? 'bg-[#ef4444]'
                  : 'bg-[#1e2d45]'
              }`}
            />
          ))}
        </div>

        <div className="bg-[#0f1724] border border-[#1e2d45] rounded-xl p-6 mb-6">
          <div className="flex items-center gap-2 mb-4">
            <TierPill tier={1} />
            <span className="text-[#ef4444] font-medium text-sm">Safety Critical</span>
          </div>

          <p className="font-mono text-2xl text-white font-bold mb-4">
            {currentT1.field_name}
          </p>

          <div className="grid grid-cols-2 gap-4 text-sm mb-4">
            {firstFile && (
              <div>
                <p className="text-[#64748b] text-xs mb-1">Found in</p>
                <p className="text-[#94a3b8] font-mono text-xs">{firstFile}</p>
              </div>
            )}
            {sampleValue && (
              <div>
                <p className="text-[#64748b] text-xs mb-1">Sample value</p>
                <p className="text-[#94a3b8] font-mono text-xs">{sampleValue}</p>
              </div>
            )}
          </div>

          <div className="border-t border-[#1e2d45] pt-4 mb-4">
            <p className="text-[#64748b] text-xs mb-1">AI Reasoning</p>
            <p className="text-[#94a3b8] text-sm leading-relaxed">{currentT1.reasoning}</p>
          </div>

          <div>
            <p className="text-[#64748b] text-xs mb-1.5">Confidence</p>
            <SmallConfidenceBar confidence={currentT1.confidence} tier={1} />
          </div>
        </div>

        {reclassifyField === currentT1.field_name ? (
          <div className="mb-4">
            <label className="block text-sm text-[#94a3b8] mb-1.5">Reclassify as:</label>
            <select
              onChange={(e) =>
                handleReclassifyT1(currentT1.field_name, parseInt(e.target.value) as 2 | 3 | 4)
              }
              className="w-full bg-[#0f1724] border border-[#1e2d45] text-white rounded-lg px-3 py-2 focus:outline-none focus:border-[#06b6d4]"
              defaultValue=""
            >
              <option value="" disabled>Select tier…</option>
              {([2, 3, 4] as const).map((t) => (
                <option key={t} value={t}>
                  T{t} — {TIER_LABELS[t]}
                </option>
              ))}
            </select>
            <button
              onClick={() => setReclassifyField(null)}
              className="mt-2 text-xs text-[#64748b] hover:text-white"
            >
              Cancel
            </button>
          </div>
        ) : (
          <button
            onClick={() => setReclassifyField(currentT1.field_name)}
            className="w-full mb-3 bg-[#0f1724] border border-[#1e2d45] hover:border-[#f59e0b] text-[#f59e0b] py-3 rounded-lg font-medium text-sm transition-colors"
          >
            Not T1 — reclassify
          </button>
        )}

        <button
          onClick={handleConfirmT1}
          className="w-full bg-[#ef4444] hover:bg-red-400 text-white font-bold py-4 rounded-xl transition-colors"
        >
          I confirm {currentT1.field_name} is T1 Safety Critical
        </button>
      </div>
    )
  }

  const renderStep5 = () => {
    const t1Reviewed = allFields.filter((f) => f.tier === 1)
    const nonT1Reviewed = allFields.filter((f) => f.tier !== 1)
    const tierCounts = { 1: 0, 2: 0, 3: 0, 4: 0 }
    allFields.forEach((f) => tierCounts[f.tier]++)

    return (
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-2xl font-bold text-white">Full Review</h2>
            <p className="text-[#64748b] text-sm mt-1">
              Final check before export
            </p>
          </div>
        </div>

        {/* Section A — T1 fields */}
        {t1Reviewed.length > 0 && (
          <div className="mb-6">
            <h3 className="text-sm font-semibold text-[#ef4444] uppercase tracking-wider mb-3 flex items-center gap-2">
              <span>⚠️</span> T1 Safety Critical — Individually Confirmed
            </h3>
            <div className="bg-[#0f1724] border border-[#1e2d45] rounded-xl overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-[#1e2d45]">
                    <th className="text-left px-4 py-3 text-[#64748b] font-medium">Field</th>
                    <th className="text-left px-4 py-3 text-[#64748b] font-medium">Confirmed at</th>
                    <th className="text-left px-4 py-3 text-[#64748b] font-medium">Final tier</th>
                    <th className="px-4 py-3" />
                  </tr>
                </thead>
                <tbody>
                  {t1Reviewed.map((f) => {
                    const conf = confirmedT1Fields.find((c) => c.field_name === f.field_name)
                    return (
                      <tr key={f.field_name} className="border-b border-[#1e2d45] last:border-0">
                        <td className="px-4 py-3 font-mono text-white">{f.field_name}</td>
                        <td className="px-4 py-3 text-[#64748b] text-xs">
                          {conf ? new Date(conf.confirmed_at).toLocaleString() : '—'}
                        </td>
                        <td className="px-4 py-3">
                          {editingT1Field === f.field_name ? (
                            <select
                              autoFocus
                              defaultValue={f.tier}
                              onChange={(e) =>
                                handleUpdateReviewField(
                                  f.field_name,
                                  parseInt(e.target.value) as 1 | 2 | 3 | 4,
                                  TIER_DEFAULTS[parseInt(e.target.value) as 1 | 2 | 3 | 4]
                                )
                              }
                              onBlur={() => setEditingT1Field(null)}
                              className="bg-[#080c18] border border-[#1e2d45] text-white text-xs rounded px-2 py-1"
                            >
                              {([1, 2, 3, 4] as const).map((t) => (
                                <option key={t} value={t}>T{t} — {TIER_LABELS[t]}</option>
                              ))}
                            </select>
                          ) : (
                            <TierPill tier={f.tier as 1 | 2 | 3 | 4} small />
                          )}
                        </td>
                        <td className="px-4 py-3 text-right">
                          <button
                            onClick={() => setEditingT1Field(f.field_name)}
                            className="text-[#64748b] hover:text-white text-sm"
                          >
                            ✏️
                          </button>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Section B — T2-T4 fields */}
        {nonT1Reviewed.length > 0 && (
          <div className="mb-6">
            <h3 className="text-sm font-semibold text-[#94a3b8] uppercase tracking-wider mb-3">
              T2–T4 Fields
            </h3>
            <div className="bg-[#0f1724] border border-[#1e2d45] rounded-xl overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-[#1e2d45]">
                    <th className="text-left px-4 py-3 text-[#64748b] font-medium">Field</th>
                    <th className="text-left px-4 py-3 text-[#64748b] font-medium">Tier</th>
                    <th className="text-left px-4 py-3 text-[#64748b] font-medium">Threshold</th>
                    <th className="px-4 py-3" />
                  </tr>
                </thead>
                <tbody>
                  {nonT1Reviewed.map((f) => {
                    const tier = f.tier as 1 | 2 | 3 | 4
                    const isEditing = editingReviewField === f.field_name
                    const bounds = TIER_THRESHOLD_BOUNDS[tier]

                    return (
                      <tr key={f.field_name} className="border-b border-[#1e2d45] last:border-0">
                        <td className="px-4 py-3 font-mono text-white">{f.field_name}</td>
                        <td className="px-4 py-3">
                          {isEditing ? (
                            <select
                              defaultValue={tier}
                              onChange={(e) => {
                                const newTier = parseInt(e.target.value) as 1 | 2 | 3 | 4
                                handleUpdateReviewField(
                                  f.field_name,
                                  newTier,
                                  TIER_DEFAULTS[newTier]
                                )
                              }}
                              className="bg-[#080c18] border border-[#1e2d45] text-white text-xs rounded px-2 py-1"
                            >
                              {([1, 2, 3, 4] as const).map((t) => (
                                <option key={t} value={t}>T{t} — {TIER_LABELS[t]}</option>
                              ))}
                            </select>
                          ) : (
                            <TierPill tier={tier} small />
                          )}
                        </td>
                        <td className="px-4 py-3">
                          {isEditing && tier !== 4 ? (
                            <input
                              type="number"
                              defaultValue={f.threshold}
                              min={bounds.min}
                              max={bounds.max}
                              step={0.01}
                              onBlur={(e) => {
                                const val = Math.min(
                                  bounds.max,
                                  Math.max(bounds.min, parseFloat(e.target.value) || bounds.min)
                                )
                                handleUpdateReviewField(f.field_name, tier, val)
                              }}
                              className="w-20 bg-[#080c18] border border-[#1e2d45] text-white text-xs rounded px-2 py-1 font-mono"
                            />
                          ) : (
                            <span className={`font-mono text-xs ${TIER_TEXT[tier]}`}>
                              {tier === 4 ? '0.00 (locked)' : f.threshold.toFixed(2)}
                            </span>
                          )}
                        </td>
                        <td className="px-4 py-3 text-right">
                          <button
                            onClick={() =>
                              setEditingReviewField(isEditing ? null : f.field_name)
                            }
                            className="text-[#64748b] hover:text-white text-sm"
                          >
                            {isEditing ? '✓' : '✏️'}
                          </button>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Stats */}
        <div className="grid grid-cols-5 gap-3 mb-6">
          {([1, 2, 3, 4] as const).map((t) => (
            <div
              key={t}
              className={`bg-[#0f1724] border ${TIER_BORDER[t]} border-opacity-40 rounded-lg p-3 text-center`}
            >
              <p className={`text-2xl font-bold ${TIER_TEXT[t]}`}>{tierCounts[t]}</p>
              <p className="text-xs text-[#64748b] mt-1">T{t}</p>
            </div>
          ))}
          <div className="bg-[#0f1724] border border-[#1e2d45] rounded-lg p-3 text-center">
            <p className="text-2xl font-bold text-white">{allFields.length}</p>
            <p className="text-xs text-[#64748b] mt-1">Total</p>
          </div>
        </div>

        {error && <p className="text-[#ef4444] text-sm mb-4">{error}</p>}

        <div className="flex justify-end">
          <button
            onClick={handleExport}
            disabled={isLoading}
            className="bg-[#06b6d4] hover:bg-cyan-400 disabled:opacity-40 text-white font-semibold px-8 py-3 rounded-lg transition-colors flex items-center gap-2"
          >
            {isLoading ? (
              <><span className="animate-spin">⟳</span> Exporting…</>
            ) : (
              'Proceed to Export →'
            )}
          </button>
        </div>
      </div>
    )
  }

  const renderStep6 = () => {
    if (!exportResult) return null

    // Pretty-print JSON for safe plain-text rendering
    let prettyContent = exportResult.content
    try {
      prettyContent = JSON.stringify(JSON.parse(exportResult.content), null, 2)
    } catch {
      // fallback to raw content if parsing fails
    }

    return (
      <div className="max-w-5xl mx-auto">
        <div className="flex items-center gap-3 mb-8">
          <span className="text-3xl text-[#06b6d4]">✓</span>
          <div>
            <h2 className="text-2xl font-bold text-white">Registry Ready</h2>
            <p className="text-[#64748b] text-sm mt-0.5">
              {exportResult.field_count} fields · {exportResult.t1_count} T1 fields ·{' '}
              {exportResult.saved_to_server ? 'saved to server' : 'content ready for download'}
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
          {/* JSON preview */}
          <div className="lg:col-span-3 bg-[#0f1724] border border-[#1e2d45] rounded-xl overflow-hidden">
            <div className="flex items-center gap-2 px-4 py-2.5 border-b border-[#1e2d45] bg-[#080c18]">
              <span className="text-xs text-[#64748b] font-mono">{exportResult.filename}</span>
            </div>
            <pre className="p-4 text-xs font-mono overflow-auto max-h-96 text-[#94a3b8] leading-relaxed whitespace-pre">
              {prettyContent}
            </pre>
          </div>

          {/* Right panel */}
          <div className="lg:col-span-2 space-y-4">
            <button
              onClick={handleDownload}
              className="w-full bg-[#06b6d4] hover:bg-cyan-400 text-white font-semibold py-3 rounded-lg transition-colors flex items-center justify-center gap-2"
            >
              ⬇ Download {exportResult.filename}
            </button>

            <div className="bg-[#0f1724] border border-[#1e2d45] rounded-xl p-5">
              <h3 className="text-sm font-semibold text-white mb-4">Next Steps</h3>
              <ol className="space-y-3 text-sm text-[#94a3b8]">
                <li className="flex gap-2.5">
                  <span className="text-[#06b6d4] font-bold flex-shrink-0">1.</span>
                  <span>
                    Copy{' '}
                    <code className="text-[#06b6d4] font-mono text-xs">
                      {exportResult.filename}
                    </code>{' '}
                    to your{' '}
                    <code className="text-[#94a3b8] font-mono text-xs">registries/</code> folder
                  </span>
                </li>
                <li className="flex gap-2.5">
                  <span className="text-[#06b6d4] font-bold flex-shrink-0">2.</span>
                  <span>
                    Set{' '}
                    <code className="text-[#94a3b8] font-mono text-xs">
                      REGISTRY_DIR=./registries
                    </code>{' '}
                    in your <code className="text-[#94a3b8] font-mono text-xs">.env</code>
                  </span>
                </li>
                <li className="flex gap-2.5">
                  <span className="text-[#06b6d4] font-bold flex-shrink-0">3.</span>
                  <span>
                    Use{' '}
                    <code className="text-[#94a3b8] font-mono text-xs">
                      registry_id=&quot;{exportResult.registry_id}&quot;
                    </code>{' '}
                    in API calls
                  </span>
                </li>
              </ol>
            </div>

            <button
              onClick={handleReset}
              className="w-full bg-[#0f1724] border border-[#1e2d45] hover:border-[#06b6d4] text-[#06b6d4] py-3 rounded-lg font-medium text-sm transition-colors"
            >
              + Start another registry
            </button>
          </div>
        </div>
      </div>
    )
  }

  const renderCurrentStep = () => {
    switch (step) {
      case 1: return renderStep1()
      case 2: return renderStep2()
      case 3: return renderStep3()
      case 4: return renderStep4()
      case 5: return renderStep5()
      case 6: return renderStep6()
    }
  }

  const fieldCount =
    step >= 3
      ? analysisResults.length
      : step === 2
      ? extractedFields.length
      : 0

  return (
    <div className="min-h-screen bg-[#080c18] text-white px-4 py-8">
      <div className="max-w-5xl mx-auto">
        <Stepper step={step} integrationName={integrationName} fieldCount={fieldCount} />
        {renderCurrentStep()}
      </div>
    </div>
  )
}
