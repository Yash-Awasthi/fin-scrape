import React, { useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useStore } from '../store';
import { IndicatorChart } from '../components/charts/IndicatorChart';
import { StatusBadge } from '../components/core/Badge';
import { formatDistanceToNow } from 'date-fns';
import { cn } from '../utils/cn';
import {
  TrendingUp,
  TrendingDown,
  Minus,
  Clock,
  Info,
  AlertTriangle,
  Lightbulb,
  ChevronRight,
  Activity,
  ArrowLeft,
} from 'lucide-react';

export const IndicatorDetails: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const { indicators, fetchIndicators } = useStore();
  const indicator = indicators.find(ind => ind.id === id);

  useEffect(() => {
    if (!indicator) {
      fetchIndicators();
    }
  }, [id, indicator, fetchIndicators]);

  if (!indicator) {
    return (
      <div className="flex items-center justify-center py-24">
        <div className="text-center">
          <Activity className="w-12 h-12 text-white/15 mx-auto mb-4" />
          <h1 className="text-2xl font-bold text-white mt-4">Indicator Not Found</h1>
          <p className="text-white/30 mt-2">Loading or invalid indicator ID: {id}</p>
          <Link to="/indicators" className="inline-flex items-center gap-2 mt-6 text-white/30 hover:text-white/50 transition-colors">
            <ArrowLeft className="w-4 h-4" />
            Back to Indicators
          </Link>
        </div>
      </div>
    );
  }

  const getTrendIcon = () => {
    if (!indicator.status.trend) return <Minus className="w-4 h-4" />;
    return indicator.status.trend === 'up' ? (
      <TrendingUp className="w-4 h-4" />
    ) : (
      <TrendingDown className="w-4 h-4" />
    );
  };

  const getTrendColor = () => {
    if (!indicator.status.trend) return 'text-white/30';
    if (indicator.greenFlag) {
      return indicator.status.trend === 'up' ? 'text-green-400' : 'text-red-400';
    }
    return indicator.status.trend === 'up' ? 'text-red-400' : 'text-green-400';
  };

  const generateInsights = () => {
    const insights: { type: string; message: string }[] = [];
    if (indicator.status.level === 'red') {
      insights.push({ type: 'warning', message: 'Critical threshold exceeded — immediate attention required.' });
    }
    if (indicator.status.level === 'amber') {
      insights.push({ type: 'info', message: 'Approaching threshold — enhanced monitoring recommended.' });
    }
    if (indicator.status.trend === 'up' && !indicator.greenFlag) {
      insights.push({ type: 'warning', message: 'Deteriorating trend detected.' });
    }
    if (indicator.status.trend === 'down' && indicator.greenFlag) {
      insights.push({ type: 'warning', message: 'Negative trend in positive indicator.' });
    }
    return insights;
  };

  const insights = generateInsights();

  return (
    <>
      {/* Page Header */}
      <div className="border-b border-white/[0.04]">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8">
          {/* Breadcrumb */}
          <div className="flex items-center gap-2 mb-4 text-sm">
            <Link to="/dashboard" className="text-white/20 hover:text-white/50 transition-colors">Dashboard</Link>
            <ChevronRight className="w-3 h-3 text-white/15" />
            <Link to="/indicators" className="text-white/20 hover:text-white/50 transition-colors">Indicators</Link>
            <ChevronRight className="w-3 h-3 text-white/15" />
            <span className="text-white/50">{indicator.name}</span>
          </div>

          <div className="flex items-center justify-between gap-4">
            <div>
              <h1 className="text-2xl font-bold text-white">{indicator.name}</h1>
              <p className="text-white/30 mt-1">{indicator.description}</p>
            </div>
            <StatusBadge level={indicator.status.level} size="lg" pulse={indicator.status.level === 'red' && indicator.critical} />
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        {/* Status + Thresholds cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Current Status */}
          <div className="glass-card p-6">
            <h2 className="text-sm font-medium text-white/20 uppercase tracking-wider mb-4">Current Status</h2>
            <div className="flex items-baseline gap-2 mb-3">
              <span className="text-4xl font-bold text-white">
                {typeof indicator.status.value === 'number'
                  ? indicator.status.value.toLocaleString(undefined, { maximumFractionDigits: 2 })
                  : indicator.status.value}
              </span>
              <span className="text-lg text-white/30">{indicator.unit}</span>
            </div>
            <div className="flex items-center gap-2 text-sm text-white/20 mb-4">
              <Clock className="w-4 h-4" />
              <span>Updated {formatDistanceToNow(new Date(indicator.status.lastUpdate), { addSuffix: true })}</span>
            </div>
            <div className="flex items-center gap-2 text-sm">
              <span className={cn('font-medium flex items-center gap-1', getTrendColor())}>
                {getTrendIcon()} {indicator.status.trend ? indicator.status.trend.toUpperCase() : 'STABLE'}
              </span>
              <span className="text-white/20">from {indicator.dataSource}</span>
            </div>
          </div>

          {/* Thresholds */}
          <div className="glass-card p-6">
            <h2 className="text-sm font-medium text-white/20 uppercase tracking-wider mb-4">Thresholds</h2>
            {(() => {
              // Get threshold values with fallbacks to alternative format
              const thresholds = indicator.thresholds;
              const amberThreshold = thresholds?.threshold_amber ?? thresholds?.amber?.min;
              const redThreshold = thresholds?.threshold_red ?? thresholds?.red?.min;
              const hasThresholds = amberThreshold !== undefined && redThreshold !== undefined;
              const isInverted = indicator.greenFlag; // For green flags, lower is better

              return (
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <div className="flex items-center gap-2">
                      <span className="w-2.5 h-2.5 rounded-full bg-green-500" />
                      <span className="text-white/50">Green</span>
                    </div>
                    <span className="text-white/30 font-mono text-sm">
                      {hasThresholds
                        ? (isInverted ? `> ${amberThreshold}` : `< ${amberThreshold}`) + ` ${indicator.unit}`
                        : 'N/A'}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <div className="flex items-center gap-2">
                      <span className="w-2.5 h-2.5 rounded-full bg-amber-500" />
                      <span className="text-white/50">Amber</span>
                    </div>
                    <span className="text-white/30 font-mono text-sm">
                      {hasThresholds
                        ? `${amberThreshold} — ${redThreshold} ${indicator.unit}`
                        : 'N/A'}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <div className="flex items-center gap-2">
                      <span className="w-2.5 h-2.5 rounded-full bg-red-500" />
                      <span className="text-white/50">Red</span>
                    </div>
                    <span className="text-white/30 font-mono text-sm">
                      {hasThresholds
                        ? (isInverted ? `< ${redThreshold}` : `> ${redThreshold}`) + ` ${indicator.unit}`
                        : 'N/A'}
                    </span>
                  </div>
                </div>
              );
            })()}
            {indicator.critical && (
              <div className="mt-4 pt-4 border-t border-white/[0.04] flex items-center gap-2 text-sm text-red-400">
                <AlertTriangle className="w-4 h-4" />
                Critical indicator — affects overall phase level
              </div>
            )}
          </div>
        </div>

        {/* Chart */}
        <div className="glass-card p-6">
          <h2 className="text-sm font-medium text-white/20 uppercase tracking-wider mb-4">Historical Trend</h2>
          <IndicatorChart indicator={indicator} height={200} />
        </div>

        {/* Insights */}
        {insights.length > 0 && (
          <div className="glass-card p-6">
            <h2 className="text-sm font-medium text-white/20 uppercase tracking-wider mb-4">Insights</h2>
            <div className="space-y-3">
              {insights.map((insight, index) => (
                <div key={index} className="flex items-start gap-3 px-3 py-2.5 rounded-lg bg-white/[0.03]">
                  {insight.type === 'warning' && <AlertTriangle className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" />}
                  {insight.type === 'info' && <Info className="w-5 h-5 text-blue-400 flex-shrink-0 mt-0.5" />}
                  {insight.type === 'action' && <Lightbulb className="w-5 h-5 text-green-400 flex-shrink-0 mt-0.5" />}
                  <p className="text-white/50 text-sm">{insight.message}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </>
  );
};
