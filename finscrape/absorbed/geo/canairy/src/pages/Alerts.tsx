import React, { useState, useMemo, useCallback } from 'react';
import { motion } from 'framer-motion';
import {
  Bell,
  CheckCircle2,
  Clock,
  ChevronRight,
  Zap,
  Info,
  AlertTriangle,
  X,
} from 'lucide-react';
import { Link } from 'react-router-dom';
import { useStore } from '../store';
import { DOMAIN_META } from '../types';
import { GlassCard } from '../components/ui/GlassCard';
import { cn } from '../utils/cn';
import { formatDistanceToNow } from 'date-fns';

type AlertFilter = 'all' | 'critical' | 'warning' | 'info';

interface AlertItem {
  id: string;
  type: 'red_threshold' | 'high_phase' | 'phase_change' | 'trend_warning';
  indicatorId?: string;
  indicatorName?: string;
  domain?: string;
  message: string;
  severity: 'critical' | 'warning' | 'info';
  timestamp: string;
}

export const Alerts: React.FC = () => {
  const { indicators } = useStore();
  const [filter, setFilter] = useState<AlertFilter>('all');

  // Dismissed alerts (persisted to localStorage)
  const [dismissedIds, setDismissedIds] = useState<Set<string>>(() => {
    try {
      const stored = localStorage.getItem('canairy_dismissed_alerts');
      return stored ? new Set(JSON.parse(stored)) : new Set();
    } catch {
      return new Set();
    }
  });

  const dismissAlert = useCallback((alertId: string) => {
    setDismissedIds(prev => {
      const next = new Set(prev);
      next.add(alertId);
      localStorage.setItem('canairy_dismissed_alerts', JSON.stringify([...next]));
      return next;
    });
  }, []);

  const clearDismissed = useCallback(() => {
    setDismissedIds(new Set());
    localStorage.removeItem('canairy_dismissed_alerts');
  }, []);

  const alerts = useMemo(() => {
    const items: AlertItem[] = [];
    const now = new Date().toISOString();

    const redCount = indicators.filter(i => i.status.level === 'red').length;
    if (redCount >= 2) {
      items.push({
        id: 'high-phase',
        type: 'high_phase',
        message: `Multiple areas need attention (${redCount} critical). Check your action plan for specific steps.`,
        severity: 'critical',
        timestamp: now,
      });
    }

    indicators.filter(i => i.status.level === 'red').forEach(ind => {
      items.push({
        id: `red-${ind.id}`,
        type: 'red_threshold',
        indicatorId: ind.id,
        indicatorName: ind.name,
        domain: ind.domain,
        message: `${ind.name} has reached a critical level. Current: ${typeof ind.status.value === 'number' ? ind.status.value.toFixed(1) : ind.status.value} ${ind.unit}.`,
        severity: ind.critical ? 'critical' : 'warning',
        timestamp: ind.status.lastUpdate,
      });
    });

    indicators.filter(i => i.status.level === 'amber').forEach(ind => {
      items.push({
        id: `amber-${ind.id}`,
        type: 'trend_warning',
        indicatorId: ind.id,
        indicatorName: ind.name,
        domain: ind.domain,
        message: `${ind.name} is elevated but not urgent yet`,
        severity: 'info',
        timestamp: ind.status.lastUpdate,
      });
    });

    items.sort((a, b) => {
      const order = { critical: 0, warning: 1, info: 2 };
      if (order[a.severity] !== order[b.severity]) return order[a.severity] - order[b.severity];
      return new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime();
    });

    return items;
  }, [indicators]);

  // Filter out dismissed alerts
  const activeAlerts = alerts.filter(a => !dismissedIds.has(a.id));
  const filtered = filter === 'all' ? activeAlerts : activeAlerts.filter(a => a.severity === filter);
  const criticalCount = activeAlerts.filter(a => a.severity === 'critical').length;
  const warningCount = activeAlerts.filter(a => a.severity === 'warning').length;
  const infoCount = activeAlerts.filter(a => a.severity === 'info').length;

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'critical': return <Zap className="w-4 h-4 text-red-400" />;
      case 'warning': return <AlertTriangle className="w-4 h-4 text-amber-400" />;
      case 'info': return <Info className="w-4 h-4 text-blue-400/60" />;
      default: return <Bell className="w-4 h-4 text-white/20" />;
    }
  };

  const getGlow = (severity: string) => {
    switch (severity) {
      case 'critical': return 'red' as const;
      case 'warning': return 'amber' as const;
      default: return 'none' as const;
    }
  };

  return (
    <>
      <div className="border-b border-white/[0.04]">
        <div className="px-4 sm:px-6 lg:px-8 py-4 sm:py-6">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
            <div>
              <h1 className="text-2xl sm:text-3xl font-display font-semibold text-white">Alerts</h1>
              <p className="text-white/30 mt-1 text-sm">Things that might affect your family</p>
            </div>
            <Link
              to="/settings"
              className="btn btn-secondary text-sm"
            >
              <Bell className="w-4 h-4" />
              Notification Settings
            </Link>
          </div>

          {/* Summary with explanations */}
          <div className="grid grid-cols-3 gap-3 mb-4">
            <GlassCard padding="sm" glow={criticalCount > 0 ? 'red' : 'none'} className="text-center">
              <div className="text-2xl font-bold text-red-400">{criticalCount}</div>
              <div className="text-xs text-white/25">Need action</div>
            </GlassCard>
            <GlassCard padding="sm" glow={warningCount > 0 ? 'amber' : 'none'} className="text-center">
              <div className="text-2xl font-bold text-amber-400">{warningCount}</div>
              <div className="text-xs text-white/25">Worth knowing</div>
            </GlassCard>
            <GlassCard padding="sm" className="text-center">
              <div className="text-2xl font-bold text-blue-400/60">{infoCount}</div>
              <div className="text-xs text-white/25">Watching</div>
            </GlassCard>
          </div>

          {/* Alert level explanations */}
          <div className="text-xs text-white/30 mb-6 p-3 rounded-lg bg-white/[0.02] border border-white/[0.04]">
            <p className="font-medium text-white/40 mb-1.5">How alert levels work:</p>
            <div className="space-y-1">
              <p><span className="text-red-400">Need action</span> — Something has crossed a critical threshold. Review the recommended actions.</p>
              <p><span className="text-amber-400">Worth knowing</span> — A signal has changed enough to be noteworthy, but no immediate action needed.</p>
              <p><span className="text-blue-400/60">Watching</span> — Elevated but stable. We're keeping an eye on it so you don't have to.</p>
            </div>
            {infoCount > 10 && (
              <p className="mt-2 text-white/20 italic">{infoCount} signals at "Watching" level is typical during moderate uncertainty.</p>
            )}
          </div>

          {/* Filter */}
          <div className="flex items-center gap-3 flex-wrap">
            <div className="flex items-center gap-1 bg-white/[0.04] rounded-xl p-1 w-fit overflow-x-auto">
              {(['all', 'critical', 'warning', 'info'] as AlertFilter[]).map(f => (
                <button
                  key={f}
                  onClick={() => setFilter(f)}
                  className={cn(
                    'px-3 py-1.5 rounded-lg text-sm font-medium transition-all whitespace-nowrap',
                    filter === f ? 'bg-white/[0.08] text-white' : 'text-white/30 hover:text-white/50'
                  )}
                >
                  {f.charAt(0).toUpperCase() + f.slice(1)}
                </button>
              ))}
            </div>
            {dismissedIds.size > 0 && (
              <button
                onClick={clearDismissed}
                className="text-xs text-white/30 hover:text-white/50 transition-colors"
              >
                Show {dismissedIds.size} dismissed
              </button>
            )}
          </div>
        </div>
      </div>

      <div className="px-4 sm:px-6 lg:px-8 py-4 sm:py-8 max-w-4xl mx-auto">
        {filtered.length > 0 ? (
          <div className="space-y-3">
            {filtered.map((alert, idx) => (
              <motion.div
                key={alert.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.03 }}
              >
                <GlassCard padding="sm" glow={getGlow(alert.severity)}>
                  <div className="flex items-start gap-3">
                    <div className="flex-shrink-0 mt-0.5">{getSeverityIcon(alert.severity)}</div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-white/70">{alert.message}</p>
                      <div className="flex flex-wrap items-center gap-3 mt-2">
                        {alert.domain && (
                          <span className="text-xs text-white/20">
                            {DOMAIN_META[alert.domain as keyof typeof DOMAIN_META]?.label ?? alert.domain}
                          </span>
                        )}
                        <span className="text-xs text-white/15 flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          {formatDistanceToNow(new Date(alert.timestamp), { addSuffix: true })}
                        </span>
                      </div>
                    </div>
                    <div className="flex items-center gap-1 flex-shrink-0">
                      {alert.indicatorId && (
                        <Link
                          to={`/indicator/${alert.indicatorId}`}
                          className="p-2 text-white/15 hover:text-white/40 hover:bg-white/5 rounded-lg transition-colors"
                        >
                          <ChevronRight className="w-4 h-4" />
                        </Link>
                      )}
                      <button
                        onClick={() => dismissAlert(alert.id)}
                        className="p-2 text-white/15 hover:text-white/40 hover:bg-white/5 rounded-lg transition-colors"
                        title="Dismiss alert"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </GlassCard>
              </motion.div>
            ))}
          </div>
        ) : (
          <div className="text-center py-16">
            <CheckCircle2 className="w-12 h-12 text-green-500/30 mx-auto mb-4" />
            <h3 className="text-lg font-display font-medium text-white mb-2">Everything looks good</h3>
            <p className="text-white/30">Nothing needs your attention right now.</p>
          </div>
        )}
      </div>
    </>
  );
};
