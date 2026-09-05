import { useCallback, useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import {
  Cpu,
  Play,
  Loader2,
  WifiOff,
  Globe2,
  FlaskConical,
  XCircle,
  RefreshCw,
  X,
  Trash2,
  History,
  CheckCircle2,
  AlertTriangle,
  Clock,
} from 'lucide-react'
import { eventApi, getErrorUserMessage, healthApi, historyApi, pipelineApi } from '../services/api'
import axios from 'axios'
import type {
  AbstractIRGEvent,
  IngestionDetail,
  NewsSourceInfo,
  PipelineTaskStatusResponse,
  PipelineTaskStep,
} from '../types'
import { toast } from '../store/toast'
import { useAppStore } from '../store'

const BG_TASK_KEY = 'ir_pipeline_bg_task'

interface BgTaskRecord {
  taskId: string
  startedAt: string
  useMock: boolean
}

function saveBgTask(record: BgTaskRecord) {
  localStorage.setItem(BG_TASK_KEY, JSON.stringify(record))
}
function loadBgTask(): BgTaskRecord | null {
  try {
    const raw = localStorage.getItem(BG_TASK_KEY)
    return raw ? (JSON.parse(raw) as BgTaskRecord) : null
  } catch {
    return null
  }
}
function clearBgTask() {
  localStorage.removeItem(BG_TASK_KEY)
}

type StepStatus = 'idle' | 'running' | 'done' | 'error'

function PipelineFlow({
  steps,
  progressDetail,
  subProgress,
  t,
}: {
  steps: PipelineTaskStep[]
  progressDetail?: string | null
  subProgress?: { current: number; total: number; label: string } | null
  t: (key: string, options?: Record<string, unknown>) => string
}) {
  if (steps.length === 0) return null

  const total = steps.length
  const doneCount = steps.filter(s => s.status === 'done' || s.status === 'error').length
  const runningIdx = steps.findIndex(s => s.status === 'running')

  let pct: number
  if (subProgress && subProgress.total > 0 && runningIdx >= 0) {
    const stepBase = doneCount / total
    const stepIncrement = (1 / total) * (subProgress.current / subProgress.total)
    pct = Math.min(99, Math.round((stepBase + stepIncrement) * 100))
  } else {
    pct = Math.round(((doneCount + (runningIdx >= 0 ? 0.5 : 0)) / total) * 100)
  }

  const allDone = steps.every(s => s.status === 'done' || s.status === 'error')
  const hasError = steps.some(s => s.status === 'error')
  if (allDone && !hasError) pct = 100

  return (
    <div className="mt-4 relative">
      <div className="absolute inset-0 rounded-xl overflow-hidden pointer-events-none opacity-20"
        style={{
          backgroundImage: 'radial-gradient(circle, #334155 1px, transparent 1px)',
          backgroundSize: '20px 20px',
        }}
      />

      <div className="relative px-4 pt-4 pb-1">
        <div className="flex items-center justify-between mb-1.5">
          <span className="text-[11px] text-slate-500">
            {runningIdx >= 0
              ? <><span className="text-amber-400 font-medium">{steps[runningIdx].label}</span> {t('pipeline.status.processing')}</>
              : allDone
                ? hasError
                  ? <span className="text-red-400">{t('pipeline.status.partialFailed')}</span>
                  : <span className="text-emerald-400">{t('pipeline.status.allComplete')}</span>
                : <span className="text-slate-600">{t('pipeline.status.waiting')}</span>
            }
          </span>
          <span className={`text-sm font-bold tabular-nums transition-colors ${
            allDone && !hasError ? 'text-emerald-400'
            : hasError ? 'text-red-400'
            : runningIdx >= 0 ? 'text-amber-400'
            : 'text-slate-500'
          }`}>
            {pct}%
          </span>
        </div>

        <div className="h-1.5 bg-slate-800 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-700 ease-out ${
              allDone && !hasError
                ? 'bg-gradient-to-r from-emerald-600 to-emerald-400'
                : hasError
                  ? 'bg-gradient-to-r from-emerald-600 to-red-500'
                  : 'bg-gradient-to-r from-emerald-600 via-emerald-500 to-amber-400'
            }`}
            style={{ width: `${pct}%` }}
          >
            {runningIdx >= 0 && (
              <div
                className="absolute right-0 top-0 h-full w-8 bg-gradient-to-r from-transparent to-amber-200/60 rounded-full"
                style={{ animation: 'progress-shimmer 1.5s ease-in-out infinite' }}
              />
            )}
          </div>
        </div>

        <div className="flex justify-between mt-1">
          <span className="text-[10px] text-slate-700">
            {t('pipeline.status.stepsComplete', { done: doneCount, total })}
          </span>
          {runningIdx >= 0 && (
            <span className="text-[10px] text-amber-700 animate-pulse">
              {t('pipeline.status.currentStep', { current: runningIdx + 1, total })}
            </span>
          )}
        </div>

        {(progressDetail || subProgress) && runningIdx >= 0 && (
          <div className="mt-2 space-y-1.5">
            {subProgress && subProgress.total > 0 && (
              <div className="flex items-center gap-2 text-[10px]">
                <span className="text-slate-500 shrink-0">{subProgress.label || `${subProgress.current}/${subProgress.total}`}</span>
                <div className="flex-1 h-1 bg-slate-800 rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-amber-600 to-amber-400 transition-all duration-500"
                    style={{ width: `${Math.round((subProgress.current / subProgress.total) * 100)}%` }}
                  />
                </div>
                <span className="text-amber-400 tabular-nums shrink-0">{subProgress.current}/{subProgress.total}</span>
              </div>
            )}
            {progressDetail && (
              <div className="flex items-center gap-1.5 text-[10px] text-slate-500 bg-slate-800/50 rounded-lg px-2.5 py-1.5 border border-slate-700/40">
                <div className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse shrink-0" />
                <span className="truncate">{progressDetail}</span>
              </div>
            )}
          </div>
        )}
      </div>

      <div className="relative flex items-center justify-between px-4 py-5 gap-0">
        {steps.map((s, i) => {
          const status = s.status as StepStatus
          const dur = (() => {
            if (typeof s.duration_seconds === 'number') return s.duration_seconds
            if (!s.started_at || !s.finished_at) return null
            return Math.max(0, (Date.parse(s.finished_at) - Date.parse(s.started_at)) / 1000)
          })()
          const isLast = i === steps.length - 1

          return (
            <div key={s.key} className="flex items-center flex-1 min-w-0">
              <div className="flex flex-col items-center shrink-0" style={{ width: 72 }}>
                <div className="relative">
                  {status === 'running' && (
                    <>
                      <div className="absolute inset-0 rounded-full bg-amber-400/20 animate-ping" />
                      <div className="absolute -inset-1.5 rounded-full border border-amber-400/30 animate-pulse" />
                    </>
                  )}
                  {status === 'done' && (
                    <div className="absolute -inset-1 rounded-full border border-emerald-500/40" />
                  )}

                  <div className={`
                    relative w-9 h-9 rounded-full flex items-center justify-center
                    border-2 transition-all duration-500 z-10
                    ${status === 'done'
                      ? 'bg-emerald-900/60 border-emerald-500 shadow-[0_0_12px_rgba(16,185,129,0.4)]'
                      : status === 'running'
                        ? 'bg-amber-900/60 border-amber-400 shadow-[0_0_12px_rgba(251,191,36,0.5)]'
                        : status === 'error'
                          ? 'bg-red-900/60 border-red-500'
                          : 'bg-slate-800 border-slate-600'
                    }
                  `}>
                    {status === 'done' && (
                      <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                        <path d="M2.5 7L5.5 10L11.5 4" stroke="#34d399" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                      </svg>
                    )}
                    {status === 'running' && (
                      <div className="w-3 h-3 border-2 border-amber-400 border-t-transparent rounded-full animate-spin" />
                    )}
                    {status === 'error' && (
                      <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                        <path d="M3.5 3.5L10.5 10.5M10.5 3.5L3.5 10.5" stroke="#f87171" strokeWidth="2" strokeLinecap="round"/>
                      </svg>
                    )}
                    {status === 'idle' && (
                      <span className="text-[10px] text-slate-600 font-mono font-bold">{i + 1}</span>
                    )}
                  </div>
                </div>

                <div className={`mt-2 text-[10px] font-medium text-center leading-tight transition-colors
                  ${status === 'done' ? 'text-emerald-400'
                    : status === 'running' ? 'text-amber-400'
                    : status === 'error' ? 'text-red-400'
                    : 'text-slate-600'}`
                }>
                  {s.label}
                </div>

                <div className={`mt-0.5 text-[9px] tabular-nums transition-colors
                  ${status === 'done' ? 'text-emerald-600'
                    : status === 'running' ? 'text-amber-600 animate-pulse'
                    : 'text-slate-700'}`
                }>
                  {status === 'running' ? t('pipeline.status.running')
                    : dur != null ? `${dur.toFixed(1)}s`
                    : '—'}
                </div>
              </div>

              {!isLast && (
                <div className="flex-1 relative mx-1" style={{ height: 6 }}>
                  <div className="absolute inset-y-0 inset-x-0 rounded-full bg-slate-800/80" />

                  {status === 'done' && (
                    <div className="absolute inset-y-0 left-0 right-0 rounded-full bg-gradient-to-r from-emerald-600 to-emerald-500" />
                  )}

                  {status === 'running' && (
                    <>
                      <div className="absolute inset-y-0 left-0 right-0 rounded-full bg-gradient-to-r from-emerald-700/60 to-amber-700/40" />
                      <div className="absolute inset-y-0 left-0 rounded-full overflow-hidden" style={{ right: 0 }}>
                        <div
                          className="absolute inset-y-0 w-1/3 rounded-full bg-gradient-to-r from-transparent via-amber-300/80 to-transparent"
                          style={{ animation: 'pipeline-flow 1.2s linear infinite' }}
                        />
                      </div>
                    </>
                  )}
                </div>
              )}
            </div>
          )
        })}
      </div>

      <style>{`
        @keyframes pipeline-flow {
          0%   { transform: translateX(-100%); }
          100% { transform: translateX(350%); }
        }
        @keyframes progress-shimmer {
          0%, 100% { opacity: 0.4; }
          50%       { opacity: 1; }
        }
      `}</style>
    </div>
  )
}

export default function PipelinePage() {
  const { t, i18n } = useTranslation()
  const navigate = useNavigate()
  const [useMock, setUseMock] = useState(false)
  const [backendOk, setBackendOk] = useState<boolean | null>(null)

  const [sources, setSources] = useState<NewsSourceInfo[]>([])
  const [running, setRunning] = useState(false)
  const [resetting, setResetting] = useState(false)
  const [taskId, setTaskId] = useState<string | null>(null)
  const [task, setTask] = useState<PipelineTaskStatusResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [events, setEvents] = useState<AbstractIRGEvent[]>([])
  const [runHistory, setRunHistory] = useState<Array<{
    run_id: string
    event_id: string
    summary: string
    status: string
    created_at: string | null
    script_ids: string[]
  }>>([])
  const [historyLoading, setHistoryLoading] = useState(false)

  const [bgRecord, setBgRecord] = useState<BgTaskRecord | null>(null)

  const cancelRef = useRef(false)

  const setPipelineRunning = useAppStore((s) => s.setPipelineRunning)
  const refreshAfterPipeline = useAppStore((s) => s.refreshAfterPipeline)

  const loadHistory = useCallback(() => {
    setHistoryLoading(true)
    historyApi.list()
      .then(res => {
        const items = res.data.items ?? res.data ?? []
        setRunHistory(items)
      })
      .catch(() => {})
      .finally(() => setHistoryLoading(false))
  }, [])

  useEffect(() => { loadHistory() }, [loadHistory])

  const refreshBackend = useCallback(() => {
    setBackendOk(null)
    healthApi.check()
      .then(() => setBackendOk(true))
      .catch(() => setBackendOk(false))
  }, [])

  useEffect(() => { refreshBackend() }, [refreshBackend])

  useEffect(() => {
    pipelineApi.listSources()
      .then((res) => setSources(res.data.sources ?? []))
      .catch((e) => toast.error(getErrorUserMessage(e, 'Failed to load RSS sources.'), { dedupeKey: 'pipeline-sources' }))
  }, [])

  useEffect(() => {
    const saved = loadBgTask()
    if (!saved) return
    pipelineApi.getTask(saved.taskId)
      .then((res) => {
        const tk = res.data
        if (tk.status === 'done' || tk.status === 'error') {
          clearBgTask()
        } else {
          setBgRecord(saved)
        }
      })
      .catch(() => {
        clearBgTask()
      })
  }, [])

  const sleepCancelRef = useRef<(() => void) | null>(null)

  useEffect(() => {
    return () => {
      cancelRef.current = true
      if (sleepCancelRef.current) sleepCancelRef.current()
    }
  }, [])

  const startPolling = useCallback(async (newTaskId: string) => {
    const sleep = (ms: number) => new Promise<void>((resolve, reject) => {
      const id = setTimeout(resolve, ms)
      sleepCancelRef.current = () => {
        clearTimeout(id)
        reject(new DOMException('Aborted', 'AbortError'))
      }
    })
    const MAX_WAIT_MS      = 95 * 60 * 1000
    const POLL_INTERVAL_MS = 3000
    const WARN_AT_CONSECUTIVE  = 3
    const GIVEUP_CONSECUTIVE   = 30
    let consecutive   = 0
    let backoffMs     = POLL_INTERVAL_MS
    let backendStartedAt: number | null = null

    while (!cancelRef.current) {
      if (backendStartedAt !== null) {
        const elapsed = Date.now() - backendStartedAt
        if (elapsed > MAX_WAIT_MS) {
          setPipelineRunning(false)
          throw new Error(
            t('pipeline.error.timeout', { minutes: Math.floor(elapsed / 60000) })
          )
        }
      }

      try {
        const res = await pipelineApi.getTask(newTaskId)
        const tk = res.data
        setTask(tk)

        if (consecutive > 0) {
          consecutive = 0
          backoffMs   = POLL_INTERVAL_MS
          setBackendOk(true)
          toast.dismissByKey('pipeline-poll')
        } else {
          setBackendOk(true)
        }

        if (backendStartedAt === null && tk.started_at) {
          backendStartedAt = new Date(tk.started_at).getTime()
        }

        if (tk.status === 'done') {
          clearBgTask()
          await refreshAfterPipeline()
          loadHistory()
          try {
            const ev = await eventApi.list()
            setEvents(ev.data.items ?? [])
          } catch { }
          return
        }
        if (tk.status === 'error') {
          clearBgTask()
          setPipelineRunning(false)
          throw new Error(tk.error ?? t('pipeline.error.backendFailed'))
        }
      } catch (e) {
        if (axios.isCancel(e)) return
        if (e instanceof DOMException && e.name === 'AbortError') return

        if (e instanceof Error && !(e as { isAxiosError?: boolean }).isAxiosError) {
          throw e
        }

        consecutive++
        backoffMs = Math.min(30000, Math.round(backoffMs * 1.5))

        if (consecutive === WARN_AT_CONSECUTIVE) {
          setBackendOk(false)
          toast.warn(
            t('pipeline.backend.connectionFlaky'),
            { dedupeKey: 'pipeline-poll' }
          )
        }
        if (consecutive >= GIVEUP_CONSECUTIVE) {
          setBackendOk(false)
          setPipelineRunning(false)
          throw new Error(
            t('pipeline.backend.connectionLost', { count: GIVEUP_CONSECUTIVE })
          )
        }
      }
      await sleep(backoffMs)
    }
  }, [refreshAfterPipeline, setPipelineRunning, t])

  const runFull = async () => {
    if (backendOk === false) {
      const msg = t('pipeline.backend.unreachableHint')
      setError(msg)
      toast.error('Backend unavailable. Start FastAPI at http://localhost:8000.', { dedupeKey: 'backend-offline' })
      return
    }
    cancelRef.current = false
    setRunning(true)
    setError(null)
    setTask(null)
    setEvents([])
    setBgRecord(null)

    try {
      const startRes = await pipelineApi.runFull(useMock)
      const newTaskId = (startRes.data as { task_id: string }).task_id
      setTaskId(newTaskId)

      setPipelineRunning(true, newTaskId)

      saveBgTask({ taskId: newTaskId, startedAt: new Date().toISOString(), useMock })

      await startPolling(newTaskId)
    } catch (e) {
      setError(getErrorUserMessage(e, t('pipeline.error.title')))
      setPipelineRunning(false)
    } finally {
      setRunning(false)
    }
  }

  const reconnectBgTask = async () => {
    if (!bgRecord) return
    setBgRecord(null)
    cancelRef.current = false
    setRunning(true)
    setError(null)
    setTask(null)
    setTaskId(bgRecord.taskId)
    setUseMock(bgRecord.useMock)
    setPipelineRunning(true, bgRecord.taskId)
    try {
      await startPolling(bgRecord.taskId)
    } catch (e) {
      setError(getErrorUserMessage(e, t('pipeline.error.resumeFailed')))
      setPipelineRunning(false)
    } finally {
      setRunning(false)
    }
  }

  const dismissBgRecord = () => {
    clearBgTask()
    setBgRecord(null)
  }

  const resetData = async () => {
    if (!window.confirm(t('pipeline.resetConfirm'))) return
    setResetting(true)
    setError(null)
    try {
      await pipelineApi.reset()
      setTask(null)
      setTaskId(null)
      setEvents([])
      clearBgTask()
      setBgRecord(null)
      await refreshAfterPipeline()
      loadHistory()
      toast.success(t('pipeline.resetSuccess'))
    } catch (e) {
      setError(getErrorUserMessage(e, t('pipeline.error.resetFailed')))
    } finally {
      setResetting(false)
    }
  }

  const isLive = !useMock
  const steps = task?.steps ?? []
  const result = (task?.result ?? {}) as Record<string, unknown>
  const getNum = (primary: unknown, fallback: unknown) =>
    (typeof primary === 'number' ? primary : (typeof fallback === 'number' ? fallback : 0))
  const summary = task?.status === 'done'
    ? {
        news: getNum(result.news_count, result.news_collected),
        clusters: getNum(result.cluster_count, result.clusters_formed),
        events: getNum(result.event_count, result.events_abstracted),
        theories: typeof result.theory_count === 'number' ? result.theory_count : 0,
        scenarios: typeof result.scenario_count === 'number' ? result.scenario_count : 0,
        data_source: typeof result.data_source === 'string' ? result.data_source : 'unknown',
        ingestion_detail: result.ingestion_detail as IngestionDetail | undefined,
      }
    : null

  return (
    <div className="min-h-screen bg-surface-950 text-slate-100 p-6 max-w-5xl mx-auto">

      <div className="flex items-start justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-100 tracking-wide flex items-center gap-2">
            <Cpu size={18} className="text-brand-500" />
            {t('pipeline.title')}
          </h1>
          <p className="text-slate-500 text-sm mt-1">
            {t('pipeline.desc')}
          </p>
        </div>

        <div className="flex flex-col items-end gap-2">
          <div className="flex items-center gap-2 bg-surface-900 rounded-xl p-1 border border-slate-700/50">
            <button
              onClick={() => setUseMock(false)}
              disabled={running}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all disabled:opacity-40 ${
                !useMock
                  ? 'bg-emerald-600 text-white shadow'
                  : 'text-slate-500 hover:text-slate-300'
              }`}
            >
              <Globe2 size={12} />
              {t('pipeline.live')}
            </button>
            <button
              onClick={() => setUseMock(true)}
              disabled={running}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all disabled:opacity-40 ${
                useMock
                  ? 'bg-blue-600 text-white shadow'
                  : 'text-slate-500 hover:text-slate-300'
              }`}
            >
              <FlaskConical size={12} />
              {t('pipeline.mock')}
            </button>
          </div>
          <div className="text-[11px] text-slate-600">
            RSS sources: {sources.length}
          </div>
        </div>
      </div>

      {backendOk === false && (
        <div className="mb-6 bg-red-900/20 border border-red-700/40 rounded-xl px-4 py-3 flex items-start gap-3">
          <WifiOff size={15} className="text-red-400 shrink-0 mt-0.5" />
          <div className="flex-1">
            <div className="text-sm text-red-300 font-medium">{t('pipeline.backend.unreachable')}</div>
            <div className="text-xs text-red-400/80 mt-0.5">
              {t('pipeline.backend.unreachableHint')}
            </div>
          </div>
          <button
            onClick={refreshBackend}
            className="shrink-0 px-3 py-1.5 rounded-lg text-xs font-medium bg-red-500/15 text-red-300 border border-red-500/30 hover:bg-red-500/20 transition-colors"
          >
            {t('pipeline.backend.retryConnect')}
          </button>
        </div>
      )}

      {bgRecord && !running && (
        <div className="mb-6 bg-amber-900/20 border border-amber-600/40 rounded-xl px-4 py-3 flex items-center gap-3">
          <Loader2 size={15} className="text-amber-400 animate-spin shrink-0" />
          <div className="flex-1 min-w-0">
            <div className="text-sm text-amber-300 font-medium">{t('pipeline.bgTask.title')}</div>
            <div className="text-xs text-amber-400/70 mt-0.5 truncate">
              {bgRecord.taskId.slice(0, 8)} · {t('pipeline.bgTask.startedAt')} {new Date(bgRecord.startedAt).toLocaleTimeString()} · {bgRecord.useMock ? t('pipeline.mock') : t('pipeline.live')} {t('pipeline.bgTask.mode')}
            </div>
          </div>
          <button
            onClick={reconnectBgTask}
            className="shrink-0 flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-amber-500/15 text-amber-300 border border-amber-500/30 hover:bg-amber-500/25 transition-colors"
          >
            <RefreshCw size={12} />
            {t('pipeline.bgTask.reconnect')}
          </button>
          <button
            onClick={dismissBgRecord}
            className="shrink-0 p-1.5 rounded-lg text-slate-500 hover:text-slate-300 hover:bg-slate-700/40 transition-colors"
            title={t('pipeline.bgTask.dismiss')}
          >
            <X size={13} />
          </button>
        </div>
      )}

      <div className="flex justify-center items-center gap-3 mb-6">
        <button
          onClick={runFull}
          disabled={running || resetting}
          className={`px-10 py-3.5 rounded-xl font-semibold text-base tracking-wide disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg flex items-center gap-2 ${
            isLive ? 'bg-emerald-700 hover:bg-emerald-600 shadow-emerald-900/40' : 'bg-blue-600 hover:bg-blue-500 shadow-blue-900/40'
          }`}
        >
          {running ? <><Loader2 size={16} className="animate-spin" /> {t('pipeline.analyzing')}</> : <><Play size={16} /> {isLive ? t('pipeline.runLive') : t('pipeline.runMock')}</>}
        </button>
        <button
          onClick={resetData}
          disabled={running || resetting}
          title={t('pipeline.reset')}
          className="px-4 py-3.5 rounded-xl font-medium text-sm disabled:opacity-40 disabled:cursor-not-allowed transition-all border border-slate-700/60 bg-slate-800/60 hover:bg-red-900/30 hover:border-red-700/50 hover:text-red-300 text-slate-400 flex items-center gap-2"
        >
          {resetting ? <Loader2 size={14} className="animate-spin" /> : <Trash2 size={14} />}
          {t('pipeline.reset')}
        </button>
      </div>

      {(taskId || task) && (
        <div className="mb-6 bg-surface-900 border border-slate-700/50 rounded-xl px-4 pt-3 pb-2">
          <div className="flex items-center justify-between gap-4">
            <div className="text-xs text-slate-500">
              {t('pipeline.taskId')}：<span className="text-slate-300 font-mono">{taskId?.slice(0, 8) ?? '—'}</span>
              {task?.running_seconds != null && (
                <span className="ml-2 text-slate-600">{t('pipeline.runningSeconds', { seconds: Math.floor(task.running_seconds) })}</span>
              )}
              {task?.started_at && (
                <span className="ml-2 text-slate-600">{t('pipeline.startedAt')} {new Date(task.started_at).toLocaleTimeString()}</span>
              )}
            </div>
            <div className="text-xs">
              <span className={`px-2 py-0.5 rounded-full text-[10px] font-medium ${
                task?.status === 'done' ? 'bg-emerald-900/50 text-emerald-400 border border-emerald-700/40' :
                task?.status === 'error' ? 'bg-red-900/50 text-red-400 border border-red-700/40' :
                task?.status === 'running' ? 'bg-amber-900/50 text-amber-400 border border-amber-700/40' :
                'bg-slate-800 text-slate-500 border border-slate-700/40'
              }`}>{task?.status ?? 'pending'}</span>
            </div>
          </div>

          <PipelineFlow
            steps={steps}
            progressDetail={task?.progress_detail}
            subProgress={task?.sub_progress as { current: number; total: number; label: string } | null}
            t={t}
          />
        </div>
      )}

      {error && (
        <div className="mb-6 bg-red-900/25 border border-red-700/50 rounded-xl px-4 py-3 flex items-start gap-3">
          <XCircle size={15} className="text-red-400 shrink-0 mt-0.5" />
          <div className="flex-1">
            <div className="text-red-300 font-semibold text-sm">{t('pipeline.error.title')}</div>
            <p className="text-red-400/80 text-xs mt-0.5">{error}</p>
            {taskId && task?.status === 'error' && (
              <button
                onClick={async () => {
                  try {
                    setRunning(true)
                    setError(null)
                    const res = await pipelineApi.resumeTask(taskId)
                    const newTaskId = res.data.task_id
                    setTaskId(newTaskId)
                    setPipelineRunning(true, newTaskId)
                    saveBgTask({ taskId: newTaskId, startedAt: new Date().toISOString(), useMock: true })
                    await startPolling(newTaskId)
                    toast.success(t('pipeline.resumeSuccess', { step: res.data.resumed_from }), { dedupeKey: 'pipeline-resume' })
                  } catch (e) {
                    setError(getErrorUserMessage(e, t('pipeline.error.resumeFailed')))
                    setPipelineRunning(false)
                  } finally {
                    setRunning(false)
                  }
                }}
                disabled={running}
                className="mt-2 flex items-center gap-1.5 px-3 py-1.5 text-xs bg-amber-600/20 hover:bg-amber-600/30 text-amber-400 border border-amber-600/30 rounded-lg transition-colors disabled:opacity-50"
              >
                <RefreshCw size={12} />
                {t('pipeline.resume')}
              </button>
            )}
          </div>
        </div>
      )}

      {summary && (
        <div className="mb-6">
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
            {[
              { label: t('pipeline.result.news'), value: summary.news, color: 'text-blue-400' },
              { label: t('pipeline.result.clusters'), value: summary.clusters, color: 'text-amber-400' },
              { label: t('pipeline.result.events'), value: summary.events, color: 'text-emerald-400' },
              { label: t('pipeline.result.theories'), value: summary.theories, color: 'text-purple-400' },
              { label: t('pipeline.result.scripts'), value: summary.scenarios, color: 'text-sky-400' },
            ].map((x) => (
              <div key={x.label} className="bg-surface-900 border border-slate-700/50 rounded-xl p-4 text-center">
                <div className={`text-3xl font-bold ${x.color}`}>{x.value}</div>
                <div className="text-slate-500 text-xs mt-0.5">{x.label}</div>
              </div>
            ))}
          </div>
          <div className="mt-3 flex items-center gap-2 justify-center">
            <button
              onClick={() => navigate('/events')}
              className="text-xs px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white transition-colors"
            >
              {t('pipeline.viewResults')}
            </button>
            <button
              onClick={() => navigate('/')}
              className="text-xs px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition-colors"
            >
              {t('pipeline.globeOverview')}
            </button>
          </div>
        </div>
      )}

      {summary?.ingestion_detail && (
        <div className="mb-6 bg-surface-900 border border-slate-700/50 rounded-xl p-4">
          <div className="text-xs text-slate-500 mb-2">{t('pipeline.ingestion.title')}</div>
          <div className="text-xs text-slate-400">
            {t('pipeline.ingestion.saved', { count: summary.ingestion_detail.total_saved })} · {t('pipeline.ingestion.failedSources', { count: summary.ingestion_detail.total_failed_sources })}
          </div>
        </div>
      )}

      {events.length > 0 && (
        <div className="bg-surface-900 border border-slate-700/50 rounded-xl overflow-hidden">
          <div className="px-5 py-3.5 border-b border-slate-700 flex items-center justify-between">
            <h2 className="text-sm font-semibold text-slate-300">{t('pipeline.abstractEventsList')}</h2>
            <span className="text-xs text-slate-500">{t('pipeline.records', { count: events.length })}</span>
          </div>
          <div className="divide-y divide-slate-800/60">
            {events.slice(0, 20).map((e) => (
              <div key={e.event_id} className="px-5 py-3">
                <div className="text-sm text-slate-200">{e.event_title}</div>
                <div className="text-xs text-slate-600 mt-0.5">{e.region} · {t('events.confidence')} {Math.round((e.event_confidence ?? 0) * 100)}%</div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="mt-8">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-semibold text-slate-400 flex items-center gap-2">
            <History size={14} className="text-slate-500" />
            {t('pipeline.history.title')}
          </h2>
          <button
            onClick={loadHistory}
            disabled={historyLoading}
            className="text-xs text-slate-600 hover:text-slate-400 flex items-center gap-1 transition-colors disabled:opacity-40"
          >
            <RefreshCw size={11} className={historyLoading ? 'animate-spin' : ''} />
            {t('pipeline.history.refresh')}
          </button>
        </div>

        {historyLoading && runHistory.length === 0 ? (
          <div className="text-center py-8 text-slate-700 text-xs">{t('pipeline.history.loading')}</div>
        ) : runHistory.length === 0 ? (
          <div className="text-center py-8 text-slate-700 text-xs border border-slate-800 rounded-xl">
            {t('pipeline.history.empty')}
          </div>
        ) : (
          <div className="space-y-2">
            {runHistory.map((run) => {
              const isComplete = run.status === 'complete'
              const isError = run.status === 'error'
              const createdAt = run.created_at ? new Date(run.created_at) : null
              const dateStr = createdAt
                ? `${createdAt.toLocaleDateString(i18n.language === 'zh' ? 'zh-CN' : 'en-US')} ${createdAt.toLocaleTimeString(i18n.language === 'zh' ? 'zh-CN' : 'en-US', { hour: '2-digit', minute: '2-digit' })}`
                : '—'
              return (
                <div
                  key={run.run_id}
                  className="bg-surface-900 border border-slate-800 rounded-xl px-4 py-3 flex items-start gap-3 hover:border-slate-700 transition-colors"
                >
                  <div className="shrink-0 mt-0.5">
                    {isComplete
                      ? <CheckCircle2 size={14} className="text-emerald-500" />
                      : isError
                        ? <AlertTriangle size={14} className="text-red-500" />
                        : <Clock size={14} className="text-amber-500" />
                    }
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-xs text-slate-500 font-mono">{run.run_id.slice(0, 8)}</span>
                      <span className={`text-[10px] px-1.5 py-0.5 rounded-full border font-medium ${
                        isComplete
                          ? 'bg-emerald-900/30 text-emerald-400 border-emerald-800'
                          : isError
                            ? 'bg-red-900/30 text-red-400 border-red-800'
                            : 'bg-amber-900/30 text-amber-400 border-amber-800'
                      }`}>
                        {isComplete ? t('pipeline.history.complete') : isError ? t('pipeline.history.failed') : run.status}
                      </span>
                      <span className="text-[10px] text-slate-600">{dateStr}</span>
                      {run.script_ids?.length > 0 && (
                        <span className="text-[10px] text-slate-600">
                          {t('pipeline.history.scripts', { count: run.script_ids.length })}
                        </span>
                      )}
                    </div>
                    {run.summary && (
                      <p className="text-xs text-slate-500 mt-1 line-clamp-2">{run.summary}</p>
                    )}
                  </div>

                  <button
                    onClick={() => navigate('/history')}
                    className="shrink-0 text-[10px] text-slate-600 hover:text-slate-400 transition-colors px-2 py-1 rounded border border-slate-800 hover:border-slate-700"
                  >
                    {t('pipeline.history.view')}
                  </button>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
