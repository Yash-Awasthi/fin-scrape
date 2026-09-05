/**
 * MPhaseSection - Migration/Relocation phase tasks
 *
 * Displays M-phase tasks when domestic control conditions trigger.
 * Uses distinct styling (blue/purple) to differentiate from standard tiers.
 */

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Check,
  ChevronDown,
  Clock,
  DollarSign,
  Plane,
  AlertTriangle,
} from 'lucide-react';
import { MPhaseTier, MPhaseTask, getMPhaseProgress } from '../../data/phaseTasks';
import { MPhaseInfo } from '../../types';
import { cn } from '../../utils/cn';

interface MPhaseSectionProps {
  tier: MPhaseTier;
  mPhaseInfo: MPhaseInfo;
  completedTasks: Set<string>;
  onToggleTask: (taskId: string) => void;
  defaultExpanded?: boolean;
}

interface MPhaseTaskRowProps {
  task: MPhaseTask;
  completed: boolean;
  onToggle: () => void;
}

const MPhaseTaskRow: React.FC<MPhaseTaskRowProps> = ({ task, completed, onToggle }) => {
  return (
    <div
      className={cn(
        'flex items-start gap-3 py-3 px-3 rounded-lg transition-colors',
        completed ? 'bg-indigo-900/20' : 'bg-indigo-900/30 hover:bg-indigo-800/40'
      )}
    >
      {/* Checkbox */}
      <button
        onClick={onToggle}
        className={cn(
          'w-5 h-5 rounded-full border-2 flex items-center justify-center flex-shrink-0 mt-0.5 transition-all',
          completed
            ? 'bg-indigo-500 border-indigo-500'
            : 'bg-transparent border-indigo-400 hover:border-indigo-300'
        )}
      >
        {completed && <Check className="w-3 h-3 text-white" />}
      </button>

      {/* Content */}
      <div className="flex-1 min-w-0">
        <div
          className={cn(
            'text-sm font-medium',
            completed ? 'text-indigo-300 line-through' : 'text-indigo-100'
          )}
        >
          {task.title}
        </div>
        {!completed && (
          <p className="text-xs text-indigo-300/70 mt-0.5 line-clamp-2">
            {task.description}
          </p>
        )}
      </div>

      {/* Meta */}
      {!completed && (
        <div className="flex items-center gap-2 text-[10px] text-indigo-400 flex-shrink-0">
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

export const MPhaseSection: React.FC<MPhaseSectionProps> = ({
  tier,
  mPhaseInfo,
  completedTasks,
  onToggleTask,
  defaultExpanded = false,
}) => {
  const progress = getMPhaseProgress(tier.level, completedTasks);
  const isComplete = progress.percentage === 100;
  const [expanded, setExpanded] = useState(!isComplete && defaultExpanded);

  // Level badge colors
  const levelColors = {
    0: 'bg-blue-500/20 text-blue-300 border-blue-500/30',
    1: 'bg-indigo-500/20 text-indigo-300 border-indigo-500/30',
    2: 'bg-purple-500/20 text-purple-300 border-purple-500/30',
  };

  return (
    <section className="scroll-mt-4">
      {/* Header */}
      <button
        onClick={() => setExpanded(!expanded)}
        className={cn(
          'w-full flex items-center justify-between gap-4 p-4 rounded-xl border transition-colors text-left',
          isComplete
            ? 'bg-indigo-500/10 border-indigo-500/30 hover:bg-indigo-500/15'
            : 'bg-gradient-to-r from-indigo-900/40 to-purple-900/30 border-indigo-600/30 hover:border-indigo-500/50'
        )}
      >
        <div className="flex items-center gap-3 min-w-0">
          {/* Icon */}
          <div
            className={cn(
              'w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0',
              isComplete
                ? 'bg-indigo-500/20 border border-indigo-500/40'
                : 'bg-indigo-600/30 border border-indigo-500/40'
            )}
          >
            {isComplete ? (
              <Check className="w-5 h-5 text-indigo-400" />
            ) : (
              <Plane className="w-5 h-5 text-indigo-300" />
            )}
          </div>

          {/* Title and info */}
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2 mb-0.5">
              <span
                className={cn(
                  'text-[10px] font-semibold px-2 py-0.5 rounded-full border',
                  levelColors[tier.level]
                )}
              >
                M-{tier.level}
              </span>
              <h3
                className={cn(
                  'font-semibold truncate',
                  isComplete ? 'text-indigo-300' : 'text-indigo-100'
                )}
              >
                {tier.title}
              </h3>
            </div>
            <p className="text-xs text-indigo-300/70 truncate">
              {isComplete ? (
                'Complete'
              ) : (
                <>
                  {progress.completed} of {progress.total} complete
                  <span className="mx-2">•</span>
                  {tier.subtitle}
                </>
              )}
            </p>
          </div>
        </div>

        {/* Expand/collapse */}
        <ChevronDown
          className={cn(
            'w-5 h-5 text-indigo-400 transition-transform flex-shrink-0',
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
              {/* Trigger reason banner */}
              <div className="flex items-start gap-2 bg-indigo-500/10 border border-indigo-500/20 rounded-lg px-3 py-2">
                <AlertTriangle className="w-4 h-4 text-indigo-400 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="text-xs text-indigo-300 font-medium">
                    Why this is showing
                  </p>
                  <p className="text-xs text-indigo-300/70 mt-0.5">
                    {mPhaseInfo.triggerReason}
                  </p>
                </div>
              </div>

              {/* Why paragraph */}
              {tier.whyContent && (
                <p className="text-sm text-indigo-200/80 italic px-1">
                  {tier.whyContent}
                </p>
              )}

              {/* Task list */}
              <div className="space-y-2">
                {tier.tasks.map(task => (
                  <MPhaseTaskRow
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

export default MPhaseSection;
