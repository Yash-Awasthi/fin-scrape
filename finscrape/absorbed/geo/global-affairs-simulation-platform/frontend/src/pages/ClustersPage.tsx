import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { clusterApi, newsApi } from '../services/api'
import type { NewsCluster, RawNews } from '../types'
import LoadingSpinner from '../components/LoadingSpinner'
import ErrorState from '../components/ErrorState'
import EmptyState from '../components/EmptyState'

export default function ClustersPage() {
  const { t, i18n } = useTranslation()
  const navigate = useNavigate()
  const [clusters, setClusters] = useState<NewsCluster[]>([])
  const [news, setNews] = useState<RawNews[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const [clusterDetail, setClusterDetail] = useState<Record<string, NewsCluster>>({})
  const [detailLoading, setDetailLoading] = useState<Record<string, boolean>>({})
  const [highlightedNewsIds, setHighlightedNewsIds] = useState<Set<string>>(new Set())
  const newsListRef = useRef<HTMLUListElement>(null)

  useEffect(() => {
    Promise.all([clusterApi.list(), newsApi.list({ limit: 100 })])
      .then(([cRes, nRes]) => {
        setClusters(cRes.data.items)
        setNews(nRes.data.items)
      })
      .catch(e => setError(e instanceof Error ? e.message : t('common.error')))
      .finally(() => setLoading(false))
  }, [t])

  const handleExpandCluster = async (cluster: NewsCluster) => {
    if (expandedId === cluster.cluster_id) {
      setExpandedId(null)
      setHighlightedNewsIds(new Set())
      return
    }
    setExpandedId(cluster.cluster_id)
    const ids = new Set(cluster.related_news_ids)
    setHighlightedNewsIds(ids)
    setTimeout(() => {
      const firstEl = newsListRef.current?.querySelector('[data-highlighted="true"]')
      firstEl?.scrollIntoView({ behavior: 'smooth', block: 'center' })
    }, 100)
    if (!clusterDetail[cluster.cluster_id]) {
      setDetailLoading(prev => ({ ...prev, [cluster.cluster_id]: true }))
      try {
        const res = await clusterApi.get(cluster.cluster_id)
        setClusterDetail(prev => ({ ...prev, [cluster.cluster_id]: res.data }))
        const detailIds = new Set(res.data.related_news_ids)
        setHighlightedNewsIds(detailIds)
      } catch {
        // 使用已有数据
      } finally {
        setDetailLoading(prev => ({ ...prev, [cluster.cluster_id]: false }))
      }
    } else {
      const detailIds = new Set(clusterDetail[cluster.cluster_id].related_news_ids)
      setHighlightedNewsIds(detailIds)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-surface-950 flex items-center justify-center">
        <LoadingSpinner message={t('common.loading')} />
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-surface-950 flex items-center justify-center">
        <ErrorState
          title={t('common.error')}
          message={error}
          onRetry={() => { setLoading(true); setError(null); window.location.reload() }}
        />
      </div>
    )
  }

  const clusterNewsMap = (cid: string, detail?: NewsCluster) => {
    const d = detail ?? clusters.find(c => c.cluster_id === cid)
    if (!d) return []
    const ids = new Set(d.related_news_ids)
    return news.filter(n => ids.has(n.news_id))
  }

  return (
    <div className="min-h-screen bg-surface-950 text-slate-100 flex flex-col">
      <div className="px-6 py-5 border-b border-slate-800 flex items-center justify-between shrink-0">
        <div>
          <h1 className="text-xl font-bold text-slate-100">{t('nav.clusters')}</h1>
          <p className="text-slate-500 text-xs mt-0.5">{t('pipeline.desc')}</p>
        </div>
        <div className="flex items-center gap-4 text-xs text-slate-500">
          <span>{t('pipeline.result.news')} <span className="text-slate-300 font-medium">{news.length}</span> {t('pipeline.records', { count: news.length })}</span>
          <span>{t('pipeline.result.clusters')} <span className="text-slate-300 font-medium">{clusters.length}</span> {t('common.total', { count: clusters.length })}</span>
        </div>
      </div>

      <div className="flex flex-1 min-h-0">
        <div className="w-72 border-r border-slate-800 flex flex-col min-h-0">
          <div className="px-4 py-3 border-b border-slate-800/50 text-xs font-semibold text-slate-500 uppercase tracking-widest shrink-0">
            {t('pipeline.result.news')}
          </div>
          {news.length === 0 ? (
            <div className="flex-1 flex items-center justify-center">
              <EmptyState title={t('common.notAvailable')} />
            </div>
          ) : (
            <ul className="flex-1 overflow-y-auto divide-y divide-slate-800/40" ref={newsListRef}>
              {news.map(item => {
                const isHighlighted = highlightedNewsIds.has(item.news_id)
                return (
                <li
                  key={item.news_id}
                  data-highlighted={isHighlighted || undefined}
                  className={`px-4 py-3 hover:bg-surface-900/50 transition-all ${
                    isHighlighted ? 'bg-blue-900/15 border-l-2 border-blue-500' : ''
                  }`}
                >
                  {item.url ? (
                    <a
                      href={item.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-xs text-slate-300 leading-relaxed line-clamp-2 hover:text-blue-400 transition-colors cursor-pointer"
                    >
                      {item.title}
                    </a>
                  ) : (
                    <div className="text-xs text-slate-300 leading-relaxed line-clamp-2">{item.title}</div>
                  )}
                  <div className="flex items-center gap-2 mt-1.5">
                    <span className="text-[10px] text-slate-600">{item.source_name}</span>
                    {item.published_at && (
                      <span className="text-[10px] text-slate-700">
                        {new Date(item.published_at).toLocaleDateString(i18n.language === 'zh' ? 'zh-CN' : 'en-US')}
                      </span>
                    )}
                    {item.cluster_id ? (
                      <span className="text-[10px] text-blue-500">{t('events.keyActors')}</span>
                    ) : (
                      <span className="text-[10px] text-slate-700">{t('common.none')}</span>
                    )}
                    {item.url && (
                      <a
                        href={item.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-[10px] text-slate-700 hover:text-blue-400 transition-colors ml-auto"
                        title={t('common.view')}
                      >
                        ↗
                      </a>
                    )}
                  </div>
                </li>
              )})}
            </ul>
          )}
        </div>

        <div className="flex-1 flex flex-col min-h-0 min-w-0">
          <div className="px-5 py-3 border-b border-slate-800/50 text-xs font-semibold text-slate-500 uppercase tracking-widest shrink-0">
            {t('nav.clusters')}
          </div>
          {clusters.length === 0 ? (
            <div className="flex-1 flex items-center justify-center">
              <EmptyState
                icon="📦"
                title={t('clusters.noClusters')}
                description={t('pipeline.history.empty')}
              />
            </div>
          ) : (
            <div className="flex-1 overflow-y-auto p-4 space-y-3">
              {clusters.map(cluster => {
                const isExpanded = expandedId === cluster.cluster_id
                const detail = clusterDetail[cluster.cluster_id]
                const clusterNews = clusterNewsMap(cluster.cluster_id, detail)

                return (
                  <div
                    key={cluster.cluster_id}
                    className={`bg-surface-900 border rounded-xl overflow-hidden transition-all ${
                      isExpanded ? 'border-blue-600/50' : 'border-slate-700 hover:border-slate-600'
                    }`}
                  >
                    <button
                      onClick={() => handleExpandCluster(cluster)}
                      className="w-full text-left px-5 py-4"
                      aria-expanded={isExpanded}
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div className="flex-1 min-w-0">
                          <div className="font-medium text-slate-200 text-sm leading-snug">{cluster.cluster_title}</div>
                          <div className="flex flex-wrap items-center gap-x-3 gap-y-1 mt-2">
                            <span className="text-xs text-slate-500">{t('clusters.newsCount')} {cluster.news_count}</span>
                            {cluster.primary_issue && (
                              <span className="text-xs text-slate-500">{t('clusters.primaryIssue')}: {cluster.primary_issue}</span>
                            )}
                            <span className="text-xs text-slate-500">
                              {t('events.confidence')} {Math.round(cluster.cluster_confidence * 100)}%
                            </span>
                            {cluster.event_id && (
                              <span className="text-xs bg-emerald-900/50 text-emerald-400 border border-emerald-700/50 px-1.5 py-0.5 rounded">
                                {t('events.keyActors')}
                              </span>
                            )}
                          </div>
                          {cluster.key_actors.length > 0 && (
                            <div className="flex flex-wrap gap-1 mt-2">
                              {cluster.key_actors.slice(0, 4).map(actor => (
                                <span key={actor} className="text-[10px] bg-slate-800 text-slate-400 px-1.5 py-0.5 rounded">
                                  {actor}
                                </span>
                              ))}
                              {cluster.key_actors.length > 4 && (
                                <span className="text-[10px] text-slate-600">+{cluster.key_actors.length - 4}</span>
                              )}
                            </div>
                          )}
                          <div className="flex flex-wrap gap-1 mt-2">
                            {cluster.escalation_signals.slice(0, 2).map(s => (
                              <span key={s} className="text-[10px] bg-red-900/30 text-red-400 border border-red-800/40 px-1.5 py-0.5 rounded">
                                ↑ {s}
                              </span>
                            ))}
                            {cluster.deescalation_signals.slice(0, 2).map(s => (
                              <span key={s} className="text-[10px] bg-emerald-900/30 text-emerald-400 border border-emerald-800/40 px-1.5 py-0.5 rounded">
                                ↓ {s}
                              </span>
                            ))}
                          </div>
                        </div>
                        <div className="flex flex-col items-end gap-2 shrink-0">
                          <div className="w-16 h-1.5 bg-slate-800 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-blue-500 rounded-full"
                              style={{ width: `${cluster.cluster_confidence * 100}%` }}
                            />
                          </div>
                          <span className="text-slate-600 text-xs">{isExpanded ? '▲' : '▼'}</span>
                        </div>
                      </div>
                    </button>

                    {isExpanded && (
                      <div className="border-t border-slate-700/50 px-5 py-4">
                        {detailLoading[cluster.cluster_id] ? (
                          <LoadingSpinner message={t('common.loading')} size="sm" />
                        ) : (
                          <>
                            {cluster.evidence_summary && (
                              <p className="text-xs text-slate-400 leading-relaxed mb-3">{cluster.evidence_summary}</p>
                            )}
                            <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">
                              {t('common.view')} ({clusterNews.length})
                            </div>
                            <div className="space-y-2">
                              {clusterNews.length === 0 ? (
                                <div className="text-xs text-slate-600">{t('common.notAvailable')}</div>
                              ) : (
                                clusterNews.map(n => (
                                  <div key={n.news_id} className="bg-slate-800/50 rounded-lg px-3 py-2">
                                    {n.url ? (
                                      <a
                                        href={n.url}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="text-xs text-slate-300 leading-relaxed hover:text-blue-400 transition-colors"
                                      >
                                        {n.title} <span className="text-slate-600">↗</span>
                                      </a>
                                    ) : (
                                      <div className="text-xs text-slate-300 leading-relaxed">{n.title}</div>
                                    )}
                                    <div className="flex items-center gap-2 mt-1">
                                      <span className="text-[10px] text-slate-600">{n.source_name}</span>
                                      {n.published_at && (
                                        <span className="text-[10px] text-slate-700">
                                          {new Date(n.published_at).toLocaleDateString(i18n.language === 'zh' ? 'zh-CN' : 'en-US')}
                                        </span>
                                      )}
                                    </div>
                                  </div>
                                ))
                              )}
                            </div>
                            {cluster.event_id && (
                              <div className="mt-3 flex items-center gap-2 text-xs">
                                <span className="text-slate-600">{t('nav.clusters')}</span>
                                <span className="text-slate-700">→</span>
                                <span className="text-emerald-400 font-medium">{t('nav.events')} #{cluster.event_id.slice(0, 8)}</span>
                                <button
                                  onClick={() => navigate(`/events?event_id=${cluster.event_id}`)}
                                  className="text-xs px-3 py-1.5 rounded-lg bg-brand-600 hover:bg-brand-500 text-white transition-colors"
                                >
                                  {t('common.view')}
                                </button>
                              </div>
                            )}
                          </>
                        )}
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
