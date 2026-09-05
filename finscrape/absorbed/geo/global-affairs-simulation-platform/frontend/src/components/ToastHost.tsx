import { X, CheckCircle2, AlertTriangle, XCircle } from 'lucide-react'
import { useToastStore } from '../store/toast'

function levelMeta(level: 'success' | 'warn' | 'error') {
  if (level === 'success') {
    return {
      icon: CheckCircle2,
      ring: 'ring-emerald-500/30',
      border: 'border-emerald-500/25',
      bg: 'bg-emerald-500/10',
      text: 'text-emerald-300',
    }
  }
  if (level === 'warn') {
    return {
      icon: AlertTriangle,
      ring: 'ring-amber-500/30',
      border: 'border-amber-500/25',
      bg: 'bg-amber-500/10',
      text: 'text-amber-300',
    }
  }
  return {
    icon: XCircle,
    ring: 'ring-red-500/30',
    border: 'border-red-500/25',
    bg: 'bg-red-500/10',
    text: 'text-red-300',
  }
}

export default function ToastHost() {
  const toasts = useToastStore((s) => s.toasts)
  const dismiss = useToastStore((s) => s.dismiss)

  if (toasts.length === 0) return null

  return (
    <div className="fixed z-[1000] bottom-4 right-4 space-y-2 w-[360px] max-w-[calc(100vw-2rem)] pointer-events-none">
      {toasts.map((t) => {
        const meta = levelMeta(t.level)
        const Icon = meta.icon
        return (
          <div
            key={t.id}
            className={`pointer-events-auto bg-surface-900 border ${meta.border} rounded-xl p-3 shadow-xl ring-1 ${meta.ring} backdrop-blur`}
          >
            <div className="flex items-start gap-2.5">
              <Icon size={16} className={`${meta.text} shrink-0 mt-0.5`} />
              <div className="flex-1 min-w-0">
                {t.title && <div className="text-xs font-semibold text-slate-200">{t.title}</div>}
                <div className="text-sm text-slate-200 leading-snug break-words">{t.message}</div>
                {t.action && (
                  <button
                    onClick={() => {
                      try { t.action?.onClick() } finally { dismiss(t.id) }
                    }}
                    className={`mt-2 inline-flex items-center justify-center px-2.5 py-1 rounded-lg text-xs font-medium ${meta.bg} ${meta.text} border ${meta.border} hover:opacity-90`}
                  >
                    {t.action.label}
                  </button>
                )}
              </div>
              <button
                onClick={() => dismiss(t.id)}
                className="p-1.5 rounded-lg text-slate-500 hover:text-white hover:bg-surface-800 transition-colors"
                aria-label="Dismiss"
              >
                <X size={14} />
              </button>
            </div>
          </div>
        )
      })}
    </div>
  )
}

