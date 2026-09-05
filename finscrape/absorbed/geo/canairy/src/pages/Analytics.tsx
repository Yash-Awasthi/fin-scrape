import React, { useMemo } from 'react';
import { motion } from 'framer-motion';
import {
  TrendingUp,
  TrendingDown,
  Minus,
  Activity,
  AlertTriangle,
} from 'lucide-react';
import { useStore } from '../store';
import { DOMAIN_META, Domain } from '../types';
import { ScoreRing } from '../components/ui/ScoreRing';
import { GlassCard } from '../components/ui/GlassCard';
import { cn } from '../utils/cn';

export const Analytics: React.FC = () => {
  const { indicators, hopiScore } = useStore();

  const domainStats = useMemo(() => {
    return Object.entries(DOMAIN_META).map(([key, meta]) => {
      const domainIndicators = indicators.filter(i => i.domain === key);
      const total = domainIndicators.length;
      const red = domainIndicators.filter(i => i.status.level === 'red').length;
      const amber = domainIndicators.filter(i => i.status.level === 'amber').length;
      const green = domainIndicators.filter(i => i.status.level === 'green').length;
      const domainScore = hopiScore?.domains[key as Domain]?.score ?? 0;
      return { key: key as Domain, ...meta, total, red, amber, green, domainScore };
    }).sort((a, b) => b.red - a.red || b.amber - a.amber);
  }, [indicators, hopiScore]);

  const trendStats = useMemo(() => {
    const up = indicators.filter(i => i.status.trend === 'up').length;
    const down = indicators.filter(i => i.status.trend === 'down').length;
    const stable = indicators.filter(i => !i.status.trend || i.status.trend === 'stable').length;
    return { up, down, stable };
  }, [indicators]);

  const sourceStats = useMemo(() => {
    const live = indicators.filter(i => i.status.dataSource === 'LIVE').length;
    const mock = indicators.filter(i => i.status.dataSource === 'MOCK').length;
    const manual = indicators.filter(i => i.status.dataSource === 'MANUAL').length;
    return { live, mock, manual };
  }, [indicators]);

  const redCount = indicators.filter(i => i.status.level === 'red').length;
  const amberCount = indicators.filter(i => i.status.level === 'amber').length;
  const greenCount = indicators.filter(i => i.status.level === 'green').length;

  return (
    <>
      <div className="border-b border-white/[0.04]">
        <div className="px-4 sm:px-6 lg:px-8 py-4 sm:py-6">
          <h1 className="text-2xl sm:text-3xl font-display font-semibold text-white">Insights</h1>
          <p className="text-white/30 mt-1 text-sm">The big picture — how things are changing across all domains</p>
        </div>
      </div>

      <div className="px-4 sm:px-6 lg:px-8 py-4 sm:py-8 space-y-8 max-w-6xl mx-auto">
        {/* Top stats */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <GlassCard padding="sm">
            <Activity className="w-4 h-4 text-white/20 mb-2" />
            <div className="text-2xl font-bold text-white">{indicators.length}</div>
            <div className="text-xs text-white/25">Monitored</div>
          </GlassCard>
          <GlassCard padding="sm" glow={redCount > 0 ? 'red' : 'none'}>
            <AlertTriangle className="w-4 h-4 text-red-400/50 mb-2" />
            <div className="text-2xl font-bold text-red-400">{redCount}</div>
            <div className="text-xs text-white/25">Need Action</div>
          </GlassCard>
          <GlassCard padding="sm" glow={amberCount > 0 ? 'amber' : 'none'}>
            <div className="text-2xl font-bold text-amber-400 mt-6">{amberCount}</div>
            <div className="text-xs text-white/25">Watching</div>
          </GlassCard>
          <GlassCard padding="sm">
            <div className="text-2xl font-bold text-green-400 mt-6">{greenCount}</div>
            <div className="text-xs text-white/25">Looking Good</div>
          </GlassCard>
        </div>

        {/* Domain Score Rings */}
        {hopiScore && (
          <GlassCard>
            <h2 className="text-xs font-medium text-white/20 uppercase tracking-wider mb-6">Domain Scores</h2>
            <div className="flex flex-wrap justify-center gap-6 sm:gap-8">
              {domainStats.filter(d => d.total > 0).slice(0, 6).map((domain, idx) => (
                <motion.div
                  key={domain.key}
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: idx * 0.05 }}
                  className="flex flex-col items-center"
                >
                  <ScoreRing
                    value={domain.domainScore}
                    max={100}
                    size="sm"
                    color={domain.domainScore > 66 ? '#EF4444' : domain.domainScore > 33 ? '#F59E0B' : '#10B981'}
                  />
                  <span className="text-xs text-white/30 mt-2 text-center max-w-[80px] truncate">{domain.label}</span>
                </motion.div>
              ))}
            </div>
          </GlassCard>
        )}

        {/* Domain Breakdown */}
        <GlassCard>
          <h2 className="text-xs font-medium text-white/20 uppercase tracking-wider mb-4">All Domains</h2>
          <div className="space-y-3">
            {domainStats.map((domain, idx) => (
              <motion.div
                key={domain.key}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: idx * 0.03 }}
                className="flex items-center gap-4"
              >
                <div className="w-32 sm:w-40 flex-shrink-0">
                  <div className="text-sm text-white/70 font-medium">{domain.label}</div>
                  <div className="text-xs text-white/20">{domain.total} indicators</div>
                </div>
                <div className="flex-1 h-5 bg-white/[0.03] rounded-lg overflow-hidden flex">
                  {domain.red > 0 && (
                    <div className="bg-red-500/70 h-full" style={{ width: `${(domain.red / domain.total) * 100}%` }} />
                  )}
                  {domain.amber > 0 && (
                    <div className="bg-amber-500/60 h-full" style={{ width: `${(domain.amber / domain.total) * 100}%` }} />
                  )}
                  {domain.green > 0 && (
                    <div className="bg-green-500/40 h-full" style={{ width: `${(domain.green / domain.total) * 100}%` }} />
                  )}
                </div>
                <div className="w-12 text-right">
                  <span className={cn(
                    'text-sm font-mono font-medium',
                    domain.domainScore > 66 ? 'text-red-400' : domain.domainScore > 33 ? 'text-amber-400' : 'text-green-400'
                  )}>
                    {Math.round(domain.domainScore)}
                  </span>
                </div>
              </motion.div>
            ))}
          </div>
        </GlassCard>

        {/* Trends + Sources */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <GlassCard>
            <h2 className="text-xs font-medium text-white/20 uppercase tracking-wider mb-4">Direction of Change</h2>
            <div className="space-y-3">
              <TrendRow icon={<TrendingUp className="w-4 h-4 text-red-400/60" />} label="Getting worse" count={trendStats.up} total={indicators.length} color="bg-red-500/60" />
              <TrendRow icon={<Minus className="w-4 h-4 text-white/20" />} label="Holding steady" count={trendStats.stable} total={indicators.length} color="bg-white/20" />
              <TrendRow icon={<TrendingDown className="w-4 h-4 text-green-400/60" />} label="Getting better" count={trendStats.down} total={indicators.length} color="bg-green-500/50" />
            </div>
          </GlassCard>
          <GlassCard>
            <h2 className="text-xs font-medium text-white/20 uppercase tracking-wider mb-4">Data Sources</h2>
            <div className="space-y-3">
              <TrendRow icon={<Activity className="w-4 h-4 text-green-400/60" />} label="Live" count={sourceStats.live} total={indicators.length} color="bg-green-500/50" />
              <TrendRow icon={<Activity className="w-4 h-4 text-amber-400/60" />} label="Estimated" count={sourceStats.mock} total={indicators.length} color="bg-amber-500/50" />
              <TrendRow icon={<Activity className="w-4 h-4 text-blue-400/60" />} label="Manual" count={sourceStats.manual} total={indicators.length} color="bg-blue-500/50" />
            </div>
          </GlassCard>
        </div>
      </div>
    </>
  );
};

function TrendRow({ icon, label, count, total, color }: { icon: React.ReactNode; label: string; count: number; total: number; color: string }) {
  const pct = total > 0 ? (count / total) * 100 : 0;
  return (
    <div className="flex items-center gap-3">
      {icon}
      <span className="text-sm text-white/40 w-24">{label}</span>
      <div className="flex-1 h-1.5 bg-white/[0.04] rounded-full overflow-hidden">
        <div className={cn('h-full rounded-full', color)} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-sm text-white/25 w-8 text-right">{count}</span>
    </div>
  );
}
