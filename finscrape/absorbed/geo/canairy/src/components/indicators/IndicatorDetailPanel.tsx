/**
 * IndicatorDetailPanel Component
 *
 * Right slide-out panel for indicator details.
 * Cards are previews — this panel is where the full story lives.
 */

import React, { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  X,
  TrendingUp,
  TrendingDown,
  Minus,
  ExternalLink,
  AlertTriangle,
  Home,
  Link2,
  Clock,
  Info,
  Activity,
} from 'lucide-react';
import { IndicatorData } from '../../types';
import { cn } from '../../utils/cn';
import { ThresholdBar, ThresholdLabels } from './ThresholdBar';
import { IndicatorChart } from '../charts/IndicatorChart';
import { generateHistoricalData } from '../../utils/historicalDataGenerator';
import {
  formatValue,
  formatDomain,
  getSourceDisplay,
  getSourceFull,
  getDescription,
  getHouseholdRelevance,
  getConnectedIndicators,
  getPhaseRelevance,
  getPhaseRelevanceLabel,
  getSourceInfo,
  formatTimeAgo,
  isCriticalIndicator,
  getCardImpactLine,
} from '../../data/indicatorDisplay';
import { getDisplayName } from '../../data/indicatorTranslations';
import { getIndicatorDescription } from '../../data/indicatorDescriptions';

interface IndicatorDetailPanelProps {
  indicator: IndicatorData;
  onClose: () => void;
  onNavigate?: (indicatorId: string) => void;
}

export const IndicatorDetailPanel: React.FC<IndicatorDetailPanelProps> = ({
  indicator,
  onClose,
  onNavigate,
}) => {
  const [timeRange, setTimeRange] = useState<'24h' | '7d' | '30d' | '90d'>('7d');

  const { status, domain, unit, sourceUrl } = indicator;
  const currentValue = typeof status.value === 'number' ? status.value : 0;
  const isCritical = isCriticalIndicator(indicator.id);

  // Get enriched data
  const description = getDescription(indicator.id, indicator.description);
  const richDescription = getIndicatorDescription(indicator.id);
  const householdRelevance = getHouseholdRelevance(indicator.id);
  const connectedIds = getConnectedIndicators(indicator.id);
  const phases = getPhaseRelevance(indicator.id);
  const sourceInfo = getSourceInfo(indicator.id);
  const impactLine = getCardImpactLine(indicator.id, status.level as 'green' | 'amber' | 'red');

  // Ensure history exists
  const history = useMemo(() => {
    return indicator.history || generateHistoricalData(indicator, timeRange);
  }, [indicator, timeRange]);

  // Status styling
  const statusColor = {
    red: 'text-red-400',
    amber: 'text-amber-400',
    green: 'text-emerald-400',
    unknown: 'text-olive-muted',
  }[status.level] || 'text-olive-muted';

  const statusBgColor = {
    red: 'bg-red-500/15 border-red-500/30',
    amber: 'bg-amber-500/15 border-amber-500/30',
    green: 'bg-emerald-500/15 border-emerald-500/30',
    unknown: 'bg-white/5 border-white/10',
  }[status.level] || 'bg-white/5 border-white/10';

  const statusDotColor = {
    red: 'bg-red-400',
    amber: 'bg-amber-400',
    green: 'bg-emerald-400',
    unknown: 'bg-olive-muted',
  }[status.level] || 'bg-olive-muted';

  // Trend
  const TrendIcon = !status.trend
    ? Minus
    : status.trend === 'up'
    ? TrendingUp
    : TrendingDown;

  const trendColor = !status.trend
    ? 'text-olive-muted'
    : indicator.greenFlag
    ? status.trend === 'up'
      ? 'text-emerald-400'
      : 'text-red-400'
    : status.trend === 'up'
    ? 'text-red-400'
    : 'text-emerald-400';

  const trendLabel = !status.trend
    ? 'Stable'
    : indicator.greenFlag
    ? status.trend === 'up'
      ? 'Improving'
      : 'Declining'
    : status.trend === 'up'
    ? 'Worsening'
    : 'Improving';

  return (
    <motion.aside
      initial={{ x: '100%' }}
      animate={{ x: 0 }}
      exit={{ x: '100%' }}
      transition={{ type: 'spring', damping: 25, stiffness: 300 }}
      className="fixed right-0 top-0 h-full w-full sm:w-[560px] bg-olive-sidebar border-l border-white/5 z-50 overflow-hidden flex flex-col"
    >
      {/* Sticky Header */}
      <header className="flex-shrink-0 p-4 border-b border-white/5 bg-olive-sidebar/95 backdrop-blur-sm">
        <div className="flex items-start justify-between gap-3">
          <div className="flex-1 min-w-0">
            {/* Name + Status */}
            <div className="flex items-center gap-2 mb-1">
              <div className={cn('w-2.5 h-2.5 rounded-full', statusDotColor)} />
              <h2 className="text-lg font-display font-semibold text-olive-primary truncate">
                {getDisplayName(indicator.id) || indicator.name}
              </h2>
            </div>
            {/* Domain + Source */}
            <p className="text-xs text-olive-data">
              {formatDomain(domain)} · {getSourceDisplay(indicator.id, indicator.dataSource)}
            </p>
          </div>

          {/* Status Badge + Close */}
          <div className="flex items-center gap-2 flex-shrink-0">
            <span
              className={cn(
                'px-2 py-1 text-xs font-mono font-medium rounded border',
                statusBgColor,
                statusColor
              )}
            >
              {status.level.toUpperCase()}
            </span>
            <button
              onClick={onClose}
              className="p-1.5 text-olive-muted hover:text-olive-primary hover:bg-white/5 rounded-lg transition-colors"
              aria-label="Close panel"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>
      </header>

      {/* Scrollable Content with Crossfade */}
      <div className="flex-1 overflow-y-auto">
        <AnimatePresence mode="wait">
          <motion.div
            key={indicator.id}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.15 }}
            className="p-4 space-y-6"
          >
          {/* Current State Section */}
          <section>
            <div className="flex items-baseline gap-3 mb-3">
              <span className={cn('text-4xl font-mono font-bold', statusColor)}>
                {formatValue(currentValue, unit)}
              </span>
              <div className={cn('flex items-center gap-1', trendColor)}>
                <TrendIcon className="w-5 h-5" />
                <span className="text-sm font-medium">{trendLabel}</span>
              </div>
            </div>

            {/* Threshold Bar with Labels */}
            {indicator.thresholds && (
              <div className="space-y-1">
                <ThresholdBar
                  value={currentValue}
                  amberThreshold={indicator.thresholds.threshold_amber}
                  redThreshold={indicator.thresholds.threshold_red}
                  inverted={indicator.greenFlag}
                  height={8}
                />
                <ThresholdLabels
                  amberThreshold={indicator.thresholds.threshold_amber}
                  redThreshold={indicator.thresholds.threshold_red}
                />
              </div>
            )}
          </section>

          {/* Current Status Summary */}
          {impactLine && (
            <section className={cn(
              "p-4 rounded-xl border",
              status.level === 'red' ? "bg-red-500/10 border-red-500/20" :
              status.level === 'amber' ? "bg-amber-500/10 border-amber-500/20" :
              "bg-emerald-500/10 border-emerald-500/20"
            )}>
              <div className="flex items-center gap-2 mb-2">
                <AlertTriangle className={cn(
                  "w-4 h-4",
                  status.level === 'red' ? "text-red-400" :
                  status.level === 'amber' ? "text-amber-400" :
                  "text-emerald-400"
                )} />
                <h3 className={cn(
                  "text-sm font-medium",
                  status.level === 'red' ? "text-red-400" :
                  status.level === 'amber' ? "text-amber-400" :
                  "text-emerald-400"
                )}>Current Status</h3>
              </div>
              <p className={cn(
                "text-sm leading-relaxed",
                status.level === 'red' ? "text-red-300/90" :
                status.level === 'amber' ? "text-amber-300/90" :
                "text-emerald-300/90"
              )}>{impactLine}</p>
            </section>
          )}

          {/* What This Indicator Tracks */}
          <section className="p-4 bg-white/[0.02] rounded-xl border border-white/5">
            <div className="flex items-center gap-2 mb-3">
              <Info className="w-4 h-4 text-olive-data" />
              <h3 className="text-sm font-medium text-olive-secondary">What we're tracking</h3>
            </div>
            <p className="text-sm text-olive-secondary leading-relaxed mb-3">
              {richDescription?.whatWeTrack || description}
            </p>
            {richDescription?.whyItMatters && (
              <div className="pt-3 border-t border-white/5">
                <p className="text-xs font-medium text-olive-muted uppercase tracking-wider mb-1.5">Why it matters</p>
                <p className="text-sm text-olive-primary leading-relaxed">{richDescription.whyItMatters}</p>
              </div>
            )}
          </section>

          {/* Why It Matters for Your Family */}
          {householdRelevance && (
            <section className="p-4 bg-amber-500/5 rounded-xl border border-amber-500/10">
              <div className="flex items-center gap-2 mb-3">
                <Home className="w-4 h-4 text-amber-400" />
                <h3 className="text-sm font-medium text-amber-400">Why it matters for your family</h3>
              </div>
              <p className="text-sm text-olive-secondary leading-relaxed mb-3">
                {householdRelevance.impact}
              </p>

              {/* Status-specific action guidance */}
              <div className="pt-3 border-t border-amber-500/10">
                <div className="flex items-center gap-2 mb-2">
                  <AlertTriangle className={cn(
                    "w-4 h-4",
                    status.level === 'red' ? "text-red-400" : "text-amber-400"
                  )} />
                  <span className={cn(
                    "text-xs font-medium uppercase tracking-wider",
                    status.level === 'red' ? "text-red-400" : "text-amber-400"
                  )}>
                    What to do {status.level === 'red' ? 'now' : status.level === 'amber' ? 'this week' : ''}
                  </span>
                </div>
                <p className="text-sm text-olive-primary leading-relaxed">
                  {richDescription?.actionGuidance?.[status.level as 'green' | 'amber' | 'red'] || householdRelevance.action}
                </p>
              </div>

              {/* Real world impact if available */}
              {richDescription?.realWorldImpact && status.level !== 'green' && (
                <div className="mt-3 pt-3 border-t border-amber-500/10">
                  <p className="text-xs font-medium text-amber-400/70 uppercase tracking-wider mb-1.5">Real world example</p>
                  <p className="text-sm text-olive-secondary leading-relaxed italic">
                    "{richDescription.realWorldImpact}"
                  </p>
                </div>
              )}
            </section>
          )}

          {/* Alert Thresholds */}
          {indicator.thresholds && (
            <section className="p-4 bg-white/[0.02] rounded-xl border border-white/5">
              <h3 className="text-sm font-medium text-olive-secondary mb-3">Alert Thresholds</h3>
              <div className="space-y-3">
                {/* Green */}
                <div className={cn(
                  "p-2.5 rounded-lg border",
                  status.level === 'green' ? "bg-emerald-500/10 border-emerald-500/30" : "border-white/5"
                )}>
                  <div className="flex items-center justify-between mb-1">
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 rounded-full bg-emerald-400" />
                      <span className="text-sm font-medium text-emerald-400">Green (Normal)</span>
                    </div>
                    <span className="text-xs font-mono text-olive-data">
                      &lt; {indicator.thresholds.threshold_amber}
                    </span>
                  </div>
                  {richDescription?.thresholds?.green && (
                    <p className="text-xs text-olive-secondary ml-4">{richDescription.thresholds.green}</p>
                  )}
                </div>

                {/* Amber */}
                <div className={cn(
                  "p-2.5 rounded-lg border",
                  status.level === 'amber' ? "bg-amber-500/10 border-amber-500/30" : "border-white/5"
                )}>
                  <div className="flex items-center justify-between mb-1">
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 rounded-full bg-amber-400" />
                      <span className="text-sm font-medium text-amber-400">Amber (Caution)</span>
                    </div>
                    <span className="text-xs font-mono text-olive-data">
                      {indicator.thresholds.threshold_amber} – {indicator.thresholds.threshold_red}
                    </span>
                  </div>
                  {richDescription?.thresholds?.amber && (
                    <p className="text-xs text-olive-secondary ml-4">{richDescription.thresholds.amber}</p>
                  )}
                </div>

                {/* Red */}
                <div className={cn(
                  "p-2.5 rounded-lg border",
                  status.level === 'red' ? "bg-red-500/10 border-red-500/30" : "border-white/5"
                )}>
                  <div className="flex items-center justify-between mb-1">
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 rounded-full bg-red-400" />
                      <span className="text-sm font-medium text-red-400">Red (Action Required)</span>
                    </div>
                    <span className="text-xs font-mono text-olive-data">
                      ≥ {indicator.thresholds.threshold_red}
                    </span>
                  </div>
                  {richDescription?.thresholds?.red && (
                    <p className="text-xs text-olive-secondary ml-4">{richDescription.thresholds.red}</p>
                  )}
                </div>
              </div>
            </section>
          )}

          {/* History Chart */}
          <section>
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <Activity className="w-4 h-4 text-olive-data" />
                <h3 className="text-sm font-medium text-olive-secondary">History</h3>
              </div>
              <div className="flex bg-white/[0.03] rounded-md p-0.5">
                {(['24h', '7d', '30d', '90d'] as const).map((range) => (
                  <button
                    key={range}
                    onClick={() => setTimeRange(range)}
                    className={cn(
                      'px-2.5 py-1 text-xs font-medium rounded transition-all',
                      timeRange === range
                        ? 'bg-white/10 text-white'
                        : 'text-olive-muted hover:text-white'
                    )}
                  >
                    {range}
                  </button>
                ))}
              </div>
            </div>
            <div className="bg-white/[0.02] rounded-xl p-3 border border-white/5">
              <IndicatorChart
                indicator={{ ...indicator, history }}
                timeRange={timeRange}
                height={120}
                className="w-full"
              />
            </div>
          </section>

          {/* Connected Indicators */}
          {connectedIds.length > 0 && (
            <section className="p-4 bg-white/[0.02] rounded-xl border border-white/5">
              <div className="flex items-center gap-2 mb-3">
                <Link2 className="w-4 h-4 text-olive-data" />
                <h3 className="text-sm font-medium text-olive-secondary">Connected Indicators</h3>
              </div>
              <div className="flex flex-wrap gap-2">
                {connectedIds.slice(0, 6).map((id) => (
                  <button
                    key={id}
                    onClick={() => onNavigate?.(id)}
                    className={cn(
                      "px-2 py-1 text-xs text-olive-secondary bg-white/5 rounded-md border border-white/5",
                      "hover:bg-white/10 hover:text-olive-primary hover:border-white/10 transition-colors",
                      onNavigate ? "cursor-pointer" : "cursor-default"
                    )}
                  >
                    {getDisplayName(id) || id.replace(/_/g, ' ')}
                  </button>
                ))}
              </div>
            </section>
          )}

          {/* Phase Relevance */}
          {phases.length > 0 && (
            <section className="p-4 bg-white/[0.02] rounded-xl border border-white/5">
              <h3 className="text-sm font-medium text-olive-secondary mb-2">Phase Relevance</h3>
              <p className="text-sm text-olive-data">
                Critical for <span className="text-olive-primary font-medium">{getPhaseRelevanceLabel(phases)}</span> of the household preparedness system.
              </p>
            </section>
          )}

          {/* Data Source */}
          <section className="p-4 bg-white/[0.02] rounded-xl border border-white/5">
            <div className="flex items-center gap-2 mb-3">
              <Clock className="w-4 h-4 text-olive-data" />
              <h3 className="text-sm font-medium text-olive-secondary">Data Source</h3>
            </div>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs text-olive-muted">Source</span>
                <span className="text-sm text-olive-primary">
                  {getSourceFull(indicator.id)}
                </span>
              </div>
              {sourceInfo?.updateFrequency && (
                <div className="flex items-center justify-between">
                  <span className="text-xs text-olive-muted">Updates</span>
                  <span className="text-sm text-olive-secondary capitalize">
                    {sourceInfo.updateFrequency}
                  </span>
                </div>
              )}
              <div className="flex items-center justify-between">
                <span className="text-xs text-olive-muted">Last updated</span>
                <span className="text-sm text-olive-secondary">
                  {formatTimeAgo(status.lastUpdate)}
                </span>
              </div>
              {sourceInfo?.description && (
                <p className="text-xs text-olive-muted mt-2 pt-2 border-t border-white/5">
                  {sourceInfo.description}
                </p>
              )}
              {(sourceUrl || sourceInfo?.url) && (
                <a
                  href={sourceUrl || sourceInfo?.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 text-xs text-amber-400 hover:text-amber-300 transition-colors mt-2"
                >
                  <span>View source</span>
                  <ExternalLink className="w-3 h-3" />
                </a>
              )}
            </div>
          </section>

          {/* Historical Context */}
          {richDescription?.historicalContext && (
            <section className="p-4 bg-white/[0.02] rounded-xl border border-white/5">
              <div className="flex items-center gap-2 mb-2">
                <Clock className="w-4 h-4 text-olive-data" />
                <h3 className="text-sm font-medium text-olive-secondary">Historical Context</h3>
              </div>
              <p className="text-sm text-olive-secondary leading-relaxed italic">
                {richDescription.historicalContext}
              </p>
            </section>
          )}

          {/* Critical Indicator Badge */}
          {isCritical && (
            <div className="p-3 bg-amber-500/10 rounded-lg border border-amber-500/20 flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-amber-400 flex-shrink-0" />
              <p className="text-xs text-amber-400">
                This is a <strong>critical indicator</strong> that can trigger phase transitions in the household preparedness system.
              </p>
            </div>
          )}
          </motion.div>
        </AnimatePresence>
      </div>
    </motion.aside>
  );
};
