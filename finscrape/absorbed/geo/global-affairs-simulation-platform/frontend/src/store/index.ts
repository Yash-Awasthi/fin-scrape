import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { AbstractIRGEvent, NewsCluster, RawNews, GlobePoint, GlobeRelationship } from '../types'
import { eventApi, globeApi } from '../services/api'

interface AppState {
  // --- 当前选中 ---
  selectedEventId: string | null
  selectedClusterId: string | null
  selectedRunId: string | null

  // --- 数据缓存 ---
  events: AbstractIRGEvent[]
  clusters: NewsCluster[]
  news: RawNews[]
  globePoints: GlobePoint[]
  globeRelationships: GlobeRelationship[]
  globeNoCoordsCount: number

  // --- 加载状态 ---
  eventsLoading: boolean
  globeLoading: boolean

  // --- 数据源/更新时间 ---
  dataSource: 'live' | 'mock' | 'stale_snapshot' | 'empty'
  isLoading: boolean
  lastUpdated: string | null

  // --- Pipeline状态 ---
  pipelineRunning: boolean
  pipelineTaskId: string | null

  // --- Setters ---
  setSelectedEvent: (id: string | null) => void
  setSelectedCluster: (id: string | null) => void
  setSelectedRun: (id: string | null) => void
  setEvents: (events: AbstractIRGEvent[]) => void
  setClusters: (clusters: NewsCluster[]) => void
  setNews: (news: RawNews[]) => void
  setGlobePoints: (points: GlobePoint[]) => void
  setDataSource: (source: AppState['dataSource']) => void
  setLoading: (loading: boolean) => void
  setLastUpdated: (ts: string) => void
  setPipelineRunning: (running: boolean, taskId?: string | null) => void

  // --- 异步获取 ---
  /** 拉事件列表写store */
  fetchEvents: () => Promise<void>
  /** 拉地球坐标写store */
  fetchGlobePoints: () => Promise<void>
  /** pipeline完成后刷数据+重置状态 */
  refreshAfterPipeline: () => Promise<void>
}

export const useAppStore = create<AppState>()(
  persist(
    (set, get) => ({
      selectedEventId: null,
      selectedClusterId: null,
      selectedRunId: null,

      events: [],
      clusters: [],
      news: [],
      globePoints: [],
      globeRelationships: [],
      globeNoCoordsCount: 0,

      eventsLoading: false,
      globeLoading: false,

      dataSource: 'empty',
      isLoading: false,
      lastUpdated: null,

      pipelineRunning: false,
      pipelineTaskId: null,

      setSelectedEvent: (id) => set({ selectedEventId: id }),
      setSelectedCluster: (id) => set({ selectedClusterId: id }),
      setSelectedRun: (id) => set({ selectedRunId: id }),
      setEvents: (events) => set({ events }),
      setClusters: (clusters) => set({ clusters }),
      setNews: (news) => set({ news }),
      setGlobePoints: (points) => set({ globePoints: points }),
      setDataSource: (dataSource) => set({ dataSource }),
      setLoading: (isLoading) => set({ isLoading }),
      setLastUpdated: (ts) => set({ lastUpdated: ts }),
      setPipelineRunning: (running, taskId = null) =>
        set({ pipelineRunning: running, pipelineTaskId: taskId }),

      fetchEvents: async () => {
        if (get().eventsLoading) return
        set({ eventsLoading: true })
        try {
          const res = await eventApi.list()
          const items = res.data.items ?? []
          set({
            events: items,
            lastUpdated: new Date().toISOString(),
            dataSource: items.length > 0 ? 'live' : 'empty',
          })
        } catch (err) {
          console.error('[store] fetchEvents failed:', err)
        } finally {
          set({ eventsLoading: false })
        }
      },

      fetchGlobePoints: async () => {
        if (get().globeLoading) {
          await new Promise<void>((resolve) => {
            const unsub = useAppStore.subscribe((state) => {
              if (!state.globeLoading) {
                unsub()
                resolve()
              }
            })
          })
          return
        }
        set({ globeLoading: true })
        try {
          const res = await globeApi.getPoints()
          set({
            globePoints: res.data.points ?? [],
            globeRelationships: res.data.relationships ?? [],
            globeNoCoordsCount: res.data.no_coords_count ?? 0,
          })
        } catch (err) {
          console.error('[store] fetchGlobePoints failed:', err)
        } finally {
          set({ globeLoading: false })
        }
      },

      refreshAfterPipeline: async () => {
        await Promise.allSettled([
          get().fetchEvents(),
          get().fetchGlobePoints(),
        ])
        set({ pipelineRunning: false, pipelineTaskId: null })
      },
    }),
    {
      name: 'ir-platform-store',
      partialize: (state) => ({
        selectedEventId: state.selectedEventId,
        selectedClusterId: state.selectedClusterId,
        selectedRunId: state.selectedRunId,
        dataSource: state.dataSource,
        lastUpdated: state.lastUpdated,
      }),
    }
  )
)
