import { useEffect, useState } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { theoryApi } from '../services/api'
import type { TheoryAnalysis } from '../types'
import { useAppStore } from '../store'
import LoadingSpinner from '../components/LoadingSpinner'
import ErrorState from '../components/ErrorState'
import EmptyState from '../components/EmptyState'

const THEORIES = [
  { key: 'realism', label: 'theories.realism' },
  { key: 'liberal_institutionalism', label: 'theories.liberalInstitutionalism' },
  { key: 'constructivism', label: 'theories.constructivism' },
  { key: 'geopolitics', label: 'theories.geopolitics' },
  { key: 'ipe', label: 'theories.internationalPoliticalEconomy' },
]

export default function TheoryPage() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()

  // --- 全局store ---
  const storeEvents = useAppStore((s) => s.events)
  const storeEventsLoading = useAppStore((s) => s.eventsLoading)
  const storeSelectedId = useAppStore((s) => s.selectedEventId)
  const setStoreSelectedEvent = useAppStore((s) => s.setSelectedEvent)
  const fetchEvents = useAppStore((s) => s.fetchEvents)

  // URL param 优先；否则用 store 选中 ID；否则留空
  const urlEventId = searchParams.get('event_id') ?? ''
  const [selectedEventId, setSelectedEventId] = useState(
    urlEventId || storeSelectedId || ''
  )

  const [analyses, setAnalyses] = useState<TheoryAnalysis[]>([])
  const [analysesLoading, setAnalysesLoading] = useState(false)
  const [analysesError, setAnalysesError] = useState<string | null>(null)

  const [activeTheory, setActiveTheory] = useState<string>('')
  const [compareTheory, setCompareTheory] = useState<string>('')
  const [compareMode, setCompareMode] = useState(false)

  // 若 store 中无数据，主动拉取
  useEffect(() => {
    if (storeEvents.length === 0 && !storeEventsLoading) {
      fetchEvents()
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // 当 store 里的事件列表就绪，且本地还没有选中事件时，自动选第一个
  useEffect(() => {
    if (!selectedEventId && storeEvents.length > 0) {
      const first = urlEventId
        ? (storeEvents.find(e => e.event_id === urlEventId)?.event_id ?? storeEvents[0].event_id)
        : storeEvents[0].event_id
      setSelectedEventId(first)
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [storeEvents])

  // 事件切换时同步到 store（跨页面通信）+ URL 参数
  const handleEventChange = (id: string) => {
    setSelectedEventId(id)
    setStoreSelectedEvent(id)
    setSearchParams({ event_id: id }, { replace: true })
  }

  // 加载理论分析
  useEffect(() => {
    if (!selectedEventId) return
    setAnalysesLoading(true)
    setAnalysesError(null)
    setAnalyses([])
    setActiveTheory('')
    setCompareTheory('')

    let cancelled = false

    theoryApi.getForEvent(selectedEventId)
      .then(async res => {
        if (cancelled) return
        if (res.data.analyses.length === 0) {
          // 不重复设loading=true
          // finally 里 setAnalysesLoading(false) 应在生成完成后才执行
          try {
            const genRes = await theoryApi.generateForEvent(selectedEventId)
            if (cancelled) return
            setAnalyses(genRes.data.analyses)
            if (genRes.data.analyses.length > 0) {
              setActiveTheory(genRes.data.analyses[0].theory_name)
            }
          } catch {
            if (!cancelled) setAnalysesError(t('theories.generateError'))
          }
        } else {
          setAnalyses(res.data.analyses)
          setActiveTheory(res.data.analyses[0].theory_name)
        }
      })
      .catch(e => { if (!cancelled) setAnalysesError(e instanceof Error ? e.message : t('theories.loadError')) })
      .finally(() => { if (!cancelled) setAnalysesLoading(false) })

    return () => { cancelled = true }
  }, [selectedEventId])

  const getAnalysis = (theoryKey: string) =>
    analyses.find(a => a.theory_name === theoryKey)

  const activeAnalysis = getAnalysis(activeTheory)
  const compareAnalysis = compareMode ? getAnalysis(compareTheory) : null

  const selectedEvent = storeEvents.find(e => e.event_id === selectedEventId)

  return (
    <div className="min-h-screen bg-surface-950 text-slate-100 flex flex-col">
      {/* 顶部 */}
      <div className="px-6 py-5 border-b border-slate-800 shrink-0">
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div>
            <h1 className="text-xl font-bold text-slate-100">{t('theories.title')}</h1>
            <p className="text-slate-500 text-xs mt-0.5">{t('theories.subtitle')}</p>
          </div>
          {/* 事件选择 */}
          <div className="flex items-center gap-3">
            <label className="text-xs text-slate-500 whitespace-nowrap">{t('theories.selectEvent')}</label>
            <select
              value={selectedEventId}
              onChange={e => handleEventChange(e.target.value)}
              disabled={storeEventsLoading}
              className="bg-surface-900 border border-slate-700 text-slate-300 text-sm rounded-lg px-3 py-2 min-w-[220px] focus:outline-none focus:border-blue-600"
            >
              {storeEventsLoading ? (
                <option>{t('common.loading')}</option>
              ) : storeEvents.length === 0 ? (
                <option value="">{t('theories.noData')}</option>
              ) : (
                storeEvents.map(ev => (
                  <option key={ev.event_id} value={ev.event_id}>
                    {ev.event_title}
                  </option>
                ))
              )}
            </select>
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-6">
        {/* 事件标题 */}
        {selectedEvent && (
          <div className="mb-5 text-sm text-slate-500">
            {t('theories.currentEvent')}<span className="text-slate-300 ml-1">{selectedEvent.event_title}</span>
          </div>
        )}

        {/* 理论选项卡 */}
        <div className="flex items-center gap-1 mb-6 flex-wrap">
          {THEORIES.map(th => {
            const has = analyses.some(a => a.theory_name === th.key)
            return (
              <button
                key={th.key}
                onClick={() => setActiveTheory(th.key)}
                disabled={!has}
                className={`px-4 py-2 text-sm rounded-lg transition-colors ${
                  activeTheory === th.key
                    ? 'bg-blue-600 text-white shadow-lg shadow-blue-900/40'
                    : has
                    ? 'bg-surface-900 text-slate-400 hover:text-slate-200 border border-slate-700'
                    : 'bg-surface-900/50 text-slate-700 border border-slate-800 cursor-not-allowed'
                }`}
              >
                {t(th.label)}
              </button>
            )
          })}
          <div className="ml-auto flex items-center gap-2">
            <button
              onClick={() => setCompareMode(v => !v)}
              className={`px-3 py-2 text-xs rounded-lg border transition-colors ${
                compareMode
                  ? 'bg-purple-600/20 text-purple-400 border-purple-700/50'
                  : 'bg-surface-900 text-slate-500 border-slate-700 hover:text-slate-300'
              }`}
            >
              {t('theories.compareView')}
            </button>
            {compareMode && (
              <select
                value={compareTheory}
                onChange={e => setCompareTheory(e.target.value)}
                className="bg-surface-900 border border-slate-700 text-slate-300 text-xs rounded-lg px-2 py-2 focus:outline-none"
              >
                <option value="">{t('theories.selectCompareTheory')}</option>
                {THEORIES.filter(th => th.key !== activeTheory && analyses.some(a => a.theory_name === th.key)).map(th => (
                  <option key={th.key} value={th.key}>{t(th.label)}</option>
                ))}
              </select>
            )}
          </div>
        </div>

        {/* 加载 */}
        {analysesLoading && (
          <LoadingSpinner message={t('theories.generating')} size="md" />
        )}

        {/* 错误 */}
        {analysesError && (
          <ErrorState message={analysesError} />
        )}

        {/* 空状态 */}
        {!analysesLoading && !analysesError && analyses.length === 0 && selectedEventId && (
          <EmptyState
            title={t('theories.noData')}
            description={t('theories.noDataHint')}
          />
        )}

        {/* 内容区 */}
        {!analysesLoading && !analysesError && (
          <div className={`grid gap-6 ${compareMode && compareAnalysis ? 'grid-cols-2' : 'grid-cols-1 max-w-3xl'}`}>
            {[activeAnalysis, compareMode ? compareAnalysis : null].filter(Boolean).map((analysis, idx) => {
              if (!analysis) return null
              const theoryLabelKey = THEORIES.find(th => th.key === analysis.theory_name)?.label ?? null
              const theoryLabel = theoryLabelKey ? t(theoryLabelKey) : analysis.theory_display_name
              return (
                <div key={idx} className="space-y-5">
                  <div className="text-sm font-semibold text-blue-400 pb-2 border-b border-slate-800">
                    {theoryLabel}
                  </div>

                  {/* 核心假设 */}
                  <div className="bg-blue-900/15 border border-blue-800/40 rounded-xl p-4">
                    <div className="text-xs font-semibold text-blue-400 uppercase tracking-widest mb-2">{t('theories.coreAssumption')}</div>
                    <p className="text-sm text-slate-300 leading-relaxed">{analysis.core_assumption}</p>
                  </div>

                  {/* 解读正文 */}
                  <div>
                    <div className="text-xs font-semibold text-slate-500 uppercase tracking-widest mb-2">{t('theories.interpretation')}</div>
                    <p className="text-sm text-slate-400 leading-relaxed">{analysis.interpretation}</p>
                  </div>

                  {/* 主要驱动力 */}
                  {analysis.main_drivers.length > 0 && (
                    <div>
                      <div className="text-xs font-semibold text-slate-500 uppercase tracking-widest mb-2">{t('theories.mainDrivers')}</div>
                      <ul className="space-y-1.5">
                        {analysis.main_drivers.map((d, i) => (
                          <li key={i} className="flex items-start gap-2 text-sm text-slate-400">
                            <span className="text-blue-500 shrink-0 mt-0.5">▸</span>{d}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* 各主体预期行为 */}
                  {Object.keys(analysis.likely_actor_responses).length > 0 && (
                    <div>
                      <div className="text-xs font-semibold text-slate-500 uppercase tracking-widest mb-2">{t('theories.expectedBehavior')}</div>
                      <div className="space-y-2">
                        {Object.entries(analysis.likely_actor_responses).map(([actor, resp]) => (
                          <div key={actor} className="bg-surface-900 border border-slate-700 rounded-lg px-4 py-3">
                            <div className="text-xs font-semibold text-slate-400 mb-1">{actor}</div>
                            <div className="text-sm text-slate-500">{resp}</div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* 升级 vs 缓和含义 */}
                  <div className="grid grid-cols-2 gap-3">
                    {analysis.escalation_implications.length > 0 && (
                      <div className="bg-red-900/10 border border-red-800/30 rounded-xl p-3">
                        <div className="text-xs font-semibold text-red-400 mb-2">{t('theories.escalationImplications')}</div>
                        <ul className="space-y-1">
                          {analysis.escalation_implications.map((imp, i) => (
                            <li key={i} className="text-xs text-slate-400">↑ {imp}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                    {analysis.deescalation_implications.length > 0 && (
                      <div className="bg-emerald-900/10 border border-emerald-800/30 rounded-xl p-3">
                        <div className="text-xs font-semibold text-emerald-400 mb-2">{t('theories.deescalationImplications')}</div>
                        <ul className="space-y-1">
                          {analysis.deescalation_implications.map((imp, i) => (
                            <li key={i} className="text-xs text-slate-400">↓ {imp}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>

                  {/* 理论局限性 */}
                  {analysis.weaknesses.length > 0 && (
                    <div>
                      <div className="text-xs font-semibold text-slate-600 uppercase tracking-widest mb-2">{t('theories.weaknesses')}</div>
                      <ul className="space-y-1">
                        {analysis.weaknesses.map((w, i) => (
                          <li key={i} className="text-xs text-slate-600">• {w}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* 反驳论点 */}
                  {analysis.counterarguments.length > 0 && (
                    <div className="border-l-2 border-slate-700 pl-3">
                      <div className="text-xs font-semibold text-slate-600 mb-1.5">{t('theories.counterarguments')}</div>
                      {analysis.counterarguments.map((ca, i) => (
                        <p key={i} className="text-xs text-slate-600 italic">{ca}</p>
                      ))}
                    </div>
                  )}

                  {/* 置信度备注 */}
                  {analysis.confidence_note && (
                    <div className="text-xs text-slate-700 italic">{analysis.confidence_note}</div>
                  )}
                </div>
              )
            })}
          </div>
        )}

        {!analysesLoading && !analysesError && selectedEventId && (
          <div className="flex items-center gap-3 mt-6 pt-4 border-t border-slate-800">
            <button
              onClick={() => navigate(`/scenarios?event_id=${selectedEventId}`)}
              className="text-xs px-3 py-2 rounded-lg bg-brand-600 hover:bg-brand-500 text-white transition-colors"
            >
              {t('theories.startScenario')}
            </button>
            <button
              onClick={() => navigate(`/analogies?event_id=${selectedEventId}`)}
              className="text-xs px-3 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 border border-slate-700 transition-colors"
            >
              {t('theories.historicalAnalogies')}
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
