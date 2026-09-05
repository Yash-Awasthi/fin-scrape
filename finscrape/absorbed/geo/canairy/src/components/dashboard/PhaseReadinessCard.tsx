/**
 * PhaseReadinessCard Component
 *
 * Shows actual phase tasks with checkboxes, not just a count.
 * Tasks come from the tier system and are persisted via localStorage.
 */

import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowRight, Check, ChevronDown, Clock } from 'lucide-react';
import { useStore } from '../../store';
import { getVisibleTiers, getTierProgress, getPhaseDescription, TaskTier } from '../../data/phaseTasks';
import { usePhaseTaskCompletion } from '../../hooks/useTaskCompletion';
import { cn } from '../../utils/cn';

export const PhaseReadinessCard: React.FC = () => {
  const { systemPhase } = useStore();
  const { completedIds, toggle, isCompleted } = usePhaseTaskCompletion();
  const [expanded, setExpanded] = useState(true);

  // Handle elevated phase state
  const isElevatedPhase = systemPhase === 'tighten-up' || (typeof systemPhase === 'number' && systemPhase >= 7);
  const phaseNum = systemPhase === 'tighten-up' ? 7 : (typeof systemPhase === 'number' ? systemPhase : 2);

  // Get visible tiers for current phase
  const visibleTiers = getVisibleTiers(phaseNum);

  // Find the first incomplete tier (the one to focus on)
  const focusTier = visibleTiers.find(tier => {
    const progress = getTierProgress(tier, completedIds);
    return progress.completed < progress.total;
  }) || visibleTiers[visibleTiers.length - 1];

  if (!focusTier) {
    return null;
  }

  const progress = getTierProgress(focusTier, completedIds);

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.2 }}
      className="glass-card overflow-hidden"
    >
      {/* Header */}
      <div className="px-5 py-3 border-b border-white/5 flex items-center justify-between">
        <div className="flex items-center gap-3">
          {/* Phase badge */}
          <div className={cn(
            'rounded-lg flex items-center justify-center w-8 h-8',
            isElevatedPhase
              ? 'bg-red-500/20'
              : 'bg-amber-500/15'
          )}>
            <span className={cn(
              'font-display font-bold text-sm',
              isElevatedPhase ? 'text-red-400' : 'text-amber-400'
            )}>
              {phaseNum}
            </span>
          </div>

          <div>
            <p className={cn(
              'text-sm font-display font-semibold',
              isElevatedPhase ? 'text-red-400' : 'text-amber-400'
            )}>
              {focusTier.title}
            </p>
            <p className="text-[11px] text-olive-tertiary">
              {focusTier.subtitle}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <span className="text-xs font-mono text-olive-data">
            {progress.completed}/{progress.total}
          </span>
          <Link
            to="/action-plan"
            className="text-xs text-amber-400 hover:text-amber-300 transition-colors font-medium flex items-center gap-1"
          >
            Full plan
            <ArrowRight size={12} />
          </Link>
        </div>
      </div>

      {/* Task list */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full px-5 py-2 flex items-center justify-between text-xs text-olive-muted hover:text-olive-secondary transition-colors border-b border-white/5"
      >
        <span>
          {progress.total - progress.completed} tasks remaining
        </span>
        <ChevronDown
          size={14}
          className={cn(
            'transition-transform duration-200',
            expanded && 'rotate-180'
          )}
        />
      </button>

      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="divide-y divide-white/5 max-h-[280px] overflow-y-auto">
              {focusTier.tasks.map((task) => {
                const taskCompleted = isCompleted(task.id);
                return (
                  <div
                    key={task.id}
                    className={cn(
                      'flex items-start gap-3 px-5 py-2.5 group',
                      taskCompleted && 'opacity-50'
                    )}
                  >
                    {/* Checkbox */}
                    <button
                      onClick={() => toggle(task.id)}
                      className={cn(
                        'mt-0.5 w-4 h-4 rounded-full border-2 flex items-center justify-center shrink-0 transition-all',
                        taskCompleted
                          ? 'bg-emerald-500/20 border-emerald-500 text-emerald-500'
                          : 'border-olive-muted hover:border-amber-500'
                      )}
                    >
                      {taskCompleted && <Check size={10} />}
                    </button>

                    {/* Task content */}
                    <div className="flex-1 min-w-0">
                      <p className={cn(
                        'text-sm',
                        taskCompleted
                          ? 'text-olive-muted line-through'
                          : 'text-olive-secondary'
                      )}>
                        {task.title}
                      </p>
                    </div>

                    {/* Time estimate */}
                    {!taskCompleted && (
                      <span className="text-[10px] font-mono text-olive-muted shrink-0 flex items-center gap-1">
                        <Clock size={10} />
                        {task.timeEstimate}
                      </span>
                    )}
                  </div>
                );
              })}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Progress bar */}
      <div className="px-5 py-2.5 border-t border-white/5">
        <div className="h-1 bg-white/5 rounded-full overflow-hidden">
          <motion.div
            className="h-full bg-amber-500 rounded-full"
            initial={{ width: 0 }}
            animate={{ width: `${progress.percentage}%` }}
            transition={{ delay: 0.3, duration: 0.5 }}
          />
        </div>
      </div>
    </motion.div>
  );
};

export default PhaseReadinessCard;
