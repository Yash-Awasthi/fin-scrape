/**
 * ActionPlanPreview
 *
 * Condensed action plan preview for the dashboard.
 * Split into two sections:
 * 1. "This week" - condition-driven actions (from indicators)
 * 2. "From your readiness plan" - tier tasks (persistent)
 *
 * Tier progress has been moved to TierProgressStrip component.
 */

import React, { useState, useMemo, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { Check, Clock, ChevronRight, ClipboardList, Zap, Shield } from 'lucide-react';
import { useStore } from '../../store';
import { generateActionList, ActionItem } from '../../data/actionGenerator';
import { computeReadinessFromTiers } from '../../data/phaseTasks';
import { cn } from '../../utils/cn';

// ============================================================================
// PERSISTENCE
// ============================================================================

const STORAGE_KEY = 'canairy_action_plan_this_week';
const TIER_STORAGE_KEY = 'canairy_action_plan_tiers';

function loadCompletedIds(key: string): Set<string> {
  try {
    const stored = localStorage.getItem(key);
    return stored ? new Set(JSON.parse(stored)) : new Set();
  } catch {
    return new Set();
  }
}

function saveCompletedIds(key: string, ids: Set<string>) {
  localStorage.setItem(key, JSON.stringify([...ids]));
}

// ============================================================================
// ACTION ROW COMPONENT
// ============================================================================

interface ActionRowProps {
  action: ActionItem;
  index: number;
  onToggle: () => void;
  showTierName?: boolean;
}

const ActionRow: React.FC<ActionRowProps> = ({ action, index, onToggle, showTierName }) => {
  const getUrgencyColor = (urgency: ActionItem['urgency']) => {
    return {
      now: 'border-red-400',
      today: 'border-amber-400',
      'this-week': 'border-olive-500',
    }[urgency];
  };

  const getUrgencyBadge = (urgency: ActionItem['urgency']) => {
    const config = {
      now: { label: 'Now', className: 'bg-red-500/15 text-red-400' },
      today: { label: 'Today', className: 'bg-amber-500/15 text-amber-400' },
      'this-week': { label: 'This week', className: 'bg-olive-500/15 text-olive-400' },
    }[urgency];
    return (
      <span className={cn('px-1.5 py-0.5 text-[9px] font-medium rounded', config.className)}>
        {config.label}
      </span>
    );
  };

  return (
    <button
      onClick={onToggle}
      className="w-full flex items-start gap-3 py-2.5 px-2 -mx-2 rounded-lg hover:bg-white/[0.03] transition-colors text-left group"
    >
      {/* Checkbox */}
      <div
        className={cn(
          'w-5 h-5 rounded-full border-2 flex items-center justify-center flex-shrink-0 mt-0.5 transition-colors',
          getUrgencyColor(action.urgency),
          'group-hover:bg-white/5'
        )}
      >
        <span className="text-[10px] font-mono text-white/40">{index + 1}</span>
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <p className="text-sm text-white truncate">{action.task}</p>
          {!action.phaseTask && getUrgencyBadge(action.urgency)}
        </div>
        <p className="text-xs text-white/30 mt-0.5 truncate">
          {showTierName && action.tierName ? (
            <span className="text-olive-400">{action.tierName}: </span>
          ) : null}
          {action.why}
        </p>
      </div>

      {/* Time estimate */}
      <span className="text-[10px] text-white/20 flex items-center gap-1 flex-shrink-0">
        <Clock className="w-3 h-3" />
        {action.timeEstimate}
      </span>
    </button>
  );
};

// ============================================================================
// MAIN COMPONENT
// ============================================================================

export const ActionPlanPreview: React.FC = () => {
  const { indicators, systemPhase } = useStore();

  // Completion state
  const [completedIds, setCompletedIds] = useState<Set<string>>(
    () => loadCompletedIds(STORAGE_KEY)
  );
  const tierCompletedIds = useMemo(
    () => loadCompletedIds(TIER_STORAGE_KEY),
    []
  );

  // Generate actions
  const actions = useMemo(() => {
    const phase = typeof systemPhase === 'number' ? systemPhase : undefined;
    return generateActionList(indicators, tierCompletedIds, phase);
  }, [indicators, tierCompletedIds, systemPhase]);

  // Split into condition-driven and tier tasks
  const { conditionActions, tierActions } = useMemo(() => {
    const condition = actions.filter(a => !a.phaseTask && !completedIds.has(a.id));
    const tier = actions.filter(a => a.phaseTask && !completedIds.has(a.id));
    return {
      conditionActions: condition.slice(0, 5),
      tierActions: tier.slice(0, 3),
    };
  }, [actions, completedIds]);

  const readiness = useMemo(() => {
    return computeReadinessFromTiers(tierCompletedIds);
  }, [tierCompletedIds]);

  // Toggle handler
  const toggleAction = useCallback((id: string) => {
    setCompletedIds(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      saveCompletedIds(STORAGE_KEY, next);
      return next;
    });
  }, []);

  const hasConditionActions = conditionActions.length > 0;
  const hasTierActions = tierActions.length > 0;

  if (!hasConditionActions && !hasTierActions) {
    return (
      <div className="glass-card px-5 py-6 text-center">
        <div className="w-12 h-12 rounded-xl bg-emerald-500/10 flex items-center justify-center mx-auto mb-3">
          <Check className="w-6 h-6 text-emerald-400" />
        </div>
        <p className="text-olive-200 font-medium">All caught up!</p>
        <p className="text-sm text-olive-400 mt-1">
          Check the{' '}
          <Link to="/action-plan" className="text-amber-400 hover:text-amber-300">
            full plan
          </Link>{' '}
          for readiness tasks.
        </p>
      </div>
    );
  }

  return (
    <div className="glass-card overflow-hidden">
      {/* Header */}
      <div className="px-5 py-4 border-b border-white/[0.04] flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-amber-500/10 flex items-center justify-center">
            <ClipboardList className="w-4 h-4 text-amber-400" />
          </div>
          <div>
            <h3 className="font-display font-semibold text-white">Your action plan</h3>
            <p className="text-xs text-white/30">{readiness.description}</p>
          </div>
        </div>
        <Link
          to="/action-plan"
          className="text-xs text-amber-400 hover:text-amber-300 transition-colors flex items-center gap-1"
        >
          Open full plan
          <ChevronRight className="w-3 h-3" />
        </Link>
      </div>

      {/* Content */}
      <div className="divide-y divide-white/[0.04]">
        {/* Condition-driven actions section */}
        {hasConditionActions && (
          <div className="px-5 py-3">
            <div className="flex items-center gap-2 mb-2">
              <Zap className="w-3 h-3 text-amber-400" />
              <span className="text-[10px] font-medium text-amber-400 uppercase tracking-wider">
                This week
              </span>
            </div>
            <div className="space-y-0">
              {conditionActions.map((action, index) => (
                <ActionRow
                  key={action.id}
                  action={action}
                  index={index}
                  onToggle={() => toggleAction(action.id)}
                />
              ))}
            </div>
          </div>
        )}

        {/* Tier tasks section */}
        {hasTierActions && (
          <div className="px-5 py-3">
            <div className="flex items-center gap-2 mb-2">
              <Shield className="w-3 h-3 text-olive-400" />
              <span className="text-[10px] font-medium text-olive-400 uppercase tracking-wider">
                From your readiness plan
              </span>
            </div>
            <div className="space-y-0">
              {tierActions.map((action, index) => (
                <ActionRow
                  key={action.id}
                  action={action}
                  index={conditionActions.length + index}
                  onToggle={() => toggleAction(action.id)}
                  showTierName
                />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
