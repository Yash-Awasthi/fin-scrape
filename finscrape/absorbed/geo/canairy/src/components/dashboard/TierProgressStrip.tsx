/**
 * TierProgressStrip
 *
 * Compact card showing tier progress - elevated from the footer of ActionPlanPreview.
 * Shows: tier name, subtitle, progress bar, task count, total time estimate, next task.
 */

import React, { useMemo } from 'react';
import { Link } from 'react-router-dom';
import { Check, Clock, ChevronRight } from 'lucide-react';
import { TaskTier, PhaseTask, getVisibleTiers, getTierProgress } from '../../data/phaseTasks';
import { cn } from '../../utils/cn';

interface TierProgressStripProps {
  systemPhase: number | 'tighten-up';
  completedTasks: Set<string>;
}

// Estimate total time for a tier
function estimateTotalTime(tier: TaskTier, completedTasks: Set<string>): string {
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
      totalMinutes += 8 * 60;
    } else if (estimate.includes('day')) {
      const match = estimate.match(/(\d+)/);
      if (match) totalMinutes += parseInt(match[1]) * 4 * 60;
    }
  }

  if (totalMinutes < 60) return `~${totalMinutes} min total`;
  const hours = Math.round(totalMinutes / 60 * 10) / 10;
  return `~${hours} hr${hours !== 1 ? 's' : ''} total`;
}

// Get next incomplete task
function getNextTask(tier: TaskTier, completedTasks: Set<string>): PhaseTask | null {
  return tier.tasks.find(t => !completedTasks.has(t.id)) || null;
}

export const TierProgressStrip: React.FC<TierProgressStripProps> = ({
  systemPhase,
  completedTasks,
}) => {
  // Get visible tiers and find the active one
  const tierInfo = useMemo(() => {
    const phase = typeof systemPhase === 'number' ? systemPhase : 5;
    const visibleTiers = getVisibleTiers(phase);

    // Find the first incomplete tier
    for (const tier of visibleTiers) {
      const progress = getTierProgress(tier, completedTasks);
      if (progress.percentage < 100) {
        const nextTask = getNextTask(tier, completedTasks);
        const totalTime = estimateTotalTime(tier, completedTasks);
        return { tier, progress, nextTask, totalTime, isComplete: false };
      }
    }

    // All complete - show last tier as complete
    const lastTier = visibleTiers[visibleTiers.length - 1];
    if (lastTier) {
      return {
        tier: lastTier,
        progress: getTierProgress(lastTier, completedTasks),
        nextTask: null,
        totalTime: '',
        isComplete: true,
      };
    }

    return null;
  }, [systemPhase, completedTasks]);

  if (!tierInfo) return null;

  const { tier, progress, nextTask, totalTime, isComplete } = tierInfo;

  return (
    <div className="glass-card px-4 py-3">
      <div className="flex items-center justify-between gap-4">
        {/* Left: Tier info */}
        <div className="flex items-center gap-3 min-w-0">
          {/* Status icon */}
          {isComplete ? (
            <div className="w-8 h-8 rounded-lg bg-emerald-500/20 flex items-center justify-center flex-shrink-0">
              <Check className="w-4 h-4 text-emerald-400" />
            </div>
          ) : (
            <div className="w-8 h-8 rounded-lg bg-olive-700/30 flex items-center justify-center flex-shrink-0">
              <span className="text-sm font-medium text-olive-300">
                {progress.completed}
              </span>
            </div>
          )}

          {/* Tier name and progress */}
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <span
                className={cn(
                  'font-medium truncate',
                  isComplete ? 'text-emerald-400' : 'text-olive-100'
                )}
              >
                {tier.title}
              </span>
              {isComplete && (
                <span className="text-xs text-emerald-400/70">Complete</span>
              )}
            </div>
            {!isComplete && (
              <div className="flex items-center gap-2 text-xs text-olive-400">
                <span>{tier.subtitle}</span>
                <span className="text-olive-600">·</span>
                <span>
                  {progress.completed} of {progress.total}
                </span>
                {totalTime && (
                  <>
                    <span className="text-olive-600">·</span>
                    <span>{totalTime}</span>
                  </>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Right: Progress bar or next task */}
        <div className="flex items-center gap-3 flex-shrink-0">
          {!isComplete && nextTask && (
            <div className="hidden sm:flex items-center gap-2 text-xs text-olive-400">
              <span>Next:</span>
              <span className="text-olive-200 max-w-[150px] truncate">
                {nextTask.title}
              </span>
              <span className="flex items-center gap-1 text-olive-500">
                <Clock className="w-3 h-3" />
                {nextTask.timeEstimate}
              </span>
            </div>
          )}
          <Link
            to="/action-plan"
            className="text-xs text-amber-400 hover:text-amber-300 transition-colors flex items-center gap-0.5"
          >
            View
            <ChevronRight className="w-3 h-3" />
          </Link>
        </div>
      </div>

      {/* Progress bar */}
      {!isComplete && (
        <div className="mt-3 h-1 bg-olive-700/30 rounded-full overflow-hidden">
          <div
            className="h-full bg-amber-500 rounded-full transition-all duration-300"
            style={{ width: `${progress.percentage}%` }}
          />
        </div>
      )}
    </div>
  );
};

export default TierProgressStrip;
