/**
 * ConditionsBridge
 *
 * Connects what's happening (indicators) to what you should do (action plan).
 * Renders 1-2 sentences that bridge the status heading to the action plan,
 * with tappable indicator names that link to the indicators page.
 */

import React from 'react';
import { Link } from 'react-router-dom';
import { IndicatorData } from '../../types';
import { getDisplayName } from '../../data/indicatorTranslations';
import { cn } from '../../utils/cn';

type ThreatState = 'normal' | 'elevated' | 'critical';

interface ConditionsBridgeProps {
  indicators: IndicatorData[];
  threatState: ThreatState;
}

// Map domains to action focus areas
function getActionFocus(elevatedIndicators: IndicatorData[]): string {
  const domains = new Set(elevatedIndicators.map(i => i.domain));

  const focusAreas: string[] = [];

  if (domains.has('supply_chain')) focusAreas.push('supplies');
  if (domains.has('economy') || domains.has('housing_mortgage')) focusAreas.push('financial buffers');
  if (domains.has('energy')) focusAreas.push('energy backup');
  if (domains.has('security_infrastructure') || domains.has('telecommunications')) focusAreas.push('communication');
  if (domains.has('global_conflict') || domains.has('oil_axis')) focusAreas.push('essentials');
  if (domains.has('jobs_labor')) focusAreas.push('prescriptions and supplies');

  if (focusAreas.length === 0) return 'general preparedness';
  if (focusAreas.length === 1) return focusAreas[0];
  if (focusAreas.length === 2) return `${focusAreas[0]} and ${focusAreas[1]}`;
  return `${focusAreas.slice(0, -1).join(', ')}, and ${focusAreas[focusAreas.length - 1]}`;
}

// Get human-readable condition descriptions
function getConditionDescription(indicator: IndicatorData): string {
  const name = getDisplayName(indicator.id).toLowerCase();
  const level = indicator.status.level;

  // Domain-specific phrasing
  if (indicator.domain === 'supply_chain') {
    return level === 'red' ? `${name} spiking` : `${name} elevated`;
  }
  if (indicator.domain === 'economy') {
    return level === 'red' ? `${name} under stress` : `${name} trending up`;
  }
  if (indicator.domain === 'energy') {
    return level === 'red' ? `${name} at critical levels` : `${name} tightening`;
  }
  if (indicator.domain === 'global_conflict') {
    return level === 'red' ? `${name} at high alert` : `${name} above normal`;
  }
  if (indicator.domain === 'jobs_labor') {
    return level === 'red' ? `${name} disrupting supply chains` : `${name} affecting availability`;
  }

  return level === 'red' ? `${name} at alert level` : `${name} at caution level`;
}

export const ConditionsBridge: React.FC<ConditionsBridgeProps> = ({
  indicators,
  threatState,
}) => {
  // Get elevated indicators (amber and red)
  const elevatedIndicators = indicators.filter(
    i => i.status.level === 'amber' || i.status.level === 'red'
  );

  // If all green, don't render
  if (elevatedIndicators.length === 0) {
    return null;
  }

  const actionFocus = getActionFocus(elevatedIndicators);

  // Sort: red first, then amber
  const sortedIndicators = [...elevatedIndicators].sort((a, b) => {
    if (a.status.level === 'red' && b.status.level !== 'red') return -1;
    if (a.status.level !== 'red' && b.status.level === 'red') return 1;
    return 0;
  });

  // Take top indicators to mention
  const mentionedIndicators = sortedIndicators.slice(0, 4);

  return (
    <div
      className={cn(
        'px-4 py-3 rounded-xl border-l-4',
        threatState === 'critical'
          ? 'bg-red-500/5 border-l-red-500'
          : threatState === 'elevated'
          ? 'bg-amber-500/5 border-l-amber-500'
          : 'bg-olive-500/5 border-l-olive-500'
      )}
    >
      <p className="text-sm text-olive-200 leading-relaxed">
        <span className="font-medium text-olive-100">
          What's driving your plan this week:
        </span>{' '}
        {mentionedIndicators.map((ind, idx) => (
          <React.Fragment key={ind.id}>
            {idx > 0 && (idx === mentionedIndicators.length - 1 ? ', and ' : ', ')}
            <Link
              to={`/indicators?highlight=${ind.id}`}
              className={cn(
                'underline underline-offset-2 hover:no-underline',
                ind.status.level === 'red'
                  ? 'text-red-400 hover:text-red-300'
                  : 'text-amber-400 hover:text-amber-300'
              )}
            >
              {getConditionDescription(ind)}
            </Link>
          </React.Fragment>
        ))}
        {elevatedIndicators.length > 4 && (
          <span className="text-olive-400">
            {' '}(+{elevatedIndicators.length - 4} more)
          </span>
        )}
        .{' '}
        <span className="text-olive-300">
          {threatState === 'critical'
            ? `Focus on the priority items in your action plan.`
            : `Your action plan prioritizes ${actionFocus}.`}
        </span>
      </p>
    </div>
  );
};

export default ConditionsBridge;
