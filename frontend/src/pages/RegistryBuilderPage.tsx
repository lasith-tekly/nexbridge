import React, { useState, useRef } from 'react'
import { TIER_COLOURS } from '@/constants/tiers'
import { nexbridgeApi } from '@/services/nexbridgeApi'
import type {
  AnalysedField,
  ConfirmedT1,
  ReviewField,
  ExportResult,
  ConfirmedMapping,
} from '@/types/registryBuilder.types'
import type {
  ProposeMappingsResponse,
  MappingProposal,
} from '@/types/nexbridge.types'

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

const STEP_LABELS = ['Extract', 'Analyse', 'Confirm T1', 'Map', 'Review', 'Export']

type Format = 'xml' | 'json'
type Step = 1 | 2 | 3 | 4 | 5 | 6 | 7

// ── Sub-components ─────────────────────────────────────────────────────────────

const Stepper: React.FC<{ step: Step; integrationName: string; fieldCount: number }> = ({
  step,
  integrationName,
  fieldCount,
}) => {
  if (step === 1) return null
  const currentIndex = step - 2

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
                className={`h-px w-6 flex-shrink-0 ${
                  i < currentIndex ? 'bg-[#06b6d4]' : 'bg-[#1e2d45]'
                }`}
              />
            )}
          </React.Fragment>
        ))}
      </div>

      {step > 1 && step < 7 && integrationName && (
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
    className={`inline-flex items-center rounded-full font-bold text-white ${TIER_COLOURS[tier].bg} ${
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
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 bg-[#1e2d45] rounded-full h-1.5">
        <div
          className={`${TIER_COLOURS[tier].bg} h-full rounded-full`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-xs font-mono text-[#64748b] w-8 text-right">
        {confidence.toFixed(2)}
      </span>
    </div>
  )
}

// Confidence colour: ≥0.9 green, 0.7–0.89 amber, <0.7 red
function confidenceColour(c: number): string {
  if (c >= 0.9) return 'text-green-400'
  if (c >= 0.7) return 'text-[#f59e0b]'
  return 'text-[#ef4444]'
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

function extractFields(content: string, fmt: Format): string[] {
  return fmt === 'xml' ? extractFieldsFromXml(content) : extractFieldsFromJson(content)
}

function buildReviewField(f: AnalysedField, confirmedT1s: ConfirmedT1[]): ReviewField {
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

// ── FileUploadZone ─────────────────────────────────────────────────────────────

interface FileUploadZoneProps {
  label: string
  files: File[]
  inputRef: React.RefObject<HTMLInputElement>
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void
}

const FileUploadZone: React.FC<FileUploadZoneProps> = ({ label, files, inputRef, onChange }) => (
  <div>
    <label className="block text-sm font-medium text-[#94a3b8] mb-1.5">{label}</label>
    <div
      onClick={() => inputRef.current?.click()}
      className="w-full bg-[#0f1724] border-2 border-dashed border-[#1e2d45] rounded-lg px-4 py-6 text-center cursor-pointer hover:border-[#06b6d4] transition-colors"
    >
      <div className="text-2xl mb-1">📂</div>
      <p className="text-[#64748b] text-sm">Click to upload .xml or .json files</p>
      <p className="text-[#334155] text-xs mt-0.5">Multiple files supported</p>
      <input
        ref={inputRef}
        type="file"
        multiple
        accept=".xml,.json"
        onChange={onChange}
        className="hidden"
      />
    </div>
    {files.length > 0 && (
      <ul className="mt-2 space-y-1">
        {files.map((f) => (
          <li key={f.name} className="text-xs text-[#06b6d4] flex items-center gap-1.5">
            <span>✓</span> {f.name}
          </li>
        ))}
      </ul>
    )}
  </div>
)

// ── Main component ─────────────────────────────────────────────────────────────

export const RegistryBuilderPage: React.FC = () => {
  const [step, setStep] = useState<Step>(1)
  const [integrationName, setIntegrationName] = useState('')
  const [sourceSystemName, setSourceSystemName] = useState('')
  const [targetSystemName, setTargetSystemName] = useState('')
  const [sourceFormat, setSourceFormat] = useState<Format>('xml')

  // System A
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([])
  const [fileContents, setFileContents] = useState<Record<string, string>>({})
  const [extractedFields, setExtractedFields] = useState<string[]>([])
  const fileInputRef = useRef<HTMLInputElement>(null)

  // System B
  const [systemBFiles, setSystemBFiles] = useState<File[]>([])
  const [systemBFileContents, setSystemBFileContents] = useState<Record<string, string>>({})
  const [systemBFields, setSystemBFields] = useState<string[]>([])
  const systemBFileInputRef = useRef<HTMLInputElement>(null)

  // Analysis
  const [analysisResults, setAnalysisResults] = useState<AnalysedField[]>([])
  const [proposeMappingsResult, setProposeMappingsResult] = useState<ProposeMappingsResponse | null>(null)

  // T1 field confirmation
  const [confirmedT1Fields, setConfirmedT1Fields] = useState<ConfirmedT1[]>([])
  const [t1Index, setT1Index] = useState(0)
  const [reclassifyField, setReclassifyField] = useState<string | null>(null)

  // Mapping review (step 5)
  const [acceptedMappingKeys, setAcceptedMappingKeys] = useState<Set<string>>(new Set())
  const [overriddenTargets, setOverriddenTargets] = useState<Record<string, string>>({})
  const [confirmedMappings, setConfirmedMappings] = useState<ConfirmedMapping[]>([])

  // Full review (step 6)
  const [allFields, setAllFields] = useState<ReviewField[]>([])
  const [editingReviewField, setEditingReviewField] = useState<string | null>(null)
  const [editingT1Field, setEditingT1Field] = useState<string | null>(null)

  // Export (step 7)
  const [exportResult, setExportResult] = useState<ExportResult | null>(null)

  // Shared UI state
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const [manualField, setManualField] = useState('')
  const [analyseFilter, setAnalyseFilter] = useState<'All' | 'T1' | 'T2' | 'T3' | 'T4'>('All')
  const [acceptedNonT1, setAcceptedNonT1] = useState<Set<string>>(new Set())
  const [overrideField, setOverrideField] = useState<string | null>(null)

  // Derived
  const t1Fields = analysisResults.filter((f) => f.suggested_tier === 1)
  const nonT1Fields = analysisResults.filter((f) => f.suggested_tier !== 1)
  const allNonT1Accepted =
    nonT1Fields.length > 0 &&
    nonT1Fields.every((f) => acceptedNonT1.has(f.field_name))
  const currentT1 = t1Fields[t1Index] ?? null
  const effectiveSrcName = sourceSystemName.trim() || 'System A'
  const effectiveTgtName = targetSystemName.trim() || 'System B'

  // ── File reading helpers ────────────────────────────────────────────────────

  function readFiles(
    files: File[],
    setFiles: React.Dispatch<React.SetStateAction<File[]>>,
    setContents: (c: Record<string, string>) => void
  ) {
    setFiles(files)
    setError('')
    const contents: Record<string, string> = {}
    let completed = 0
    files.forEach((file) => {
      const reader = new FileReader()
      reader.onload = (ev) => {
        contents[file.name] = ev.target?.result as string
        completed++
        if (completed === files.length) setContents({ ...contents })
      }
      reader.onerror = () => {
        completed++
        setError(`Failed to read file: ${file.name}`)
        setFiles((prev) => prev.filter((f) => f.name !== file.name))
        if (completed === files.length) setContents({ ...contents })
      }
      reader.readAsText(file)
    })
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    readFiles(Array.from(e.target.files ?? []), setUploadedFiles, setFileContents)
  }

  const handleSystemBFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    readFiles(Array.from(e.target.files ?? []), setSystemBFiles, setSystemBFileContents)
  }

  // ── Step handlers ────────────────────────────────────────────────────────────

  const handleExtract = () => {
    if (!integrationName.trim()) { setError('Integration name is required.'); return }
    if (uploadedFiles.length === 0) { setError('Please upload at least one System A file.'); return }
    setError('')

    const allA = new Set<string>()
    for (const content of Object.values(fileContents)) {
      extractFields(content, sourceFormat).forEach((n) => allA.add(n))
    }
    setExtractedFields(Array.from(allA))

    const detectFormat = (filename: string): Format =>
      filename.endsWith('.json') ? 'json' : 'xml'

    const allB = new Set<string>()
    for (const [filename, content] of Object.entries(systemBFileContents)) {
      extractFields(content, detectFormat(filename)).forEach((n) => allB.add(n))
    }
    setSystemBFields(Array.from(allB))

    setStep(2)
  }

  const handleAddManualField = () => {
    const name = manualField.trim()
    if (name && !extractedFields.includes(name)) setExtractedFields((prev) => [...prev, name])
    setManualField('')
  }

  const handleAnalyse = async () => {
    setIsLoading(true)
    setError('')
    try {
      const firstContent = Object.values(fileContents)[0] ?? ''

      // Step 1: await analyse so we have real tier data before proposing mappings
      const analyseRes = await fetch('http://localhost:8000/registry/analyse', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          payload: firstContent,
          source_format: sourceFormat,
          context: integrationName,
        }),
      })
      if (!analyseRes.ok) {
        const err = await analyseRes.json()
        throw new Error(err.detail ?? 'Analysis failed')
      }
      const analyseData = await analyseRes.json()
      setAnalysisResults(analyseData.fields)
      setAcceptedNonT1(new Set())

      // Step 2: if System B present, call propose-mappings with real tiers
      if (systemBFields.length > 0) {
        const result = await nexbridgeApi.proposeMappings({
          domain: integrationName,
          source_system: effectiveSrcName,
          target_system: effectiveTgtName,
          system_a_fields: analyseData.fields.map((f: AnalysedField) => ({
            name: f.field_name,
            tier: f.suggested_tier,
            threshold: TIER_DEFAULTS[f.suggested_tier as 1 | 2 | 3 | 4],
          })),
          system_b_fields: systemBFields,
        }).catch(() => null) // non-fatal: degrade gracefully if propose-mappings fails
        setProposeMappingsResult(result)
      }

      setStep(3)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Analysis failed')
    } finally {
      setIsLoading(false)
    }
  }

  const handleAcceptField = (fieldName: string) =>
    setAcceptedNonT1((prev) => new Set([...prev, fieldName]))

  const handleAcceptAllNonT1 = () =>
    setAcceptedNonT1(new Set(nonT1Fields.map((f) => f.field_name)))

  const handleOverrideTier = (fieldName: string, newTier: 1 | 2 | 3 | 4) => {
    setAnalysisResults((prev) =>
      prev.map((f) =>
        f.field_name === fieldName
          ? { ...f, suggested_tier: newTier, suggested_label: TIER_LABELS[newTier] }
          : f
      )
    )
    setOverrideField(null)
    if (newTier !== 1) setAcceptedNonT1((prev) => new Set([...prev, fieldName]))
  }

  const handleProceedToT1 = () => {
    if (t1Fields.length === 0) {
      setAllFields(analysisResults.map((f) => buildReviewField(f, [])))
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
      setAllFields(analysisResults.map((f) => buildReviewField(f, updated)))
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
      setAllFields(analysisResults.map((f) => buildReviewField(f, confirmedT1Fields)))
      setStep(5)
    }
  }

  // Step 5 — Mapping Review handlers

  const handleConfirmMapping = (sourceField: string) =>
    setAcceptedMappingKeys((prev) => new Set([...prev, sourceField]))

  const handleAcceptAllNonT1Mappings = () => {
    const proposals = proposeMappingsResult?.proposed_mappings ?? []
    const keys = proposals
      .filter((m) => m.effective_tier > 1)
      .map((m) => m.source_field)
    setAcceptedMappingKeys((prev) => new Set([...prev, ...keys]))
  }

  const handleOverrideTarget = (sourceField: string, newTarget: string) =>
    setOverriddenTargets((prev) => ({ ...prev, [sourceField]: newTarget }))

  const handleProceedFromMappingReview = () => {
    const proposals = proposeMappingsResult?.proposed_mappings ?? []
    const bTiers = proposeMappingsResult?.system_b_tiers ?? {}
    const confirmed: ConfirmedMapping[] = proposals.map((m) => {
      const resolvedTarget = overriddenTargets[m.source_field] ?? m.target_field
      const resolvedTargetTier =
        bTiers[resolvedTarget]?.tier ?? m.target_tier
      const effectiveTier = Math.min(m.source_tier, resolvedTargetTier)
      return {
        sourceField: m.source_field,
        targetField: resolvedTarget,
        confidence: m.confidence,
        sourceTier: m.source_tier,
        targetTier: resolvedTargetTier,
        effectiveTier,
        llmGenerated: !overriddenTargets[m.source_field],
        confirmedAt: new Date().toISOString(),
      }
    })
    setConfirmedMappings(confirmed)
    setStep(6)
  }

  // Step 6 — Full Review handlers

  const handleUpdateReviewField = (fieldName: string, newTier: 1 | 2 | 3 | 4, newThreshold: number) => {
    if (newTier === 1) {
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
          ? { ...f, tier: newTier, label: TIER_LABELS[newTier], threshold: newThreshold, confirmed_individually: false }
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
      // Build target_schema from System B tier classifications
      const targetSchema: Record<string, { type: string; tier: number }> = {}
      if (proposeMappingsResult) {
        for (const [fieldName, tierResult] of Object.entries(proposeMappingsResult.system_b_tiers)) {
          targetSchema[fieldName] = { type: 'string', tier: tierResult.tier }
        }
      }

      // Build approved_mappings from confirmed mapping state
      const approvedMappings: Record<string, {
        target_field: string
        confidence: number
        approved_by: string
        approved_at: string
        llm_generated: boolean
      }> = {}
      for (const mapping of confirmedMappings) {
        approvedMappings[mapping.sourceField] = {
          target_field: mapping.targetField,
          confidence: mapping.confidence,
          approved_by: 'registry_builder',
          approved_at: mapping.confirmedAt,
          llm_generated: mapping.llmGenerated,
        }
      }

      const res = await fetch('http://localhost:8000/registry/export', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          fields: allFields,
          integration_name: integrationName,
          domain: integrationName,
          target_schema: Object.keys(targetSchema).length > 0 ? targetSchema : undefined,
          approved_mappings: Object.keys(approvedMappings).length > 0 ? approvedMappings : undefined,
        }),
      })
      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail ?? 'Export failed')
      }
      const data: ExportResult = await res.json()
      setExportResult(data)
      setStep(7)
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
    setSourceSystemName('')
    setTargetSystemName('')
    setSourceFormat('xml')
    setUploadedFiles([])
    setFileContents({})
    setExtractedFields([])
    setSystemBFiles([])
    setSystemBFileContents({})
    setSystemBFields([])
    setAnalysisResults([])
    setProposeMappingsResult(null)
    setConfirmedT1Fields([])
    setT1Index(0)
    setAcceptedMappingKeys(new Set())
    setOverriddenTargets({})
    setConfirmedMappings([])
    setAllFields([])
    setExportResult(null)
    setError('')
    setAcceptedNonT1(new Set())
    setAnalyseFilter('All')
  }

  // ── Screen renderers ─────────────────────────────────────────────────────────

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
          <label className="block text-sm font-medium text-[#94a3b8] mb-1.5">Integration Name</label>
          <input
            type="text"
            value={integrationName}
            onChange={(e) => setIntegrationName(e.target.value)}
            placeholder="e.g. flight-ops, hr-system, patient-records"
            className="w-full bg-[#0f1724] border border-[#1e2d45] rounded-lg px-4 py-3 text-white placeholder-[#334155] focus:outline-none focus:border-[#06b6d4] transition-colors"
          />
          <p className="text-xs text-[#64748b] mt-1">
            Use letters, numbers, hyphens, or underscores (e.g. flight-ops)
          </p>
        </div>

        <div>
          <label className="block text-sm font-medium text-[#94a3b8] mb-1.5">Source Format</label>
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

        {/* System A upload */}
        <div className="bg-[#0f1724] border border-[#1e2d45] rounded-xl p-4 space-y-3">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-semibold text-[#06b6d4] uppercase tracking-wider">System A — Sender</span>
          </div>
          <div>
            <label className="block text-sm font-medium text-[#94a3b8] mb-1.5">System Name</label>
            <input
              type="text"
              value={sourceSystemName}
              onChange={(e) => setSourceSystemName(e.target.value)}
              placeholder="e.g. FMS"
              className="w-full bg-[#080c18] border border-[#1e2d45] rounded-lg px-3 py-2 text-sm text-white placeholder-[#334155] focus:outline-none focus:border-[#06b6d4] transition-colors"
            />
          </div>
          <FileUploadZone
            label="Sample Payload Files"
            files={uploadedFiles}
            inputRef={fileInputRef}
            onChange={handleFileChange}
          />
        </div>

        {/* System B upload */}
        <div className="bg-[#0f1724] border border-[#1e2d45] rounded-xl p-4 space-y-3">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-semibold text-[#94a3b8] uppercase tracking-wider">System B — Receiver</span>
            <span className="text-xs text-[#64748b]">(optional)</span>
          </div>
          <div>
            <label className="block text-sm font-medium text-[#94a3b8] mb-1.5">System Name</label>
            <input
              type="text"
              value={targetSystemName}
              onChange={(e) => setTargetSystemName(e.target.value)}
              placeholder="e.g. GSP"
              className="w-full bg-[#080c18] border border-[#1e2d45] rounded-lg px-3 py-2 text-sm text-white placeholder-[#334155] focus:outline-none focus:border-[#06b6d4] transition-colors"
            />
          </div>
          <FileUploadZone
            label="Sample Payload Files"
            files={systemBFiles}
            inputRef={systemBFileInputRef}
            onChange={handleSystemBFileChange}
          />
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

  const renderStep2 = () => {
    const hasB = systemBFields.length > 0
    return (
      <div className="max-w-4xl mx-auto">
        <div className="mb-6">
          <h2 className="text-2xl font-bold text-white">Extracted Fields</h2>
          <p className="text-[#64748b] text-sm mt-1">
            {extractedFields.length} System A fields
            {hasB ? ` · ${systemBFields.length} System B fields` : ''}
            {' '}· {sourceFormat.toUpperCase()}
          </p>
        </div>

        <div className={`grid ${hasB ? 'grid-cols-2' : 'grid-cols-1'} gap-6 mb-6`}>
          {/* System A */}
          <div>
            {hasB && (
              <p className="text-xs font-semibold text-[#06b6d4] uppercase tracking-wider mb-2">
                {effectiveSrcName}
              </p>
            )}
            <div className="grid grid-cols-2 gap-2">
              {extractedFields.map((name) => (
                <div
                  key={name}
                  className="bg-[#0f1724] border border-[#1e2d45] rounded-lg px-3 py-2 font-mono text-sm text-white"
                >
                  {name}
                </div>
              ))}
            </div>
          </div>

          {/* System B */}
          {hasB && (
            <div>
              <p className="text-xs font-semibold text-[#94a3b8] uppercase tracking-wider mb-2">
                {effectiveTgtName}
              </p>
              <div className="grid grid-cols-2 gap-2">
                {systemBFields.map((name) => (
                  <div
                    key={name}
                    className="bg-[#0f1724] border border-[#1e2d45] rounded-lg px-3 py-2 font-mono text-sm text-[#94a3b8]"
                  >
                    {name}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        <div className="flex gap-2 mb-6">
          <input
            type="text"
            value={manualField}
            onChange={(e) => setManualField(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleAddManualField()}
            placeholder="Add System A field manually..."
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
          {isLoading ? <><span className="animate-spin">⟳</span> Analysing with AI…</> : 'Analyse with AI →'}
        </button>
      </div>
    )
  }

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

    const bTiers = proposeMappingsResult?.system_b_tiers ?? {}
    const hasB = Object.keys(bTiers).length > 0

    return (
      <div className="max-w-5xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-2xl font-bold text-white">AI Analysis Results</h2>
            <p className="text-[#64748b] text-sm mt-1">Review and accept tier classifications</p>
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

        <div className={`grid ${hasB ? 'grid-cols-2' : 'grid-cols-1'} gap-6 mb-4`}>
          {/* System A tier results */}
          <div>
            {hasB && (
              <p className="text-xs font-semibold text-[#06b6d4] uppercase tracking-wider mb-2">
                {effectiveSrcName} — Tier Analysis
              </p>
            )}
            <div className="bg-[#0f1724] border border-[#1e2d45] rounded-xl overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-[#1e2d45]">
                    <th className="text-left px-3 py-3 text-[#64748b] font-medium">Field</th>
                    <th className="text-left px-3 py-3 text-[#64748b] font-medium">Tier</th>
                    <th className="text-left px-3 py-3 text-[#64748b] font-medium">Conf.</th>
                    <th className="px-3 py-3" />
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
                        className={`border-b border-[#1e2d45] last:border-0 ${isT1 ? 'border-l-2 border-l-[#ef4444]' : ''}`}
                      >
                        <td className="px-3 py-2.5">
                          <span className="font-mono text-white text-xs">{f.field_name}</span>
                        </td>
                        <td className="px-3 py-2.5">
                          <div className="flex items-center gap-1">
                            <TierPill tier={tier} small />
                            {isT1 && <span className="text-[#ef4444] text-xs">⚠️</span>}
                          </div>
                        </td>
                        <td className="px-3 py-2.5 w-24">
                          <SmallConfidenceBar confidence={f.confidence} tier={tier} />
                        </td>
                        <td className="px-3 py-2.5 text-right">
                          {isT1 ? (
                            <span className="text-xs text-[#ef4444] font-medium">→ confirm</span>
                          ) : (
                            <div className="flex items-center gap-1.5 justify-end">
                              {overrideField === f.field_name ? (
                                <select
                                  autoFocus
                                  onChange={(e) => handleOverrideTier(f.field_name, parseInt(e.target.value) as 1 | 2 | 3 | 4)}
                                  onBlur={() => setOverrideField(null)}
                                  className="bg-[#080c18] border border-[#1e2d45] text-white text-xs rounded px-2 py-1"
                                  defaultValue={tier}
                                >
                                  {([1, 2, 3, 4] as const).map((t) => (
                                    <option key={t} value={t}>T{t}</option>
                                  ))}
                                </select>
                              ) : (
                                <>
                                  <button onClick={() => setOverrideField(f.field_name)} className="text-[#64748b] hover:text-white text-xs">✏️</button>
                                  <button
                                    onClick={() => handleAcceptField(f.field_name)}
                                    disabled={accepted}
                                    className={`text-xs px-2 py-0.5 rounded font-medium transition-colors ${
                                      accepted ? 'text-green-400 cursor-default' : 'text-[#06b6d4] hover:text-white'
                                    }`}
                                  >
                                    {accepted ? '✓' : 'Accept'}
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
          </div>

          {/* System B tier results */}
          {hasB && (
            <div>
              <p className="text-xs font-semibold text-[#94a3b8] uppercase tracking-wider mb-2">
                {effectiveTgtName} — Tier Analysis
              </p>
              <div className="bg-[#0f1724] border border-[#1e2d45] rounded-xl overflow-hidden">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-[#1e2d45]">
                      <th className="text-left px-3 py-3 text-[#64748b] font-medium">Field</th>
                      <th className="text-left px-3 py-3 text-[#64748b] font-medium">Tier</th>
                      <th className="text-left px-3 py-3 text-[#64748b] font-medium">Reasoning</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(bTiers).map(([name, result]) => {
                      const tier = result.tier as 1 | 2 | 3 | 4
                      const isT1 = tier === 1
                      return (
                        <tr
                          key={name}
                          className={`border-b border-[#1e2d45] last:border-0 ${isT1 ? 'border-l-2 border-l-[#ef4444]' : ''}`}
                        >
                          <td className="px-3 py-2.5 font-mono text-[#94a3b8] text-xs">{name}</td>
                          <td className="px-3 py-2.5">
                            <div className="flex items-center gap-1">
                              <TierPill tier={tier} small />
                              {isT1 && <span className="text-[#ef4444] text-xs">⚠️</span>}
                            </div>
                          </td>
                          <td className="px-3 py-2.5 text-[#64748b] text-xs max-w-xs">{result.reasoning}</td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}
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

  // Step 4 — T1 confirmation (unchanged logic)
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
    } catch { sampleValue = '' }

    return (
      <div className="max-w-xl mx-auto">
        <div className="bg-[#1a0a0a] border border-[#ef4444] border-opacity-50 rounded-xl p-4 mb-6 flex items-center gap-3 text-sm text-[#ef4444]">
          <span className="text-lg">⚠️</span>
          <div>
            <p className="font-semibold">T1 Safety Critical — Individual Confirmation Required</p>
            <p className="opacity-80 text-xs mt-0.5">Field {t1Index + 1} of {t1Fields.length}</p>
          </div>
        </div>

        <div className="flex gap-1.5 mb-6">
          {t1Fields.map((_, i) => (
            <div
              key={i}
              className={`h-1.5 flex-1 rounded-full ${i < t1Index ? 'bg-[#06b6d4]' : i === t1Index ? 'bg-[#ef4444]' : 'bg-[#1e2d45]'}`}
            />
          ))}
        </div>

        <div className="bg-[#0f1724] border border-[#1e2d45] rounded-xl p-6 mb-6">
          <div className="flex items-center gap-2 mb-4">
            <TierPill tier={1} />
            <span className="text-[#ef4444] font-medium text-sm">Safety Critical</span>
          </div>
          <p className="font-mono text-2xl text-white font-bold mb-4">{currentT1.field_name}</p>
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
              onChange={(e) => handleReclassifyT1(currentT1.field_name, parseInt(e.target.value) as 2 | 3 | 4)}
              className="w-full bg-[#0f1724] border border-[#1e2d45] text-white rounded-lg px-3 py-2 focus:outline-none focus:border-[#06b6d4]"
              defaultValue=""
            >
              <option value="" disabled>Select tier…</option>
              {([2, 3, 4] as const).map((t) => (
                <option key={t} value={t}>T{t} — {TIER_LABELS[t]}</option>
              ))}
            </select>
            <button onClick={() => setReclassifyField(null)} className="mt-2 text-xs text-[#64748b] hover:text-white">Cancel</button>
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

  // Step 5 — Mapping Review (new)
  const renderStep5 = () => {
    const proposals = proposeMappingsResult?.proposed_mappings ?? []
    const bTiers = proposeMappingsResult?.system_b_tiers ?? {}

    const allMappingsAccepted =
      proposals.length > 0 && proposals.every((m) => acceptedMappingKeys.has(m.source_field))

    const t1MappingsPending = proposals.filter(
      (m) => m.effective_tier === 1 && !acceptedMappingKeys.has(m.source_field)
    )

    if (!proposeMappingsResult || proposals.length === 0) {
      return (
        <div className="max-w-2xl mx-auto text-center">
          <h2 className="text-2xl font-bold text-white mb-3">Review Proposed Mappings</h2>
          <div className="bg-[#0f1724] border border-[#1e2d45] rounded-xl p-8 mb-6">
            <p className="text-[#64748b]">System B not uploaded — mappings will be generated at runtime.</p>
          </div>
          <button
            onClick={() => { setConfirmedMappings([]); setStep(6) }}
            className="bg-[#06b6d4] hover:bg-cyan-400 text-white font-semibold px-8 py-3 rounded-lg transition-colors"
          >
            Skip →
          </button>
        </div>
      )
    }

    return (
      <div className="max-w-5xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-2xl font-bold text-white">Review Proposed Mappings</h2>
            <p className="text-[#64748b] text-sm mt-1">
              AI has proposed the following field mappings between{' '}
              <span className="text-[#06b6d4]">{effectiveSrcName}</span> and{' '}
              <span className="text-[#94a3b8]">{effectiveTgtName}</span>.
              Confirm or override each one.
            </p>
          </div>
          <button
            onClick={handleAcceptAllNonT1Mappings}
            className="bg-[#0f1724] border border-[#1e2d45] hover:border-[#06b6d4] text-[#06b6d4] px-4 py-2 rounded-lg text-sm font-medium transition-colors flex-shrink-0"
          >
            Accept All Non-T1 Mappings
          </button>
        </div>

        <div className="bg-[#0f1724] border border-[#1e2d45] rounded-xl overflow-hidden mb-4">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[#1e2d45]">
                <th className="text-left px-4 py-3 text-[#64748b] font-medium">Source Field</th>
                <th className="text-left px-4 py-3 text-[#64748b] font-medium">→ Target Field</th>
                <th className="text-left px-4 py-3 text-[#64748b] font-medium">Confidence</th>
                <th className="text-left px-4 py-3 text-[#64748b] font-medium">Effective Tier</th>
                <th className="text-left px-4 py-3 text-[#64748b] font-medium">Mismatch</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody>
              {proposals.map((m: MappingProposal) => {
                const effectiveTier = m.effective_tier as 1 | 2 | 3 | 4
                const isT1Effective = effectiveTier === 1
                const isConfirmed = acceptedMappingKeys.has(m.source_field)
                const resolvedTarget = overriddenTargets[m.source_field] ?? m.target_field
                const sourceTier = m.source_tier as 1 | 2 | 3 | 4
                const resolvedTargetTier = (bTiers[resolvedTarget]?.tier ?? m.target_tier) as 1 | 2 | 3 | 4

                return (
                  <tr
                    key={m.source_field}
                    className={`border-b border-[#1e2d45] last:border-0 ${isT1Effective ? 'border-l-2 border-l-[#ef4444]' : ''}`}
                  >
                    {/* Source field */}
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-white text-xs">{m.source_field}</span>
                        <TierPill tier={sourceTier} small />
                      </div>
                    </td>

                    {/* Target field — editable */}
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <select
                          value={resolvedTarget}
                          onChange={(e) => handleOverrideTarget(m.source_field, e.target.value)}
                          className="bg-[#080c18] border border-[#1e2d45] text-white text-xs rounded px-2 py-1 font-mono focus:outline-none focus:border-[#06b6d4]"
                        >
                          {systemBFields.map((f) => (
                            <option key={f} value={f}>{f}</option>
                          ))}
                        </select>
                        <TierPill tier={resolvedTargetTier} small />
                      </div>
                    </td>

                    {/* Confidence */}
                    <td className="px-4 py-3">
                      <span className={`font-mono text-xs font-semibold ${confidenceColour(m.confidence)}`}>
                        {Math.round(m.confidence * 100)}%
                      </span>
                    </td>

                    {/* Effective tier */}
                    <td className="px-4 py-3">
                      <TierPill tier={effectiveTier} small />
                    </td>

                    {/* Mismatch badge */}
                    <td className="px-4 py-3">
                      {m.tier_mismatch ? (
                        <span className="inline-flex items-center gap-1 text-xs bg-amber-900 text-amber-300 px-2 py-0.5 rounded-full font-medium">
                          ⚠ Tier Mismatch
                        </span>
                      ) : (
                        <span className="text-xs text-[#64748b]">—</span>
                      )}
                    </td>

                    {/* Action */}
                    <td className="px-4 py-3 text-right">
                      {isConfirmed ? (
                        <span className="text-xs text-green-400 font-medium">✓ Confirmed</span>
                      ) : isT1Effective ? (
                        <button
                          onClick={() => handleConfirmMapping(m.source_field)}
                          className="text-xs px-3 py-1.5 rounded-lg font-semibold bg-[#1a0a0a] border border-[#ef4444] text-[#ef4444] hover:bg-[#ef4444] hover:text-white transition-colors"
                        >
                          Confirm individually
                        </button>
                      ) : (
                        <button
                          onClick={() => handleConfirmMapping(m.source_field)}
                          className="text-xs px-3 py-1 rounded-lg font-medium bg-[#0f1724] border border-[#1e2d45] hover:border-[#06b6d4] text-[#06b6d4] transition-colors"
                        >
                          Accept
                        </button>
                      )}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>

        {t1MappingsPending.length > 0 && (
          <div className="bg-[#1a0a0a] border border-[#ef4444] border-opacity-40 rounded-lg px-4 py-3 mb-4 flex items-center gap-2 text-sm text-[#ef4444]">
            ⚠️ {t1MappingsPending.length} T1-effective mapping{t1MappingsPending.length !== 1 ? 's' : ''} require individual confirmation before continuing
          </div>
        )}

        <div className="flex justify-end">
          <button
            onClick={handleProceedFromMappingReview}
            disabled={!allMappingsAccepted}
            className="bg-[#06b6d4] hover:bg-cyan-400 disabled:opacity-40 disabled:cursor-not-allowed text-white font-semibold px-8 py-3 rounded-lg transition-colors"
          >
            Continue →
          </button>
        </div>
      </div>
    )
  }

  // Step 6 — Full Review (was step 5, + confirmed mappings section)
  const renderStep6 = () => {
    const t1Reviewed = allFields.filter((f) => f.tier === 1)
    const nonT1Reviewed = allFields.filter((f) => f.tier !== 1)
    const tierCounts = { 1: 0, 2: 0, 3: 0, 4: 0 }
    allFields.forEach((f) => tierCounts[f.tier]++)

    return (
      <div className="max-w-4xl mx-auto">
        <div className="mb-6">
          <h2 className="text-2xl font-bold text-white">Full Review</h2>
          <p className="text-[#64748b] text-sm mt-1">Final check before export</p>
        </div>

        {/* Confirmed Mappings section */}
        <div className="mb-6">
          <h3 className="text-sm font-semibold text-[#06b6d4] uppercase tracking-wider mb-3">
            Confirmed Mappings
          </h3>
          {confirmedMappings.length > 0 ? (
            <div className="bg-[#0f1724] border border-[#1e2d45] rounded-xl overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-[#1e2d45]">
                    <th className="text-left px-4 py-3 text-[#64748b] font-medium">Source → Target</th>
                    <th className="text-left px-4 py-3 text-[#64748b] font-medium">Effective Tier</th>
                    <th className="text-left px-4 py-3 text-[#64748b] font-medium">Confidence</th>
                  </tr>
                </thead>
                <tbody>
                  {confirmedMappings.map((m) => (
                    <tr key={m.sourceField} className="border-b border-[#1e2d45] last:border-0">
                      <td className="px-4 py-2.5 font-mono text-sm text-white">
                        <span className="text-[#06b6d4]">{m.sourceField}</span>
                        <span className="text-[#64748b] mx-2">→</span>
                        <span className="text-[#94a3b8]">{m.targetField}</span>
                        {!m.llmGenerated && (
                          <span className="ml-2 text-xs text-[#f59e0b]">(overridden)</span>
                        )}
                      </td>
                      <td className="px-4 py-2.5">
                        <TierPill tier={m.effectiveTier as 1 | 2 | 3 | 4} small />
                      </td>
                      <td className="px-4 py-2.5">
                        <span className={`font-mono text-xs font-semibold ${confidenceColour(m.confidence)}`}>
                          {Math.round(m.confidence * 100)}%
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="bg-[#0f1724] border border-[#1e2d45] rounded-xl px-4 py-4 text-[#64748b] text-sm">
              No pre-approved mappings — runtime LLM mapping enabled.
            </div>
          )}
        </div>

        {/* T1 fields */}
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
                          <button onClick={() => setEditingT1Field(f.field_name)} className="text-[#64748b] hover:text-white text-sm">✏️</button>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* T2–T4 fields */}
        {nonT1Reviewed.length > 0 && (
          <div className="mb-6">
            <h3 className="text-sm font-semibold text-[#94a3b8] uppercase tracking-wider mb-3">T2–T4 Fields</h3>
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
                                handleUpdateReviewField(f.field_name, newTier, TIER_DEFAULTS[newTier])
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
                                const val = Math.min(bounds.max, Math.max(bounds.min, parseFloat(e.target.value) || bounds.min))
                                handleUpdateReviewField(f.field_name, tier, val)
                              }}
                              className="w-20 bg-[#080c18] border border-[#1e2d45] text-white text-xs rounded px-2 py-1 font-mono"
                            />
                          ) : (
                            <span className={`font-mono text-xs ${TIER_COLOURS[tier].text}`}>
                              {tier === 4 ? '0.00 (locked)' : f.threshold.toFixed(2)}
                            </span>
                          )}
                        </td>
                        <td className="px-4 py-3 text-right">
                          <button
                            onClick={() => setEditingReviewField(isEditing ? null : f.field_name)}
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
            <div key={t} className={`bg-[#0f1724] border ${TIER_COLOURS[t].border} border-opacity-40 rounded-lg p-3 text-center`}>
              <p className={`text-2xl font-bold ${TIER_COLOURS[t].text}`}>{tierCounts[t]}</p>
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
            {isLoading ? <><span className="animate-spin">⟳</span> Exporting…</> : 'Proceed to Export →'}
          </button>
        </div>
      </div>
    )
  }

  // Step 7 — Export (was step 6, unchanged visually)
  const renderStep7 = () => {
    if (!exportResult) return null
    let prettyContent = exportResult.content
    try { prettyContent = JSON.stringify(JSON.parse(exportResult.content), null, 2) } catch { /* use raw */ }

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
          <div className="lg:col-span-3 bg-[#0f1724] border border-[#1e2d45] rounded-xl overflow-hidden">
            <div className="flex items-center gap-2 px-4 py-2.5 border-b border-[#1e2d45] bg-[#080c18]">
              <span className="text-xs text-[#64748b] font-mono">{exportResult.filename}</span>
            </div>
            <pre className="p-4 text-xs font-mono overflow-auto max-h-96 text-[#94a3b8] leading-relaxed whitespace-pre">
              {prettyContent}
            </pre>
          </div>

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
                  <span>Copy <code className="text-[#06b6d4] font-mono text-xs">{exportResult.filename}</code> to your <code className="text-[#94a3b8] font-mono text-xs">registries/</code> folder</span>
                </li>
                <li className="flex gap-2.5">
                  <span className="text-[#06b6d4] font-bold flex-shrink-0">2.</span>
                  <span>Set <code className="text-[#94a3b8] font-mono text-xs">REGISTRY_DIR=./registries</code> in your <code className="text-[#94a3b8] font-mono text-xs">.env</code></span>
                </li>
                <li className="flex gap-2.5">
                  <span className="text-[#06b6d4] font-bold flex-shrink-0">3.</span>
                  <span>Use <code className="text-[#94a3b8] font-mono text-xs">registry_id=&quot;{exportResult.registry_id}&quot;</code> in API calls</span>
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
      case 7: return renderStep7()
    }
  }

  const fieldCount =
    step >= 3 ? analysisResults.length
    : step === 2 ? extractedFields.length
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
