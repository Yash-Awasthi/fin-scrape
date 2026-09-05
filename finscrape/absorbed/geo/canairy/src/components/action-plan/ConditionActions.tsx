/**
 * ConditionActions - "This Week" actions based on current conditions
 *
 * Shows timely responses driven by elevated indicators.
 * Visually distinct from persistent phase tasks with urgency borders.
 */

import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Check, Clock, AlertTriangle, Zap, ChevronDown, ChevronUp } from 'lucide-react';
import { ActionItem, ActionUrgency } from '../../data/actionGenerator';
import { cn } from '../../utils/cn';

interface ConditionActionsProps {
  actions: ActionItem[];
  completedIds: Set<string>;
  onToggle: (id: string) => void;
}

const urgencyConfig: Record<ActionUrgency, {
  label: string;
  border: string;
  badge: string;
  icon: React.FC<{ className?: string }>;
}> = {
  now: {
    label: 'Do this now',
    border: 'border-l-red-500',
    badge: 'bg-red-500/15 text-red-400 border-red-500/30',
    icon: AlertTriangle,
  },
  today: {
    label: 'Today',
    border: 'border-l-amber-500',
    badge: 'bg-amber-500/15 text-amber-400 border-amber-500/30',
    icon: Zap,
  },
  'this-week': {
    label: 'This week',
    border: 'border-l-olive-500',
    badge: 'bg-olive-500/15 text-olive-400 border-olive-500/30',
    icon: Clock,
  },
};

interface ActionRowProps {
  action: ActionItem;
  completed: boolean;
  onToggle: () => void;
}

const ActionRow: React.FC<ActionRowProps> = ({ action, completed, onToggle }) => {
  const [expanded, setExpanded] = React.useState(false);
  const config = urgencyConfig[action.urgency];
  const hasContext = action.context && (
    action.context.dataPoints?.length ||
    action.context.historicalNote ||
    action.context.consequence
  );

  return (
    <div
      className={cn(
        'rounded-lg border-l-4 transition-colors',
        config.border,
        completed ? 'bg-olive-900/20' : 'bg-olive-900/40'
      )}
    >
      <div className="flex items-start gap-3 p-3">
        {/* Checkbox */}
        <button
          onClick={onToggle}
          className={cn(
            'w-5 h-5 rounded-full border-2 flex items-center justify-center flex-shrink-0 mt-0.5 transition-all',
            completed
              ? 'bg-emerald-500 border-emerald-500'
              : action.urgency === 'now'
              ? 'border-red-400 hover:bg-red-500/10'
              : action.urgency === 'today'
              ? 'border-amber-400 hover:bg-amber-500/10'
              : 'border-olive-500 hover:bg-olive-500/10'
          )}
        >
          {completed && <Check className="w-3 h-3 text-white" />}
        </button>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2">
            <div
              className={cn(
                'text-sm font-medium',
                completed ? 'text-olive-400 line-through' : 'text-olive-100'
              )}
            >
              {action.task}
            </div>

            {/* Urgency badge */}
            {!completed && (
              <span
                className={cn(
                  'px-2 py-0.5 text-[10px] font-medium rounded-md border flex-shrink-0',
                  config.badge
                )}
              >
                {config.label}
              </span>
            )}
          </div>

          {!completed && (
            <>
              <p className="text-xs text-olive-400 mt-1">{action.why}</p>

              <div className="flex items-center gap-3 mt-2">
                <span className="text-[10px] text-olive-500 flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  {action.timeEstimate}
                </span>

                {hasContext && (
                  <button
                    onClick={() => setExpanded(!expanded)}
                    className="text-[10px] text-olive-400 hover:text-olive-300 flex items-center gap-1"
                  >
                    {expanded ? (
                      <>
                        Less detail <ChevronUp className="w-3 h-3" />
                      </>
                    ) : (
                      <>
                        Why this matters <ChevronDown className="w-3 h-3" />
                      </>
                    )}
                  </button>
                )}
              </div>
            </>
          )}
        </div>
      </div>

      {/* Expanded context */}
      <AnimatePresence>
        {expanded && !completed && action.context && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.15 }}
            className="overflow-hidden"
          >
            <div className="px-3 pb-3 pt-1 ml-8 space-y-2 text-xs text-olive-400 border-t border-olive-700/30 mt-1">
              {action.context.dataPoints && action.context.dataPoints.length > 0 && (
                <div>
                  <span className="text-olive-300 font-medium">The data: </span>
                  {action.context.dataPoints.join('. ')}.
                </div>
              )}
              {action.context.historicalNote && (
                <div>
                  <span className="text-olive-300 font-medium">Context: </span>
                  {action.context.historicalNote}
                </div>
              )}
              {action.context.consequence && (
                <div>
                  <span className="text-amber-400 font-medium">If you wait: </span>
                  {action.context.consequence}
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export const ConditionActions: React.FC<ConditionActionsProps> = ({
  actions,
  completedIds,
  onToggle,
}) => {
  // Filter to only indicator-driven actions (not phase tasks)
  const conditionActions = actions.filter(a => !a.phaseTask);

  // If no condition-driven actions, don't render
  if (conditionActions.length === 0) {
    return null;
  }

  const incompleteCount = conditionActions.filter(a => !completedIds.has(a.id)).length;

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-olive-100">
          This Week
        </h2>
        <span className="text-xs text-olive-400">
          Based on current conditions
        </span>
      </div>

      {incompleteCount === 0 ? (
        <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-xl p-4 text-center">
          <Check className="w-6 h-6 text-emerald-400 mx-auto mb-2" />
          <p className="text-sm text-emerald-300">All caught up for this week</p>
        </div>
      ) : (
        <div className="space-y-2">
          {conditionActions.map(action => (
            <ActionRow
              key={action.id}
              action={action}
              completed={completedIds.has(action.id)}
              onToggle={() => onToggle(action.id)}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export default ConditionActions;
