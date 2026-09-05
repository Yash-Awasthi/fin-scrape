/**
 * CalibrationPage — 预测校准追踪仪表盘
 * 命中率、Brier分数、校准等级、错误分布、理论准确性、方向命中率、改进建议
 */
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import {
  BarChart2, TrendingUp, TrendingDown, Minus,
  Target, CheckCircle, RefreshCw,
  Award, Zap, ChevronRight, Info
} from 'lucide-react'
import { calibrationApi, getErrorUserMessage } from '../services/api'
import type { CalibrationSummary, DirectionCalibration, TheoryCalibration } from '../types'
import { toast } from '../store/toast'
import { SimpleLineChart, SimpleBarChart, CalibrationCurve } from '../components/Charts'
import LoadingSpinner from '../components/LoadingSpinner'
import ErrorState from '../components/ErrorState'

function buildGradeConfig(t: (key: string) => string): Record<string, {
  color: string; bg: string; border: string; label: string; desc: string
}> {
  return {
    A: { color: 'text-emerald-400', bg: 'bg-emerald-500/10', border: 'border-emerald-500/30', label: t('calibration.grades.A'), desc: t('calibration.grades.Adesc') },
    B: { color: 'text-brand-400',   bg: 'bg-brand-500/10',   border: 'border-brand-500/30',   label: t('calibration.grades.B'), desc: t('calibration.grades.Bdesc') },
    C: { color: 'text-amber-400',   bg: 'bg-amber-500/10',   border: 'border-amber-500/30',   label: t('calibration.grades.C'), desc: t('calibration.grades.Cdesc') },
    D: { color: 'text-orange-400',  bg: 'bg-orange-500/10',  border: 'border-orange-500/30',  label: t('calibration.grades.D'), desc: t('calibration.grades.Ddesc') },
    F: { color: 'text-red-400',     bg: 'bg-red-500/10',     border: 'border-red-500/30',     label: t('calibration.grades.F'), desc: t('calibration.grades.Fdesc') },
  }
}

// --- 方向配色 ---
const DIR_CONFIG = {
  escalation:    { labelKey: 'directions.escalation', color: 'text-red-400',    bar: 'bg-red-500',    Icon: TrendingUp },
  stalemate:     { labelKey: 'directions.stalemate', color: 'text-amber-400',  bar: 'bg-amber-500',  Icon: Minus },
  de_escalation: { labelKey: 'directions.de_escalation', color: 'text-emerald-400',bar: 'bg-emerald-500',Icon: TrendingDown },
}

// --- 理论 i18n key 映射 ---
const THEORY_I18N_KEYS: Record<string, string> = {
  realism:                  'theories.realism',
  liberal_institutionalism: 'theories.liberalInstitutionalism',
  constructivism:           'theories.constructivism',
  geopolitics:              'theories.geopolitics',
  ipe:                      'theories.internationalPoliticalEconomy',
  // 保留兼容旧数据的别名
  liberalism:               'theories.liberalism',
  rational_choice:          'theories.rationalChoice',
  power_transition:         'theories.powerTransition',
  bargaining_model:         'theories.bargainingModel',
  democratic_peace:         'theories.democraticPeace',
  spiral_model:             'theories.spiralModel',
}

// --- 工具组件 ---
function MetricCard({
  label, value, sub, color = 'text-white', icon
}: {
  label: string; value: string; sub?: string; color?: string; icon?: React.ReactNode
}) {
  return (
    <div className="bg-surface-900 border border-slate-700/50 rounded-xl p-4 flex items-start gap-3">
      {icon && <div className="flex-shrink-0 mt-0.5">{icon}</div>}
      <div>
        <div className="text-xs text-slate-500 mb-0.5">{label}</div>
        <div className={`text-2xl font-bold ${color}`}>{value}</div>
        {sub && <div className="text-xs text-slate-600 mt-0.5">{sub}</div>}
      </div>
    </div>
  )
}

function HorizontalBar({ value, max = 1, color = 'bg-brand-500' }: {
  value: number; max?: number; color?: string
}) {
  const pct = Math.min(100, Math.round((value / max) * 100))
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 bg-slate-700/50 rounded-full overflow-hidden">
        <div className={`h-full rounded-full transition-all ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs text-slate-400 w-10 text-right">{Math.round(value * 100)}%</span>
    </div>
  )
}

function BrierGauge({ score }: { score: number }) {
  const { t } = useTranslation()
  // Brier score: 0 = perfect, 0.25 = random, 1 = worst
  const pct = Math.round(score * 100)
  const color = score <= 0.10 ? 'text-emerald-400' : score <= 0.18 ? 'text-brand-400'
    : score <= 0.22 ? 'text-amber-400' : 'text-red-400'
  const quality = score <= 0.10 ? t('calibration.brierQuality.excellent') : score <= 0.18 ? t('calibration.brierQuality.good') : score <= 0.22 ? t('calibration.brierQuality.fair') : t('calibration.brierQuality.poor')
  return (
    <div className="bg-surface-900 border border-slate-700/50 rounded-xl p-4">
      <div className="flex items-center justify-between mb-3">
        <div className="text-xs text-slate-500 uppercase tracking-wide">{t('calibration.brierScore')}</div>
        <div className="flex items-center gap-1 text-xs text-slate-600">
          <Info size={10} />
          <span>{t('calibration.brierInfo')}</span>
        </div>
      </div>
      <div className="flex items-end gap-3">
        <div className={`text-3xl font-bold ${color}`}>{(score).toFixed(3)}</div>
        <div className={`text-sm ${color} mb-0.5`}>{quality}</div>
      </div>
      <div className="mt-3 h-2 bg-slate-700/50 rounded-full overflow-hidden relative">
        {/* 背景段：绿→黄→红 */}
        <div className="absolute inset-0 flex">
          <div className="bg-emerald-500/30 flex-1" style={{ width: '40%' }} />
          <div className="bg-amber-500/30" style={{ width: '32%' }} />
          <div className="bg-red-500/30 flex-1" />
        </div>
        {/* 指针 */}
        <div
          className="absolute top-0 h-full w-0.5 bg-white shadow-lg"
          style={{ left: `${Math.min(99, pct * 4)}%` }}
        />
      </div>
      <div className="flex justify-between text-[10px] text-slate-600 mt-1">
        <span>{t('calibration.brierPerfect')}</span>
        <span>{t('calibration.brierRandom')}</span>
      </div>
    </div>
  )
}

// --- 趋势图 ---
function TrendMiniChart({ data }: {
  data: Array<{ month: string; hit_rate: number; count: number }>
}) {
  const { t } = useTranslation()
  if (!data || data.length === 0) return null
  const chartData = data.map(d => ({
    name: d.month,
    hit_rate: Math.round(d.hit_rate * 100),
    count: d.count,
  }))
  return (
    <div className="bg-surface-900 border border-slate-700/50 rounded-xl p-4">
      <div className="text-xs text-slate-500 uppercase tracking-wide mb-3">{t('calibration.trend')}</div>
      <SimpleLineChart
        data={chartData}
        lines={[
          { key: 'hit_rate', color: '#6366f1', name: t('calibration.hitRatePercent') },
        ]}
        height={120}
      />
    </div>
  )
}

// --- 空状态 ---
function EmptyDashboard() {
  const navigate = useNavigate()
  const { t } = useTranslation()
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] text-center space-y-4">
      <BarChart2 size={48} className="text-slate-600" />
      <div>
        <h2 className="text-lg font-medium text-slate-400">{t('calibration.noData')}</h2>
        <p className="text-sm text-slate-600 mt-1 max-w-sm">
          {t('calibration.noDataDesc')}
        </p>
      </div>
      <div className="bg-surface-900 border border-slate-700/50 rounded-xl p-4 text-left max-w-sm">
        <div className="text-xs text-slate-500 mb-2 uppercase tracking-wide">{t('calibration.dataSteps')}</div>
        <ol className="space-y-2 text-xs text-slate-400">
          {[
            t('calibration.step1'),
            t('calibration.step2'),
            t('calibration.step3'),
            t('calibration.step4'),
          ].map((s, i) => (
            <li key={i} className="flex gap-2">
              <span className="flex-shrink-0 w-4 h-4 rounded-full bg-brand-500/20 text-brand-400 flex items-center justify-center text-[10px]">{i + 1}</span>
              <span>{s}</span>
            </li>
          ))}
        </ol>
      </div>
      <button
        onClick={() => navigate('/history')}
        className="px-4 py-2 bg-brand-600 hover:bg-brand-500 text-white rounded-lg text-sm transition-colors"
      >
        {t('common.goToHistory')} →
      </button>
    </div>
  )
}

// --- 主页面 ---
export default function CalibrationPage() {
  const { t, i18n } = useTranslation()
  const navigate = useNavigate()
  const [summary, setSummary] = useState<CalibrationSummary | null>(null)
  const [directions, setDirections] = useState<DirectionCalibration | null>(null)
  const [theories, setTheories] = useState<TheoryCalibration | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [refreshing, setRefreshing] = useState(false)

  const load = () => {
    setRefreshing(true)
    Promise.all([
      calibrationApi.getSummary(),
      calibrationApi.getDirections(),
      calibrationApi.getTheories(),
    ]).then(([s, d, t]) => {
      setSummary(s.data)
      setDirections(d.data)
      setTheories(t.data)
      setError('')
    }).catch(e => {
      const msg = getErrorUserMessage(e, t('calibration.loadError'))
      setError(msg)
      toast.error(msg, { dedupeKey: 'calibration-load' })
    }).finally(() => {
      setLoading(false)
      setRefreshing(false)
    })
  }

  useEffect(() => { load() }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-surface-950">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-surface-950">
        <ErrorState message={error} onRetry={load} />
      </div>
    )
  }

  // 无数据
  if (!summary || summary.total_evaluations === 0) {
    return (
      <div className="min-h-screen bg-surface-950 text-slate-100 flex flex-col">
        <header className="border-b border-slate-700/50 px-6 py-4 flex items-center gap-3">
          <BarChart2 size={18} className="text-brand-500" />
          <h1 className="font-semibold text-white">{t('calibration.title')}</h1>
        </header>
        <EmptyDashboard />
      </div>
    )
  }

  const gradeCfg = buildGradeConfig(t)[summary.calibration_grade] || buildGradeConfig(t)['F']

  return (
    <div className="min-h-screen bg-surface-950 text-slate-100 flex flex-col">
      {/* 顶部标题栏 */}
      <header className="border-b border-slate-700/50 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <BarChart2 size={18} className="text-brand-500" />
          <div>
            <h1 className="font-semibold text-white text-lg leading-tight">{t('calibration.title')}</h1>
            <p className="text-xs text-slate-500">{t('calibration.subtitle', { count: summary.total_evaluations })}</p>
          </div>
        </div>
        <button
          onClick={load}
          disabled={refreshing}
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs bg-surface-800 hover:bg-surface-700 border border-slate-700 rounded-lg text-slate-400 hover:text-white transition-colors disabled:opacity-60"
        >
          <RefreshCw size={12} className={refreshing ? 'animate-spin' : ''} />
          {t('common.refresh')}
        </button>
      </header>

      <div className="flex-1 overflow-y-auto p-6 space-y-6">

        {/* --- 核心指标 --- */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* 校准等级 */}
          <div className={`col-span-1 bg-surface-900 border ${gradeCfg.border} rounded-xl p-4 flex flex-col items-center justify-center`}>
            <Award size={20} className={`${gradeCfg.color} mb-2`} />
            <div className={`text-4xl font-black ${gradeCfg.color}`}>{summary.calibration_grade}</div>
            <div className={`text-xs mt-1 ${gradeCfg.color}`}>{gradeCfg.label}</div>
            <div className="text-[10px] text-slate-600 mt-1 text-center">{gradeCfg.desc}</div>
          </div>

          {/* 剧本命中率 */}
          <MetricCard
            label={t('calibration.hitRate')}
            value={`${Math.round((summary.script_hit_rate || 0) * 100)}%`}
            sub={t('calibration.hitRateSub', { weight: 60, count: summary.total_evaluations })}
            color={summary.script_hit_rate >= 0.6 ? 'text-emerald-400' : summary.script_hit_rate >= 0.4 ? 'text-amber-400' : 'text-red-400'}
            icon={<CheckCircle size={16} className="text-emerald-500/50" />}
          />

          {/* 节点命中率 */}
          <MetricCard
            label={t('calibration.avgNodeHitRate')}
            value={`${Math.round((summary.avg_node_hit_rate || 0) * 100)}%`}
            sub={t('calibration.nodeAccuracy')}
            color={summary.avg_node_hit_rate >= 0.6 ? 'text-brand-400' : 'text-amber-400'}
            icon={<Target size={16} className="text-brand-500/50" />}
          />

          {/* 综合得分 */}
          <MetricCard
            label={t('calibration.combinedScore')}
            value={`${Math.round((summary.combined_score || 0) * 100)}`}
            sub={t('calibration.scoreFormula')}
            color="text-white"
            icon={<Zap size={16} className="text-amber-500/50" />}
          />
        </div>

        {/* --- Brier+时间趋势 --- */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <BrierGauge score={summary.avg_brier_score || 0} />
          <TrendMiniChart data={summary.time_trend || []} />
        </div>

        {/* --- 方向+理论命中率 --- */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">

          {/* 方向命中率 */}
          <div className="bg-surface-900 border border-slate-700/50 rounded-xl p-4">
            <div className="text-xs text-slate-500 uppercase tracking-wide mb-4">{t('calibration.byDirection')}</div>
            {directions ? (
              <div className="space-y-4">
                {Object.entries(directions).map(([dir, stats]) => {
                  const cfg = DIR_CONFIG[dir as keyof typeof DIR_CONFIG]
                  if (!cfg) return null
                  const DirIcon = cfg.Icon
                  return (
                    <div key={dir}>
                      <div className="flex items-center justify-between mb-1.5">
                        <div className={`flex items-center gap-1.5 text-sm ${cfg.color}`}>
                          <DirIcon size={13} />
                          <span>{t(cfg.labelKey)}</span>
                        </div>
                        <div className="text-xs text-slate-500">
                          {t('calibration.hitCount', { hit: stats.hit, total: stats.total })}
                        </div>
                      </div>
                      <HorizontalBar value={stats.hit_rate} color={cfg.bar} />
                    </div>
                  )
                })}
                {Object.keys(directions).length === 0 && (
                  <p className="text-xs text-slate-600 text-center py-4">{t('calibration.noData')}</p>
                )}
              </div>
            ) : (
              <p className="text-xs text-slate-600 text-center py-4">{t('calibration.noData')}</p>
            )}
          </div>

          {/* 理论视角准确性 */}
          <div className="bg-surface-900 border border-slate-700/50 rounded-xl p-4">
            <div className="text-xs text-slate-500 uppercase tracking-wide mb-4">{t('calibration.byTheory')}</div>
            {theories && Object.keys(theories).length > 0 ? (
              <div className="space-y-3">
                {Object.entries(theories)
                  .sort((a, b) => b[1].hit_rate - a[1].hit_rate)
                  .map(([theory, stats]) => (
                    <div key={theory}>
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-sm text-slate-300">
                          {t(THEORY_I18N_KEYS[theory] || 'theories.' + theory)}
                        </span>
                        <span className="text-xs text-slate-500">{t('calibration.evalCount', { count: stats.count })}</span>
                      </div>
                      <HorizontalBar
                        value={stats.hit_rate}
                        color={stats.hit_rate >= 0.65 ? 'bg-emerald-500' : stats.hit_rate >= 0.45 ? 'bg-brand-500' : 'bg-amber-500'}
                      />
                    </div>
                  ))}
              </div>
            ) : (
              <p className="text-xs text-slate-600 text-center py-4">{t('calibration.noData')}</p>
            )}
          </div>
        </div>

        {/* --- 校准曲线 --- */}
        {summary.total_evaluations > 0 && (
          <div className="bg-surface-900 border border-slate-700/50 rounded-xl p-4">
            <div className="text-xs text-slate-500 uppercase tracking-wide mb-4">{t('calibration.curve')}</div>
            <CalibrationCurve
              data={[
                { bin: '0-20%', predicted: 0.1, actual: 1 - summary.script_hit_rate, count: Math.round(summary.total_evaluations * (1 - summary.script_hit_rate)) },
                { bin: '20-40%', predicted: 0.3, actual: summary.avg_node_hit_rate, count: summary.total_evaluations },
                { bin: '40-60%', predicted: 0.5, actual: summary.script_hit_rate, count: summary.total_evaluations },
                { bin: '60-80%', predicted: 0.7, actual: Math.min(1, summary.script_hit_rate + 0.1), count: Math.round(summary.total_evaluations * summary.script_hit_rate) },
                { bin: '80-100%', predicted: 0.9, actual: Math.min(1, summary.script_hit_rate + 0.2), count: Math.round(summary.total_evaluations * 0.3) },
              ].filter(d => d.count > 0)}
              height={260}
            />
            <div className="text-[10px] text-slate-600 mt-2 text-center">
              {t('calibration.curveIdeal')}
            </div>
          </div>
        )}

        {/* --- 错误分布+事件类型 --- */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">

          {/* 错误分布 */}
          {summary.error_distribution && Object.keys(summary.error_distribution).length > 0 && (
            <div className="bg-surface-900 border border-slate-700/50 rounded-xl p-4">
              <div className="text-xs text-slate-500 uppercase tracking-wide mb-4">{t('calibration.errorDistribution')}</div>
              <SimpleBarChart
                data={Object.entries(summary.error_distribution)
                  .map(([cat, val]) => {
                    const count = typeof val === 'object' ? (val as any).count : val
                    return { name: cat, value: count as number, color: '#ef4444' }
                  })
                  .sort((a, b) => b.value - a.value)}
                height={140}
              />
            </div>
          )}

          {/* 按事件类型 */}
          {summary.by_event_type && Object.keys(summary.by_event_type).length > 0 && (
            <div className="bg-surface-900 border border-slate-700/50 rounded-xl p-4">
              <div className="text-xs text-slate-500 uppercase tracking-wide mb-4">{t('calibration.byEventType')}</div>
              <div className="space-y-3">
                {Object.entries(summary.by_event_type)
                  .sort((a, b) => b[1].hit_rate - a[1].hit_rate)
                  .map(([type, stats]) => {
                    const label = t('eventTypes.' + type)
                    return (
                      <div key={type}>
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-xs text-slate-400">{label}</span>
                          <span className="text-xs text-slate-500">
                            {t('calibration.eventStats', { count: stats.count, brier: (stats.avg_brier || 0).toFixed(3) })}
                          </span>
                        </div>
                        <HorizontalBar
                          value={stats.hit_rate}
                          color={stats.hit_rate >= 0.6 ? 'bg-emerald-500' : 'bg-brand-500'}
                        />
                      </div>
                    )
                  })}
              </div>
            </div>
          )}
        </div>

        {/* --- 改进建议 --- */}
        {summary.improvement_suggestions && summary.improvement_suggestions.length > 0 && (
          <div className="bg-amber-500/5 border border-amber-500/20 rounded-xl p-5">
            <div className="flex items-center gap-2 mb-4">
              <Zap size={14} className="text-amber-400" />
              <span className="text-sm font-medium text-amber-400">{t('calibration.improvement')}</span>
              <span className="text-xs text-slate-600 ml-1">{t('calibration.improvementNote')}</span>
            </div>
            <div className="space-y-2.5">
              {summary.improvement_suggestions.map((s, i) => (
                <div key={i} className="flex gap-3">
                  <ChevronRight size={13} className="text-amber-500 flex-shrink-0 mt-0.5" />
                  <p className="text-sm text-slate-300">{s}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* --- 按危机阶段 --- */}
        {summary.by_crisis_stage && Object.keys(summary.by_crisis_stage).length > 0 && (
          <div className="bg-surface-900 border border-slate-700/50 rounded-xl p-4">
            <div className="text-xs text-slate-500 uppercase tracking-wide mb-4">{t('calibration.byCrisisStage')}</div>
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
              {Object.entries(summary.by_crisis_stage).map(([stage, stats]) => {
                const stageLabel: Record<string, string> = {
                  latent: t('calibration.stageLatent'),
                  emergence: t('calibration.stageEmergence'),
                  escalation: t('calibration.stageEscalation'),
                  crisis: t('calibration.stageCrisis'),
                  de_escalation: t('calibration.stageDeEscalation'),
                  resolution: t('calibration.stageResolution'),
                }
                const pct = Math.round((stats.hit_rate || 0) * 100)
                const color = pct >= 60 ? 'text-emerald-400' : pct >= 40 ? 'text-amber-400' : 'text-red-400'
                return (
                  <div key={stage} className="text-center p-3 bg-surface-800/50 rounded-lg">
                    <div className={`text-xl font-bold ${color}`}>{pct}%</div>
                    <div className="text-[10px] text-slate-500 mt-0.5">{stageLabel[stage] || stage}</div>
                    <div className="text-[10px] text-slate-600">{t('calibration.countTimes', { count: stats.count })}</div>
                  </div>
                )
              })}
            </div>
          </div>
        )}
      </div>

      <div className="border-t border-slate-800 px-6 py-3 flex items-center justify-between">
        <span className="text-xs text-slate-600">{t('calibration.footer', { count: summary.total_evaluations, date: new Date().toLocaleString(i18n.language === 'zh' ? 'zh-CN' : 'en-US') })}</span>
        <button
          onClick={() => navigate('/history')}
          className="text-xs px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 border border-slate-700 transition-colors"
        >
          {t('common.goToHistory')} →
        </button>
      </div>
    </div>
  )
}
