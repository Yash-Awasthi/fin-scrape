import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { eventApi, pipelineApi, reportApi } from '../services/api'
import type { AbstractIRGEvent, PredictionRun } from '../types'

type ReportType = 'event_brief' | 'scenario_report' | 'thematic_report' | 'review_report'

interface ReportTypeConfig {
  type: ReportType
  label: string
  description: string
  needsEvent: boolean
  needsRun: boolean
  previewFields: string[]
  icon: string
}

export default function ReportPage() {
  const { t, i18n } = useTranslation()
  const [events, setEvents] = useState<AbstractIRGEvent[]>([])
  const [runs, setRuns] = useState<PredictionRun[]>([])
  const [dataLoading, setDataLoading] = useState(true)

  const [selectedType, setSelectedType] = useState<ReportType | null>(null)
  const [selectedEventId, setSelectedEventId] = useState('')
  const [selectedRunId, setSelectedRunId] = useState('')

  const [exporting, setExporting] = useState(false)
  const [exportError, setExportError] = useState<string | null>(null)
  const [exportSuccess, setExportSuccess] = useState(false)

  const REPORT_TYPES: ReportTypeConfig[] = [
    {
      type: 'event_brief',
      label: t('reports.types.event_brief.label'),
      description: t('reports.types.event_brief.description'),
      needsEvent: true,
      needsRun: false,
      previewFields: t('reports.types.event_brief.fields', { returnObjects: true }) as string[],
      icon: '⚡',
    },
    {
      type: 'scenario_report',
      label: t('reports.types.scenario_report.label'),
      description: t('reports.types.scenario_report.description'),
      needsEvent: true,
      needsRun: true,
      previewFields: t('reports.types.scenario_report.fields', { returnObjects: true }) as string[],
      icon: '🌿',
    },
    {
      type: 'thematic_report',
      label: t('reports.types.thematic_report.label'),
      description: t('reports.types.thematic_report.description'),
      needsEvent: true,
      needsRun: false,
      previewFields: t('reports.types.thematic_report.fields', { returnObjects: true }) as string[],
      icon: '📚',
    },
    {
      type: 'review_report',
      label: t('reports.types.review_report.label'),
      description: t('reports.types.review_report.description'),
      needsEvent: false,
      needsRun: true,
      previewFields: t('reports.types.review_report.fields', { returnObjects: true }) as string[],
      icon: '🔍',
    },
  ]

  useEffect(() => {
    Promise.all([eventApi.list(), pipelineApi.getRuns()])
      .then(([evRes, runsRes]) => {
        setEvents(evRes.data.items)
        const items: PredictionRun[] = runsRes.data.items ?? runsRes.data ?? []
        setRuns(items)
      })
      .catch(() => {})
      .finally(() => setDataLoading(false))
  }, [])

  const selectedConfig = REPORT_TYPES.find(r => r.type === selectedType)
  const selectedEvent = events.find(e => e.event_id === selectedEventId)
  const selectedRun = runs.find(r => r.run_id === selectedRunId)

  const filteredRuns = selectedEventId
    ? runs.filter(r => r.event_id === selectedEventId)
    : runs

  const canExport = selectedType && (
    (!selectedConfig!.needsEvent || selectedEventId) &&
    (!selectedConfig!.needsRun || selectedRunId)
  )

  const handleExport = async () => {
    if (!selectedType || !canExport) return
    setExporting(true)
    setExportError(null)
    setExportSuccess(false)
    try {
      await reportApi.export({
        report_type: selectedType,
        event_id: selectedEventId || undefined,
        run_id: selectedRunId || undefined,
      })
      setExportSuccess(true)
    } catch (e) {
      setExportError(e instanceof Error ? e.message : t('reports.exportFailed'))
    } finally {
      setExporting(false)
    }
  }

  return (
    <div className="min-h-screen bg-surface-950 text-slate-100 flex flex-col">
      <div className="px-6 py-5 border-b border-slate-800 shrink-0">
        <h1 className="text-xl font-bold text-slate-100">{t('reports.title')}</h1>
        <p className="text-slate-500 text-xs mt-0.5">{t('reports.subtitle')}</p>
      </div>

      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-4xl space-y-6">
          <div>
            <div className="text-xs font-semibold text-slate-500 uppercase tracking-widest mb-3">{t('reports.reportType')}</div>
            <div className="grid grid-cols-2 gap-3">
              {REPORT_TYPES.map(rt => (
                <button
                  key={rt.type}
                  onClick={() => {
                    setSelectedType(rt.type)
                    setExportError(null)
                    setExportSuccess(false)
                  }}
                  className={`text-left p-4 rounded-xl border transition-all ${
                    selectedType === rt.type
                      ? 'border-blue-600/60 bg-blue-900/15 shadow-lg shadow-blue-900/20'
                      : 'border-slate-700 bg-surface-900 hover:border-slate-600'
                  }`}
                >
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-xl">{rt.icon}</span>
                    <span className="text-sm font-semibold text-slate-200">{rt.label}</span>
                    {selectedType === rt.type && (
                      <span className="ml-auto text-xs text-blue-400">✓</span>
                    )}
                  </div>
                  <p className="text-xs text-slate-500 leading-relaxed">{rt.description}</p>
                  <div className="flex items-center gap-2 mt-2">
                    {rt.needsEvent && (
                      <span className="text-[10px] bg-slate-800 text-slate-600 px-1.5 py-0.5 rounded">{t('reports.needsEvent')}</span>
                    )}
                    {rt.needsRun && (
                      <span className="text-[10px] bg-slate-800 text-slate-600 px-1.5 py-0.5 rounded">{t('reports.needsRun')}</span>
                    )}
                  </div>
                </button>
              ))}
            </div>
          </div>

          {selectedConfig && (
            <div className="bg-surface-900 border border-slate-700 rounded-xl p-5 space-y-4">
              <div className="text-xs font-semibold text-slate-500 uppercase tracking-widest">{t('reports.configParams')}</div>

              {selectedConfig.needsEvent && (
                <div>
                  <label className="block text-xs text-slate-500 mb-1.5">
                    {t('reports.analyzeEvent')} <span className="text-red-500">*</span>
                  </label>
                  {dataLoading ? (
                    <div className="text-xs text-slate-600">{t('common.loading')}</div>
                  ) : (
                    <select
                      value={selectedEventId}
                      onChange={e => {
                        setSelectedEventId(e.target.value)
                        setSelectedRunId('')
                      }}
                      className="w-full bg-slate-800 border border-slate-700 text-slate-300 text-sm rounded-lg px-3 py-2 focus:outline-none focus:border-blue-600"
                    >
                      <option value="">-- {t('reports.selectEvent')} --</option>
                      {events.map(ev => (
                        <option key={ev.event_id} value={ev.event_id}>
                          {ev.event_title}
                        </option>
                      ))}
                    </select>
                  )}
                </div>
              )}

              {selectedConfig.needsRun && (
                <div>
                  <label className="block text-xs text-slate-500 mb-1.5">
                    {t('reports.deductionRun')} <span className="text-red-500">*</span>
                  </label>
                  {dataLoading ? (
                    <div className="text-xs text-slate-600">{t('common.loading')}</div>
                  ) : (
                    <select
                      value={selectedRunId}
                      onChange={e => setSelectedRunId(e.target.value)}
                      className="w-full bg-slate-800 border border-slate-700 text-slate-300 text-sm rounded-lg px-3 py-2 focus:outline-none focus:border-blue-600"
                    >
                      <option value="">-- {t('reports.selectRun')} --</option>
                      {filteredRuns.map(run => (
                        <option key={run.run_id} value={run.run_id}>
                          {run.run_id.slice(0, 16)}...
                          {run.created_at ? ` (${new Date(run.created_at).toLocaleDateString(i18n.language === 'zh' ? 'zh-CN' : 'en-US')})` : ''}
                          {run.summary ? ` - ${run.summary.slice(0, 30)}${run.summary.length > 30 ? '...' : ''}` : ''}
                        </option>
                      ))}
                    </select>
                  )}
                </div>
              )}
            </div>
          )}

          {selectedConfig && (
            <div className="bg-surface-900 border border-slate-700 rounded-xl overflow-hidden">
              <div className="px-5 py-3 border-b border-slate-700 flex items-center justify-between">
                <div className="text-xs font-semibold text-slate-500 uppercase tracking-widest">{t('reports.reportPreview')}</div>
                <div className="flex items-center gap-2 text-xs text-slate-600">
                  {selectedEvent && <span>{selectedEvent.event_title}</span>}
                  {selectedRun && (
                    <span className="font-mono">{selectedRun.run_id.slice(0, 8)}...</span>
                  )}
                  {(selectedEventId || selectedRunId) && (
                    <span className="text-slate-700">·</span>
                  )}
                  <span>{new Date().toLocaleDateString(i18n.language === 'zh' ? 'zh-CN' : 'en-US')}</span>
                </div>
              </div>

              <div className="p-5">
                <div className="flex items-center gap-3 mb-5">
                  <span className="text-2xl">{selectedConfig.icon}</span>
                  <div>
                    <h3 className="text-base font-bold text-slate-200">{selectedConfig.label}</h3>
                    <p className="text-xs text-slate-500 mt-0.5">{selectedConfig.description}</p>
                  </div>
                </div>

                <div className="space-y-2">
                  {selectedConfig.previewFields.map((field, i) => (
                    <div key={i} className="flex items-center gap-3">
                      <div className="w-5 h-5 rounded bg-slate-800 flex items-center justify-center text-[10px] text-slate-600 font-mono shrink-0">
                        {i + 1}
                      </div>
                      <div className="flex-1 h-px bg-slate-800" />
                      <div className="text-xs text-slate-500 min-w-[180px]">{field}</div>
                    </div>
                  ))}
                </div>

                {(selectedRunId || selectedEventId) && (
                  <div className="mt-5 border-t border-slate-800 pt-4 flex items-center gap-4 text-xs text-slate-700">
                    {selectedRunId && <span>Run ID: {selectedRunId.slice(0, 12)}...</span>}
                    <span>{t('reports.generateTime')}: {new Date().toLocaleString(i18n.language === 'zh' ? 'zh-CN' : 'en-US')}</span>
                  </div>
                )}
              </div>
            </div>
          )}

          {selectedType && (
            <div className="space-y-3">
              <button
                onClick={handleExport}
                disabled={!canExport || exporting}
                className="w-full py-3 rounded-xl font-semibold text-sm bg-blue-600 hover:bg-blue-500 disabled:opacity-40 disabled:cursor-not-allowed transition-all shadow-lg shadow-blue-900/30 flex items-center justify-center gap-2"
              >
                {exporting ? (
                  <>
                    <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                    </svg>
                    {t('reports.generating')}
                  </>
                ) : (
                  <>
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    {t('reports.exportPdf')}
                  </>
                )}
              </button>

              {!canExport && !exporting && (
                <p className="text-xs text-center text-slate-700">
                  {selectedConfig?.needsEvent && !selectedEventId ? t('reports.selectEvent') : ''}
                  {selectedConfig?.needsRun && !selectedRunId ? t('reports.selectRun') : ''}
                </p>
              )}

              {exportError && (
                <div className="bg-red-900/20 border border-red-700/50 rounded-xl px-4 py-3 text-red-400 text-sm text-center">
                  {exportError}
                </div>
              )}

              {exportSuccess && (
                <div className="bg-emerald-900/20 border border-emerald-700/50 rounded-xl px-4 py-3 text-emerald-400 text-sm text-center flex items-center justify-center gap-2">
                  <span>✓</span>
                  <span>{t('reports.downloadStarted')}</span>
                </div>
              )}
            </div>
          )}

          {!selectedType && (
            <div className="text-center py-10 text-slate-700">
              <div className="text-3xl mb-2">☝️</div>
              <div className="text-sm">{t('reports.selectReportType')}</div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
