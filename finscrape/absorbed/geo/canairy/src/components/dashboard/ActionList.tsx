/**
 * ActionList Component
 *
 * The primary element on the dashboard - a numbered checklist of actionable tasks.
 * Tasks are generated from indicators, AI insights, and phase tasks.
 * Each action is expandable to show supporting data and reasons.
 */

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Check, ChevronDown, ChevronRight, Clock, AlertTriangle, History, ExternalLink } from 'lucide-react';
import { ActionItem, ActionContext as ActionContextType, getUrgencyLabel, getUrgencyStyles } from '../../data/actionGenerator';
import { cn } from '../../utils/cn';

interface ActionListProps {
  actions: ActionItem[];
  completedIds: Set<string>;
  onToggle: (id: string) => void;
  onExpand?: (insightId?: string) => void;
}

export const ActionList: React.FC<ActionListProps> = ({
  actions,
  completedIds,
  onToggle,
  onExpand,
}) => {
  const [showCompleted, setShowCompleted] = useState(false);

  const incomplete = actions.filter(a => !completedIds.has(a.id));
  const completed = actions.filter(a => completedIds.has(a.id));

  if (actions.length === 0) {
    return (
      <div className="glass-card p-6 text-center">
        <div className="w-12 h-12 bg-emerald-500/10 rounded-full flex items-center justify-center mx-auto mb-3">
          <Check className="w-6 h-6 text-emerald-400" />
        </div>
        <p className="text-olive-primary font-medium mb-1">You're all caught up</p>
        <p className="text-sm text-olive-secondary">
          No urgent actions right now. Check the playbook for ways to work ahead.
        </p>
      </div>
    );
  }

  return (
    <div className="glass-card overflow-hidden">
      {/* Header */}
      <div className="px-5 py-3 border-b border-white/5 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <h2 className="text-sm font-display font-semibold text-olive-primary">
            Your action list
          </h2>
          {incomplete.length > 0 && (
            <span className="text-xs font-mono text-olive-data bg-white/5 px-1.5 py-0.5 rounded">
              {incomplete.length} remaining
            </span>
          )}
        </div>
        <span className="text-xs text-olive-muted">
          Based on current conditions
        </span>
      </div>

      {/* Incomplete actions */}
      <div className="divide-y divide-white/5">
        <AnimatePresence initial={false}>
          {incomplete.map((action, i) => (
            <ActionRow
              key={action.id}
              action={action}
              index={i + 1}
              isCompleted={false}
              onToggle={() => onToggle(action.id)}
              onExpand={onExpand}
            />
          ))}
        </AnimatePresence>
      </div>

      {/* Completed section */}
      {completed.length > 0 && (
        <div className="border-t border-white/5">
          <button
            onClick={() => setShowCompleted(!showCompleted)}
            className="w-full px-5 py-2.5 flex items-center justify-between text-xs text-olive-muted hover:text-olive-secondary transition-colors"
          >
            <span>{completed.length} completed</span>
            <ChevronDown
              size={14}
              className={cn(
                'transition-transform duration-200',
                showCompleted && 'rotate-180'
              )}
            />
          </button>

          <AnimatePresence>
            {showCompleted && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                transition={{ duration: 0.2 }}
                className="overflow-hidden"
              >
                <div className="divide-y divide-white/5">
                  {completed.map((action) => (
                    <ActionRow
                      key={action.id}
                      action={action}
                      index={null}
                      isCompleted={true}
                      onToggle={() => onToggle(action.id)}
                      onExpand={onExpand}
                    />
                  ))}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      )}
    </div>
  );
};

// ============================================================================
// ActionRow Component
// ============================================================================

interface ActionRowProps {
  action: ActionItem;
  index: number | null;
  isCompleted: boolean;
  onToggle: () => void;
  onExpand?: (insightId?: string) => void;
}

const ActionRow: React.FC<ActionRowProps> = ({
  action,
  index,
  isCompleted,
  onToggle,
  onExpand: _onExpand,
}) => {
  const [expanded, setExpanded] = useState(false);
  const hasContext = action.context && (
    action.context.dataPoints?.length ||
    action.context.historicalNote ||
    action.context.consequence
  );

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, height: 0 }}
      transition={{ duration: 0.2 }}
      className={cn(
        isCompleted && 'opacity-50'
      )}
    >
      <div className={cn(
        'flex items-start gap-3 px-5 py-3 group',
        hasContext && !isCompleted && 'cursor-pointer hover:bg-white/[0.02]'
      )}
        onClick={() => hasContext && !isCompleted && setExpanded(!expanded)}
      >
        {/* Checkbox */}
        <button
          onClick={(e) => {
            e.stopPropagation();
            onToggle();
          }}
          className={cn(
            'mt-0.5 w-5 h-5 rounded-full border-2 flex items-center justify-center shrink-0 transition-all',
            isCompleted
              ? 'bg-emerald-500/20 border-emerald-500 text-emerald-500'
              : 'border-olive-muted hover:border-olive-secondary group-hover:border-olive-primary'
          )}
        >
          {isCompleted && <Check size={12} />}
        </button>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            {/* Expand indicator */}
            {hasContext && !isCompleted && (
              <ChevronRight
                size={12}
                className={cn(
                  'text-olive-muted transition-transform duration-200 shrink-0',
                  expanded && 'rotate-90'
                )}
              />
            )}

            {/* Priority number */}
            {index !== null && !isCompleted && (
              <span className="text-xs font-mono text-olive-muted w-4 shrink-0">
                {index}.
              </span>
            )}

            {/* Task */}
            <p
              className={cn(
                'text-sm text-olive-primary',
                isCompleted && 'line-through text-olive-muted'
              )}
            >
              {action.task}
            </p>
          </div>

          {/* Why - only show if not completed */}
          {!isCompleted && (
            <p className={cn(
              'text-xs text-olive-data mt-0.5',
              hasContext ? 'ml-[18px]' : 'ml-4'
            )}>
              {action.why}
            </p>
          )}

          {/* Phase task badge */}
          {action.phaseTask && !isCompleted && action.tierName && (
            <div className={cn('mt-1', hasContext ? 'ml-[18px]' : 'ml-4')}>
              <span className="text-[10px] text-olive-muted bg-white/5 px-1.5 py-0.5 rounded">
                {action.tierName}
              </span>
            </div>
          )}
        </div>

        {/* Right side: urgency + time */}
        <div className="flex items-center gap-2 shrink-0">
          {!isCompleted && (
            <>
              <span
                className={cn(
                  'text-[10px] font-mono px-1.5 py-0.5 rounded',
                  getUrgencyStyles(action.urgency)
                )}
              >
                {getUrgencyLabel(action.urgency)}
              </span>
              <span className="text-[10px] font-mono text-olive-muted flex items-center gap-1">
                <Clock size={10} />
                {action.timeEstimate}
              </span>
            </>
          )}
        </div>
      </div>

      {/* Expanded context */}
      <AnimatePresence>
        {expanded && action.context && !isCompleted && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <ActionContextPanel context={action.context} />
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
};

// ============================================================================
// ActionContextPanel Component - Expanded details
// ============================================================================

interface ActionContextPanelProps {
  context: ActionContextType;
}

const ActionContextPanel: React.FC<ActionContextPanelProps> = ({ context }) => {
  return (
    <div className="ml-11 mr-5 mb-3 mt-1 p-3 bg-olive-card/50 rounded-lg border border-white/5 space-y-2.5">
      {/* Data points */}
      {context.dataPoints && context.dataPoints.length > 0 && (
        <div>
          <p className="text-[10px] uppercase tracking-wider text-olive-muted mb-1 font-medium">
            Key Data
          </p>
          <ul className="space-y-0.5">
            {context.dataPoints.map((point, i) => (
              <li key={i} className="text-xs text-olive-secondary flex items-start gap-2">
                <span className="text-amber-400 mt-0.5">•</span>
                <span>{point}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Historical note */}
      {context.historicalNote && (
        <div className="flex items-start gap-2">
          <History size={12} className="text-olive-muted mt-0.5 shrink-0" />
          <p className="text-xs text-olive-secondary">
            <span className="text-olive-muted">History: </span>
            {context.historicalNote}
          </p>
        </div>
      )}

      {/* Consequence */}
      {context.consequence && (
        <div className="flex items-start gap-2">
          <AlertTriangle size={12} className="text-amber-500 mt-0.5 shrink-0" />
          <p className="text-xs text-olive-secondary">
            <span className="text-amber-400 font-medium">If you wait: </span>
            {context.consequence}
          </p>
        </div>
      )}

      {/* Sources */}
      {context.sources && context.sources.length > 0 && (
        <div className="pt-1.5 border-t border-white/5">
          <div className="flex items-center gap-1.5 flex-wrap">
            <ExternalLink size={10} className="text-olive-muted" />
            {context.sources.map((source, i) => (
              <span key={i} className="text-[10px] text-olive-muted font-mono">
                {source}{i < context.sources!.length - 1 && ' ·'}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default ActionList;
