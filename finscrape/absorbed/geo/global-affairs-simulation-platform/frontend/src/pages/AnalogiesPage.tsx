/**
 * AnalogiesPage — Historical Analogy Engine
 * Left: historical case library (filterable + CRUD)
 * Right: current event → analogy analysis (similarity, structural comparison, historical base rates)
 */
import { useEffect, useState, useCallback } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import {
  BookOpen, Search, RefreshCw, ChevronDown, ChevronUp,
  TrendingUp, TrendingDown, Minus, AlertTriangle,
  CheckCircle, XCircle, Target, Zap, Plus, Pencil, Trash2
} from 'lucide-react'
import { analogyApi, eventApi, getErrorUserMessage } from '../services/api'
import type {
  AbstractIRGEvent, AnalogyResult, MatchedCase, HistoricalCase
} from '../types'
import { EVENT_TYPE_LABELS, DIRECTION_CONFIG as SHARED_DIR } from '../types'
import { toast } from '../store/toast'
import LoadingSpinner from '../components/LoadingSpinner'
import useFocusTrap from '../hooks/useFocusTrap'

const DIRECTION_CONFIG = {
  escalation:   { ...SHARED_DIR.escalation,   Icon: TrendingUp },
  stalemate:    { ...SHARED_DIR.stalemate,    Icon: Minus },
  de_escalation:{ ...SHARED_DIR.de_escalation, Icon: TrendingDown },
}

function similarityColor(score: number) {
  if (score >= 0.80) return 'text-emerald-400'
  if (score >= 0.65) return 'text-brand-400'
  if (score >= 0.50) return 'text-amber-400'
  return 'text-slate-500'
}

function similarityLabel(score: number, t: (key: string) => string) {
  if (score >= 0.80) return t('analogies.similarityLabels.high')
  if (score >= 0.65) return t('analogies.similarityLabels.strong')
  if (score >= 0.50) return t('analogies.similarityLabels.partial')
  return t('analogies.similarityLabels.weak')
}

const REGION_OPTIONS = [
  'East Asia', 'Middle East', 'Europe', 'Americas', 'South Asia',
  'Africa', 'Central Asia', 'Southeast Asia', 'Global',
]

function ProbBar({ escalation, stalemate, de_escalation }: {
  escalation: number; stalemate: number; de_escalation: number
}) {
  const { t } = useTranslation()
  const total = (escalation + stalemate + de_escalation) || 1
  const ePct = Math.round((escalation / total) * 100)
  const sPct = Math.round((stalemate / total) * 100)
  const dPct = 100 - ePct - sPct
  return (
    <div className="space-y-1">
      <div className="flex h-2 rounded-full overflow-hidden gap-0.5">
        <div className="bg-red-500/70" style={{ width: `${ePct}%` }} />
        <div className="bg-amber-500/70" style={{ width: `${sPct}%` }} />
        <div className="bg-emerald-500/70" style={{ width: `${dPct}%` }} />
      </div>
      <div className="flex justify-between text-[10px] text-slate-500">
        <span className="text-red-400">{ePct}% {t('directions.escalation')}</span>
        <span className="text-amber-400">{sPct}% {t('directions.stalemate')}</span>
        <span className="text-emerald-400">{dPct}% {t('directions.de_escalation')}</span>
      </div>
    </div>
  )
}

function MatchedCaseCard({ mc, rank }: { mc: MatchedCase; rank: number }) {
  const { t } = useTranslation()
  const [open, setOpen] = useState(rank === 0)
  const dir = mc.outcome_direction as keyof typeof DIRECTION_CONFIG
  const dirCfg = DIRECTION_CONFIG[dir] || DIRECTION_CONFIG.stalemate
  const DirIcon = dirCfg.Icon

  return (
    <div className="bg-surface-900 border border-slate-700/50 rounded-xl overflow-hidden">
      <button
        onClick={() => setOpen(v => !v)}
        className="w-full flex items-start gap-3 p-4 hover:bg-surface-800/50 transition-colors text-left"
      >
        <div className="flex-shrink-0 w-7 h-7 rounded-full bg-brand-500/20 flex items-center justify-center text-brand-400 text-xs font-bold">
          #{rank + 1}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-medium text-white text-sm">{mc.title}</span>
            <span className="text-xs text-slate-500">{mc.year}</span>
            <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-700/50 text-slate-400">
              {EVENT_TYPE_LABELS[mc.event_type as keyof typeof EVENT_TYPE_LABELS] || mc.event_type}
            </span>
            <span className={`text-[10px] px-1.5 py-0.5 rounded ${dirCfg.bg} ${dirCfg.color} flex items-center gap-0.5`}>
              <DirIcon size={9} />{t('directions.' + dir)}
            </span>
          </div>
          <div className="mt-1 flex items-center gap-3">
            <span className={`text-lg font-bold ${similarityColor(mc.similarity_score)}`}>
              {Math.round(mc.similarity_score * 100)}%
            </span>
            <span className={`text-xs ${similarityColor(mc.similarity_score)}`}>
              {similarityLabel(mc.similarity_score, t)}
            </span>
            <span className="text-xs text-slate-600">{mc.region}</span>
          </div>
        </div>
        {open ? <ChevronUp size={14} className="text-slate-500 flex-shrink-0 mt-1" />
               : <ChevronDown size={14} className="text-slate-500 flex-shrink-0 mt-1" />}
      </button>

      {open && (
        <div className="px-4 pb-4 space-y-4 border-t border-slate-700/50 pt-4">
          <div>
            <div className="text-xs text-slate-500 mb-2 uppercase tracking-wide">{t('analogies.historicalOutcomeDist')}</div>
            <ProbBar
              escalation={mc.historical_base_rates?.escalation ?? 0}
              stalemate={mc.historical_base_rates?.stalemate ?? 0}
              de_escalation={mc.historical_base_rates?.de_escalation ?? 0}
            />
          </div>
          {mc.structural_similarities?.length > 0 && (
            <div>
              <div className="text-xs text-slate-500 mb-1.5 uppercase tracking-wide flex items-center gap-1">
                <CheckCircle size={10} className="text-emerald-500" />{t('analogies.structuralSimilarities')}
              </div>
              <ul className="space-y-1">
                {mc.structural_similarities.map((s, i) => (
                  <li key={i} className="flex gap-2 text-xs text-slate-300">
                    <span className="text-emerald-500 mt-0.5 flex-shrink-0">✓</span><span>{s}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
          {mc.key_differences?.length > 0 && (
            <div>
              <div className="text-xs text-slate-500 mb-1.5 uppercase tracking-wide flex items-center gap-1">
                <XCircle size={10} className="text-red-500" />{t('analogies.keyDifferences')}
              </div>
              <ul className="space-y-1">
                {mc.key_differences.map((d, i) => (
                  <li key={i} className="flex gap-2 text-xs text-slate-400">
                    <span className="text-red-500 mt-0.5 flex-shrink-0">✓</span><span>{d}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
          {mc.probability_adjustment && (
            <div className="bg-brand-500/5 border border-brand-500/20 rounded-lg p-3">
              <div className="text-xs text-brand-400 mb-1 flex items-center gap-1">
                <Target size={10} />{t('analogies.probAdjustment')}
              </div>
              {typeof mc.probability_adjustment === 'string' ? (
                <p className="text-xs text-slate-300">{mc.probability_adjustment}</p>
              ) : (
                <ul className="space-y-0.5">
                  {Object.entries(mc.probability_adjustment as Record<string, unknown>).map(([k, v]) => (
                    <li key={k} className="text-xs text-slate-300">
                      <span className="text-slate-500">{k.replace(/_/g, ' ')}→</span>{String(v)}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )}
          {mc.key_lessons?.length > 0 && (
            <div>
              <div className="text-xs text-slate-500 mb-1.5 uppercase tracking-wide flex items-center gap-1">
                <Zap size={10} className="text-amber-500" />{t('analogies.historicalInsights')}
              </div>
              <ul className="space-y-1">
                {mc.key_lessons.map((l, i) => (
                  <li key={i} className="flex gap-2 text-xs text-slate-300">
                    <span className="text-amber-500 mt-0.5 flex-shrink-0">✓</span><span>{l}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
          {mc.tags?.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {mc.tags.map(t => (
                <span key={t} className="text-[10px] px-1.5 py-0.5 rounded bg-slate-700/50 text-slate-500">{t}</span>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function HistoricalCaseCard({ c, onClick, onEdit, onDelete }: {
  c: HistoricalCase; onClick: () => void; onEdit: (e: React.MouseEvent) => void; onDelete: (e: React.MouseEvent) => void
}) {
  const { t } = useTranslation()
  const dir = c.actual_outcome_direction as keyof typeof DIRECTION_CONFIG
  const dirCfg = DIRECTION_CONFIG[dir] || DIRECTION_CONFIG.stalemate
  const DirIcon = dirCfg.Icon
  return (
    <div className="relative group bg-surface-900 border border-slate-700/50 rounded-xl p-4 hover:border-brand-500/40 hover:bg-surface-800/60 transition-all">
      <button onClick={onClick} className="w-full text-left">
        <div className="flex items-start gap-3">
          <div className="flex-shrink-0 mt-0.5">
            <BookOpen size={14} className="text-brand-500" />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="font-medium text-white text-sm leading-tight">{c.title}</span>
              <span className="text-xs text-slate-500">{c.year}</span>
            </div>
            <div className="mt-1 flex items-center gap-2 flex-wrap">
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-700/50 text-slate-400">
                {EVENT_TYPE_LABELS[c.event_type as keyof typeof EVENT_TYPE_LABELS] || c.event_type}
              </span>
              <span className="text-[10px] text-slate-500">{c.region}</span>
              <span className={`text-[10px] px-1.5 py-0.5 rounded ${dirCfg.bg} ${dirCfg.color} flex items-center gap-0.5`}>
                <DirIcon size={9} />{t('directions.' + (dir || 'stalemate'))}
              </span>
            </div>
            <p className="mt-2 text-xs text-slate-500 line-clamp-2">{c.outcome_summary}</p>
          </div>
        </div>
      </button>
      <div className="absolute top-2 right-2 hidden group-hover:flex items-center gap-1">
        <button onClick={onEdit} className="p-1 rounded bg-surface-800 hover:bg-brand-500/20 text-slate-400 hover:text-brand-400 transition-colors" title={t('common.edit')}>
          <Pencil size={12} />
        </button>
        <button onClick={onDelete} className="p-1 rounded bg-surface-800 hover:bg-red-500/20 text-slate-400 hover:text-red-400 transition-colors" title={t('common.delete')}>
          <Trash2 size={12} />
        </button>
      </div>
    </div>
  )
}

function CaseDetailModal({ c, onClose, onEdit, onDelete }: {
  c: HistoricalCase; onClose: () => void; onEdit: () => void; onDelete: () => void
}) {
  const { t } = useTranslation()
  const dir = c.actual_outcome_direction as keyof typeof DIRECTION_CONFIG
  const dirCfg = DIRECTION_CONFIG[dir] || DIRECTION_CONFIG.stalemate
  const DirIcon = dirCfg.Icon
  const focusTrapRef = useFocusTrap({ isActive: true, onClose })
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4" role="dialog" aria-modal="true">
      <div ref={focusTrapRef as React.RefObject<HTMLDivElement>} className="bg-surface-900 border border-slate-700 rounded-2xl max-w-2xl w-full max-h-[85vh] overflow-y-auto">
        <div className="sticky top-0 bg-surface-900 border-b border-slate-700/50 p-5 flex items-start justify-between z-10">
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <h2 className="font-semibold text-white">{c.title}</h2>
              <span className={`text-[10px] px-1.5 py-0.5 rounded ${dirCfg.bg} ${dirCfg.color} flex items-center gap-0.5`}>
                <DirIcon size={9} />{t('directions.' + (dir || 'stalemate'))}
              </span>
            </div>
            <div className="mt-1 text-xs text-slate-500">{c.title_en} · {c.year} · {c.region} · {c.duration_days} {t('analogies.days')}</div>
          </div>
          <div className="flex items-center gap-2 ml-4">
            <button onClick={onEdit} className="p-1.5 rounded-lg bg-surface-800 hover:bg-brand-500/20 text-slate-400 hover:text-brand-400 transition-colors" title={t('common.edit')}>
              <Pencil size={14} />
            </button>
            <button onClick={onDelete} className="p-1.5 rounded-lg bg-surface-800 hover:bg-red-500/20 text-slate-400 hover:text-red-400 transition-colors" title={t('common.delete')}>
              <Trash2 size={14} />
            </button>
            <button onClick={onClose} className="text-slate-500 hover:text-white text-xl leading-none ml-2">&times;</button>
          </div>
        </div>
        <div className="p-5 space-y-5">
          <div>
            <div className="text-xs text-slate-500 mb-2 uppercase tracking-wide">{t('analogies.historicalOutcomeDist')}</div>
            <ProbBar
              escalation={c.probability_realized?.escalation ?? 0}
              stalemate={c.probability_realized?.stalemate ?? 0}
              de_escalation={c.probability_realized?.de_escalation ?? 0}
            />
          </div>
          {c.primary_issue && (
            <div>
              <div className="text-xs text-slate-500 mb-1">{t('analogies.primaryIssue')}</div>
              <p className="text-sm text-slate-300">{c.primary_issue}</p>
            </div>
          )}
          {c.key_triggers?.length > 0 && (
            <div>
              <div className="text-xs text-slate-500 mb-1.5 uppercase tracking-wide">{t('analogies.keyTriggers')}</div>
              <ul className="space-y-1">
                {c.key_triggers.map((k, i) => (
                  <li key={i} className="flex gap-2 text-xs text-slate-300">
                    <span className="text-amber-500 mt-0.5 flex-shrink-0">✓</span><span>{k}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
          {c.escalation_path?.length > 0 && (
            <div>
              <div className="text-xs text-slate-500 mb-1">{t('analogies.escalationPath')}</div>
              <div className="flex flex-wrap gap-1">
                {c.escalation_path.map((s, i) => (
                  <span key={i} className="text-xs text-slate-400">{i > 0 && <span className="text-slate-600 mx-1">✓</span>}{s}</span>
                ))}
              </div>
            </div>
          )}
          {c.resolution && (
            <div>
              <div className="text-xs text-slate-500 mb-1">{t('analogies.resolution')}</div>
              <p className="text-xs text-slate-400">{c.resolution}</p>
            </div>
          )}
          {c.key_lessons?.length > 0 && (
            <div>
              <div className="text-xs text-slate-500 mb-1.5 uppercase tracking-wide flex items-center gap-1">
                <Zap size={10} className="text-amber-500" />{t('analogies.keyLessons')}
              </div>
              <ul className="space-y-1">
                {c.key_lessons.map((l, i) => (
                  <li key={i} className="flex gap-2 text-xs text-slate-300">
                    <span className="text-brand-400 mt-0.5 flex-shrink-0">✓</span><span>{l}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
          {c.analogous_features?.length > 0 && (
            <div>
              <div className="text-xs text-slate-500 mb-1.5 uppercase tracking-wide">{t('analogies.analogousFeatures')}</div>
              <div className="flex flex-wrap gap-1.5">
                {c.analogous_features.map((f, i) => (
                  <span key={i} className="text-[10px] px-2 py-0.5 rounded-full bg-brand-500/10 text-brand-400 border border-brand-500/20">{f}</span>
                ))}
              </div>
            </div>
          )}
          {c.prediction_accuracy_notes && (
            <div className="bg-surface-800 rounded-lg p-3">
              <div className="text-xs text-slate-500 mb-1">{t('analogies.predictionAccuracyNotes')}</div>
              <p className="text-xs text-slate-400">{c.prediction_accuracy_notes}</p>
            </div>
          )}
          {c.tags?.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {c.tags.map(k => (
                <span key={k} className="text-[10px] px-1.5 py-0.5 rounded bg-slate-700/50 text-slate-500">#{k}</span>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

const EMPTY_CASE: Partial<HistoricalCase> = {
  title: '', title_en: '', year: null, duration_days: null,
  event_type: '', region: '', crisis_stage_peak: '',
  key_actors: [], actor_roles: {}, primary_issue: '',
  strategic_dimensions: [], key_triggers: [], key_constraints: [],
  escalation_path: [], resolution: '', resolution_type: '',
  outcome_summary: '', key_lessons: [], analogous_features: [],
  probability_realized: { escalation: 0, stalemate: 0, de_escalation: 0 },
  actual_outcome_direction: '', prediction_accuracy_notes: '', tags: [],
}

function CaseFormModal({ initial, onSave, onClose }: {
  initial: Partial<HistoricalCase>
  onSave: (data: Partial<HistoricalCase>) => void
  onClose: () => void
}) {
  const { t } = useTranslation()
  const focusTrapRef = useFocusTrap({ isActive: true, onClose })
  const [form, setForm] = useState<Partial<HistoricalCase>>({ ...EMPTY_CASE, ...initial })

  const setField = <K extends keyof HistoricalCase>(key: K, val: HistoricalCase[K]) => {
    setForm(prev => ({ ...prev, [key]: val }))
  }

  const setStringList = (key: keyof HistoricalCase, val: string) => {
    setField(key, val.split('\n').map(s => s.trim()).filter(Boolean) as string[])
  }

  const listToString = (val: string[] | undefined) => (val || []).join('\n')

  const isEdit = !!initial.case_id

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4" role="dialog" aria-modal="true">
      <div ref={focusTrapRef as React.RefObject<HTMLDivElement>} className="bg-surface-900 border border-slate-700 rounded-2xl max-w-3xl w-full max-h-[90vh] overflow-y-auto">
        <div className="sticky top-0 bg-surface-900 border-b border-slate-700/50 p-5 flex items-center justify-between z-10">
          <h2 className="font-semibold text-white">{isEdit ? t('analogies.editCase') : t('analogies.newCase')}</h2>
          <button onClick={onClose} className="text-slate-500 hover:text-white text-xl leading-none" aria-label={t('common.close')}>&times;</button>
        </div>
        <div className="p-5 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-xs text-slate-500 mb-1 block">{t('analogies.titleRequired')}</label>
              <input value={form.title || ''} onChange={e => setField('title', e.target.value)}
                className="w-full bg-surface-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-brand-500" />
            </div>
            <div>
              <label className="text-xs text-slate-500 mb-1 block">{t('analogies.titleEn')}</label>
              <input value={form.title_en || ''} onChange={e => setField('title_en', e.target.value)}
                className="w-full bg-surface-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-brand-500" />
            </div>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div>
              <label className="text-xs text-slate-500 mb-1 block">{t('analogies.year')}</label>
              <input type="number" value={form.year ?? ''} onChange={e => setField('year', e.target.value ? Number(e.target.value) : null)}
                className="w-full bg-surface-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-brand-500" />
            </div>
            <div>
              <label className="text-xs text-slate-500 mb-1 block">{t('analogies.durationDays')}</label>
              <input type="number" value={form.duration_days ?? ''} onChange={e => setField('duration_days', e.target.value ? Number(e.target.value) : null)}
                className="w-full bg-surface-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-brand-500" />
            </div>
            <div>
              <label className="text-xs text-slate-500 mb-1 block">{t('analogies.eventType')}</label>
              <select value={form.event_type || ''} onChange={e => setField('event_type', e.target.value)}
                className="w-full bg-surface-800 border border-slate-700 rounded-lg px-2 py-2 text-xs text-slate-400 focus:outline-none focus:border-brand-500">
                <option value="">{t('analogies.selectType')}</option>
                {Object.entries(EVENT_TYPE_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
              </select>
            </div>
            <div>
              <label className="text-xs text-slate-500 mb-1 block">{t('analogies.region')}</label>
              <select value={form.region || ''} onChange={e => setField('region', e.target.value)}
                className="w-full bg-surface-800 border border-slate-700 rounded-lg px-2 py-2 text-xs text-slate-400 focus:outline-none focus:border-brand-500">
                <option value="">{t('analogies.selectRegion')}</option>
                {REGION_OPTIONS.map(r => <option key={r} value={r}>{r}</option>)}
              </select>
            </div>
          </div>
          <div>
            <label className="text-xs text-slate-500 mb-1 block">{t('analogies.primaryIssue')}</label>
            <textarea value={form.primary_issue || ''} onChange={e => setField('primary_issue', e.target.value)} rows={2}
              className="w-full bg-surface-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-brand-500 resize-none" />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-xs text-slate-500 mb-1 block">{t('analogies.keyActorsHint')}</label>
              <textarea value={listToString(form.key_actors as string[] | undefined)} onChange={e => setStringList('key_actors', e.target.value)} rows={3}
                className="w-full bg-surface-800 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-brand-500 resize-none" />
            </div>
            <div>
              <label className="text-xs text-slate-500 mb-1 block">{t('analogies.keyTriggersHint')}</label>
              <textarea value={listToString(form.key_triggers as string[] | undefined)} onChange={e => setStringList('key_triggers', e.target.value)} rows={3}
                className="w-full bg-surface-800 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-brand-500 resize-none" />
            </div>
          </div>
          <div>
            <label className="text-xs text-slate-500 mb-1 block">{t('analogies.escalationPathHint')}</label>
            <textarea value={listToString(form.escalation_path as string[] | undefined)} onChange={e => setStringList('escalation_path', e.target.value)} rows={2}
              className="w-full bg-surface-800 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-brand-500 resize-none" />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-xs text-slate-500 mb-1 block">{t('analogies.resolution')}</label>
              <textarea value={form.resolution || ''} onChange={e => setField('resolution', e.target.value)} rows={2}
                className="w-full bg-surface-800 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-brand-500 resize-none" />
            </div>
            <div>
              <label className="text-xs text-slate-500 mb-1 block">{t('analogies.outcomeSummary')}</label>
              <textarea value={form.outcome_summary || ''} onChange={e => setField('outcome_summary', e.target.value)} rows={2}
                className="w-full bg-surface-800 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-brand-500 resize-none" />
            </div>
          </div>
          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="text-xs text-slate-500 mb-1 block">{t('analogies.escalationProb')}</label>
              <input type="number" step="0.05" min="0" max="1" value={form.probability_realized?.escalation ?? 0}
                onChange={e => setField('probability_realized', { ...form.probability_realized!, escalation: Number(e.target.value) })}
                className="w-full bg-surface-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-brand-500" />
            </div>
            <div>
              <label className="text-xs text-slate-500 mb-1 block">{t('analogies.stalemateProb')}</label>
              <input type="number" step="0.05" min="0" max="1" value={form.probability_realized?.stalemate ?? 0}
                onChange={e => setField('probability_realized', { ...form.probability_realized!, stalemate: Number(e.target.value) })}
                className="w-full bg-surface-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-brand-500" />
            </div>
            <div>
              <label className="text-xs text-slate-500 mb-1 block">{t('analogies.deescalationProb')}</label>
              <input type="number" step="0.05" min="0" max="1" value={form.probability_realized?.de_escalation ?? 0}
                onChange={e => setField('probability_realized', { ...form.probability_realized!, de_escalation: Number(e.target.value) })}
                className="w-full bg-surface-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-brand-500" />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-xs text-slate-500 mb-1 block">{t('analogies.actualOutcomeDir')}</label>
              <select value={form.actual_outcome_direction || ''} onChange={e => setField('actual_outcome_direction', e.target.value)}
                className="w-full bg-surface-800 border border-slate-700 rounded-lg px-2 py-2 text-xs text-slate-400 focus:outline-none focus:border-brand-500">
                <option value="">{t('analogies.selectDirection')}</option>
                <option value="escalation">{t('directions.escalation')}</option>
                <option value="stalemate">{t('directions.stalemate')}</option>
                <option value="de_escalation">{t('directions.de_escalation')}</option>
              </select>
            </div>
            <div>
              <label className="text-xs text-slate-500 mb-1 block">{t('analogies.resolutionType')}</label>
              <select value={form.resolution_type || ''} onChange={e => setField('resolution_type', e.target.value)}
                className="w-full bg-surface-800 border border-slate-700 rounded-lg px-2 py-2 text-xs text-slate-400 focus:outline-none focus:border-brand-500">
                <option value="">{t('analogies.selectType')}</option>
                <option value="de_escalation">{t('directions.de_escalation')}</option>
                <option value="escalation">{t('directions.escalation')}</option>
                <option value="stalemate">{t('directions.stalemate')}</option>
                <option value="ongoing">{t('analogies.ongoing')}</option>
              </select>
            </div>
          </div>
          <div>
            <label className="text-xs text-slate-500 mb-1 block">{t('analogies.keyLessonsHint')}</label>
            <textarea value={listToString(form.key_lessons as string[] | undefined)} onChange={e => setStringList('key_lessons', e.target.value)} rows={3}
              className="w-full bg-surface-800 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-brand-500 resize-none" />
          </div>
          <div>
            <label className="text-xs text-slate-500 mb-1 block">{t('analogies.tagsHint')}</label>
            <input value={(form.tags || []).join(', ')} onChange={e => setField('tags', e.target.value.split(',').map(s => s.trim()).filter(Boolean))}
              className="w-full bg-surface-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-brand-500" />
          </div>
          <div className="flex justify-end gap-3 pt-2">
            <button onClick={onClose} className="px-4 py-2 text-sm text-slate-400 hover:text-white transition-colors">{t('common.cancel')}</button>
            <button onClick={() => onSave(form)} disabled={!form.title}
              className="px-5 py-2 bg-brand-500 hover:bg-brand-600 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-60">
              {isEdit ? t('analogies.saveChanges') : t('analogies.createCase')}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default function AnalogiesPage() {
  const { t, i18n } = useTranslation()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const initEventId = searchParams.get('event_id') || ''

  const [events, setEvents] = useState<AbstractIRGEvent[]>([])
  const [selectedEventId, setSelectedEventId] = useState(initEventId)
  const [analogy, setAnalogy] = useState<AnalogyResult | null>(null)
  const [analogyLoading, setAnalogyLoading] = useState(false)
  const [analogyError, setAnalogyError] = useState('')
  const [generating, setGenerating] = useState(false)

  const [cases, setCases] = useState<HistoricalCase[]>([])
  const [casesLoading, setCasesLoading] = useState(true)
  const [caseSearch, setCaseSearch] = useState('')
  const [caseTypeFilter, setCaseTypeFilter] = useState('')
  const [caseRegionFilter, setCaseRegionFilter] = useState('')
  const [selectedCase, setSelectedCase] = useState<HistoricalCase | null>(null)
  const [editingCase, setEditingCase] = useState<Partial<HistoricalCase> | null>(null)
  const [deletingCaseId, setDeletingCaseId] = useState<string | null>(null)

  const loadCases = useCallback(() => {
    setCasesLoading(true)
    analogyApi.listCases().then(res => {
      setCases(res.data.cases ?? [])
    }).catch((e) => {
      toast.error(getErrorUserMessage(e, t('analogies.loadCasesFailed')), { dedupeKey: 'analogies-cases' })
      setCases([])
    }).finally(() => setCasesLoading(false))
  }, [t])

  useEffect(() => {
    eventApi.list().then(res => {
      setEvents(res.data.items)
      if (!selectedEventId && res.data.items.length > 0) {
        setSelectedEventId(res.data.items[0].event_id)
      }
    }).catch((e) => {
      toast.error(getErrorUserMessage(e, t('analogies.loadEventsFailed')), { dedupeKey: 'analogies-events' })
    })
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => { loadCases() }, [loadCases])

  useEffect(() => {
    if (!selectedEventId) return
    setAnalogyLoading(true)
    setAnalogyError('')
    analogyApi.getForEvent(selectedEventId).then(res => {
      if (res.data.status === 'not_generated') {
        setAnalogy(null)
      } else {
        setAnalogy(res.data)
      }
    }).catch((e) => {
      toast.error(getErrorUserMessage(e, t('analogies.loadAnalogiesFailed')), { dedupeKey: 'analogies-for-event' })
      setAnalogy(null)
    }).finally(() => setAnalogyLoading(false))
  }, [selectedEventId, t])

  const handleGenerate = (force = false) => {
    if (!selectedEventId) return
    setGenerating(true)
    setAnalogyError('')
    analogyApi.buildForEvent(selectedEventId, force).then(res => {
      setAnalogy(res.data)
    }).catch(e => {
      const msg = getErrorUserMessage(e, t('analogies.generateFailed'))
      setAnalogyError(msg)
      toast.error(msg, { dedupeKey: 'analogies-generate' })
    }).finally(() => setGenerating(false))
  }

  const handleSaveCase = (data: Partial<HistoricalCase>) => {
    const isEdit = !!data.case_id
    const op = isEdit
      ? analogyApi.updateCase(data.case_id!, data)
      : analogyApi.createCase(data as Partial<HistoricalCase> & { title: string })

    op.then(() => {
      toast.success(isEdit ? t('analogies.caseUpdated') : t('analogies.caseCreated'), { dedupeKey: 'case-save' })
      setEditingCase(null)
      setSelectedCase(null)
      loadCases()
    }).catch(e => {
      toast.error(getErrorUserMessage(e, t('analogies.saveFailed')), { dedupeKey: 'case-save-err' })
    })
  }

  const handleDeleteCase = (caseId: string) => {
    analogyApi.deleteCase(caseId).then(() => {
      toast.success(t('analogies.caseDeleted'), { dedupeKey: 'case-delete' })
      setDeletingCaseId(null)
      setSelectedCase(null)
      loadCases()
    }).catch(e => {
      toast.error(getErrorUserMessage(e, t('analogies.deleteFailed')), { dedupeKey: 'case-delete-err' })
    })
  }

  const filteredCases = cases.filter(c => {
    const q = caseSearch.toLowerCase()
    const matchText = !q || c.title.toLowerCase().includes(q) ||
      c.title_en.toLowerCase().includes(q) ||
      c.region.toLowerCase().includes(q)
    const matchType = !caseTypeFilter || c.event_type === caseTypeFilter
    const matchRegion = !caseRegionFilter || c.region === caseRegionFilter
    return matchText && matchType && matchRegion
  })

  const allRegions = [...new Set(cases.map(c => c.region))].sort()
  const selectedEvent = events.find(e => e.event_id === selectedEventId)

  return (
    <div className="min-h-screen bg-surface-950 text-slate-100 flex flex-col">
      <header className="border-b border-slate-700/50 px-6 py-4 flex items-center gap-3">
        <BookOpen size={18} className="text-brand-500" />
        <div>
          <h1 className="font-semibold text-white text-lg leading-tight">{t('analogies.title')}</h1>
          <p className="text-xs text-slate-500">{t('analogies.subtitle', { count: cases.length })}</p>
        </div>
      </header>

      <div className="flex flex-1 min-h-0 overflow-hidden">
        <div className="w-full md:w-[55%] border-r border-slate-700/30 flex flex-col overflow-hidden">
          <div className="p-4 border-b border-slate-700/30 bg-surface-900/30">
            <div className="text-xs text-slate-500 mb-2 uppercase tracking-wide">{t('analogies.selectEvent')}</div>
            <select
              value={selectedEventId}
              onChange={e => setSelectedEventId(e.target.value)}
              className="w-full bg-surface-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-brand-500"
            >
              <option value="">{t('analogies.selectEventPlaceholder')}</option>
              {events.map(e => (
                <option key={e.event_id} value={e.event_id}>{e.event_title}</option>
              ))}
            </select>
          </div>

          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {!selectedEventId ? (
              <div className="flex flex-col items-center justify-center h-full text-slate-500">
                <BookOpen size={40} className="mb-3 opacity-30" />
                <p>{t('analogies.selectEventHint')}</p>
              </div>
            ) : analogyLoading ? (
              <div className="flex items-center justify-center h-full">
                <LoadingSpinner />
              </div>
            ) : !analogy ? (
              <div className="flex flex-col items-center justify-center h-full text-center space-y-4">
                <AlertTriangle size={36} className="text-amber-500/50" />
                <div>
                  <p className="text-slate-400 mb-1">{t('analogies.notGenerated')}</p>
                  <p className="text-xs text-slate-600">{t('analogies.notGeneratedHint', { count: cases.length })}</p>
                </div>
                <button
                  onClick={() => handleGenerate(false)}
                  disabled={generating}
                  className="flex items-center gap-2 px-5 py-2.5 bg-brand-500 hover:bg-brand-600 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-60"
                >
                  {generating ? (
                    <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/>
                    </svg>
                  ) : <Search size={14} />}
                  {generating ? t('analogies.analyzing') : t('analogies.startAnalysis')}
                </button>
                {analogyError && <p className="text-xs text-red-400">{analogyError}</p>}
              </div>
            ) : (
              <>
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="font-medium text-white text-sm">{selectedEvent?.event_title}</h2>
                    <p className="text-xs text-slate-500 mt-0.5">
                      {t('analogies.matchSummary', { total: analogy.total_cases_searched, found: analogy.matched_cases?.length || 0 })}
                      {analogy.generated_at && ` · ${new Date(analogy.generated_at).toLocaleDateString(i18n.language === 'zh' ? 'zh-CN' : 'en-US')}`}
                    </p>
                  </div>
                  <button
                    onClick={() => handleGenerate(true)}
                    disabled={generating}
                    className="flex items-center gap-1.5 px-3 py-1.5 text-xs bg-surface-800 hover:bg-surface-700 border border-slate-700 rounded-lg text-slate-400 hover:text-white transition-colors disabled:opacity-60"
                  >
                    <RefreshCw size={12} className={generating ? 'animate-spin' : ''} />
                    {t('analogies.regenerate')}
                  </button>
                </div>

                {analogy.historical_base_rate && (
                  <div className="bg-surface-900 border border-slate-700/50 rounded-xl p-4">
                    <div className="text-xs text-slate-500 mb-2 uppercase tracking-wide flex items-center gap-1">
                      <Target size={10} />{t('analogies.combinedBaseRate')}
                    </div>
                    <ProbBar
                      escalation={analogy.historical_base_rate.escalation || 0}
                      stalemate={analogy.historical_base_rate.stalemate || 0}
                      de_escalation={analogy.historical_base_rate.de_escalation || 0}
                    />
                  </div>
                )}

                {analogy.synthesis && (
                  <div className="bg-brand-500/5 border border-brand-500/20 rounded-xl p-4">
                    <div className="text-xs text-brand-400 mb-2 flex items-center gap-1">
                      <BookOpen size={10} />{t('analogies.synthesis')}
                    </div>
                    <p className="text-sm text-slate-300 leading-relaxed">{analogy.synthesis}</p>
                  </div>
                )}

                {analogy.unique_modern_factors?.length > 0 && (
                  <div className="bg-surface-900 border border-slate-700/50 rounded-xl p-4">
                    <div className="text-xs text-slate-500 mb-2 flex items-center gap-1">
                      <AlertTriangle size={10} className="text-amber-500" />
                      {t('analogies.modernDifferences')}
                    </div>
                    <ul className="space-y-1.5">
                      {analogy.unique_modern_factors.map((f, i) => (
                        <li key={i} className="flex gap-2 text-xs text-slate-300">
                          <span className="text-amber-500 mt-0.5 flex-shrink-0">✓</span><span>{f}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                <div className="space-y-3">
                  <div className="text-xs text-slate-500 uppercase tracking-wide">{t('analogies.matchedCases')}</div>
                  {(analogy.matched_cases || []).map((mc, i) => (
                    <MatchedCaseCard key={mc.case_id} mc={mc} rank={i} />
                  ))}
                </div>

                {selectedEventId && (
                  <div className="flex items-center gap-2 pt-2">
                    <button onClick={() => navigate(`/events?event_id=${selectedEventId}`)}
                      className="text-xs px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 border border-slate-700 transition-colors">
                      {t('analogies.viewEvent')}
                    </button>
                    <button onClick={() => navigate(`/scenarios?event_id=${selectedEventId}`)}
                      className="text-xs px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 border border-slate-700 transition-colors">
                      {t('analogies.viewDeduction')}
                    </button>
                  </div>
                )}
              </>
            )}
          </div>
        </div>

        <div className="flex-1 flex flex-col overflow-hidden">
          <div className="p-4 border-b border-slate-700/30 space-y-3 bg-surface-900/20">
            <div className="text-xs text-slate-500 uppercase tracking-wide flex items-center justify-between">
              <span>{t('analogies.caseLibrary')}</span>
              <div className="flex items-center gap-2">
                <span className="text-slate-600">{filteredCases.length} / {cases.length}</span>
                <button
                  onClick={() => setEditingCase({ ...EMPTY_CASE })}
                  className="flex items-center gap-1 px-2 py-1 text-[10px] bg-brand-500/20 hover:bg-brand-500/30 text-brand-400 rounded-lg transition-colors"
                >
                  <Plus size={10} />{t('analogies.addNew')}
                </button>
              </div>
            </div>
            <div className="relative">
              <Search size={13} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
              <input
                type="text"
                placeholder={t('analogies.searchPlaceholder')}
                value={caseSearch}
                onChange={e => setCaseSearch(e.target.value)}
                className="w-full bg-surface-800 border border-slate-700 rounded-lg pl-8 pr-3 py-2 text-sm text-white placeholder-slate-600 focus:outline-none focus:border-brand-500"
              />
            </div>
            <div className="grid grid-cols-2 gap-2">
              <select
                value={caseTypeFilter}
                onChange={e => setCaseTypeFilter(e.target.value)}
                className="bg-surface-800 border border-slate-700 rounded-lg px-2 py-1.5 text-xs text-slate-400 focus:outline-none focus:border-brand-500"
              >
                <option value="">{t('analogies.allTypes')}</option>
                {Object.entries(EVENT_TYPE_LABELS).map(([k, v]) => (
                  <option key={k} value={k}>{v}</option>
                ))}
              </select>
              <select
                value={caseRegionFilter}
                onChange={e => setCaseRegionFilter(e.target.value)}
                className="bg-surface-800 border border-slate-700 rounded-lg px-2 py-1.5 text-xs text-slate-400 focus:outline-none focus:border-brand-500"
              >
                <option value="">{t('analogies.allRegions')}</option>
                {allRegions.map(r => (
                  <option key={r} value={r}>{r}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="flex-1 overflow-y-auto p-4 space-y-3">
            {casesLoading ? (
              <div className="flex justify-center py-12">
                <LoadingSpinner size="sm" />
              </div>
            ) : filteredCases.length === 0 ? (
              <div className="text-center py-12 text-slate-600">
                <BookOpen size={28} className="mx-auto mb-2 opacity-30" />
                <p className="text-sm">{t('analogies.noMatchingCases')}</p>
              </div>
            ) : (
              filteredCases.map(c => (
                <HistoricalCaseCard
                  key={c.case_id}
                  c={c}
                  onClick={() => setSelectedCase(c)}
                  onEdit={(e) => { e.stopPropagation(); setEditingCase({ ...c }) }}
                  onDelete={(e) => { e.stopPropagation(); setDeletingCaseId(c.case_id) }}
                />
              ))
            )}
          </div>
        </div>
      </div>

      {selectedCase && !editingCase && (
        <CaseDetailModal
          c={selectedCase}
          onClose={() => setSelectedCase(null)}
          onEdit={() => setEditingCase({ ...selectedCase })}
          onDelete={() => setDeletingCaseId(selectedCase.case_id)}
        />
      )}

      {editingCase && (
        <CaseFormModal
          initial={editingCase}
          onSave={handleSaveCase}
          onClose={() => setEditingCase(null)}
        />
      )}

      {deletingCaseId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="bg-surface-900 border border-slate-700 rounded-2xl max-w-sm w-full p-6 text-center space-y-4">
            <AlertTriangle size={28} className="mx-auto text-red-400" />
            <div>
              <h3 className="font-medium text-white">{t('analogies.confirmDelete')}</h3>
              <p className="text-xs text-slate-400 mt-1">{t('analogies.deleteWarning')}</p>
            </div>
            <div className="flex justify-center gap-3">
              <button onClick={() => setDeletingCaseId(null)}
                className="px-4 py-2 text-sm text-slate-400 hover:text-white transition-colors">
                {t('common.cancel')}
              </button>
              <button onClick={() => handleDeleteCase(deletingCaseId)}
                className="px-4 py-2 bg-red-500 hover:bg-red-600 text-white rounded-lg text-sm font-medium transition-colors">
                {t('analogies.confirmDelete')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
