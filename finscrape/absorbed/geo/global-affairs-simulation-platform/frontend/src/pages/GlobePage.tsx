﻿﻿﻿﻿﻿import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Globe, RefreshCw, AlertCircle, MapPin, Loader2, X,
  ExternalLink, Layers, ChevronRight,
} from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { eventApi, getErrorUserMessage } from '../services/api'
import type { AbstractIRGEvent, GlobePoint, RelationshipType } from '../types'
import { toast } from '../store/toast'
import { useAppStore } from '../store'
import Globe2DFallback from '../components/Globe2DFallback'
import { isWebGLAvailable } from '../utils/webgl'

const EARTH_TEXTURE_DARK   = '/earth-dark.jpg'
const EARTH_TEXTURE_MARBLE = '/earth-blue-marble.jpg'
const EARTH_TEXTURE_NIGHT  = '/earth-night.jpg'
const BUMP_MAP_URL         = '/earth-topology.png'
const NIGHT_SKY_URL        = '/night-sky.png'
const COUNTRIES_GEOJSON    = '/ne_110m_admin_0_countries.geojson'

type GlobeInstance = any // eslint-disable-line @typescript-eslint/no-explicit-any
type MapStyle = 'dark' | 'marble' | 'night'
type RelationMode = 'none' | 'shared_actor' | 'same_region' | 'causal_chain' | 'escalation_cascade' | 'semantic_similar' | 'actor_conflict' | 'all'

// --- 危机阶段配色 ---
const STAGE_COLOR: Record<string, string> = {
  latent:        '#3b82f6',
  emergence:     '#eab308',
  escalation:    '#f97316',
  crisis:        '#ef4444',
  de_escalation: '#22c55e',
  resolution:    '#06b6d4',
  post_crisis:   '#8b5cf6',
}
const TYPE_ICON: Record<string, string> = {
  military_escalation:                    '⚔',
  diplomatic_negotiation:                 '🤝',
  economic_coercion:                      '💰',
  alliance_realignment:                   '🔗',
  energy_shipping_risk:                   '⛽',
  domestic_political_spillover:           '🏛',
  information_psychological_operations:   '📡',
}

// 弧线颜色
const REL_COLOR: Record<RelationshipType, string> = {
  shared_actor:       'rgba(139,92,246,0.55)',
  same_region:        'rgba(56,189,248,0.4)',
  causal_chain:       'rgba(251,146,60,0.55)',
  escalation_cascade: 'rgba(239,68,68,0.55)',
  semantic_similar:   'rgba(34,197,94,0.4)',
  actor_conflict:     'rgba(244,63,94,0.6)',
}

const REL_LABEL_KEY: Record<RelationshipType, string> = {
  shared_actor:       'globe.relSharedActor',
  same_region:        'globe.relSameRegion',
  causal_chain:       'globe.relCausalChain',
  escalation_cascade: 'globe.relEscalationCascade',
  semantic_similar:   'globe.relSemanticSimilar',
  actor_conflict:     'globe.relActorConflict',
}

function sc(stage?: string) {
  return STAGE_COLOR[stage ?? ''] ?? '#94a3b8'
}
function pointSize(p: GlobePoint) {
  const c = p.event_confidence ?? 0.5
  const bonus = p.scenario_summary?.has_scenarios
    ? Math.min((p.scenario_summary.script_count ?? 1) * 0.04, 0.2)
    : 0
  return Math.max(0.22, 0.28 + c * 0.32 + bonus)
}
function esc(s: string) {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;')
}
function debounce<T extends (...a: any[]) => void>(fn: T, ms: number): T { // eslint-disable-line
  let t: ReturnType<typeof setTimeout>
  return ((...a: any[]) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms) }) as T // eslint-disable-line
}

export default function GlobePage() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const mountRef  = useRef<HTMLDivElement>(null)
  const globeRef  = useRef<GlobeInstance>(null)
  const abortRef  = useRef<AbortController | null>(null)
  // 用 ref 跟踪选中 ID，避免 pointColor 函数更新触发全量重建
  const selectedIdRef = useRef<string | null>(null)
  const tRef = useRef(t)
  tRef.current = t

  const points          = useAppStore((s) => s.globePoints)
  const relationships   = useAppStore((s) => s.globeRelationships)
  const globeLoading    = useAppStore((s) => s.globeLoading)
  const globeNoCoordsCount = useAppStore((s) => s.globeNoCoordsCount)
  const fetchGlobePoints = useAppStore((s) => s.fetchGlobePoints)

  const [dataLoading, setDataLoading] = useState(points.length === 0)
  const [error,       setError]       = useState<string | null>(null)
  const [globeReady,  setGlobeReady]  = useState(false)
  const [globeError,  setGlobeError]  = useState<string | null>(null)
  const [mapStyle,    setMapStyle]    = useState<MapStyle>('marble')
  const [relationMode, setRelationMode] = useState<RelationMode>('shared_actor')
  const [countriesGeo, setCountriesGeo] = useState<any[] | null>(null) // eslint-disable-line

  // 详情面板
  const [selected,      setSelected]     = useState<GlobePoint | null>(null)
  const [detail,        setDetail]       = useState<AbstractIRGEvent | null>(null)
  const [detailLoading, setDetailLoading] = useState(false)

  // --- 数据加载 ---
  const loadPoints = useCallback(() => {
    setDataLoading(true); setError(null)
    fetchGlobePoints()
      .catch((e) => { const m = getErrorUserMessage(e); setError(m); toast.error(m, { dedupeKey: 'globe' }) })
      .finally(() => setDataLoading(false))
  }, [fetchGlobePoints])

  useEffect(() => {
    if (points.length === 0 && !globeLoading) loadPoints()
    else setDataLoading(false)
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    fetch(COUNTRIES_GEOJSON).then(r => r.json())
      .then(d => setCountriesGeo((d.features ?? []).filter((f: any) => f.properties?.ISO_A2 !== 'AQ'))) // eslint-disable-line
      .catch(() => {})
  }, [])

  // --- globe.gl初始化 ---
  useEffect(() => {
    if (!mountRef.current) return
    let globe: GlobeInstance = null
    let cancelled = false

    if (!isWebGLAvailable()) {
      setGlobeError(t('globe.webglNotSupported')); setGlobeReady(true); return
    }

    const tid = setTimeout(() => {
      if (!cancelled && !globeRef.current) {
        setGlobeError(t('common.error')); setGlobeReady(true)
      }
    }, 15000)

    import('globe.gl').then((mod) => {
      if (cancelled || !mountRef.current) return
      clearTimeout(tid)
      const GlobeGL = (mod.default ?? mod) as any // eslint-disable-line
      const el = mountRef.current
      try {
        const factory = typeof GlobeGL === 'function' ? GlobeGL : GlobeGL.default
        globe = factory({ animateIn: true })(el)
        globe
          .globeImageUrl(EARTH_TEXTURE_MARBLE)
          .bumpImageUrl(BUMP_MAP_URL)
          .backgroundImageUrl(NIGHT_SKY_URL)
          .showGraticules(true)
          .atmosphereColor('#1e40af')
          .atmosphereAltitude(0.15)
          .width(el.clientWidth)
          .height(el.clientHeight)

        const canvas = el.querySelector('canvas')
        if (canvas) {
          canvas.addEventListener('webglcontextlost', (e: Event) => {
            e.preventDefault(); setGlobeError(t('common.error'))
          })
        }

        globeRef.current = globe
        setGlobeReady(true)
      } catch (err) {
        if (!cancelled) {
          setGlobeError(`${t('common.error')}: ${err instanceof Error ? err.message : err}`)
          setGlobeReady(true)
        }
      }
    }).catch((e) => {
      clearTimeout(tid)
      if (!cancelled) { setGlobeError(`${t('common.error')}: ${e?.message ?? e}`); setGlobeReady(true) }
    })

    const resize = debounce(() => {
      if (globeRef.current && mountRef.current) {
        globeRef.current.width(mountRef.current.clientWidth).height(mountRef.current.clientHeight)
      }
    }, 150)
    const ro = new ResizeObserver(resize)
    if (mountRef.current) ro.observe(mountRef.current)

    return () => {
      cancelled = true; clearTimeout(tid); ro.disconnect()
      if (globe) {
        try {
          if (typeof globe._destructor === 'function') globe._destructor()
          const renderer = globe.renderer?.()
          if (renderer?.dispose) renderer.dispose()
        } catch {}
      }
      if (mountRef.current) mountRef.current.innerHTML = ''
      globeRef.current = null
    }
  }, [])

  // --- 地图纹理切换 ---
  useEffect(() => {
    if (!globeReady || !globeRef.current) return
    const url = mapStyle === 'marble' ? EARTH_TEXTURE_MARBLE
      : mapStyle === 'night' ? EARTH_TEXTURE_NIGHT : EARTH_TEXTURE_DARK
    globeRef.current.globeImageUrl(url)
  }, [globeReady, mapStyle])

  // --- 国家边界 ---
  useEffect(() => {
    if (!globeReady || !globeRef.current || !countriesGeo?.length) return
    globeRef.current
      .polygonsData(countriesGeo)
      .polygonGeoJsonGeometry((d: any) => d.geometry) // eslint-disable-line
      .polygonCapColor(() => 'rgba(0,0,0,0)')
      .polygonSideColor(() => 'rgba(0,0,0,0)')
      .polygonStrokeColor(() => 'rgba(148,163,184,0.2)')
      .polygonAltitude(0.001)
      .polygonCapCurvatureResolution(2)
  }, [globeReady, countriesGeo])

  // --- 点数据 ---
  useEffect(() => {
    if (!globeReady || !globeRef.current || !points.length) return

    const selectedId = selectedIdRef.current

    const data = points.map((p) => ({
      lat:    p.lat,
      lng:    p.lng,
      size:   pointSize(p),
      // 选中时高亮，其余半透明；无选中时全亮
      color:  selectedId && p.event_id !== selectedId ? sc(p.stage_of_crisis) + '55' : sc(p.stage_of_crisis),
      __p:    p,
    }))

    globeRef.current
      .pointsData(data)
      .pointColor('color')
      .pointRadius('size')
      .pointAltitude(0.008)
      .pointLabel((d: { __p: GlobePoint }) => {
        const p = d.__p
        const color = sc(p.stage_of_crisis)
        const label = tRef.current(`crisisStages.${p.stage_of_crisis ?? ''}`, p.stage_of_crisis ?? '')
        const icon  = TYPE_ICON[p.event_type ?? ''] ?? '📌'
        const actors = (p.key_actors ?? []).slice(0, 3).join('、') || '—'
        return `<div style="
          background:rgba(10,15,28,0.93);
          border:1px solid ${color}44;
          border-left:3px solid ${color};
          border-radius:6px;padding:7px 11px;
          font-size:12px;color:#e2e8f0;
          max-width:210px;line-height:1.5;
          pointer-events:none">
          <div style="font-weight:600;margin-bottom:3px">${icon} ${esc(p.event_title)}</div>
          <div style="display:flex;gap:6px;align-items:center;margin-bottom:3px">
            <span style="background:${color}22;color:${color};border-radius:3px;padding:0 5px;font-size:10px">${label}</span>
            <span style="color:#64748b;font-size:10px">${esc(p.region ?? '')}</span>
          </div>
          <div style="color:#94a3b8;font-size:10px">👥 ${esc(actors)}</div>
        </div>`
      })
      .onPointClick((d: { __p: GlobePoint }) => openDetail(d.__p))
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [globeReady, points])

  // --- 选中变化更新颜色 ---
  useEffect(() => {
    if (!globeReady || !globeRef.current) return
    const sid = selectedIdRef.current
    globeRef.current.pointColor((d: { __p: GlobePoint }) => {
      const p = d.__p; if (!p) return '#94a3b8'
      return sid && p.event_id !== sid ? sc(p.stage_of_crisis) + '55' : sc(p.stage_of_crisis)
    })
  }, [globeReady, selected])

  // --- 弧线 ---
  const arcsData = useMemo(() => {
    const coord = new Map(points.map((p) => [p.event_id, { lat: p.lat, lng: p.lng }]))
    const selectedId = selected?.event_id ?? null

    return relationships
      .filter((r) => {
        if (relationMode === 'none') return false
        if (relationMode !== 'all' && r.type !== relationMode) return false
        return true
      })
      .map((r) => {
        const a = coord.get(r.from); const b = coord.get(r.to)
        if (!a || !b) return null
        const isRelated = selectedId && (r.from === selectedId || r.to === selectedId)
        const baseColor = REL_COLOR[r.type as RelationshipType] ?? 'rgba(148,163,184,0.3)'
        // 选中时：相关弧线高亮，其余暗化
        const color = selectedId
          ? isRelated ? baseColor.replace(/[\d.]+\)$/, '0.85)') : baseColor.replace(/[\d.]+\)$/, '0.1)')
          : baseColor
        return { startLat: a.lat, startLng: a.lng, endLat: b.lat, endLng: b.lng, color, __type: r.type }
      })
      .filter((d): d is NonNullable<typeof d> => d !== null)
  }, [points, relationships, relationMode, selected])

  useEffect(() => {
    if (!globeReady || !globeRef.current) return
    globeRef.current
      .arcsData(arcsData)
      .arcColor('color')
      .arcDashLength(0.35)
      .arcDashGap(0.15)
      .arcDashAnimateTime(2500)
      .arcStroke(0.25)
  }, [globeReady, arcsData])

  // --- 打开详情 ---
  const openDetail = useCallback(async (p: GlobePoint) => {
    if (abortRef.current) abortRef.current.abort()
    const ctrl = new AbortController()
    abortRef.current = ctrl

    selectedIdRef.current = p.event_id
    setSelected(p)
    setDetail(null)
    setDetailLoading(true)

    if (globeRef.current) {
      globeRef.current.pointOfView({ lat: p.lat, lng: p.lng, altitude: 1.8 }, 700)
    }

    try {
      const res = await eventApi.get(p.event_id)
      if (!ctrl.signal.aborted) setDetail(res.data)
    } catch {}
    finally { if (!ctrl.signal.aborted) setDetailLoading(false) }
  }, [])

  const closeDetail = useCallback(() => {
    if (abortRef.current) abortRef.current.abort()
    selectedIdRef.current = null
    setSelected(null)
    setDetail(null)
  }, [])

  useEffect(() => () => { abortRef.current?.abort() }, [])

  // --- 关联事件列表 ---
  const relatedPoints = useMemo(() => {
    if (!selected || relationMode === 'none') return []
    const ids = new Set(
      relationships
        .filter((r) => (r.from === selected.event_id || r.to === selected.event_id) && (relationMode === 'all' || r.type === relationMode))
        .map((r) => r.from === selected.event_id ? r.to : r.from)
    )
    return points.filter((p) => ids.has(p.event_id)).slice(0, 6)
  }, [selected, relationships, points, relationMode])

  // --- 渲染 ---
  return (
    <div className="relative w-full h-full bg-slate-950 overflow-hidden">

      {/* --- 顶部控制栏 --- */}
      <header className="absolute top-0 left-0 right-0 z-20 px-4 py-2.5 flex items-center gap-3
        bg-gradient-to-b from-slate-950/90 to-transparent pointer-events-none">

        {/* 标题 */}
        <div className="pointer-events-auto flex items-center gap-2 shrink-0">
          <Globe size={16} className="text-brand-500" />
          <div>
            <div className="text-sm font-semibold text-white leading-tight">{t('globe.title')}</div>
            <div className="text-[10px] text-slate-500">
              {points.length} {t('globe.events')}{globeNoCoordsCount > 0 ? ` · ${globeNoCoordsCount} ${t('globe.noCoords')}` : ''}
            </div>
          </div>
        </div>

        <div className="flex-1" />

        {/* 关系模式 */}
        <div className="pointer-events-auto flex items-center gap-0.5 bg-slate-900/80
          border border-slate-700/50 rounded-lg p-1 overflow-x-auto">
          {([
            ['none',               '×',   ''],
            ['shared_actor',       t('globe.relSharedActor'), t('analogies.caseTypes.shared_actor', 'Shared Actor')],
            ['same_region',        t('globe.relSameRegion'), t('globe.relSameRegion')],
            ['causal_chain',       t('globe.relCausalChain'), t('globe.relCausalChain')],
            ['escalation_cascade', t('directions.escalation'), t('globe.relEscalationCascade')],
            ['semantic_similar',   t('globe.relSemanticSimilar'), t('globe.relSemanticSimilar')],
            ['actor_conflict',     t('globe.relActorConflict'), t('globe.relActorConflict')],
            ['all',                t('common.all'), t('common.all')],
          ] as const).map(([mode, label, tip]) => (
            <button key={mode} title={tip}
              onClick={() => setRelationMode(mode as RelationMode)}
              className={`px-2 py-1 rounded text-[11px] whitespace-nowrap transition-colors ${
                relationMode === mode ? 'bg-brand-600 text-white' : 'text-slate-400 hover:text-slate-200'
              }`}>
              {label}
            </button>
          ))}
        </div>

        {/* 地图样式 */}
        <div className="pointer-events-auto flex items-center gap-0.5 bg-slate-900/80
          border border-slate-700/50 rounded-lg p-1">
          <Layers size={11} className="text-slate-600 mx-1" />
          {(['marble', 'dark', 'night'] as const).map((s) => (
            <button key={s} onClick={() => setMapStyle(s)}
              className={`px-2 py-1 rounded text-[11px] transition-colors ${
                mapStyle === s ? 'bg-slate-700 text-white' : 'text-slate-500 hover:text-slate-300'
              }`}>
              {s === 'marble' ? t('globe.mapSatellite') : s === 'dark' ? t('globe.mapDark') : t('globe.mapNight')}
            </button>
          ))}
        </div>

        <button onClick={loadPoints}
          className="pointer-events-auto p-2 rounded-lg bg-slate-900/80 border border-slate-700/50
            hover:bg-slate-800 text-slate-400 hover:text-slate-200 transition-colors">
          <RefreshCw size={13} />
        </button>
      </header>

      {/* --- Globe挂载点 --- */}
      <div ref={mountRef} className="absolute inset-0" style={{ willChange: 'transform' }} />

      {/* --- 加载遮罩 --- */}
      {(dataLoading || (!globeReady && !globeError)) && (
        <div className="absolute inset-0 z-30 flex items-center justify-center bg-slate-950/60 backdrop-blur-sm">
          <div className="flex items-center gap-2 text-slate-400 text-sm">
            <Loader2 className="animate-spin" size={16} />
            {dataLoading ? t('globe.loadingData') : t('globe.initGlobe')}
          </div>
        </div>
      )}

      {/* --- 错误 --- */}
      {globeError && !globeReady && (
        <div className="absolute inset-0 z-10">
          <Globe2DFallback points={points} onSelectPoint={(pt) => {
            if (pt.event_id) navigate(`/events?event_id=${pt.event_id}`)
          }} />
        </div>
      )}
      {globeError && globeReady && (
        <div className="absolute top-14 left-1/2 -translate-x-1/2 z-20
          bg-amber-900/80 border border-amber-600/40 rounded-lg px-4 py-2
          text-xs text-amber-300 flex items-center gap-2">
          <AlertCircle size={12} />
          {globeError}
        </div>
      )}
      {!dataLoading && error && (
        <div className="absolute inset-0 z-30 flex items-center justify-center">
          <div className="bg-slate-900 border border-slate-700/50 rounded-2xl p-6 text-center max-w-xs">
            <AlertCircle size={32} className="text-red-400 mx-auto mb-3" />
            <div className="text-sm text-slate-300 mb-1">{t('common.error')}</div>
            <div className="text-xs text-slate-600 mb-4">{error}</div>
            <button onClick={loadPoints}
              className="px-4 py-2 bg-brand-500 hover:bg-brand-600 text-white rounded-lg text-sm transition-colors">
              {t('common.retry')}
            </button>
          </div>
        </div>
      )}

      {/* --- 空状态 --- */}
      {!dataLoading && !error && globeReady && points.length === 0 && (
        <div className="absolute bottom-8 left-1/2 -translate-x-1/2 z-20
          bg-slate-900/80 border border-slate-700/40 rounded-xl px-5 py-3
          flex items-center gap-3 text-sm text-slate-400">
          <MapPin size={14} className="text-slate-600" />
          {t('globe.noEvents')} — {t('globe.noEventsHint')}
        </div>
      )}

      {/* --- 图例 --- */}
      {globeReady && points.length > 0 && (
        <div className="absolute bottom-4 left-4 z-20
          bg-slate-900/85 border border-slate-700/40 rounded-xl p-3
          text-[10px] text-slate-400 space-y-1.5 select-none">
          <div className="text-[10px] font-medium text-slate-500 mb-2">{t('globe.crisisStage')}</div>
          {Object.entries(STAGE_COLOR).map(([k, c]) => (
            <div key={k} className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full shrink-0" style={{ background: c }} />
              <span>{t(`crisisStages.${k}`, k)}</span>
            </div>
          ))}
          {relationMode !== 'none' && (
            <div className="pt-1.5 mt-1 border-t border-slate-700/40 space-y-1.5">
              <div className="text-[10px] font-medium text-slate-500">{t('globe.relationshipType')}</div>
              {(Object.entries(REL_COLOR) as [RelationshipType, string][]).map(([k, c]) => {
                const count = relationships.filter((r) => r.type === k).length
                if (!count || (relationMode !== 'all' && relationMode !== k)) return null
                return (
                  <div key={k} className="flex items-center gap-2">
                    <div className="w-4 h-0.5 rounded shrink-0" style={{ background: c }} />
                    <span>{t(REL_LABEL_KEY[k])}</span>
                    <span className="text-slate-600">({count})</span>
                  </div>
                )
              })}
            </div>
          )}
        </div>
      )}

      {/* --- 详情侧栏 --- */}
      {selected && (
        <div className="absolute top-14 right-4 bottom-4 z-30
          w-72 md:w-72 max-w-[90vw] bg-slate-900/95 border border-slate-700/50 rounded-2xl
          flex flex-col overflow-hidden backdrop-blur-sm shadow-2xl">

          {/* 标题 */}
          <div className="p-4 border-b border-slate-700/40">
            <div className="flex items-start justify-between gap-2">
              <div className="min-w-0 flex-1">
                {/* 危机阶段标签 */}
                <span className="inline-block text-[10px] px-1.5 py-0.5 rounded mb-1.5"
                  style={{
                    background: sc(selected.stage_of_crisis) + '22',
                    color: sc(selected.stage_of_crisis),
                  }}>
                  {TYPE_ICON[selected.event_type ?? ''] ?? '📌'}&nbsp;
                  {t(`crisisStages.${selected.stage_of_crisis ?? ''}`, selected.stage_of_crisis ?? t('common.unknown'))}
                </span>
                <div className="text-sm font-semibold text-white leading-snug line-clamp-2">
                  {selected.event_title}
                </div>
                <div className="text-[11px] text-slate-500 mt-1">
                  {selected.region} · {selected.lat.toFixed(2)}, {selected.lng.toFixed(2)}
                </div>
              </div>
              <button onClick={closeDetail}
                className="shrink-0 p-1.5 rounded hover:bg-slate-800 text-slate-500
                  hover:text-slate-300 transition-colors">
                <X size={14} />
              </button>
            </div>
          </div>

          {/* 滚动内容 */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">

            {/* 导航按钮 */}
            <div className="grid grid-cols-2 gap-2">
              <button
                onClick={() => navigate(`/events?event_id=${selected.event_id}`)}
                className="flex items-center justify-between px-3 py-2 rounded-lg text-[11px]
                  bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition-colors">
                <span>{t('globe.scenarioScripts')}</span>
                <ChevronRight size={12} />
              </button>
              <button
                onClick={() => navigate(`/clusters?event_id=${selected.event_id}`)}
                className="flex items-center justify-between px-3 py-2 rounded-lg text-[11px]
                  bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition-colors">
                <span>{t('globe.newsCluster')}</span>
                <ChevronRight size={12} />
              </button>
              {selected.scenario_summary?.has_scenarios && (
                <button
                  onClick={() => navigate(`/history?event_id=${selected.event_id}`)}
                  className="col-span-2 flex items-center justify-between px-3 py-2 rounded-lg text-[11px]
                    bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition-colors">
                  <span>{t('globe.historyEval')}</span>
                  <ChevronRight size={12} />
                </button>
              )}
            </div>

            {/* 推演概率 */}
            {selected.scenario_summary?.has_scenarios && (
              <div className="bg-slate-800/50 rounded-xl p-3 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-medium text-slate-400">{t('globe.simulationProb')}</span>
                  <span className="text-[10px] text-brand-400">
                    {selected.scenario_summary.script_count} {t('globe.scripts')}
                  </span>
                </div>
                {([
                  ['escalation',    t('directions.escalation'), '#f97316'],
                  ['stalemate',     t('directions.stalemate'), '#f59e0b'],
                  ['de_escalation', t('directions.de_escalation'), '#22c55e'],
                ] as const).map(([k, label, color]) => {
                  const val = selected.scenario_summary![k]
                  return (
                    <div key={k} className="flex items-center gap-2">
                      <span className="w-8 text-[10px] text-slate-400 shrink-0">{label}</span>
                      <div className="flex-1 h-1.5 bg-slate-700 rounded-full overflow-hidden">
                        <div className="h-full rounded-full transition-all duration-500"
                          style={{ width: `${Math.round((val ?? 0) * 100)}%`, background: color }} />
                      </div>
                      <span className="text-[10px] w-6 text-right shrink-0" style={{ color }}>
                        {val != null ? `${Math.round(val * 100)}%` : '—'}
                      </span>
                    </div>
                  )
                })}
              </div>
            )}

            {/* 详细信息（异步加载） */}
            {detailLoading && (
              <div className="flex items-center gap-2 text-slate-500 text-xs">
                <Loader2 className="animate-spin" size={12} />
                {t('globe.loadDetail')}
              </div>
            )}
            {!detailLoading && detail && (
              <div className="space-y-3">
                {/* 行为体 */}
                {(detail.key_actors ?? []).length > 0 && (
                  <div>
                    <div className="text-[10px] text-slate-500 mb-1">{t('globe.keyActors')}</div>
                    <div className="flex flex-wrap gap-1">
                      {detail.key_actors.slice(0, 6).map((a) => (
                        <span key={a} className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-300">
                          {a}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* 当前态势 */}
                {detail.current_balance && (
                  <div>
                    <div className="text-[10px] text-slate-500 mb-1">{t('globe.currentSituation')}</div>
                    <div className="text-xs text-slate-300 leading-relaxed line-clamp-4">
                      {detail.current_balance}
                    </div>
                  </div>
                )}

                {/* 主要风险 */}
                {(detail.major_risks ?? []).length > 0 && (
                  <div>
                    <div className="text-[10px] text-slate-500 mb-1">{t('globe.majorRisks')}</div>
                    <ul className="space-y-0.5">
                      {(detail.major_risks ?? []).slice(0, 3).map((r, i) => (
                        <li key={i} className="text-xs text-red-400/80 flex gap-1">
                          <span className="shrink-0">•</span>{r}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* 置信度 */}
                <div>
                  <div className="text-[10px] text-slate-500 mb-1">{t('globe.confidence')}</div>
                  <div className="flex items-center gap-2">
                    <div className="flex-1 h-1.5 bg-slate-800 rounded-full overflow-hidden">
                      <div className="h-full bg-brand-500 rounded-full"
                        style={{ width: `${Math.round((detail.event_confidence ?? 0) * 100)}%` }} />
                    </div>
                    <span className="text-xs text-slate-400">
                      {Math.round((detail.event_confidence ?? 0) * 100)}%
                    </span>
                  </div>
                </div>

                <button
                  onClick={() => navigate(`/events?event_id=${selected.event_id}`)}
                  className="w-full flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg
                    bg-brand-600/20 hover:bg-brand-600/30 text-brand-400 text-xs transition-colors">
                  <ExternalLink size={11} />
                  {t('globe.viewFullDetail')}
                </button>
              </div>
            )}

            {/* 关联事件 */}
            {relatedPoints.length > 0 && (
              <div>
                <div className="text-[10px] text-slate-500 mb-2">{t('globe.relatedEvents')}</div>
                <div className="space-y-1.5">
                  {relatedPoints.map((p) => (
                    <button key={p.event_id} onClick={() => openDetail(p)}
                      className="w-full text-left bg-slate-800/50 hover:bg-slate-700/50
                        rounded-lg px-3 py-2 transition-colors">
                      <div className="flex items-center gap-1.5">
                        <div className="w-1.5 h-1.5 rounded-full shrink-0" style={{ background: sc(p.stage_of_crisis) }} />
                        <div className="text-[11px] text-slate-200 truncate">{p.event_title}</div>
                      </div>
                      <div className="text-[10px] text-slate-500 mt-0.5 ml-3">{p.region}</div>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
