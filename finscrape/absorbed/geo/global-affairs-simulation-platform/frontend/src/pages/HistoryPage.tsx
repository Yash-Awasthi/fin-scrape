import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { historyApi, scenarioApi } from '../services/api'
import type { PredictionRun } from '../types'
import { EVENT_TYPE_LABELS } from '../types'
import { toast } from '../store/toast'
import LoadingSpinner from '../components/LoadingSpinner'
import ErrorState from '../components/ErrorState'
import EmptyState from '../components/EmptyState'

interface HistoryItem extends PredictionRun {
  event_title?: string
  actual_outcome?: {
    actual_summary: string
    actual_event_type: string
    matched_script_id?: string
  }
  evaluation?: {
    accuracy_rate: number
    error_types: string[]
    notes: string
  }
}

interface OutcomeForm {
  actual_summary: string
  actual_event_type: string
  matched_script_id: string
}

export default function HistoryPage() {
  const { t, i18n } = useTranslation()
  const navigate = useNavigate()
  const [history, setHistory] = useState<HistoryItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const [outcomeFormId, setOutcomeFormId] = useState<string | null>(null)
  const [scriptOptions, setScriptOptions] = useState<Record<string, Array<{ script_id: string; script_title: string }>>>({})
  const [evalLoading, setEvalLoading] = useState<Record<string, boolean>>({})

  // 实际结果表单
  const [outcomeForms, setOutcomeForms] = useState<Record<string, OutcomeForm>>({})
  const [submitLoading, setSubmitLoading] = useState<Record<string, boolean>>({})
  const [submitSuccess, setSubmitSuccess] = useState<Record<string, boolean>>({})

  const loadHistory = () => {
    setLoading(true)
    historyApi.list()
      .then(res => {
        const items: HistoryItem[] = res.data.items ?? res.data ?? []
        setHistory(items)
      })
      .catch(e => setError(e instanceof Error ? e.message : t('history.loadFailed', '数据加载失败')))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    loadHistory()
  }, [])

  const handleExpand = async (item: HistoryItem) => {
    if (expandedId === item.run_id) {
      setExpandedId(null)
      return
    }
    setExpandedId(item.run_id)
    // 展开新条目时清旧submitSuccess
    setSubmitSuccess(prev => ({ ...prev, [item.run_id]: false }))

    // 加载该 run 对应的剧本列表（用于选择命中剧本）
    if (!scriptOptions[item.run_id] && item.event_id) {
      try {
        const res = await scenarioApi.getForEvent(item.event_id, item.run_id)
        setScriptOptions(prev => ({
          ...prev,
          [item.run_id]: res.data.scripts.map(s => ({
            script_id: s.script_id,
            script_title: s.script_title,
          })),
        }))
      } catch {
        setScriptOptions(prev => ({ ...prev, [item.run_id]: [] }))
      }
    }
  }

  const updateForm = (runId: string, field: keyof OutcomeForm, value: string) => {
    setOutcomeForms(prev => ({
      ...prev,
      [runId]: { ...prev[runId] ?? { actual_summary: '', actual_event_type: '', matched_script_id: '' }, [field]: value },
    }))
  }

  const handleSubmitOutcome = async (item: HistoryItem) => {
    const form = outcomeForms[item.run_id]
    if (!form?.actual_summary?.trim() || !form?.actual_event_type) return
    setSubmitLoading(prev => ({ ...prev, [item.run_id]: true }))
    try {
      await historyApi.recordOutcome(item.run_id, {
        event_id: item.event_id,
        actual_summary: form.actual_summary,
        actual_event_type: form.actual_event_type,
        matched_script_id: form.matched_script_id || undefined,
      })
      setSubmitSuccess(prev => ({ ...prev, [item.run_id]: true }))
      setOutcomeFormId(null)
      loadHistory()
    } catch (e: unknown) {
      // 不静默吞错，给用户反馈
      const msg = e instanceof Error ? e.message : t('history.submitError', '提交失败，请稍后重试')
      toast.error(msg)
    } finally {
      setSubmitLoading(prev => ({ ...prev, [item.run_id]: false }))
    }
  }

  const handleGenerateEvaluation = async (item: HistoryItem) => {
    if (!item.actual_outcome) {
      toast.error(t('history.recordOutcomeFirst', '请先记录实际结果，再生成评估'))
      return
    }
    setEvalLoading(prev => ({ ...prev, [item.run_id]: true }))
    try {
      await historyApi.autoEvaluation(item.run_id)
      toast.success(t('history.evalGenerated', '评估已生成，可前往预测校准页面查看'))
      loadHistory()
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : t('history.evalGenerateFailed', '评估生成失败')
      toast.error(msg)
    } finally {
      setEvalLoading(prev => ({ ...prev, [item.run_id]: false }))
    }
  }

  // 排序memoize，避免重复排序
  const sortedHistory = useMemo(() =>
    [...history].sort((a, b) => {
      const ta = a.created_at ? new Date(a.created_at).getTime() : 0
      const tb = b.created_at ? new Date(b.created_at).getTime() : 0
      return tb - ta
    }),
    [history]
  )

  if (loading) {
    return (
      <div className="min-h-screen bg-surface-950 flex items-center justify-center">
        <LoadingSpinner />
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-surface-950 flex items-center justify-center">
        <ErrorState message={error} onRetry={loadHistory} />
      </div>
    )
  }

  if (history.length === 0) {
    return (
      <div className="min-h-screen bg-surface-950 flex items-center justify-center">
        <EmptyState icon="📭" title={t('history.noRuns')} description={t('history.selectRun')} />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-surface-950 text-slate-100 flex flex-col">
      {/* 顶部 */}
      <div className="px-6 py-5 border-b border-slate-800 shrink-0">
        <h1 className="text-xl font-bold text-slate-100">{t('history.title')}</h1>
        <p className="text-slate-500 text-xs mt-0.5">{t('history.subtitle', '推演记录、实际结果对照与误差分析')}</p>
      </div>

      {/* 列表 */}
      <div className="flex-1 overflow-y-auto p-6 space-y-3">
        {sortedHistory.map(item => (
          <div
            key={item.run_id}
            className={`bg-surface-900 border rounded-xl overflow-hidden transition-colors ${
              expandedId === item.run_id ? 'border-blue-700/50' : 'border-slate-700'
            }`}
          >
            {/* 记录头 */}
            <button
              onClick={() => handleExpand(item)}
              className="w-full text-left px-5 py-4 hover:bg-slate-800/20 transition-colors"
            >
              <div className="flex items-center justify-between gap-3">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-xs font-mono text-slate-500">{item.run_id.slice(0, 16)}...</span>
                    <span className={`text-[10px] px-1.5 py-0.5 rounded ${
                      item.status === 'completed'
                        ? 'bg-emerald-900/40 text-emerald-400'
                        : 'bg-slate-800 text-slate-500'
                    }`}>
                      {item.status}
                    </span>
                    {item.actual_outcome && (
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-blue-900/40 text-blue-400">
                        {t('history.outcomeRecorded', '已记录结果')}
                      </span>
                    )}
                    {item.evaluation && (
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-purple-900/40 text-purple-400">
                        {t('history.evaluated', '已评估')}
                      </span>
                    )}
                  </div>
                  {item.event_title && (
                    <div className="text-sm font-medium text-slate-300 mt-1">{item.event_title}</div>
                  )}
                  <div className="text-xs text-slate-500 mt-0.5 line-clamp-1">{item.summary}</div>
                </div>
                <div className="text-right shrink-0">
                  {item.created_at && (
                    <div className="text-xs text-slate-600">{new Date(item.created_at).toLocaleString(i18n.language === 'zh' ? 'zh-CN' : 'en-US')}</div>
                  )}
                  <div className="text-xs text-slate-600 mt-0.5">{t('pipeline.history.scripts', { count: item.script_ids.length })}</div>
                  <div className="text-slate-700 text-xs mt-1">{expandedId === item.run_id ? '▲' : '▼'}</div>
                </div>
              </div>
            </button>

            {/* 展开详情 */}
            {expandedId === item.run_id && (
              <div className="border-t border-slate-700/50 px-5 py-4 space-y-5">
                {/* 推演摘要 */}
                <div>
                  <div className="text-xs font-semibold text-slate-500 uppercase tracking-widest mb-2">{t('history.summary')}</div>
                  <p className="text-sm text-slate-400 leading-relaxed">{item.summary}</p>
                  <div className="text-xs text-slate-600 mt-1">{t('history.scripts')}：{item.script_ids.length}</div>
                </div>

                {/* 实际结果对照 */}
                {item.actual_outcome && (
                  <div className="bg-blue-900/10 border border-blue-800/30 rounded-xl p-4">
                    <div className="text-xs font-semibold text-blue-400 uppercase tracking-widest mb-3">{t('history.actualOutcome')}</div>
                    <div className="space-y-2">
                      <div>
                        <span className="text-xs text-slate-500">{t('history.actualSummary', '实际摘要')}：</span>
                        <span className="text-sm text-slate-300">{item.actual_outcome.actual_summary}</span>
                      </div>
                      <div>
                        <span className="text-xs text-slate-500">{t('history.actualEventType', '实际事件类型')}：</span>
                        <span className="text-sm text-slate-300">
                          {EVENT_TYPE_LABELS[item.actual_outcome.actual_event_type as keyof typeof EVENT_TYPE_LABELS] ?? item.actual_outcome.actual_event_type}
                        </span>
                      </div>
                      {item.actual_outcome.matched_script_id && (
                        <div>
                          <span className="text-xs text-slate-500">{t('history.scriptHit')}：</span>
                          <span className="text-xs font-mono text-emerald-400">{item.actual_outcome.matched_script_id.slice(0, 12)}...</span>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* 误差分析 */}
                {item.evaluation && (
                  <div className="bg-purple-900/10 border border-purple-800/30 rounded-xl p-4">
                    <div className="text-xs font-semibold text-purple-400 uppercase tracking-widest mb-3">{t('history.errorAnalysis')}</div>
                    <div className="flex items-center gap-4 mb-3">
                      <div className="text-center">
                        <div className="text-2xl font-bold text-purple-400">
                          {Math.round(item.evaluation.accuracy_rate * 100)}%
                        </div>
                        <div className="text-xs text-slate-600">{t('history.hitRate', '命中率')}</div>
                      </div>
                      <div className="flex-1">
                        <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
                          <div
                            className="h-full bg-purple-500 rounded-full"
                            style={{ width: `${item.evaluation.accuracy_rate * 100}%` }}
                          />
                        </div>
                      </div>
                    </div>
                    {item.evaluation.error_types.length > 0 && (
                      <div className="flex flex-wrap gap-1.5">
                        {item.evaluation.error_types.map((et, i) => (
                          <span key={i} className="text-xs bg-purple-900/30 text-purple-500 border border-purple-700/40 px-2 py-0.5 rounded">
                            {et}
                          </span>
                        ))}
                      </div>
                    )}
                    {item.evaluation.notes && (
                      <p className="text-xs text-slate-600 mt-2 italic">{item.evaluation.notes}</p>
                    )}
                  </div>
                )}

                {/* 操作按钮 */}
                <div className="flex items-center gap-2 flex-wrap">
                  <button
                    onClick={() => navigate(`/scenarios?event_id=${item.event_id}`)}
                    className="text-xs px-3 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 border border-slate-700 transition-colors"
                  >
                    {t('common.view')}
                  </button>
                  {item.actual_outcome && !item.evaluation && (
                    <button
                      onClick={() => handleGenerateEvaluation(item)}
                      disabled={evalLoading[item.run_id]}
                      className="text-xs px-3 py-2 rounded-lg bg-purple-600 hover:bg-purple-500 disabled:opacity-50 disabled:cursor-not-allowed text-white transition-colors flex items-center gap-1.5"
                    >
                      {evalLoading[item.run_id] && (
                        <svg className="animate-spin w-3 h-3" viewBox="0 0 24 24" fill="none">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                        </svg>
                      )}
                      {t('history.autoEvaluate')}
                    </button>
                  )}
                </div>

                {/* 记录实际结果表单 */}
                {!item.actual_outcome && (
                  <div>
                    {outcomeFormId !== item.run_id ? (
                      <button
                        onClick={() => setOutcomeFormId(item.run_id)}
                        className="text-xs px-3 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 border border-slate-700 transition-colors"
                      >
                        + {t('history.recordOutcome')}
                      </button>
                    ) : (
                      <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-4 space-y-3">
                        <div className="text-xs font-semibold text-slate-400 mb-1">{t('history.recordOutcome')}</div>

                        <div>
                          <label className="block text-xs text-slate-500 mb-1">{t('history.actualSummary', '实际摘要')}</label>
                          <textarea
                            value={outcomeForms[item.run_id]?.actual_summary ?? ''}
                            onChange={e => updateForm(item.run_id, 'actual_summary', e.target.value)}
                            rows={2}
                            placeholder={t('history.actualSummaryPlaceholder', '描述实际发生的情况...')}
                            className="w-full bg-slate-800 border border-slate-700 text-slate-300 text-xs rounded-lg px-3 py-2 focus:outline-none focus:border-blue-600 placeholder-slate-700 resize-none"
                          />
                        </div>

                        <div>
                          <label className="block text-xs text-slate-500 mb-1">{t('history.actualEventType', '实际事件类型')}</label>
                          <select
                            value={outcomeForms[item.run_id]?.actual_event_type ?? ''}
                            onChange={e => updateForm(item.run_id, 'actual_event_type', e.target.value)}
                            className="w-full bg-slate-800 border border-slate-700 text-slate-300 text-xs rounded-lg px-3 py-2 focus:outline-none focus:border-blue-600"
                          >
                            <option value="">{t('history.selectEventType', '选择事件类型')}</option>
                            {Object.entries(EVENT_TYPE_LABELS).map(([k, v]) => (
                              <option key={k} value={k}>{v}</option>
                            ))}
                          </select>
                        </div>

                        <div>
                          <label className="block text-xs text-slate-500 mb-1">{t('history.scriptHitOptional', '命中的剧本（可选）')}</label>
                          <select
                            value={outcomeForms[item.run_id]?.matched_script_id ?? ''}
                            onChange={e => updateForm(item.run_id, 'matched_script_id', e.target.value)}
                            className="w-full bg-slate-800 border border-slate-700 text-slate-300 text-xs rounded-lg px-3 py-2 focus:outline-none focus:border-blue-600"
                          >
                            <option value="">{t('history.noMatchingScript', '无匹配剧本')}</option>
                            {(scriptOptions[item.run_id] ?? []).map(s => (
                              <option key={s.script_id} value={s.script_id}>{s.script_title}</option>
                            ))}
                          </select>
                        </div>

                        <div className="flex items-center gap-2 pt-1">
                          <button
                            onClick={() => handleSubmitOutcome(item)}
                            disabled={
                              submitLoading[item.run_id] ||
                              !outcomeForms[item.run_id]?.actual_summary?.trim() ||
                              !outcomeForms[item.run_id]?.actual_event_type
                            }
                            className="px-3 py-1.5 text-xs rounded-lg bg-blue-600 hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-1.5"
                          >
                            {submitLoading[item.run_id] && (
                              <svg className="animate-spin w-3 h-3" viewBox="0 0 24 24" fill="none">
                                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                              </svg>
                            )}
                            {t('common.submit')}
                          </button>
                          <button
                            onClick={() => setOutcomeFormId(null)}
                            className="px-3 py-1.5 text-xs rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-500 transition-colors"
                          >
                            {t('common.cancel')}
                          </button>
                          {submitSuccess[item.run_id] && (
                            <span className="text-xs text-emerald-400">✓ {t('history.submitted', '已提交')}</span>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
