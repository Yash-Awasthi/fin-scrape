import { BrowserRouter, Routes, Route, NavLink, Navigate, useLocation } from 'react-router-dom'
import {
  Globe2, Newspaper, Layers, BookOpen,
  GitBranch, History, FileText, Cpu, Activity,
  BookMarked, BarChart2, PowerOff, Loader2, Menu, X,
  Sun, Moon, Languages
} from 'lucide-react'
import { useEffect, useRef, useState, useCallback } from 'react'
import type { ReactNode } from 'react'
import { useTranslation } from 'react-i18next'
import { healthApi } from './services/api'
import ToastHost from './components/ToastHost'
import ErrorBoundary from './components/ErrorBoundary'
import OnboardingTour from './components/OnboardingTour'
import { useAppStore } from './store'

import GlobePage from './pages/GlobePage'
import ClustersPage from './pages/ClustersPage'
import EventsPage from './pages/EventsPage'
import TheoryPage from './pages/TheoryPage'
import ScenariosPage from './pages/ScenariosPage'
import BranchPage from './pages/BranchPage'
import HistoryPage from './pages/HistoryPage'
import ReportPage from './pages/ReportPage'
import PipelinePage from './pages/PipelinePage'
import AnalogiesPage from './pages/AnalogiesPage'
import CalibrationPage from './pages/CalibrationPage'

function PageErrorBoundary({ children }: { children: ReactNode }) {
  const location = useLocation()
  return (
    <ErrorBoundary resetKey={location.pathname}>
      {children}
    </ErrorBoundary>
  )
}

export default function App() {
  const { t, i18n } = useTranslation()
  const [backendOk, setBackendOk] = useState<boolean | null>(null)
  const [exitConfirm, setExitConfirm] = useState(false)
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [darkMode, setDarkMode] = useState(() => {
    const saved = localStorage.getItem('ir_platform_theme')
    return saved ? saved === 'dark' : true
  })
  const backendOkRef = useRef<boolean | null>(null)

  const pipelineRunning = useAppStore((s) => s.pipelineRunning)
  const eventCount = useAppStore((s) => s.events.length)
  const fetchEvents = useAppStore((s) => s.fetchEvents)
  const fetchGlobePoints = useAppStore((s) => s.fetchGlobePoints)

  const closeSidebar = useCallback(() => setSidebarOpen(false), [])

  useEffect(() => {
    document.documentElement.classList.toggle('light', !darkMode)
    document.documentElement.classList.toggle('dark', darkMode)
    localStorage.setItem('ir_platform_theme', darkMode ? 'dark' : 'light')
  }, [darkMode])

  const toggleLang = useCallback(() => {
    const next = i18n.language === 'zh' ? 'en' : 'zh'
    i18n.changeLanguage(next)
    localStorage.setItem('ir_platform_lang', next)
  }, [i18n])

  const pipelineRunningRef = useRef(pipelineRunning)
  useEffect(() => { pipelineRunningRef.current = pipelineRunning }, [pipelineRunning])

  useEffect(() => {
    let timer: ReturnType<typeof setTimeout>

    const check = () => {
      healthApi.check()
        .then(() => {
          if (backendOkRef.current !== true) {
            setBackendOk(true)
            backendOkRef.current = true
          }
        })
        .catch(() => {
          if (backendOkRef.current !== false) {
            setBackendOk(false)
            backendOkRef.current = false
          }
        })
        .finally(() => {
          const offline = backendOkRef.current === false
          const interval = offline ? 8000 : pipelineRunningRef.current ? 10000 : 30000
          timer = setTimeout(check, interval)
        })
    }

    check()

    return () => clearTimeout(timer)
  }, [])

  useEffect(() => {
    fetchEvents()
    fetchGlobePoints()
  }, [fetchEvents, fetchGlobePoints])

  const exitTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const handleExit = () => {
    if (exitConfirm) {
      if (exitTimerRef.current) clearTimeout(exitTimerRef.current)
      window.close()
      setTimeout(() => { window.location.href = 'about:blank' }, 200)
    } else {
      setExitConfirm(true)
      if (exitTimerRef.current) clearTimeout(exitTimerRef.current)
      exitTimerRef.current = setTimeout(() => setExitConfirm(false), 3000)
    }
  }

  const navItems = [
    { to: '/', icon: Globe2, label: t('nav.globe'), end: true },
    { to: '/pipeline', icon: Cpu, label: t('nav.pipeline') },
    { to: '/clusters', icon: Newspaper, label: t('nav.clusters') },
    { to: '/events', icon: Layers, label: t('nav.events') },
    { to: '/theories', icon: BookOpen, label: t('nav.theories') },
    { to: '/scenarios', icon: Activity, label: t('nav.scenarios') },
    { to: '/branches', icon: GitBranch, label: t('nav.branches') },
    { to: '/analogies', icon: BookMarked, label: t('nav.analogies') },
    { to: '/history', icon: History, label: t('nav.history') },
    { to: '/calibration', icon: BarChart2, label: t('nav.calibration') },
    { to: '/reports', icon: FileText, label: t('nav.reports') },
  ]

  return (
    <BrowserRouter>
      <div className="flex h-screen overflow-hidden bg-surface-950">
        <ToastHost />
        <OnboardingTour />

        <div className="md:hidden fixed top-0 left-0 right-0 z-40 h-12 bg-surface-900 border-b border-surface-700/50 flex items-center px-3">
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="p-1.5 text-slate-400 hover:text-white"
            aria-label={sidebarOpen ? t('common.closeMenu') : t('common.openMenu')}
            aria-expanded={sidebarOpen}
          >
            {sidebarOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
          <div className="flex items-center gap-2 ml-2">
            <Globe2 className="text-brand-500" size={16} />
            <span className="text-sm font-semibold text-white">{t('app.name')}</span>
          </div>
          <div className="ml-auto flex items-center gap-1.5">
            <div className={`w-1.5 h-1.5 rounded-full ${
              backendOk === null ? 'bg-slate-500' :
              backendOk ? 'bg-green-500 animate-pulse' : 'bg-red-500'
            }`} />
            <span className="text-[10px] text-slate-500">
              {backendOk === null ? '...' : backendOk ? t('app.online') : t('app.offline')}
            </span>
          </div>
        </div>

        {sidebarOpen && (
          <div
            className="md:hidden fixed inset-0 z-40 bg-black/50"
            onClick={closeSidebar}
            aria-hidden="true"
          />
        )}

        <aside className={`sidebar fixed md:static z-50 h-full transition-transform duration-200 ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'
        }`}>
          <div className="p-4 border-b border-surface-700/50">
            <div className="flex items-center gap-2">
              <Globe2 className="text-brand-500" size={20} />
              <div>
                <div className="text-sm font-semibold text-white leading-tight">{t('app.name')}</div>
                <div className="text-xs text-slate-500">{t('app.subtitle')}</div>
              </div>
            </div>
            <div className="mt-2 flex items-center gap-1.5">
              <div className={`w-1.5 h-1.5 rounded-full ${
                backendOk === null ? 'bg-slate-500' :
                backendOk ? 'bg-green-500 animate-pulse' : 'bg-red-500'
              }`} />
              <span className="text-xs text-slate-500">
                {backendOk === null ? t('app.connecting') : backendOk ? t('app.backendOnline') : t('app.backendOffline')}
              </span>
            </div>

            {pipelineRunning && (
              <div className="mt-2 flex items-center gap-1.5 px-2 py-1.5 rounded-md bg-brand-500/10 border border-brand-500/30">
                <Loader2 size={11} className="text-brand-400 animate-spin shrink-0" />
                <span className="text-[11px] text-brand-400 leading-tight">{t('app.analysisInProgress')}</span>
              </div>
            )}

            {!pipelineRunning && eventCount > 0 && (
              <div className="mt-2 text-[10px] text-slate-600">
                {t('app.eventsLoaded', { count: eventCount })}
              </div>
            )}
          </div>

          <nav className="flex-1 p-2 space-y-0.5 overflow-y-auto" aria-label={t('nav.main')}>
            {navItems.map(({ to, icon: Icon, label, end }) => (
              <NavLink
                key={to}
                to={to}
                end={end}
                onClick={closeSidebar}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-all ${
                    isActive
                      ? 'bg-brand-500/20 text-brand-400 font-medium'
                      : 'text-slate-400 hover:text-white hover:bg-surface-800'
                  }`
                }
              >
                <Icon size={16} />
                {label}
                {to === '/pipeline' && pipelineRunning && (
                  <span className="ml-auto w-1.5 h-1.5 rounded-full bg-brand-400 animate-pulse" />
                )}
              </NavLink>
            ))}
          </nav>

          <div className="p-2 border-t border-surface-700/50 space-y-1">
            <div className="flex items-center gap-1 px-3 py-1.5">
              <button
                onClick={toggleLang}
                className="flex items-center gap-1.5 px-2 py-1 rounded text-xs text-slate-400 hover:text-white hover:bg-surface-800 transition-colors"
                title={t('common.language')}
                aria-label={t('common.switchLanguage')}
                aria-pressed={i18n.language === 'en'}
              >
                <Languages size={13} />
                <span>{i18n.language === 'zh' ? '中文' : 'EN'}</span>
              </button>
              <button
                onClick={() => setDarkMode(v => !v)}
                className="flex items-center gap-1.5 px-2 py-1 rounded text-xs text-slate-400 hover:text-white hover:bg-surface-800 transition-colors"
                title={t('common.theme')}
                aria-label={t('common.switchTheme')}
                aria-pressed={darkMode}
              >
                {darkMode ? <Sun size={13} /> : <Moon size={13} />}
                <span>{darkMode ? t('common.light') : t('common.dark')}</span>
              </button>
            </div>
            <button
              onClick={handleExit}
              className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-md text-sm transition-all ${
                exitConfirm
                  ? 'bg-red-500/20 text-red-400 ring-1 ring-red-500/40'
                  : 'text-slate-500 hover:text-red-400 hover:bg-surface-800'
              }`}
              aria-label={t('app.exit')}
            >
              <PowerOff size={15} />
              <span>{exitConfirm ? t('app.exitConfirm') : t('app.exit')}</span>
            </button>
          </div>
        </aside>

        <main className="main-content pt-12 md:pt-0">
          <PageErrorBoundary>
            <Routes>
              <Route path="/" element={<GlobePage />} />
              <Route path="/pipeline" element={<PipelinePage />} />
              <Route path="/clusters" element={<ClustersPage />} />
              <Route path="/events" element={<EventsPage />} />
              <Route path="/theories" element={<TheoryPage />} />
              <Route path="/scenarios" element={<ScenariosPage />} />
              <Route path="/branches" element={<BranchPage />} />
              <Route path="/analogies" element={<AnalogiesPage />} />
              <Route path="/history" element={<HistoryPage />} />
              <Route path="/calibration" element={<CalibrationPage />} />
              <Route path="/reports" element={<ReportPage />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </PageErrorBoundary>
        </main>
      </div>
    </BrowserRouter>
  )
}
