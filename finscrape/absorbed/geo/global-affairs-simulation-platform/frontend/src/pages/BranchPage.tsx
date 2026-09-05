import { useEffect, useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { pipelineApi, branchApi, eventApi } from '../services/api'
import type { PredictionRun, BranchRun, DirectionType, AbstractIRGEvent } from '../types'
import { DIRECTION_CONFIG } from '../types'
import LoadingSpinner from '../components/LoadingSpinner'
import EmptyState from '../components/EmptyState'

const DIR_STYLE = {
  escalation:    { border: 'border-red-600/60',     bg: DIRECTION_CONFIG.escalation.bg,     text: DIRECTION_CONFIG.escalation.color,     line: DIRECTION_CONFIG.escalation.hex },
  stalemate:     { border: 'border-amber-600/60',   bg: DIRECTION_CONFIG.stalemate.bg,      text: DIRECTION_CONFIG.stalemate.color,      line: DIRECTION_CONFIG.stalemate.hex },
  de_escalation: { border: 'border-emerald-600/60', bg: DIRECTION_CONFIG.de_escalation.bg,  text: DIRECTION_CONFIG.de_escalation.color,  line: DIRECTION_CONFIG.de_escalation.hex },
} as const

function BranchMindMap({
  baseRun,
  branches,
  selectedEvent,
}: {
  baseRun: PredictionRun
  branches: BranchRun[]
  selectedEvent: AbstractIRGEvent | null
}) {
  const { t, i18n } = useTranslation()
  const [activeNode, setActiveNode] = useState<string | null>(null)

  if (branches.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-slate-600 gap-2">
        <div className="text-3xl" aria-hidden="true">🌿</div>
        <div className="text-sm">{t('branches.noBranches')}</div>
      </div>
    )
  }

  const ROOT_W  = 176
  const ROOT_H  = 92
  const BRANCH_W = 200
  const BRANCH_H = 74
  const GAP_Y   = 20
  const PAD     = 28
  const COL_GAP = 130

  const totalBranchH = branches.length * BRANCH_H + (branches.length - 1) * GAP_Y
  const canvasH = Math.max(ROOT_H + PAD * 2, totalBranchH + PAD * 2)
  const canvasW = PAD + ROOT_W + COL_GAP + BRANCH_W + PAD

  const rootX  = PAD
  const rootY  = canvasH / 2 - ROOT_H / 2
  const rootCX = rootX + ROOT_W
  const rootCY = rootY + ROOT_H / 2

  const branchX     = PAD + ROOT_W + COL_GAP
  const branchStartY = canvasH / 2 - totalBranchH / 2

  const nodes = branches.map((b, i) => ({
    branch: b,
    x: branchX,
    y: branchStartY + i * (BRANCH_H + GAP_Y),
  }))

  const getDir = (b: BranchRun) => (b.expected_direction ?? 'stalemate') as keyof typeof DIR_STYLE
  const getStyle = (b: BranchRun) => DIR_STYLE[getDir(b)] ?? DIR_STYLE.stalemate

  const activeBranch = branches.find(b => b.branch_run_id === activeNode)

  const dirLabels: Record<string, string> = {
    escalation: t('directions.escalation'),
    stalemate: t('directions.stalemate'),
    de_escalation: t('directions.de_escalation'),
  }

  return (
    <div>
      <div className="overflow-auto rounded-xl border border-slate-800 bg-surface-950/60">
        <div style={{ position: 'relative', width: canvasW, height: canvasH, minHeight: 300 }}>
          <svg
            style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', pointerEvents: 'none' }}
            aria-hidden="true"
          >
            {nodes.map(({ branch, x, y }) => {
              const s  = getStyle(branch)
              const bCY = y + BRANCH_H / 2
              const cx  = (rootCX + x) / 2
              const isActive = activeNode === branch.branch_run_id
              return (
                <path
                  key={branch.branch_run_id}
                  d={`M ${rootCX} ${rootCY} C ${cx} ${rootCY}, ${cx} ${bCY}, ${x} ${bCY}`}
                  stroke={s.line}
                  strokeWidth={isActive ? 2.5 : 1.5}
                  strokeOpacity={isActive ? 1 : 0.45}
                  fill="none"
                  strokeLinecap="round"
                />
              )
            })}
          </svg>

          <div
            style={{ position: 'absolute', left: rootX, top: rootY, width: ROOT_W, height: ROOT_H }}
            className="bg-surface-900 border-2 border-blue-600/70 rounded-xl p-3 flex flex-col justify-center shadow-lg"
          >
            <div className="text-[10px] text-blue-400 font-semibold tracking-wide mb-1">{t('branches.baseSimulation')}</div>
            <div className="text-xs text-slate-200 leading-snug line-clamp-3">
              {selectedEvent?.event_title ?? baseRun.summary ?? baseRun.run_id?.slice(0, 12)}
            </div>
            <div className="text-[10px] text-slate-600 mt-1.5">{branches.length} {t('branches.existingBranches')}</div>
          </div>

          {nodes.map(({ branch, x, y }) => {
            const s       = getStyle(branch)
            const isActive = activeNode === branch.branch_run_id
            const title   = branch.hypothesis_title ?? branch.branch_run_id?.slice(0, 12)
            const dirLabel = dirLabels[getDir(branch)] ?? getDir(branch)
            return (
              <button
                key={branch.branch_run_id}
                style={{ position: 'absolute', left: x, top: y, width: BRANCH_W, height: BRANCH_H }}
                onClick={() => setActiveNode(isActive ? null : branch.branch_run_id)}
                className={`text-left rounded-xl border-2 p-3 transition-all duration-200 ${s.bg} ${
                  isActive ? `${s.border} shadow-xl scale-[1.03]` : 'border-slate-700/50 hover:border-slate-600'
                }`}
              >
                <div className={`text-[10px] font-bold mb-1 ${s.text}`}>{dirLabel}</div>
                <div className="text-xs text-slate-300 leading-snug line-clamp-2">{title}</div>
                <div className="text-[10px] text-slate-600 mt-1.5">
                  {branch.created_at ? new Date(branch.created_at).toLocaleDateString(i18n.language === 'zh' ? 'zh-CN' : 'en-US') : ''}
                </div>
              </button>
            )
          })}
        </div>
      </div>

      {activeBranch && (() => {
        const s = getStyle(activeBranch)
        const dirLabel = dirLabels[getDir(activeBranch)] ?? getDir(activeBranch)
        return (
          <div className={`mt-4 rounded-xl border-2 p-5 space-y-3.5 ${s.bg} ${s.border}`}>
            <div className="flex items-center justify-between">
              <h3 className={`text-sm font-semibold ${s.text}`}>
                {activeBranch.hypothesis_title ?? t('branches.selectBranch')}
                <span className={`ml-2 text-[10px] font-normal px-1.5 py-0.5 rounded ${s.bg} border ${s.border}`}>
                  {dirLabel}
                </span>
              </h3>
              <button
                onClick={() => setActiveNode(null)}
                className="text-slate-600 hover:text-slate-400 text-lg leading-none"
                aria-label={t('common.close')}
              >&times;</button>
            </div>

            {activeBranch.hypothesis_description && (
              <p className="text-xs text-slate-400 leading-relaxed">
                {activeBranch.hypothesis_description}
              </p>
            )}

            {activeBranch.diff_summary && (
              <div>
                <div className="text-[10px] text-slate-500 mb-1">{t('branches.summary')}</div>
                <p className="text-xs text-slate-300 leading-relaxed">{activeBranch.diff_summary}</p>
              </div>
            )}
          </div>
        )
      })()}
    </div>
  )
}

export default function BranchPage() {
  const { t, i18n } = useTranslation()
  const navigate = useNavigate()
  const [runs, setRuns] = useState<PredictionRun[]>([])
  const [runsLoading, setRunsLoading] = useState(true)
  const [selectedRun, setSelectedRun] = useState<PredictionRun | null>(null)

  const [events, setEvents] = useState<AbstractIRGEvent[]>([])
  const [selectedEvent, setSelectedEvent] = useState<AbstractIRGEvent | null>(null)

  const [hypothesisType, setHypothesisType] = useState('actor_decision')
  const [hypothesisTitle, setHypothesisTitle] = useState('')
  const [hypothesisDesc, setHypothesisDesc] = useState('')
  const [affectedActors, setAffectedActors] = useState<string[]>([])
  const [expectedDirection, setExpectedDirection] = useState<DirectionType>('escalation')

  const [submitting, setSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState<string | null>(null)
  const [branchResult, setBranchResult] = useState<{
    branch_summary: string
    divergence_point: string
    key_differences: string[]
    new_steps: Array<{ title: string; actor: string; why: string }>
  } | null>(null)

  const [viewMode, setViewMode] = useState<'create' | 'mindmap'>('create')

  const [existingBranches, setExistingBranches] = useState<BranchRun[]>([])
  const [branchesLoading, setBranchesLoading] = useState(false)
  const [expandedBranch, setExpandedBranch] = useState<string | null>(null)

  useEffect(() => {
    Promise.all([pipelineApi.getRuns(), eventApi.list()])
      .then(([runsRes, eventsRes]) => {
        const items: PredictionRun[] = runsRes.data.items ?? runsRes.data ?? []
        setRuns(items)
        setEvents(eventsRes.data.items ?? eventsRes.data ?? [])
        if (items.length > 0) {
          setSelectedRun(items[0])
        }
      })
      .catch(() => {
        setRuns([])
        setEvents([])
      })
      .finally(() => setRunsLoading(false))
  }, [])

  useEffect(() => {
    if (!selectedRun) return
    const ev = events.find(e => e.event_id === selectedRun.event_id)
    setSelectedEvent(ev ?? null)
    setAffectedActors([])
    loadBranches(selectedRun.run_id)
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedRun, events])

  const loadBranches = async (runId: string) => {
    setBranchesLoading(true)
    try {
      const res = await branchApi.getForRun(runId)
      const items: BranchRun[] = res.data.branches ?? res.data.items ?? res.data ?? []
      setExistingBranches(items)
    } catch {
      setExistingBranches([])
    } finally {
      setBranchesLoading(false)
    }
  }

  const toggleActor = useCallback((actor: string) => {
    setAffectedActors(prev =>
      prev.includes(actor) ? prev.filter(a => a !== actor) : [...prev, actor]
    )
  }, [])

  const handleDeleteBranch = async (branchRunId: string) => {
    if (!confirm(t('branches.deleteConfirm'))) return
    try {
      await branchApi.delete(branchRunId)
      setExistingBranches(prev => prev.filter(b => b.branch_run_id !== branchRunId))
      if (expandedBranch === branchRunId) setExpandedBranch(null)
    } catch {
      alert(t('branches.deleteFailed'))
    }
  }

  const handleRetractBranch = async (branchRunId: string) => {
    try {
      await branchApi.retract(branchRunId)
      setExistingBranches(prev =>
        prev.map(b => b.branch_run_id === branchRunId ? { ...b, status: 'retracted' } : b)
      )
    } catch {
      alert(t('branches.retractFailed'))
    }
  }

  const isTitleValid = hypothesisTitle.trim().length >= 4
  const isDescValid = hypothesisDesc.trim().length >= 10
  const isFormValid = !!selectedRun && isTitleValid && isDescValid && affectedActors.length > 0

  const handleSubmit = async () => {
    if (!isFormValid) return
    setSubmitting(true)
    setSubmitError(null)
    setBranchResult(null)
    try {
      const res = await branchApi.create({
        base_run_id: selectedRun.run_id,
        hypothesis_type: hypothesisType,
        hypothesis_title: hypothesisTitle,
        hypothesis_description: hypothesisDesc,
        affected_actors: affectedActors,
        expected_direction: expectedDirection,
      })
      const data = res.data
      setBranchResult({
        branch_summary: data.summary ?? data.branch_summary ?? t('branches.createBranch'),
        divergence_point: data.divergence_point ?? '',
        key_differences: data.key_differences ?? [],
        new_steps: data.new_steps ?? data.scripts?.[0]?.steps?.map((s: { title: string; which_actor_acts_first: string; why_this_step_happens: string }) => ({
          title: s.title,
          actor: s.which_actor_acts_first,
          why: s.why_this_step_happens,
        })) ?? [],
      })
      await loadBranches(selectedRun.run_id)
    } catch (e) {
      setSubmitError(e instanceof Error ? e.message : String(t('common.error')))
    } finally {
      setSubmitting(false)
    }
  }

  const directionOptions: { value: DirectionType; label: string }[] = [
    { value: 'escalation', label: t('directions.escalation') },
    { value: 'stalemate', label: t('directions.stalemate') },
    { value: 'de_escalation', label: t('directions.de_escalation') },
  ]

  const hypothesisTypeLabel = (type: string) => {
    const key = `branches.hypothesisTypes.${type}` as const
    return t(key, type)
  }

  return (
    <div className="min-h-screen bg-surface-950 text-slate-100 flex flex-col">
      <div className="px-6 py-5 border-b border-slate-800 shrink-0">
        <h1 className="text-xl font-bold text-slate-100">{t('branches.title')}</h1>
        <p className="text-slate-500 text-xs mt-0.5">{t('branches.subtitle')}</p>
      </div>

      <div className="flex flex-1 min-h-0">
        <div className="w-72 border-r border-slate-800 flex flex-col min-h-0 shrink-0">
          <div className="px-4 py-3 border-b border-slate-800/50 text-xs font-semibold text-slate-500 uppercase tracking-widest shrink-0">
            {t('branches.baseSimulation')}
          </div>
          {runsLoading ? (
            <div className="flex-1 flex items-center justify-center">
              <LoadingSpinner size="sm" />
            </div>
          ) : runs.length === 0 ? (
            <div className="flex-1 flex items-center justify-center text-center px-4">
              <EmptyState
                title={t('branches.noRuns')}
                description={t('branches.noRunsHint')}
              />
            </div>
          ) : (
            <ul className="flex-1 overflow-y-auto divide-y divide-slate-800/40">
              {runs.map(run => (
                <li key={run.run_id}>
                  <button
                    onClick={() => setSelectedRun(run)}
                    className={`w-full text-left px-4 py-3.5 hover:bg-surface-900/50 transition-colors ${
                      selectedRun?.run_id === run.run_id ? 'bg-surface-900 border-l-2 border-blue-500' : ''
                    }`}
                  >
                    <div className="text-xs font-mono text-slate-400">{run.run_id?.slice(0, 12) ?? 'unknown'}...</div>
                    {run.created_at && (
                      <div className="text-[10px] text-slate-600 mt-0.5">
                        {new Date(run.created_at).toLocaleString(i18n.language === 'zh' ? 'zh-CN' : 'en-US')}
                      </div>
                    )}
                    <div className="text-[10px] text-slate-500 mt-1 line-clamp-2">{run.summary}</div>
                    <div className="flex items-center gap-2 mt-1.5">
                      <span className={`text-[10px] px-1.5 py-0.5 rounded ${
                        run.status === 'completed' ? 'bg-emerald-900/40 text-emerald-400' : 'bg-slate-800 text-slate-500'
                      }`}>
                        {run.status}
                      </span>
                      <span className="text-[10px] text-slate-600">{run.script_ids.length} {t('pipeline.result.scripts')}</span>
                    </div>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="flex-1 flex flex-col min-h-0 min-w-0">
          {selectedRun && (
            <div className="shrink-0 flex items-center gap-1 px-6 pt-4 pb-0 border-b border-slate-800">
              <button
                onClick={() => setViewMode('create')}
                className={`px-4 py-2 text-xs font-semibold rounded-t-lg transition-colors border-b-2 -mb-px ${
                  viewMode === 'create'
                    ? 'text-blue-400 border-blue-500 bg-surface-900/60'
                    : 'text-slate-500 border-transparent hover:text-slate-300'
                }`}
              >
                {t('branches.createTab')}
              </button>
              <button
                onClick={() => setViewMode('mindmap')}
                className={`px-4 py-2 text-xs font-semibold rounded-t-lg transition-colors border-b-2 -mb-px flex items-center gap-1.5 ${
                  viewMode === 'mindmap'
                    ? 'text-blue-400 border-blue-500 bg-surface-900/60'
                    : 'text-slate-500 border-transparent hover:text-slate-300'
                }`}
              >
                {t('branches.mindMap')}
                {existingBranches.length > 0 && (
                  <span className="text-[10px] bg-slate-700 text-slate-400 px-1.5 py-0.5 rounded-full">
                    {existingBranches.length}
                  </span>
                )}
              </button>
            </div>
          )}

          <div className="flex-1 overflow-y-auto p-6 space-y-6 min-w-0">
          {!selectedRun ? (
            <div className="flex items-center justify-center h-full">
              <EmptyState
                title={t('branches.noBaseRun')}
              />
            </div>
          ) : (
            <>
              {viewMode === 'mindmap' && (
                <BranchMindMap
                  baseRun={selectedRun}
                  branches={existingBranches}
                  selectedEvent={selectedEvent}
                />
              )}

              {viewMode === 'create' && (<>
              <div className="bg-surface-900 border border-slate-700 rounded-xl px-4 py-3">
                <div className="text-xs text-slate-500 mb-0.5">{t('branches.baseRun')}</div>
                <div className="text-sm font-mono text-slate-400">{selectedRun.run_id}</div>
                {selectedEvent && (
                  <div className="text-xs text-slate-500 mt-1">{t('branches.associatedEvent')}: {selectedEvent.event_title}</div>
                )}
              </div>

              <div className="bg-surface-900 border border-slate-700 rounded-xl p-5 space-y-4">
                <h2 className="text-sm font-semibold text-slate-300">{t('branches.inputHypothesis')}</h2>

                <div>
                  <label className="block text-xs text-slate-500 mb-1.5">{t('branches.hypothesisType')}</label>
                  <select
                    value={hypothesisType}
                    onChange={e => setHypothesisType(e.target.value)}
                    className="w-full bg-slate-800 border border-slate-700 text-slate-300 text-sm rounded-lg px-3 py-2 focus:outline-none focus:border-blue-600"
                  >
                    {(['actor_decision', 'external_shock', 'policy_change', 'information_revelation'] as const).map(tp => (
                      <option key={tp} value={tp}>{hypothesisTypeLabel(tp)}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs text-slate-500 mb-1.5">{t('branches.hypothesisTitle')}</label>
                  <input
                    type="text"
                    value={hypothesisTitle}
                    onChange={e => setHypothesisTitle(e.target.value)}
                    placeholder={t('branches.titlePlaceholder')}
                    className="w-full bg-slate-800 border border-slate-700 text-slate-300 text-sm rounded-lg px-3 py-2 focus:outline-none focus:border-blue-600 placeholder-slate-700"
                  />
                </div>

                <div>
                  <label className="block text-xs text-slate-500 mb-1.5">{t('branches.hypothesisDescription')}</label>
                  <textarea
                    value={hypothesisDesc}
                    onChange={e => setHypothesisDesc(e.target.value)}
                    placeholder={t('branches.descPlaceholder')}
                    rows={3}
                    className="w-full bg-slate-800 border border-slate-700 text-slate-300 text-sm rounded-lg px-3 py-2 focus:outline-none focus:border-blue-600 placeholder-slate-700 resize-none"
                  />
                </div>

                {selectedEvent && selectedEvent.key_actors.length > 0 && (
                  <div>
                    <label className="block text-xs text-slate-500 mb-1.5">{t('branches.affectedActors')}</label>
                    <div className="flex flex-wrap gap-2">
                      {selectedEvent.key_actors.map(actor => (
                        <button
                          key={actor}
                          onClick={() => toggleActor(actor)}
                          className={`text-xs px-2.5 py-1 rounded-lg border transition-colors ${
                            affectedActors.includes(actor)
                              ? 'bg-blue-600/30 text-blue-400 border-blue-600/60'
                              : 'bg-slate-800 text-slate-500 border-slate-700 hover:border-slate-500'
                          }`}
                        >
                          {affectedActors.includes(actor) ? '✓ ' : ''}{actor}
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                <div>
                  <label className="block text-xs text-slate-500 mb-1.5">{t('branches.expectedDirection')}</label>
                  <div className="flex gap-2">
                    {directionOptions.map(d => (
                      <button
                        key={d.value}
                        onClick={() => setExpectedDirection(d.value)}
                        className={`flex-1 py-2 text-xs rounded-lg border transition-colors ${
                          expectedDirection === d.value
                            ? d.value === 'escalation'
                              ? 'bg-red-600/30 text-red-400 border-red-700/60'
                              : d.value === 'stalemate'
                              ? 'bg-amber-600/30 text-amber-400 border-amber-700/60'
                              : 'bg-emerald-600/30 text-emerald-400 border-emerald-700/60'
                            : 'bg-slate-800 text-slate-500 border-slate-700 hover:border-slate-500'
                        }`}
                      >
                        {d.label}
                      </button>
                    ))}
                  </div>
                </div>

                <button
                  onClick={handleSubmit}
                  disabled={submitting || !isFormValid}
                  className="w-full py-2.5 text-sm font-medium rounded-lg bg-blue-600 hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
                >
                  {submitting && (
                    <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                    </svg>
                  )}
                  {submitting ? t('branches.generating') : t('branches.createBranch')}
                </button>
                {!hypothesisTitle.trim() && selectedRun && (
                  <p className="text-xs text-slate-600 text-center">{t('branches.fillTitle')}</p>
                )}
                {hypothesisTitle.trim() && !isTitleValid && (
                  <p className="text-xs text-amber-600 text-center">{t('branches.titleMinLength')}</p>
                )}
                {isTitleValid && !hypothesisDesc.trim() && (
                  <p className="text-xs text-slate-600 text-center">{t('branches.fillDesc')}</p>
                )}
                {hypothesisDesc.trim() && !isDescValid && (
                  <p className="text-xs text-amber-600 text-center">{t('branches.descMinLength')}</p>
                )}
                {isTitleValid && isDescValid && affectedActors.length === 0 && (
                  <p className="text-xs text-slate-600 text-center">{t('branches.selectActor')}</p>
                )}

                {submitError && (
                  <div className="text-xs text-red-400 bg-red-900/20 border border-red-700/40 rounded-lg px-3 py-2">
                    {submitError}
                  </div>
                )}
              </div>

              {branchResult && (
                <div className="bg-surface-900 border border-blue-700/40 rounded-xl p-5 space-y-4">
                  <h2 className="text-sm font-semibold text-blue-400">{t('branches.branchResult')}</h2>

                  <div>
                    <div className="text-xs text-slate-500 mb-1">{t('branches.summary')}</div>
                    <p className="text-sm text-slate-300 leading-relaxed">{branchResult.branch_summary}</p>
                  </div>

                  <div>
                    <div className="text-xs text-slate-500 mb-1">{t('branches.divergencePoint')}</div>
                    <p className="text-sm text-amber-400">{branchResult.divergence_point}</p>
                  </div>

                  {branchResult.key_differences.length > 0 && (
                    <div>
                      <div className="text-xs text-slate-500 mb-2">{t('branches.keyDifferences')}</div>
                      <ul className="space-y-1.5">
                        {branchResult.key_differences.map((d, i) => (
                          <li key={i} className="flex items-start gap-2 text-sm text-slate-400">
                            <span className="text-blue-500 shrink-0">&Delta;</span>{d}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {branchResult.new_steps.length > 0 && (
                    <div>
                      <div className="text-xs text-slate-500 mb-2">{t('branches.newSteps')}</div>
                      <div className="space-y-2">
                        {branchResult.new_steps.map((step, i) => (
                          <div key={i} className="bg-blue-900/15 border border-blue-800/30 rounded-lg px-3 py-2.5">
                            <div className="text-sm font-medium text-blue-300">{step.title}</div>
                            <div className="text-xs text-slate-500 mt-0.5">{t('scenarios.actor')}: {step.actor}</div>
                            <div className="text-xs text-slate-500 mt-0.5">{step.why}</div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  {selectedEvent && (
                    <div className="pt-3 border-t border-slate-700/50">
                      <button
                        onClick={() => navigate(`/scenarios?event_id=${selectedEvent.event_id}`)}
                        className="text-xs px-3 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 border border-slate-700 transition-colors"
                      >
                        {t('branches.viewFullScript')}
                      </button>
                    </div>
                  )}
                </div>
              )}

              <div>
                <div className="flex items-center justify-between mb-3">
                  <h2 className="text-sm font-semibold text-slate-400">{t('branches.existingBranches')}</h2>
                  <span className="text-xs text-slate-600">{existingBranches.length}</span>
                </div>
                {branchesLoading ? (
                  <div className="text-center py-6">
                    <LoadingSpinner size="sm" />
                  </div>
                ) : existingBranches.length === 0 ? (
                  <div className="text-center py-6 text-slate-700 text-xs">{t('branches.noBranchesYet')}</div>
                ) : (
                  <div className="space-y-2">
                    {existingBranches.map(branch => (
                      <div key={branch.branch_run_id} className={`bg-surface-900 border rounded-xl overflow-hidden ${branch.status === 'retracted' ? 'border-slate-800 opacity-60' : 'border-slate-700'}`}>
                        <div className="flex items-start">
                          <button
                            onClick={() => setExpandedBranch(expandedBranch === branch.branch_run_id ? null : branch.branch_run_id)}
                            className="flex-1 text-left px-4 py-3 hover:bg-slate-800/30 transition-colors min-w-0"
                          >
                            <div className="flex items-center gap-2">
                              <span className="text-xs font-mono text-slate-500">{branch.branch_run_id?.slice(0, 12) ?? 'unknown'}...</span>
                              {branch.created_at && (
                                <span className="text-[10px] text-slate-700">
                                  {new Date(branch.created_at).toLocaleDateString(i18n.language === 'zh' ? 'zh-CN' : 'en-US')}
                                </span>
                              )}
                              {branch.status === 'retracted' && (
                                <span className="text-[10px] text-amber-600 border border-amber-800 px-1 rounded">{t('branches.retracted')}</span>
                              )}
                            </div>
                            <div className="text-xs text-slate-400 mt-1 font-medium line-clamp-1">{branch.hypothesis_title}</div>
                            <div className="text-xs text-slate-600 mt-0.5 line-clamp-1">{branch.diff_summary}</div>
                          </button>
                          <div className="flex items-center gap-1 px-2 pt-2 shrink-0">
                            {branch.status !== 'retracted' && (
                              <button
                                onClick={() => handleRetractBranch(branch.branch_run_id)}
                                title={t('branches.retract')}
                                className="p-1.5 rounded text-slate-600 hover:text-amber-400 hover:bg-amber-900/20 transition-colors"
                                aria-label={t('branches.retract')}
                              >
                                <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 14l-4-4 4-4M5 10h11a4 4 0 010 8h-1" />
                                </svg>
                              </button>
                            )}
                            <button
                              onClick={() => handleDeleteBranch(branch.branch_run_id)}
                              title={t('branches.delete')}
                              className="p-1.5 rounded text-slate-600 hover:text-red-400 hover:bg-red-900/20 transition-colors"
                              aria-label={t('branches.delete')}
                            >
                              <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                                <path strokeLinecap="round" strokeLinejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                              </svg>
                            </button>
                            <span className="text-slate-700 text-xs ml-1">{expandedBranch === branch.branch_run_id ? '▲' : '▼'}</span>
                          </div>
                        </div>
                        {expandedBranch === branch.branch_run_id && (
                          <div className="border-t border-slate-700/50 px-4 py-3">
                            <p className="text-xs text-slate-500 leading-relaxed">{branch.diff_summary}</p>
                            <div className="flex items-center gap-3 mt-2">
                              <span className="text-[10px] text-slate-600">{t('branches.type')}: {hypothesisTypeLabel(branch.hypothesis_type)}</span>
                              <span className="text-[10px] text-slate-600">{t('branches.direction')}: {branch.expected_direction}</span>
                              <span className="text-[10px] text-slate-600">{t('branches.status')}: {branch.status}</span>
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </>)}
            </>
          )}
        </div>
        </div>
      </div>
    </div>
  )
}
