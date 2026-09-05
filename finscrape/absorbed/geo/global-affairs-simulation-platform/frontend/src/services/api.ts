import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios'
import type {
  RawNews,
  NewsCluster,
  AbstractIRGEvent,
  TheoryAnalysis,
  ScenarioScript,
  BranchRequest,
  GlobePoint,
  GlobeRelationship,
  AnalogyResult,
  HistoricalCase,
  CalibrationSummary,
  RunCalibrationDetail,
  TheoryCalibration,
  DirectionCalibration,
  NewsSourceInfo,
  SourceTestResult,
  PipelineTaskStatusResponse,
  Annotation,
  AnnotationCreate,
  AnnotationUpdate,
  EventVersion,
  FieldChange,
} from '../types'

type RetryableConfig = InternalAxiosRequestConfig & { __retryCount?: number }
const MAX_RETRY_COUNT = 2

function sleep(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

function shouldRetry(err: AxiosError, cfg?: RetryableConfig): boolean {
  if (!cfg) return false
  if ((cfg.method ?? 'get').toLowerCase() !== 'get') return false
  if (cfg.signal?.aborted) return false
  if ((cfg.__retryCount ?? 0) >= MAX_RETRY_COUNT) return false
  if (!err.response) return true
  return [502, 503, 504].includes(err.response.status)
}

const API_PREFIX = '/api/v1'

const api = axios.create({
  baseURL: API_PREFIX,
  timeout: 30000,
})

function extractDetail(data: unknown): string | undefined {
  if (!data) return undefined
  if (typeof data === 'string') return data
  if (typeof data === 'object') {
    const anyData = data as Record<string, unknown>
    if (typeof anyData.detail === 'string') return anyData.detail
    if (typeof anyData.message === 'string') return anyData.message
  }
  return undefined
}

function toUserMessage(err: unknown): string {
  const fallback = '请求失败，请重试。'
  if (!err) return fallback

  const ax = err as AxiosError
  const code = (ax as unknown as { code?: string }).code
  const isTimeout =
    code === 'ECONNABORTED' || (ax.message ?? '').toLowerCase().includes('timeout')
  if (isTimeout) return '请求超时（后端响应慢或不可达），请稍后重试。'

  // AbortController取消不算错
  if (axios.isCancel(err)) return ''

  if (ax.response) {
    const status = ax.response.status
    const detail = extractDetail(ax.response.data)
    if (detail) return `HTTP ${status}: ${detail}`
    return `HTTP ${status}`
  }

  const msg = (ax.message ?? '').toLowerCase()
  if (
    msg.includes('network error') ||
    msg.includes('econnrefused') ||
    msg.includes('failed to fetch')
  ) {
    return '后端不可达，请确认 FastAPI 服务已启动（http://localhost:8000）。'
  }

  return (ax.message || fallback).slice(0, 200)
}

export function getErrorUserMessage(err: unknown, fallback?: string) {
  const anyErr = err as { userMessage?: string; message?: string }
  const msg = anyErr?.userMessage || anyErr?.message || fallback || '请求失败。'
  return msg || fallback || '请求失败。'
}

function _normalizeIsBranch(data: unknown): void {
  if (!data || typeof data !== 'object') return
  const d = data as Record<string, unknown>
  if ('is_branch' in d && typeof d.is_branch === 'string') {
    d.is_branch = d.is_branch === 'true'
  }
  if ('scripts' in d && Array.isArray(d.scripts)) {
    for (const s of d.scripts) _normalizeIsBranch(s)
  }
  if ('items' in d && Array.isArray(d.items)) {
    for (const item of d.items) _normalizeIsBranch(item)
  }
  if ('runs' in d && Array.isArray(d.runs)) {
    for (const r of d.runs) _normalizeIsBranch(r)
  }
}

// 请求拦截器，不自动创建AbortController了
// 需要取消就自己传signal
api.interceptors.request.use((config: InternalAxiosRequestConfig) => config)

api.interceptors.response.use(
  (resp) => {
    _normalizeIsBranch(resp.data)
    return resp
  },
  async (err: unknown) => {
    // 主动取消的请求静默处理
    if (axios.isCancel(err)) return Promise.reject(err)

    const ax = err as AxiosError
    const cfg = ax.config as RetryableConfig | undefined
    if (cfg && shouldRetry(ax, cfg)) {
      cfg.__retryCount = (cfg.__retryCount ?? 0) + 1
      await sleep(200 * cfg.__retryCount)
      return api.request(cfg)
    }

    const userMessage = toUserMessage(err)
    if (err && typeof err === 'object') {
      ;(err as { userMessage?: string }).userMessage = userMessage
    }
    return Promise.reject(err)
  },
)

// --- Pipeline ---
export const pipelineApi = {
  runFull: (useMock: boolean = false, sourceIds?: string) =>
    api.post('/pipeline/run-full', null, {
      params: { use_mock: useMock, ...(sourceIds ? { source_ids: sourceIds } : {}) },
      timeout: 120000, // 完整流程可能2分钟
    }),

  reset: async () => {
    // 后端需要两步确认：第一次获取 confirm_token，第二次带 token 执行删除
    const step1 = await api.post<{ confirm_token?: string }>('/pipeline/reset', null, { timeout: 10000 })
    const token = step1.data?.confirm_token
    if (!token) throw new Error('未收到确认 token')
    return api.post('/pipeline/reset', null, { params: { confirm_token: token }, timeout: 30000 })
  },

  resumeTask: (taskId: string) =>
    api.post<{ task_id: string; status: string; resumed_from: string; original_task_id: string }>(
      `/pipeline/tasks/${taskId}/resume`, null, { timeout: 30000 },
    ),

  runAnalysis: (eventId: string) =>
    api.post(`/pipeline/run-analysis/${eventId}`, null, { timeout: 180000 }), // 3分钟

  getRuns: (eventId?: string) =>
    api.get('/pipeline/runs', { params: { event_id: eventId } }),

  getRun: (runId: string) => api.get(`/pipeline/runs/${runId}`),

  listSources: () => api.get<{ total: number; sources: NewsSourceInfo[] }>('/pipeline/sources'),

  testSource: (sourceId: string) => api.post<SourceTestResult>(`/pipeline/sources/${sourceId}/test`),

  getTask: (taskId: string) =>
    api.get<PipelineTaskStatusResponse>(`/pipeline/tasks/${taskId}`, {
      timeout: 20000, // 轮询20s，LLM偶尔慢
    }),
}

// --- News ---
export const newsApi = {
  list: (params?: { status?: string; limit?: number }) =>
    api.get<{ total: number; items: RawNews[] }>('/news', { params }),
}

// --- Clusters ---
export const clusterApi = {
  list: () => api.get<{ total: number; items: NewsCluster[] }>('/clusters'),
  get: (clusterId: string) => api.get<NewsCluster>(`/clusters/${clusterId}`),
}

// --- Events ---
export const eventApi = {
  list: () => api.get<{ total: number; items: AbstractIRGEvent[] }>('/events'),
  get: (eventId: string) => api.get<AbstractIRGEvent>(`/events/${eventId}`),

  listVersions: (eventId: string) =>
    api.get<{ event_id: string; versions: EventVersion[]; total: number }>(`/events/${eventId}/versions`),
  getVersion: (eventId: string, versionNumber: number) =>
    api.get<EventVersion>(`/events/${eventId}/versions/${versionNumber}`),
  createVersion: (eventId: string, changeSource: string = 'manual', changeSummary: string = '') =>
    api.post<EventVersion>(`/events/${eventId}/versions`, null, {
      params: { change_source: changeSource, change_summary: changeSummary },
    }),
  rollbackVersion: (eventId: string, versionNumber: number) =>
    api.post<EventVersion>(`/events/${eventId}/versions/rollback`, null, {
      params: { version_number: versionNumber },
    }),
  diffVersions: (eventId: string, v1: number, v2: number) =>
    api.get<{ event_id: string; version_a: number; version_b: number; changes: FieldChange[]; change_count: number }>(
      `/events/${eventId}/versions/diff`, { params: { v1, v2 } },
    ),
}

// --- Theories ---
export const theoryApi = {
  getForEvent: (eventId: string) =>
    api.get<{ event_id: string; analyses: TheoryAnalysis[] }>(`/events/${eventId}/theories`),

  generateForEvent: (eventId: string) =>
    api.post<{ event_id: string; analyses: TheoryAnalysis[] }>(`/events/${eventId}/theories/generate`, null, {
      timeout: 180000,
    }),
}

// --- Scenarios ---
export const scenarioApi = {
  getForEvent: (eventId: string, runId?: string) =>
    api.get<{ event_id: string; scripts: ScenarioScript[] }>(`/events/${eventId}/scripts`, {
      params: { run_id: runId },
    }),
}

// --- Branches ---
export const branchApi = {
  // 分支推演LLM调用，10分钟
  create: (data: BranchRequest) => api.post('/branches', data, { timeout: 600000 }),
  getForRun: (baseRunId: string) => api.get(`/branches/${baseRunId}`),
  delete: (branchRunId: string) => api.delete<{ status: string; branch_run_id: string }>(`/branches/${branchRunId}`),
  retract: (branchRunId: string) => api.patch<{ status: string; branch_run_id: string }>(`/branches/${branchRunId}/retract`),
}

// --- History ---
export const historyApi = {
  list: (eventId?: string) => api.get('/history', { params: { event_id: eventId } }),
  recordOutcome: (
    runId: string,
    data: { event_id: string; actual_summary: string; actual_event_type: string; matched_script_id?: string },
  ) => api.post(`/runs/${runId}/outcome`, data),
  createEvaluation: (runId: string, data: object) => api.post(`/runs/${runId}/evaluation`, data),
  // LLM自动评估
  autoEvaluation: (runId: string) => api.post(`/runs/${runId}/auto-evaluation`, {}, { timeout: 180000 }),
}

// --- Globe ---
export const globeApi = {
  getPoints: () => api.get<{ total: number; total_events: number; no_coords_count: number; points: GlobePoint[]; relationships: GlobeRelationship[] }>('/globe/events'),
}

// --- Reports ---
export const reportApi = {
  export: async (params: { report_type: string; event_id?: string; run_id?: string }) => {
    const controller = new AbortController()
    const response = await api.get('/reports/export', {
      params,
      responseType: 'blob',
      signal: controller.signal,
      timeout: 60000, // 下载1分钟超时
    })
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `report_${params.report_type}_${Date.now()}.pdf`)
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
  },
}

// --- Health ---
export const healthApi = {
  check: () => api.get('/health', { timeout: 5000 }), // 5s
}

// --- Analogies ---
export const analogyApi = {
  getForEvent: (eventId: string) => api.get<AnalogyResult>(`/events/${eventId}/analogies`),
  buildForEvent: (eventId: string, forceRegenerate: boolean = false) =>
    api.post<AnalogyResult>(`/events/${eventId}/build-analogies`, null, {
      params: { force_regenerate: forceRegenerate },
      timeout: 120000,
    }),
  listCases: (params?: { event_type?: string; region?: string; year_from?: number; year_to?: number }) =>
    api.get<{ total: number; cases: HistoricalCase[] }>('/analogies/cases', { params }),
  getCase: (caseId: string) => api.get<HistoricalCase>(`/analogies/cases/${caseId}`),
  createCase: (data: Partial<HistoricalCase> & { title: string }) =>
    api.post<HistoricalCase>('/analogies/cases', data),
  updateCase: (caseId: string, data: Partial<HistoricalCase>) =>
    api.put<HistoricalCase>(`/analogies/cases/${caseId}`, data),
  deleteCase: (caseId: string) =>
    api.delete<{ status: string; case_id: string }>(`/analogies/cases/${caseId}`),
  seedCases: () =>
    api.post<{ seeded: number; message: string }>('/analogies/cases/seed'),
}

// --- Calibration ---
export const calibrationApi = {
  getSummary: () => api.get<CalibrationSummary>('/calibration/summary'),
  getRunDetail: (runId: string) => api.get<RunCalibrationDetail>(`/calibration/runs/${runId}`),
  getTheories: () => api.get<TheoryCalibration>('/calibration/theories'),
  getDirections: () => api.get<DirectionCalibration>('/calibration/directions'),
}

// --- Annotations ---
export const annotationApi = {
  create: (data: AnnotationCreate) =>
    api.post<Annotation>('/annotations', data),

  list: (params?: {
    entity_type?: string
    entity_id?: string
    tag?: string
    importance?: string
    limit?: number
  }) => api.get<{ total: number; items: Annotation[] }>('/annotations', { params }),

  getForEntity: (entityType: string, entityId: string) =>
    api.get<{ entity_type: string; entity_id: string; total: number; items: Annotation[] }>(
      `/annotations/entity/${entityType}/${entityId}`
    ),

  get: (annotationId: string) =>
    api.get<Annotation>(`/annotations/${annotationId}`),

  update: (annotationId: string, data: AnnotationUpdate) =>
    api.patch<Annotation>(`/annotations/${annotationId}`, data),

  delete: (annotationId: string) =>
    api.delete<{ status: string; annotation_id: string }>(`/annotations/${annotationId}`),
}
