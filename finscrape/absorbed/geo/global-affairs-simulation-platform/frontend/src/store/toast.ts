import { create } from 'zustand'

export type ToastLevel = 'success' | 'warn' | 'error'

export interface ToastAction {
  label: string
  onClick: () => void
}

export interface ToastItem {
  id: string
  level: ToastLevel
  message: string
  title?: string
  action?: ToastAction
  createdAt: number
  durationMs: number
  dedupeKey?: string
}

interface ToastState {
  toasts: ToastItem[]
  _recent: Record<string, number>
  push: (t: Omit<ToastItem, 'id' | 'createdAt'> & { dedupeWindowMs?: number }) => string | null
  dismiss: (id: string) => void
  clear: () => void
}

function uid() {
  return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`
}

// timer放外部Map，不污染ToastItem，dismiss时精确clearTimeout
const _timers = new Map<string, ReturnType<typeof setTimeout>>()

export const useToastStore = create<ToastState>((set, get) => ({
  toasts: [],
  _recent: {},

  push: (t) => {
    const now = Date.now()
    const dedupeKey = t.dedupeKey
    const windowMs = t.dedupeWindowMs ?? 5000
    if (dedupeKey) {
      const last = get()._recent[dedupeKey] ?? 0
      if (now - last < windowMs) return null
    }

    const id = uid()
    const item: ToastItem = {
      id,
      level: t.level,
      title: t.title,
      message: t.message,
      action: t.action,
      durationMs: t.durationMs,
      createdAt: now,
      dedupeKey,
    }

    set((s) => ({
      toasts: [item, ...s.toasts].slice(0, 5),
      _recent: dedupeKey ? { ...s._recent, [dedupeKey]: now } : s._recent,
    }))

    // 外部Map持有timer，dismiss时clearTimeout
    const timerId = setTimeout(() => {
      _timers.delete(id)
      get().dismiss(id)
    }, item.durationMs)
    _timers.set(id, timerId)

    return id
  },

  dismiss: (id) => {
    // 清timer
    const timerId = _timers.get(id)
    if (timerId !== undefined) {
      clearTimeout(timerId)
      _timers.delete(id)
    }
    set((s) => ({ toasts: s.toasts.filter((x) => x.id !== id) }))
  },

  clear: () => {
    // 清空所有timer
    _timers.forEach((id) => clearTimeout(id))
    _timers.clear()
    set({ toasts: [] })
  },
}))

export const toast = {
  success: (message: string, opts?: Partial<Omit<ToastItem, 'id' | 'createdAt' | 'message' | 'level'>>) =>
    useToastStore.getState().push({
      level: 'success',
      message,
      durationMs: opts?.durationMs ?? 3500,
      title: opts?.title,
      action: opts?.action,
      dedupeKey: opts?.dedupeKey,
      dedupeWindowMs: 5000,
    }),
  warn: (message: string, opts?: Partial<Omit<ToastItem, 'id' | 'createdAt' | 'message' | 'level'>>) =>
    useToastStore.getState().push({
      level: 'warn',
      message,
      durationMs: opts?.durationMs ?? 4500,
      title: opts?.title,
      action: opts?.action,
      dedupeKey: opts?.dedupeKey,
      dedupeWindowMs: 5000,
    }),
  error: (message: string, opts?: Partial<Omit<ToastItem, 'id' | 'createdAt' | 'message' | 'level'>>) =>
    useToastStore.getState().push({
      level: 'error',
      message,
      durationMs: opts?.durationMs ?? 8000,
      title: opts?.title,
      action: opts?.action,
      dedupeKey: opts?.dedupeKey,
      dedupeWindowMs: 8000,
    }),
  /** 按key移除toast */
  dismissByKey: (dedupeKey: string) => {
    const store = useToastStore.getState()
    const item = store.toasts.find((t) => t.dedupeKey === dedupeKey)
    if (item) store.dismiss(item.id)
  },
}
