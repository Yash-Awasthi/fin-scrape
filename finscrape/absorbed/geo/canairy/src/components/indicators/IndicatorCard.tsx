/**
 * IndicatorCard Component
 *
 * Simplified card that answers three questions in under 2 seconds:
 * 1. What is this?
 * 2. Is it okay?
 * 3. Is it getting worse?
 *
 * All detail lives in the modal/panel, not here.
 */

import React from 'react';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { IndicatorData } from '../../types';
import { cn } from '../../utils/cn';
import {
  formatValue,
  formatDomain,
  getSourceDisplay,
  isCriticalIndicator,
  formatTimeAgo,
  getHouseholdRelevance,
  getDescription,
} from '../../data/indicatorDisplay';
import { getDisplayName } from '../../data/indicatorTranslations';

interface IndicatorCardProps {
  indicator: IndicatorData;
  onClick?: () => void;
  isSelected?: boolean;
}

export const IndicatorCard: React.FC<IndicatorCardProps> = ({
  indicator,
  onClick,
  isSelected = false,
}) => {
  const { status, domain, unit } = indicator;
  const isCritical = isCriticalIndicator(indicator.id);
  const currentValue = typeof status.value === 'number' ? status.value : 0;

  // Status-driven styling
  const borderColor = {
    red: 'border-red-500/40 hover:border-red-500/60',
    amber: 'border-amber-500/25 hover:border-amber-500/40',
    green: 'border-white/[0.06] hover:border-white/10',
    unknown: 'border-white/[0.06] hover:border-white/10',
  }[status.level] || 'border-white/[0.06]';

  const statusDotColor = {
    red: 'bg-red-400',
    amber: 'bg-amber-400',
    green: 'bg-emerald-400',
    unknown: 'bg-olive-muted',
  }[status.level] || 'bg-olive-muted';

  const statusBadgeStyle = {
    red: 'bg-red-500/15 text-red-400 border-red-500/20',
    amber: 'bg-amber-500/15 text-amber-400 border-amber-500/20',
    green: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/20',
    unknown: 'bg-white/5 text-olive-muted border-white/10',
  }[status.level] || 'bg-white/5 text-olive-muted';

  const valueColor = {
    red: 'text-red-400',
    amber: 'text-amber-400',
    green: 'text-emerald-400',
    unknown: 'text-olive-secondary',
  }[status.level] || 'text-olive-secondary';

  // Trend arrow
  const TrendIcon = !status.trend
    ? Minus
    : status.trend === 'up'
    ? TrendingUp
    : TrendingDown;

  // For most indicators, up = worse. For greenFlag, up = better.
  const trendColor = !status.trend
    ? 'text-olive-muted'
    : indicator.greenFlag
    ? status.trend === 'up'
      ? 'text-emerald-400'
      : 'text-red-400'
    : status.trend === 'up'
    ? 'text-red-400'
    : 'text-emerald-400';

  // Threshold bar calculation
  const amberThreshold = indicator.thresholds?.threshold_amber;
  const redThreshold = indicator.thresholds?.threshold_red;
  const hasThresholds = amberThreshold !== undefined && redThreshold !== undefined;

  let thresholdBarContent = null;
  if (hasThresholds) {
    const max = redThreshold * 1.5;
    const amberPct = (amberThreshold / max) * 100;
    const redPct = (redThreshold / max) * 100;
    const valuePct = Math.min((currentValue / max) * 100, 100);

    const markerColor =
      currentValue >= redThreshold
        ? '#EF4444'
        : currentValue >= amberThreshold
        ? '#F59E0B'
        : '#10B981';

    thresholdBarContent = (
      <div className="relative h-1 rounded-full overflow-hidden">
        <div className="absolute inset-0 flex">
          <div className="bg-emerald-500/20" style={{ width: `${amberPct}%` }} />
          <div className="bg-amber-500/20" style={{ width: `${redPct - amberPct}%` }} />
          <div className="bg-red-500/20" style={{ width: `${100 - redPct}%` }} />
        </div>
        <div
          className="absolute top-0 bottom-0 w-1 rounded-full"
          style={{
            left: `${valuePct}%`,
            backgroundColor: markerColor,
            transform: 'translateX(-50%)',
          }}
        />
      </div>
    );
  }

  return (
    <button
      onClick={onClick}
      className={cn(
        'w-full text-left rounded-xl p-4',
        'bg-olive-card border transition-all duration-150',
        borderColor,
        isCritical && 'border-l-2 border-l-amber-500/60',
        isSelected && 'ring-1 ring-amber-500/40 bg-olive-lead',
        'hover:bg-olive-lead cursor-pointer group'
      )}
    >
      {/* Row 1: Name + Badge */}
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2 min-w-0 flex-1">
          <div className={cn('w-2 h-2 rounded-full shrink-0', statusDotColor)} />
          <h3 className="text-sm font-display font-medium text-olive-primary truncate">
            {getDisplayName(indicator.id) || indicator.name}
          </h3>
        </div>
        <span
          className={cn(
            'text-[10px] font-mono font-medium px-1.5 py-0.5 rounded border shrink-0',
            statusBadgeStyle
          )}
        >
          {status.level.toUpperCase()}
        </span>
      </div>

      {/* Row 2: Domain + Source */}
      <p className="text-[11px] text-olive-data mt-1 ml-4 truncate">
        {formatDomain(domain)} · {getSourceDisplay(indicator.id, indicator.dataSource)}
      </p>

      {/* Row 3: Value + Trend */}
      <div className="flex items-baseline gap-2 mt-3">
        <span className={cn('text-2xl font-mono font-semibold', valueColor)}>
          {formatValue(currentValue, unit)}
        </span>
        <TrendIcon className={cn('w-4 h-4', trendColor)} />
      </div>

      {/* Row 4: Threshold bar (no labels) */}
      {hasThresholds && <div className="mt-3">{thresholdBarContent}</div>}

      {/* Row 5: Preview description - why this matters to your family */}
      <p className="text-[11px] text-olive-secondary mt-2 line-clamp-2 leading-relaxed">
        {getHouseholdRelevance(indicator.id)?.impact ||
         getDescription(indicator.id, indicator.description)}
      </p>

      {/* Row 6: Timestamp */}
      <p className="text-[10px] text-olive-data mt-3">
        Updated {formatTimeAgo(status.lastUpdate)}
      </p>
    </button>
  );
};
