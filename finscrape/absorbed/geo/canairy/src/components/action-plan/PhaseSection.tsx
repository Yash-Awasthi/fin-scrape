/**
 * PhaseSection - A single tier/phase with its tasks
 *
 * Shows the phase header, why paragraph, and task list.
 * Collapses to a single line when complete.
 */

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Check, ChevronDown, Clock, DollarSign } from 'lucide-react';
import { TaskTier, PhaseTask, getTierProgress } from '../../data/phaseTasks';
import { cn } from '../../utils/cn';

interface PhaseSectionProps {
  tier: TaskTier;
  completedTasks: Set<string>;
  onToggleTask: (taskId: string) => void;
  defaultExpanded?: boolean;
  id?: string;
}

// Estimate remaining time for incomplete tasks
function estimateRemainingTime(tier: TaskTier, completedTasks: Set<string>): string {
  const incompleteTasks = tier.tasks.filter(t => !completedTasks.has(t.id));
  if (incompleteTasks.length === 0) return '';

  let totalMinutes = 0;
  for (const task of incompleteTasks) {
    const estimate = task.timeEstimate.toLowerCase();
    if (estimate.includes('min')) {
      const match = estimate.match(/(\d+)/);
      if (match) totalMinutes += parseInt(match[1]);
    } else if (estimate.includes('hr')) {
      const match = estimate.match(/(\d+)/);
      if (match) totalMinutes += parseInt(match[1]) * 60;
    } else if (estimate.includes('weekend')) {
      totalMinutes += 8 * 60; // Assume 8 hours for a weekend
    } else if (estimate.includes('day')) {
      const match = estimate.match(/(\d+)/);
      if (match) totalMinutes += parseInt(match[1]) * 4 * 60;
    }
  }

  if (totalMinutes < 60) return `~${totalMinutes} min`;
  const hours = Math.round(totalMinutes / 60 * 10) / 10;
  return `~${hours} hr${hours !== 1 ? 's' : ''}`;
}

interface TaskRowProps {
  task: PhaseTask;
  completed: boolean;
  onToggle: () => void;
}

const TaskRow: React.FC<TaskRowProps> = ({ task, completed, onToggle }) => {
  return (
    <div
      className={cn(
        'flex items-start gap-3 py-3 px-3 rounded-lg transition-colors',
        completed ? 'bg-olive-900/20' : 'bg-olive-900/40 hover:bg-olive-800/50'
      )}
    >
      {/* Checkbox */}
      <button
        onClick={onToggle}
        className={cn(
          'w-5 h-5 rounded-full border-2 flex items-center justify-center flex-shrink-0 mt-0.5 transition-all',
          completed
            ? 'bg-emerald-500 border-emerald-500'
            : 'bg-transparent border-olive-500 hover:border-olive-400'
        )}
      >
        {completed && <Check className="w-3 h-3 text-white" />}
      </button>

      {/* Content */}
      <div className="flex-1 min-w-0">
        <div
          className={cn(
            'text-sm font-medium',
            completed ? 'text-olive-400 line-through' : 'text-olive-100'
          )}
        >
          {task.title}
        </div>
        {!completed && (
          <p className="text-xs text-olive-400 mt-0.5 line-clamp-2">
            {task.description}
          </p>
        )}
      </div>

      {/* Meta */}
      {!completed && (
        <div className="flex items-center gap-2 text-[10px] text-olive-500 flex-shrink-0">
          <span className="flex items-center gap-1">
            <Clock className="w-3 h-3" />
            {task.timeEstimate}
          </span>
          {task.costEstimate && (
            <span className="flex items-center gap-1">
              <DollarSign className="w-3 h-3" />
              {task.costEstimate}
            </span>
          )}
        </div>
      )}
    </div>
  );
};

export const PhaseSection: React.FC<PhaseSectionProps> = ({
  tier,
  completedTasks,
  onToggleTask,
  defaultExpanded = false,
  id,
}) => {
  const progress = getTierProgress(tier, completedTasks);
  const isComplete = progress.percentage === 100;
  const [expanded, setExpanded] = useState(!isComplete && defaultExpanded);
  const remainingTime = estimateRemainingTime(tier, completedTasks);

  return (
    <section id={id} className="scroll-mt-4">
      {/* Header - always visible */}
      <button
        onClick={() => setExpanded(!expanded)}
        className={cn(
          'w-full flex items-center justify-between gap-4 p-4 rounded-xl border transition-colors text-left',
          isComplete
            ? 'bg-emerald-500/5 border-emerald-500/20 hover:bg-emerald-500/10'
            : 'bg-olive-900/30 border-olive-700/30 hover:bg-olive-800/40'
        )}
      >
        <div className="flex items-center gap-3 min-w-0">
          {/* Completion indicator */}
          {isComplete ? (
            <div className="w-8 h-8 rounded-full bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center flex-shrink-0">
              <Check className="w-4 h-4 text-emerald-400" />
            </div>
          ) : (
            <div className="w-8 h-8 rounded-full bg-olive-700/30 flex items-center justify-center flex-shrink-0">
              <span className="text-sm font-medium text-olive-300">
                {progress.completed}
              </span>
            </div>
          )}

          {/* Title and progress */}
          <div className="min-w-0">
            <h3
              className={cn(
                'font-semibold truncate',
                isComplete ? 'text-emerald-300' : 'text-olive-100'
              )}
            >
              {tier.title}
            </h3>
            <p className="text-xs text-olive-400 truncate">
              {isComplete ? (
                'Complete'
              ) : (
                <>
                  {progress.completed} of {progress.total} complete
                  {remainingTime && <span className="ml-2">{remainingTime} remaining</span>}
                </>
              )}
            </p>
          </div>
        </div>

        {/* Expand/collapse */}
        <ChevronDown
          className={cn(
            'w-5 h-5 text-olive-400 transition-transform flex-shrink-0',
            expanded && 'rotate-180'
          )}
        />
      </button>

      {/* Expandable content */}
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="pt-4 space-y-4">
              {/* Why paragraph */}
              {tier.whyContent && (
                <p className="text-sm text-olive-300 italic px-1">
                  {tier.whyContent}
                </p>
              )}

              {/* Condition note */}
              {tier.conditionNote && !isComplete && (
                <div className="bg-amber-500/10 border border-amber-500/20 rounded-lg px-3 py-2">
                  <p className="text-xs text-amber-300">{tier.conditionNote}</p>
                </div>
              )}

              {/* Task list */}
              <div className="space-y-2">
                {tier.tasks.map(task => (
                  <TaskRow
                    key={task.id}
                    task={task}
                    completed={completedTasks.has(task.id)}
                    onToggle={() => onToggleTask(task.id)}
                  />
                ))}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </section>
  );
};

export default PhaseSection;
