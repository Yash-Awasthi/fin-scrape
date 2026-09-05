import { useEffect, useState, useCallback, useMemo, useRef } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import Fuse from 'fuse.js'
import { useVirtualizer } from '@tanstack/react-virtual'
import { eventApi, pipelineApi } from '../services/api'
import type { AbstractIRGEvent } from '../types'
import { EVENT_TYPE_LABELS, CRISIS_STAGE_LABELS, EVENT_TYPE_COLORS } from '../types'
import { useAppStore } from '../store'
import { toast } from '../store/toast'
import { SimplePieChart, SimpleBarChart } from '../components/Charts'
import LoadingSpinner from '../components/LoadingSpinner'
import ErrorState from '../components/ErrorState'
import EmptyState from '../components/EmptyState'

const STAGE_COLORS: Record<string, string> = {
  latent: 'text-slate-400 bg-slate-800',
  emergence: 'text-blue-400 bg-blue-900/40',
  escalation: 'text-amber-400 bg-amber-900/40',
  crisis: 'text-red-400 bg-red-900/40',
  de_escalation: 'text-emerald-400 bg-emerald-900/40',
  resolution: 'text-teal-400 bg-teal-900/40',
  post_crisis: 'text-slate-400 bg-slate-800',
}

function VirtualEventList({
  events,
  selectedId,
  onSelect,
}: {
  events: AbstractIRGEvent[]
  selectedId: string | null
  onSelect: (ev: AbstractIRGEvent) => void
}) {
  const parentRef = useRef<HTMLDivElement>(null)

  const virtualizer = useVirtualizer({
    count: events.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 88,
    overscan: 5,
  })

  return (
    <div ref={parentRef} className="h-full overflow-y-auto">
      <ul
        style={{
          height: `${virtualizer.getTotalSize()}px`,
          width: '100%',
          position: 'relative',
        }}
      >
        {virtualizer.getVirtualItems().map((virtualItem) => {
          const ev = events[virtualItem.index]
          return (
            <li
              key={virtualItem.key}
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                width: '100%',
                height: `${virtualItem.size}px`,
                transform: `translateY(${virtualItem.start}px)`,
              }}
            >
              <button
                onClick={() => onSelect(ev)}
                className={`w-full text-left px-5 py-4 hover:bg-surface-900/60 transition-colors ${
                  selectedId === ev.event_id ? 'bg-surface-900 border-l-2 border-blue-500' : ''
                }`}
              >
                <div className="text-sm font-medium text-slate-200 leading-snug">{ev.event_title}</div>
                <div className="flex items-center gap-2 mt-2 flex-wrap">
                  <span
                    className="text-[10px] px-1.5 py-0.5 rounded font-medium"
                    style={{
                      backgroundColor: EVENT_TYPE_COLORS[ev.event_type] + '20',
                      color: EVENT_TYPE_COLORS[ev.event_type],
                      border: `1px solid ${EVENT_TYPE_COLORS[ev.event_type]}40`,
                    }}
                  >
                    {EVENT_TYPE_LABELS[ev.event_type]}
                  </span>
                  <span className={`text-[10px] px-1.5 py-0.5 rounded ${STAGE_COLORS[ev.stage_of_crisis] ?? 'text-slate-500 bg-slate-800'}`}>
                    {CRISIS_STAGE_LABELS[ev.stage_of_crisis]}
                  </span>
                </div>
                <div className="flex items-center gap-1.5 mt-1.5">
                  <div className="flex-1 h-1 bg-slate-800 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-blue-500 rounded-full"
                      style={{ width: `${ev.event_confidence * 100}%` }}
                    />
                  </div>
                  <span className="text-[10px] text-slate-600">{Math.round(ev.event_confidence * 100)}%</span>
                </div>
              </button>
            </li>
          )
        })}
      </ul>
    </div>
  )
}

export default function EventsPage() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const initialEventId = searchParams.get('event_id')

  // --- 全局store ---
  const store = useAppStore()
  const { events: storeEvents, eventsLoading: storeEventsLoading, selectedEventId: storeSelectedId, setSelectedEvent: setStoreSelectedEvent, fetchEvents } = store

  // 本地 UI 状态（detail panel）
  const [selectedId, setSelectedId] = useState<string | null>(storeSelectedId)
  const [detail, setDetail] = useState<AbstractIRGEvent | null>(null)
  const [detailLoading, setDetailLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const scrollRef = useRef<HTMLDivElement>(null)

  const fuse = useMemo(() => new Fuse(storeEvents, {
    keys: ['event_title', 'event_type', 'region', 'key_actors'],
    threshold: 0.4,
    includeScore: true,
  }), [storeEvents])

  const filteredEvents = useMemo(() => {
    if (!searchQuery.trim()) return storeEvents
    return fuse.search(searchQuery).map(r => r.item)
  }, [searchQuery, fuse, storeEvents])

  // 若 store 中无数据，主动拉取
  useEffect(() => {
    if (storeEvents.length === 0 && !storeEventsLoading) {
      fetchEvents().catch(e => setError(e instanceof Error ? e.message : t('common.error')))
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // store 就绪后，若本地无选中事件则自动选第一个或URL指定的
  useEffect(() => {
    if (!selectedId && storeEvents.length > 0) {
      const target = initialEventId
        ? storeEvents.find(e => e.event_id === initialEventId)
        : storeEvents[0]
      if (target) handleSelect(target)
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [storeEvents])

  const handleSelect = useCallback(async (ev: AbstractIRGEvent) => {
    setSelectedId(ev.event_id)
    setStoreSelectedEvent(ev.event_id)
    setSearchParams({ event_id: ev.event_id }, { replace: true })
    setDetailLoading(true)
    try {
      const res = await eventApi.get(ev.event_id)
      setDetail(res.data)
    } catch {
      setDetail(ev)
    } finally {
      setDetailLoading(false)
    }
  }, [setStoreSelectedEvent])

  if (storeEventsLoading && storeEvents.length === 0) {
    return (
      <div className="min-h-screen bg-surface-950 flex items-center justify-center">
        <LoadingSpinner message={t('events.loading')} />
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-surface-950 flex items-center justify-center">
        <ErrorState message={error} onRetry={() => { setError(null); fetchEvents(); }} />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-surface-950 text-slate-100 flex flex-col">
      {/* 顶部 */}
      <div className="px-6 py-5 border-b border-slate-800 shrink-0">
        <h1 className="text-xl font-bold text-slate-100">{t('events.title')}</h1>
        <p className="text-slate-500 text-xs mt-0.5">
          {t('events.total', { count: storeEvents.length })}
          {searchQuery && ` · ${t('events.matched', { count: filteredEvents.length })}`}
        </p>
      </div>

      <div className="flex flex-1 min-h-0">
        {/* 左侧：事件列表 */}
        <div className="w-80 border-r border-slate-800 flex flex-col min-h-0 shrink-0">
          {/* 搜索框 */}
          <div className="px-3 py-2 border-b border-slate-800/60">
            <input
              type="text"
              placeholder={t('events.search')}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-surface-800 border border-slate-700/50 rounded-md px-3 py-1.5 text-sm text-slate-200 placeholder:text-slate-600 focus:outline-none focus:ring-1 focus:ring-brand-500/50"
            />
          </div>
          {filteredEvents.length === 0 ? (
            <div className="flex-1 flex items-center justify-center text-slate-600 text-sm">
              <EmptyState icon="📋" title={t('events.noData')} />
            </div>
          ) : (
              <div ref={scrollRef} className="flex-1 overflow-y-auto" id="event-list-scroll">
                <VirtualEventList
                  events={filteredEvents}
                  selectedId={selectedId}
                  onSelect={handleSelect}
                />
              </div>
          )}
        </div>

        {/* 右侧：事件详情 */}
        <div className="flex-1 overflow-y-auto p-6 min-w-0">
          {detailLoading ? (
            <div className="flex items-center justify-center h-40">
              <LoadingSpinner size="sm" />
            </div>
          ) : !detail ? (
            <div className="flex flex-col items-center justify-center h-full text-slate-600">
              {storeEvents.length > 0 && (
                <div className="w-full max-w-lg space-y-6 mb-6">
                  <div>
                    <div className="text-xs text-slate-500 mb-2 uppercase tracking-wide">{t('events.typeDistribution')}</div>
                    <SimplePieChart
                      data={Object.entries(
                        storeEvents.reduce<Record<string, number>>((acc, e) => {
                          const label = EVENT_TYPE_LABELS[e.event_type] || e.event_type
                          acc[label] = (acc[label] || 0) + 1
                          return acc
                        }, {})
                      ).map(([name, value]) => ({
                        name, value,
                        color: (EVENT_TYPE_COLORS as Record<string, string>)[Object.entries(EVENT_TYPE_LABELS).find(([, v]) => v === name)?.[0] || ''] || '#6366f1',
                      }))}
                      height={200}
                      innerRadius={40}
                    />
                  </div>
                  <div>
                    <div className="text-xs text-slate-500 mb-2 uppercase tracking-wide">{t('events.regionDistribution')}</div>
                    <SimpleBarChart
                      data={Object.entries(
                        storeEvents.reduce<Record<string, number>>((acc, e) => {
                          const r = e.region || 'Unknown'
                          acc[r] = (acc[r] || 0) + 1
                          return acc
                        }, {})
                      ).sort((a, b) => b[1] - a[1]).slice(0, 8).map(([name, value]) => ({ name, value }))}
                      height={160}
                    />
                  </div>
                </div>
              )}
              <div className="text-center">
                <div className="text-sm">{t('events.selectEvent')}</div>
              </div>
            </div>
          ) : (
            <div className="max-w-3xl space-y-6">
              {/* 标题区 */}
              <div>
                <div className="flex items-start gap-3 flex-wrap">
                  <h2 className="text-2xl font-bold text-slate-100 flex-1">{detail.event_title}</h2>
                </div>
                <div className="flex items-center gap-2 mt-3 flex-wrap">
                  <span
                    className="text-xs px-2 py-1 rounded font-medium"
                    style={{
                      backgroundColor: EVENT_TYPE_COLORS[detail.event_type] + '25',
                      color: EVENT_TYPE_COLORS[detail.event_type],
                      border: `1px solid ${EVENT_TYPE_COLORS[detail.event_type]}50`,
                    }}
                  >
                    {EVENT_TYPE_LABELS[detail.event_type]}
                  </span>
                  <span className={`text-xs px-2 py-1 rounded ${STAGE_COLORS[detail.stage_of_crisis]}`}>
                    {CRISIS_STAGE_LABELS[detail.stage_of_crisis]}
                  </span>
                  <span className="text-xs text-slate-500">{detail.region}</span>
                  <span className="text-xs text-slate-600">{t('events.confidence')} {Math.round(detail.event_confidence * 100)}%</span>
                  {detail.is_fallback && (
                    <span
                      className="text-xs px-2 py-0.5 rounded bg-amber-900/30 text-amber-400 border border-amber-700/40"
                      title={t('events.ruleFallbackDetail', 'Claude API 调用失败，此事件由规则引擎回退生成。数据字段不完整，仅供参考。')}
                    >
                      ⚠ {t('events.fallback')}
                    </span>
                  )}
                </div>
              </div>

              {/* 行为主体表格 */}
              {detail.key_actors.length > 0 && (
                <div className="bg-surface-900 border border-slate-700 rounded-xl overflow-hidden">
                  <div className="px-4 py-2.5 border-b border-slate-700 text-xs font-semibold text-slate-500 uppercase tracking-widest">
                    {t('events.keyActors')}
                  </div>
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-slate-800">
                        <th className="text-left px-4 py-2 text-xs text-slate-600">{t('events.actor')}</th>
                        <th className="text-left px-4 py-2 text-xs text-slate-600">{t('events.role')}</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/50">
                      {detail.key_actors.map(actor => (
                        <tr key={actor}>
                          <td className="px-4 py-2.5 text-sm text-slate-300 font-medium">{actor}</td>
                          <td className="px-4 py-2.5 text-sm text-slate-500">
                            {detail.actor_roles[actor] ?? t('common.none')}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {/* 战略维度 */}
              {detail.strategic_dimensions.length > 0 && (
                <div>
                  <div className="text-xs font-semibold text-slate-500 uppercase tracking-widest mb-2">{t('events.strategicDimensions')}</div>
                  <div className="flex flex-wrap gap-2">
                    {detail.strategic_dimensions.map(d => (
                      <span key={d} className="text-xs bg-purple-900/30 text-purple-400 border border-purple-700/40 px-2 py-1 rounded">
                        {d}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* 驱动力 */}
              {detail.driving_forces.length > 0 && (
                <div>
                  <div className="text-xs font-semibold text-slate-500 uppercase tracking-widest mb-2">{t('events.drivingForces')}</div>
                  <ul className="space-y-1.5">
                    {detail.driving_forces.map((f, i) => (
                      <li key={i} className="flex items-start gap-2 text-sm text-slate-400">
                        <span className="text-blue-500 mt-0.5 shrink-0">▸</span>
                        {f}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* 约束条件 */}
              {detail.constraints.length > 0 && (
                <div>
                  <div className="text-xs font-semibold text-slate-500 uppercase tracking-widest mb-2">{t('events.constraints')}</div>
                  <ul className="space-y-1.5">
                    {detail.constraints.map((c, i) => (
                      <li key={i} className="flex items-start gap-2 text-sm text-slate-400">
                        <span className="text-amber-500 mt-0.5 shrink-0">⊘</span>
                        {c}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* 即时触发器 */}
              {detail.immediate_triggers.length > 0 && (
                <div>
                  <div className="text-xs font-semibold text-slate-500 uppercase tracking-widest mb-2">{t('events.immediateTriggers')}</div>
                  <ul className="space-y-1.5">
                    {detail.immediate_triggers.map((t, i) => (
                      <li key={i} className="flex items-start gap-2 text-sm text-slate-400">
                        <span className="text-red-500 mt-0.5 shrink-0">⚡</span>
                        {t}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* 当前力量对比 */}
              {detail.current_balance && (
                <div className="bg-surface-900 border border-slate-700 rounded-xl p-4">
                  <div className="text-xs font-semibold text-slate-500 uppercase tracking-widest mb-2">{t('events.currentBalance')}</div>
                  <p className="text-sm text-slate-400 leading-relaxed">{detail.current_balance}</p>
                </div>
              )}

              {/* 风险 & 机会 */}
              <div className="grid grid-cols-2 gap-4">
                {detail.major_risks.length > 0 && (
                  <div className="bg-red-900/10 border border-red-800/40 rounded-xl p-4">
                    <div className="text-xs font-semibold text-red-500 uppercase tracking-widest mb-2">{t('events.majorRisks')}</div>
                    <div className="flex flex-wrap gap-1.5">
                      {detail.major_risks.map((r, i) => (
                        <span key={i} className="text-xs bg-red-900/40 text-red-400 border border-red-700/40 px-2 py-0.5 rounded">
                          {r}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
                {detail.current_opportunities.length > 0 && (
                  <div className="bg-emerald-900/10 border border-emerald-800/40 rounded-xl p-4">
                    <div className="text-xs font-semibold text-emerald-500 uppercase tracking-widest mb-2">{t('events.currentOpportunities')}</div>
                    <div className="flex flex-wrap gap-1.5">
                      {detail.current_opportunities.map((o, i) => (
                        <span key={i} className="text-xs bg-emerald-900/40 text-emerald-400 border border-emerald-700/40 px-2 py-0.5 rounded">
                          {o}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* 操作按钮 */}
              <div className="flex items-center gap-3 pt-2">
                <button
                  onClick={() => navigate(`/theories?event_id=${detail.event_id}`)}
                  className="px-4 py-2 text-sm rounded-lg bg-purple-600/20 hover:bg-purple-600/30 text-purple-400 border border-purple-700/50 transition-colors"
                >
                  {t('events.theoryAnalysis')}
                </button>
                <button
                  onClick={() => navigate(`/scenarios?event_id=${detail.event_id}`)}
                  className="px-4 py-2 text-sm rounded-lg bg-blue-600 hover:bg-blue-500 text-white transition-colors shadow-lg shadow-blue-900/40"
                >
                  {t('events.startSimulation')}
                </button>
                <button
                  onClick={() => navigate(`/analogies?event_id=${detail.event_id}`)}
                  className="text-xs px-3 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 border border-slate-700 transition-colors"
                >
                  {t('events.historicalAnalogy')}
                </button>
                <button
                  onClick={async () => {
                    try {
                      toast.warn(t('events.reSimulating'))
                      await pipelineApi.runAnalysis(detail.event_id)
                      toast.success(t('events.simulateComplete'))
                      navigate(`/scenarios?event_id=${detail.event_id}`)
                    } catch (e) {
                      toast.error(e instanceof Error ? e.message : t('events.simulateFailed'))
                    }
                  }}
                  className="text-xs px-3 py-2 rounded-lg bg-amber-600/20 hover:bg-amber-600/30 text-amber-400 border border-amber-700/50 transition-colors"
                >
                  {t('events.reSimulate')}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
