/**
 * ConditionsSummary - Explains why the current phase is active
 *
 * Connects indicators to the task list by showing which indicators
 * are elevated and what that means for the family's focus.
 */

import React from 'react';
import { Link } from 'react-router-dom';
import { AlertTriangle, TrendingUp } from 'lucide-react';
import { IndicatorData } from '../../types';
import { cn } from '../../utils/cn';

interface ConditionsSummaryProps {
  indicators: IndicatorData[];
  systemPhase: number | 'tighten-up';
}

// Get the focus area based on which indicators are elevated
function getActionFocus(elevatedIndicators: IndicatorData[]): string {
  const domains = new Set(elevatedIndicators.map(i => i.domain));

  if (domains.has('supply_chain') || domains.has('energy')) {
    return 'building supply buffers and energy resilience';
  }
  if (domains.has('economy') || domains.has('housing_mortgage')) {
    return 'strengthening your financial position';
  }
  if (domains.has('global_conflict') || domains.has('security_infrastructure')) {
    return 'security and communication preparedness';
  }
  if (domains.has('domestic_control') || domains.has('rights_governance')) {
    return 'document organization and digital security';
  }

  return 'general preparedness';
}

export const ConditionsSummary: React.FC<ConditionsSummaryProps> = ({
  indicators,
}) => {
  // Get indicators at caution (amber) or alert (red) level
  const elevatedIndicators = indicators.filter(
    i => i.status.level === 'amber' || i.status.level === 'red'
  );

  // If all green, don't render anything
  if (elevatedIndicators.length === 0) {
    return null;
  }

  const redCount = elevatedIndicators.filter(i => i.status.level === 'red').length;
  const amberCount = elevatedIndicators.filter(i => i.status.level === 'amber').length;
  const actionFocus = getActionFocus(elevatedIndicators);

  // Build the level description
  const levelParts: string[] = [];
  if (redCount > 0) levelParts.push(`${redCount} at alert level`);
  if (amberCount > 0) levelParts.push(`${amberCount} at caution level`);
  const levelDescription = levelParts.join(', ');

  return (
    <div
      className={cn(
        'rounded-xl p-4 border',
        redCount >= 2
          ? 'bg-red-500/5 border-red-500/20'
          : redCount === 1
          ? 'bg-amber-500/5 border-amber-500/20'
          : 'bg-olive-500/5 border-olive-500/20'
      )}
    >
      <div className="flex items-start gap-3">
        {redCount > 0 ? (
          <AlertTriangle className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" />
        ) : (
          <TrendingUp className="w-5 h-5 text-olive-400 flex-shrink-0 mt-0.5" />
        )}

        <div className="space-y-2">
          <p className="text-olive-200 text-sm leading-relaxed">
            <span className="font-medium text-olive-100">
              What's happening:
            </span>{' '}
            {elevatedIndicators.length} indicator{elevatedIndicators.length !== 1 ? 's' : ''}{' '}
            {levelDescription} —{' '}
            {elevatedIndicators.slice(0, 5).map((ind, idx) => (
              <React.Fragment key={ind.id}>
                {idx > 0 && ', '}
                <Link
                  to={`/indicators?highlight=${ind.id}`}
                  className={cn(
                    'underline underline-offset-2 hover:no-underline',
                    ind.status.level === 'red'
                      ? 'text-red-400 hover:text-red-300'
                      : 'text-amber-400 hover:text-amber-300'
                  )}
                >
                  {ind.name}
                </Link>
              </React.Fragment>
            ))}
            {elevatedIndicators.length > 5 && (
              <span className="text-olive-400">
                {' '}and {elevatedIndicators.length - 5} more
              </span>
            )}
            .
          </p>

          <p className="text-olive-300 text-sm">
            These conditions suggest focusing on{' '}
            <span className="text-olive-100">{actionFocus}</span>.
          </p>
        </div>
      </div>
    </div>
  );
};

export default ConditionsSummary;
