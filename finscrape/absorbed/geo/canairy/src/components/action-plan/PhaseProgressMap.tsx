/**
 * PhaseProgressMap - Visual timeline showing the full preparedness journey
 *
 * Shows where the family is in their preparedness journey with a vertical
 * timeline that collapses completed phases and highlights the active one.
 */

import React from 'react';
import { Check, Circle, Dot } from 'lucide-react';
import { TaskTier, getTierProgress } from '../../data/phaseTasks';
import { cn } from '../../utils/cn';

interface PhaseProgressMapProps {
  tiers: TaskTier[];
  completedTasks: Set<string>;
  onTierClick?: (tierId: string) => void;
}

type TierState = 'complete' | 'active' | 'next' | 'future';

function getTierState(
  tier: TaskTier,
  completedTasks: Set<string>,
  tierIndex: number,
  activeTierIndex: number
): TierState {
  const progress = getTierProgress(tier, completedTasks);

  if (progress.percentage === 100) return 'complete';
  if (tierIndex === activeTierIndex) return 'active';
  if (tierIndex === activeTierIndex + 1) return 'next';
  return 'future';
}

export const PhaseProgressMap: React.FC<PhaseProgressMapProps> = ({
  tiers,
  completedTasks,
  onTierClick,
}) => {
  // Find the first incomplete tier (the active one)
  const activeTierIndex = tiers.findIndex(tier => {
    const progress = getTierProgress(tier, completedTasks);
    return progress.percentage < 100;
  });

  // If all complete, active is the last one
  const effectiveActiveIndex = activeTierIndex === -1 ? tiers.length - 1 : activeTierIndex;

  return (
    <div className="bg-olive-900/30 rounded-xl border border-olive-700/30 p-4 max-h-[200px] overflow-y-auto">
      <h3 className="text-xs font-medium text-olive-400 uppercase tracking-wider mb-3">
        Your Journey
      </h3>

      <div className="relative">
        {/* Vertical line */}
        <div className="absolute left-[11px] top-2 bottom-2 w-0.5 bg-olive-700/50" />

        <div className="space-y-1">
          {tiers.map((tier, index) => {
            const state = getTierState(tier, completedTasks, index, effectiveActiveIndex);
            const progress = getTierProgress(tier, completedTasks);

            return (
              <button
                key={tier.id}
                onClick={() => onTierClick?.(tier.id)}
                className={cn(
                  'w-full text-left flex items-start gap-3 py-1.5 px-1 rounded-lg transition-colors',
                  'hover:bg-olive-800/30',
                  state === 'active' && 'bg-olive-800/20'
                )}
              >
                {/* Status icon */}
                <div className="relative z-10 flex-shrink-0">
                  {state === 'complete' ? (
                    <div className="w-6 h-6 rounded-full bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center">
                      <Check className="w-3.5 h-3.5 text-emerald-400" />
                    </div>
                  ) : state === 'active' ? (
                    <div className="w-6 h-6 rounded-full bg-olive-500/30 border-2 border-olive-400 flex items-center justify-center">
                      <div className="w-2 h-2 rounded-full bg-olive-400" />
                    </div>
                  ) : state === 'next' ? (
                    <div className="w-6 h-6 rounded-full border border-olive-600 flex items-center justify-center">
                      <Circle className="w-3 h-3 text-olive-500" />
                    </div>
                  ) : (
                    <div className="w-6 h-6 rounded-full flex items-center justify-center">
                      <Dot className="w-4 h-4 text-olive-600" />
                    </div>
                  )}
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <div
                    className={cn(
                      'text-sm font-medium truncate',
                      state === 'complete' && 'text-olive-400',
                      state === 'active' && 'text-olive-100',
                      state === 'next' && 'text-olive-300',
                      state === 'future' && 'text-olive-500'
                    )}
                  >
                    {tier.title}
                  </div>

                  {/* Show subtitle and progress for active and next tiers */}
                  {(state === 'active' || state === 'next') && (
                    <div className="mt-0.5">
                      <div className="text-xs text-olive-400 truncate">
                        {tier.subtitle}
                      </div>
                      {state === 'active' && progress.total > 0 && (
                        <div className="flex items-center gap-2 mt-1">
                          <div className="flex-1 h-1 bg-olive-700/50 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-olive-400 rounded-full transition-all duration-300"
                              style={{ width: `${progress.percentage}%` }}
                            />
                          </div>
                          <span className="text-[10px] text-olive-500 flex-shrink-0">
                            {progress.completed}/{progress.total}
                          </span>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default PhaseProgressMap;
