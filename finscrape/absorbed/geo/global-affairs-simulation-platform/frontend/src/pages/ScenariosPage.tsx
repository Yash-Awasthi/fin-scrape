import { useEffect, useState, useCallback } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { scenarioApi, pipelineApi } from '../services/api'
import type { ScenarioScript, ScenarioStep, DirectionType } from '../types'
import { DIRECTION_CONFIG } from '../types'
import { useAppStore } from '../store'
import LoadingSpinner from '../components/LoadingSpinner'
import ErrorState from '../components/ErrorState'
import EmptyState from '../components/EmptyState'
import useFocusTrap from '../hooks/useFocusTrap'

const CONFIDENCE_COLORS: Record<string, string> = {
  high: 'text-emerald-400 bg-emerald-900/30 border-emerald-700/40',
  medium: 'text-amber-400 bg-amber-900/30 border-amber-700/40',
  low: 'text-red-400 bg-red-900/30 border-red-700/40',
}

interface StepDrawerProps {
  step: ScenarioStep
  onClose: () => void
}

function StepDrawer({ step, onClose }: StepDrawerProps) {
  const { t } = useTranslation()
  const focusTrapRef = useFocusTrap({ isActive: true, onClose })

  return (
    <div className="fixed inset-0 z-50 flex" role="dialog" aria-modal="true" aria-label={t('scenarios.step') + ' ' + step.step_number}>
      <div className="flex-1 bg-black/50" onClick={onClose} aria-hidden="true" />
      <div ref={focusTrapRef as React.RefObject<HTMLDivElement>} className="w-full md:w-[420px] bg-surface-900 border-l border-slate-700 flex flex-col overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-700 flex items-center justify-between shrink-0">
          <div>
            <div className="text-xs text-slate-500 mb-0.5">{t('scenarios.step')} {step.step_number}</div>
            <h3 className="text-base font-semibold text-slate-100">{step.title}</h3>
          </div>
          <button onClick={onClose} className="text-slate-600 hover:text-slate-300 text-xl leading-none" aria-label={t('common.close')}>&times;</button>
        </div>
        <div className="flex-1 overflow-y-auto p-5 space-y-5">
          <div>
            <div className="text-xs font-semibold text-slate-500 uppercase tracking-widest mb-1.5">{t('scenarios.actor')}</div>
            <span className="text-sm font-medium text-blue-400">{step.which_actor_acts_first}</span>
          </div>
          <div>
            <div className="text-xs font-semibold text-slate-500 uppercase tracking-widest mb-1.5">{t('scenarios.reason')}</div>
            <p className="text-sm text-slate-400 leading-relaxed">{step.why_this_step_happens}</p>
          </div>
          {Object.keys(step.how_other_actors_react).length > 0 && (
            <div>
              <div className="text-xs font-semibold text-slate-500 uppercase tracking-widest mb-2">{t('scenarios.reactions')}</div>
              <div className="space-y-2">
                {Object.entries(step.how_other_actors_react).map(([actor, reaction]) => (
                  <div key={actor} className="bg-slate-800/50 rounded-lg px-3 py-2">
                    <div className="text-xs text-slate-500 mb-0.5">{actor}</div>
                    <div className="text-sm text-slate-400">{reaction}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
          {step.supporting_evidence.length > 0 && (
            <div>
              <div className="text-xs font-semibold text-slate-500 uppercase tracking-widest mb-1.5">{t('scenarios.supportingEvidence')}</div>
              <ul className="space-y-1">
                {step.supporting_evidence.map((e, i) => (
                  <li key={i} className="text-xs text-slate-500 flex items-start gap-1.5">
                    <span className="text-emerald-600 shrink-0">&check;</span>{e}
                  </li>
                ))}
              </ul>
            </div>
          )}
          {step.counter_evidence.length > 0 && (
            <div>
              <div className="text-xs font-semibold text-slate-500 uppercase tracking-widest mb-1.5">{t('scenarios.counterEvidence')}</div>
              <ul className="space-y-1">
                {step.counter_evidence.map((e, i) => (
                  <li key={i} className="text-xs text-slate-500 flex items-start gap-1.5">
                    <span className="text-red-500 shrink-0">&cross;</span>{e}
                  </li>
                ))}
              </ul>
            </div>
          )}
          {step.uncertainty && (
            <div>
              <div className="text-xs font-semibold text-slate-500 uppercase tracking-widest mb-1.5">{t('scenarios.uncertainty')}</div>
              <p className="text-sm text-amber-500/80 italic">{step.uncertainty}</p>
            </div>
          )}
          {step.impact_on_next_step && (
            <div>
              <div className="text-xs font-semibold text-slate-500 uppercase tracking-widest mb-1.5">{t('scenarios.impactOnNext')}</div>
              <p className="text-sm text-slate-400 leading-relaxed">{step.impact_on_next_step}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

interface ScriptCardProps {
  script: ScenarioScript
  direction: DirectionType
}

function ScriptCard({ script, direction }: ScriptCardProps) {
  const { t } = useTranslation()
  const [expanded, setExpanded] = useState(false)
  const [selectedStep, setSelectedStep] = useState<ScenarioStep | null>(null)
  const cfg = DIRECTION_CONFIG[direction]
  const pLow = script.probability_low !== null ? Math.round(script.probability_low * 100) : null
  const pHigh = script.probability_high !== null ? Math.round(script.probability_high * 100) : null
  const pCentral = script.probability_central !== null ? Math.round(script.probability_central * 100) : null

  const confidenceLabel = script.confidence_level
    ? t(`scenarios.confidence.${script.confidence_level}`, script.confidence_level)
    : null

  return (
    <>
      {selectedStep && (
        <StepDrawer step={selectedStep} onClose={() => setSelectedStep(null)} />
      )}
      <div className={`bg-surface-900 border ${cfg.border} rounded-xl overflow-hidden`}>
        <div className="px-4 py-3">
          <div className="flex items-start justify-between gap-2">
            <h4 className="text-sm font-medium text-slate-200 leading-snug flex-1">{script.script_title}</h4>
            {script.confidence_level && (
              <span className={`text-[10px] px-1.5 py-0.5 rounded border shrink-0 ${CONFIDENCE_COLORS[script.confidence_level] ?? 'text-slate-500 bg-slate-800 border-slate-700'}`}>
                {confidenceLabel}
              </span>
            )}
          </div>

          {pLow !== null && pHigh !== null && (
            <div className="mt-3">
              <div className="flex items-center justify-between text-[10px] text-slate-600 mb-1">
                <span>{pLow}%</span>
                {pCentral !== null && <span className={`font-semibold ${cfg.color}`}>{pCentral}%</span>}
                <span>{pHigh}%</span>
              </div>
              <div className="h-1.5 bg-slate-800 rounded-full overflow-hidden relative">
                <div
                  className="absolute h-full rounded-full opacity-30"
                  style={{
                    left: `${pLow}%`,
                    width: `${pHigh - pLow}%`,
                    backgroundColor: cfg.hex,
                  }}
                />
                {pCentral !== null && (
                  <div
                    className={`absolute w-1.5 h-1.5 rounded-full top-0 -translate-x-1/2 ${cfg.dot}`}
                    style={{ left: `${pCentral}%` }}
                  />
                )}
              </div>
            </div>
          )}

          {script.trigger_conditions.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-2">
              {script.trigger_conditions.slice(0, 2).map((tc, i) => (
                <span key={i} className="text-[10px] bg-slate-800 text-slate-500 px-1.5 py-0.5 rounded">{t('scenarios.triggerConditions')}: {tc}</span>
              ))}
            </div>
          )}
          {script.invalidation_conditions.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-1">
              {script.invalidation_conditions.slice(0, 1).map((ic, i) => (
                <span key={i} className="text-[10px] bg-slate-800/50 text-slate-600 px-1.5 py-0.5 rounded">{t('scenarios.invalidationConditions')}: {ic}</span>
              ))}
            </div>
          )}

          <button
            onClick={() => setExpanded(v => !v)}
            className={`mt-3 text-xs flex items-center gap-1 ${cfg.color} hover:opacity-80`}
          >
            {expanded ? t('scenarios.collapseSteps') : t('scenarios.expandSteps', { count: script.steps?.length ?? 0 })}
          </button>
        </div>

        {expanded && script.steps && script.steps.length > 0 && (
          <div className="border-t border-slate-700/50 px-4 py-3 space-y-2">
            {script.steps.map((step, idx) => (
              <div key={step.step_id} className="flex items-start gap-3">
                <div className="flex flex-col items-center shrink-0">
                  <div className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold ${cfg.bg} ${cfg.color} border ${cfg.border}`}>
                    {step.step_number}
                  </div>
                  {idx < (script.steps?.length ?? 0) - 1 && (
                    <div className="w-px h-4 bg-slate-700 mt-1" />
                  )}
                </div>
                <button
                  onClick={() => setSelectedStep(step)}
                  className="flex-1 text-left bg-slate-800/40 hover:bg-slate-800 rounded-lg px-3 py-2 transition-colors group"
                >
                  <div className="text-xs font-medium text-slate-300 group-hover:text-slate-100">{step.title}</div>
                  <div className="text-[10px] text-slate-600 mt-0.5">{step.which_actor_acts_first} &middot; {t('scenarios.viewStepDetail')}</div>
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </>
  )
}

export default function ScenariosPage() {
  const { t, i18n } = useTranslation()
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const initialEventId = searchParams.get('event_id') ?? ''

  const storeEvents = useAppStore((s) => s.events)
  const storeEventsLoading = useAppStore((s) => s.eventsLoading)
  const storeSelectedId = useAppStore((s) => s.selectedEventId)
  const setStoreSelectedEvent = useAppStore((s) => s.setSelectedEvent)
  const fetchEvents = useAppStore((s) => s.fetchEvents)

  const [selectedEventId, setSelectedEventId] = useState(
    initialEventId || storeSelectedId || ''
  )

  const [runs, setRuns] = useState<Array<{ run_id: string; created_at: string | null; summary: string }>>([])
  const [selectedRunId, setSelectedRunId] = useState<string>('')

  const [scripts, setScripts] = useState<ScenarioScript[]>([])
  const [scriptsLoading, setScriptsLoading] = useState(false)
  const [scriptsError, setScriptsError] = useState<string | null>(null)

  useEffect(() => {
    if (storeEvents.length === 0 && !storeEventsLoading) {
      fetchEvents()
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    if (!selectedEventId && storeEvents.length > 0) {
      const first = initialEventId
        ? (storeEvents.find(e => e.event_id === initialEventId)?.event_id ?? storeEvents[0].event_id)
        : storeEvents[0].event_id
      setSelectedEventId(first)
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [storeEvents])

  const handleEventChange = useCallback((id: string) => {
    setSelectedEventId(id)
    setStoreSelectedEvent(id)
    setSearchParams({ event_id: id }, { replace: true })
  }, [setStoreSelectedEvent, setSearchParams])

  useEffect(() => {
    if (!selectedEventId) return
    pipelineApi.getRuns(selectedEventId)
      .then(res => {
        const items = res.data.items ?? res.data ?? []
        setRuns(items)
        setSelectedRunId('')
      })
      .catch(() => setRuns([]))
  }, [selectedEventId])

  useEffect(() => {
    if (!selectedEventId) return
    setScriptsLoading(true)
    setScriptsError(null)
    scenarioApi.getForEvent(selectedEventId, selectedRunId || undefined)
      .then(res => setScripts(res.data.scripts ?? []))
      .catch(e => setScriptsError(e instanceof Error ? e.message : String(t('common.error'))))
      .finally(() => setScriptsLoading(false))
  }, [selectedEventId, selectedRunId, t])

  const directions: DirectionType[] = ['escalation', 'stalemate', 'de_escalation']

  const getScriptsByDirection = (dir: DirectionType) =>
    scripts.filter(s => s.direction_type === dir)

  const dirLabels: Record<DirectionType, string> = {
    escalation: t('scenarios.escalation'),
    stalemate: t('scenarios.stalemate'),
    de_escalation: t('scenarios.de_escalation'),
  }

  return (
    <div className="min-h-screen bg-surface-950 text-slate-100 flex flex-col">
      <div className="px-6 py-5 border-b border-slate-800 shrink-0">
        <div className="flex items-center flex-wrap gap-4">
          <div className="flex-1">
            <h1 className="text-xl font-bold text-slate-100">{t('scenarios.title')}</h1>
            <p className="text-slate-500 text-xs mt-0.5">{t('scenarios.subtitle')}</p>
          </div>
          <div className="flex items-center gap-3 flex-wrap">
            <select
              value={selectedEventId}
              onChange={e => handleEventChange(e.target.value)}
              disabled={storeEventsLoading}
              className="bg-surface-900 border border-slate-700 text-slate-300 text-sm rounded-lg px-3 py-2 min-w-[200px] focus:outline-none focus:border-blue-600"
              aria-label={t('events.title')}
            >
              {storeEventsLoading ? <option>{t('common.loading')}</option> : storeEvents.length === 0 ? <option value="">{t('events.noData')}</option> : (
                storeEvents.map(ev => <option key={ev.event_id} value={ev.event_id}>{ev.event_title}</option>)
              )}
            </select>
            <button
              onClick={() => navigate('/branches')}
              className="text-xs px-3 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 border border-slate-700 transition-colors"
            >
              {t('scenarios.createBranch')}
            </button>
            {runs.length > 0 && (
              <select
                value={selectedRunId}
                onChange={e => setSelectedRunId(e.target.value)}
                className="bg-surface-900 border border-slate-700 text-slate-300 text-sm rounded-lg px-3 py-2 focus:outline-none focus:border-blue-600"
                aria-label={t('scenarios.allRuns')}
              >
                <option value="">{t('scenarios.allRuns')}</option>
                {runs.map(r => (
                  <option key={r.run_id} value={r.run_id}>
                    {r.created_at ? new Date(r.created_at).toLocaleDateString(i18n.language === 'zh' ? 'zh-CN' : 'en-US') : r.run_id.slice(0, 8)}
                    {r.summary ? ` - ${r.summary.slice(0, 30)}${r.summary.length > 30 ? '...' : ''}` : ''}
                  </option>
                ))}
              </select>
            )}
          </div>
        </div>
      </div>

      {scriptsLoading && (
        <div className="flex-1 flex items-center justify-center">
          <LoadingSpinner message={t('scenarios.loading')} />
        </div>
      )}

      {scriptsError && (
        <div className="p-6">
          <ErrorState
            title={t('common.error')}
            message={scriptsError}
            onRetry={() => { setScriptsLoading(true); setScriptsError(null); }}
          />
        </div>
      )}

      {!scriptsLoading && !scriptsError && scripts.length === 0 && (
        <div className="flex-1 flex items-center justify-center">
          <EmptyState
            title={t('scenarios.noScripts')}
            description={t('scenarios.noScriptsHint')}
          />
        </div>
      )}

      {!scriptsLoading && !scriptsError && scripts.length > 0 && (
        <div className="flex-1 grid grid-cols-1 md:grid-cols-3 divide-x divide-slate-800 min-h-0 overflow-hidden">
          {directions.map(dir => {
            const dirScripts = getScriptsByDirection(dir)
            const cfg = DIRECTION_CONFIG[dir]
            return (
              <div key={dir} className="flex flex-col min-h-0">
                <div className={`px-4 py-3 border-b border-slate-800 shrink-0 ${cfg.bg}`}>
                  <div className="flex items-center gap-2">
                    <div className={`w-2.5 h-2.5 rounded-full ${cfg.dot}`} />
                    <span className={`text-sm font-semibold ${cfg.color}`}>{dirLabels[dir]}</span>
                    <span className="text-xs text-slate-600 ml-auto">{t('scenarios.scriptCount', { count: dirScripts.length })}</span>
                  </div>
                </div>
                <div className="flex-1 overflow-y-auto p-3 space-y-3">
                  {dirScripts.length === 0 ? (
                    <div className="text-center py-8 text-slate-700 text-xs">{t('scenarios.noScriptsInDirection')}</div>
                  ) : (
                    dirScripts.map(script => (
                      <ScriptCard key={script.script_id} script={script} direction={dir} />
                    ))
                  )}
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
