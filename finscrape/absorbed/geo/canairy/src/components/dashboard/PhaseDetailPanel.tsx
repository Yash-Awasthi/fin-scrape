import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Shield,
  ChevronRight,
  ChevronDown,
  ChevronUp,
  CheckCircle2,
  Zap,
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '../core/Card';
import { Badge } from '../core/Badge';
import { cn } from '../../utils/cn';
import { useStore } from '../../store';
import { PHASES, getPhaseByNumber, CRITICAL_JUMP_RULES } from '../../data/phaseData';

const STORAGE_KEY = 'canairy_phase_actions';

export const PhaseDetailPanel: React.FC = () => {
  const { hopiScore, indicators } = useStore();
  const [showAllPhases, setShowAllPhases] = useState(false);
  const [completedActions, setCompletedActions] = useState<Set<string>>(() => {
    // Load from localStorage on initial render
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        const parsed = JSON.parse(saved);
        return new Set(parsed.items || []);
      }
    } catch {
      // Ignore parse errors
    }
    return new Set();
  });

  // Save to localStorage whenever completedActions changes
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify({
        items: Array.from(completedActions),
        lastUpdated: new Date().toISOString()
      }));
    } catch {
      // Ignore storage errors
    }
  }, [completedActions]);

  const currentPhaseNum = hopiScore?.phase ?? 0;
  const currentPhase = getPhaseByNumber(currentPhaseNum);
  const nextPhase = PHASES.find((p) => p.number > currentPhaseNum);

  // Check if any critical jump rules are active
  const activeJumps = CRITICAL_JUMP_RULES.filter((rule) => {
    return rule.indicatorIds.every((id) => {
      const ind = indicators.find((i) => i.id === id);
      return ind && ind.status.level === 'red';
    });
  });

  const toggleAction = (key: string) => {
    setCompletedActions((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  };

  if (!currentPhase) return null;

  const completedCount = currentPhase.actions.filter((_, i) =>
    completedActions.has(`${currentPhaseNum}-${i}`)
  ).length;
  const progress = Math.round(
    (completedCount / currentPhase.actions.length) * 100
  );

  return (
    <Card className="mb-8">
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Shield className="w-5 h-5" style={{ color: currentPhase.color }} />
            <span>Phase {currentPhaseNum}: {currentPhase.name}</span>
            <Badge
              variant={currentPhaseNum >= 7 ? 'red' : currentPhaseNum >= 3 ? 'amber' : 'default'}
              size="sm"
            >
              ACTIVE
            </Badge>
          </div>
          <div className="flex items-center gap-3">
            <div className="text-sm text-white/30">
              {completedCount}/{currentPhase.actions.length} done
            </div>
            <div className="w-16 h-2 bg-white/5 rounded-full overflow-hidden">
              <div
                className="h-full rounded-full transition-all"
                style={{
                  width: `${progress}%`,
                  backgroundColor: currentPhase.color,
                }}
              />
            </div>
          </div>
        </CardTitle>
      </CardHeader>

      <CardContent>
        {/* Current phase description */}
        <p className="text-sm text-white/30 mb-4">{currentPhase.description}</p>

        {/* Trigger conditions */}
        <div className="mb-4 p-3 bg-white/[0.03] rounded-lg">
          <div className="text-xs font-medium text-white/20 mb-1">TRIGGER</div>
          <div className="text-sm text-white/50">
            {currentPhase.triggers.join(' | ')}
          </div>
        </div>

        {/* Critical jump warnings */}
        {activeJumps.length > 0 && (
          <div className="mb-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg">
            <div className="flex items-center gap-2 mb-2">
              <Zap className="w-4 h-4 text-red-400" />
              <span className="text-sm font-medium text-red-400">
                Critical Jump Rule Active
              </span>
            </div>
            {activeJumps.map((jump) => (
              <div key={jump.id} className="text-sm text-red-300/80">
                {jump.condition} — minimum Phase {jump.minPhase} ({jump.timeLimit})
              </div>
            ))}
          </div>
        )}

        {/* Action checklist */}
        <div className="mb-4">
          <h4 className="text-sm font-medium text-white/50 mb-3">
            Phase {currentPhaseNum} Actions:
          </h4>
          <div className="space-y-1">
            {currentPhase.actions.map((action, i) => {
              const key = `${currentPhaseNum}-${i}`;
              const done = completedActions.has(key);
              return (
                <button
                  key={i}
                  onClick={() => toggleAction(key)}
                  className={cn(
                    'w-full flex items-center gap-3 px-3 py-2 rounded-lg text-left transition-colors',
                    done
                      ? 'bg-green-500/10'
                      : 'hover:bg-white/5'
                  )}
                >
                  <div
                    className={cn(
                      'w-5 h-5 rounded border-2 flex items-center justify-center flex-shrink-0',
                      done
                        ? 'bg-green-500 border-green-500'
                        : 'border-white/15'
                    )}
                  >
                    {done && <CheckCircle2 className="w-3 h-3 text-white" />}
                  </div>
                  <span
                    className={cn(
                      'text-sm text-white/50',
                      done && 'line-through opacity-60'
                    )}
                  >
                    {action}
                  </span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Next phase preview */}
        {nextPhase && (
          <div className="p-3 border border-white/[0.04] rounded-lg">
            <div className="flex items-center gap-2 mb-1">
              <ChevronRight className="w-4 h-4 text-white/20" />
              <span className="text-xs font-medium text-white/20">
                NEXT: Phase {nextPhase.number} — {nextPhase.name}
              </span>
            </div>
            <div className="text-xs text-white/20">
              Triggers: {nextPhase.triggers.join(' | ')}
            </div>
          </div>
        )}

        {/* Show all phases toggle */}
        <button
          onClick={() => setShowAllPhases(!showAllPhases)}
          className="mt-4 flex items-center gap-2 text-sm text-white/20 hover:text-white/50 transition-colors"
        >
          {showAllPhases ? (
            <ChevronUp className="w-4 h-4" />
          ) : (
            <ChevronDown className="w-4 h-4" />
          )}
          {showAllPhases ? 'Hide' : 'Show'} all phases
        </button>

        <AnimatePresence>
          {showAllPhases && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="overflow-hidden"
            >
              <div className="mt-4 space-y-2">
                {PHASES.map((phase) => {
                  const isCurrent = phase.number === currentPhaseNum;
                  const isPast = phase.number < currentPhaseNum;
                  return (
                    <div
                      key={phase.number}
                      className={cn(
                        'flex items-center gap-3 px-3 py-2 rounded-lg text-sm',
                        isCurrent && 'bg-white/5 border border-white/[0.08]',
                        isPast && 'opacity-50'
                      )}
                    >
                      <div
                        className="w-3 h-3 rounded-full flex-shrink-0"
                        style={{ backgroundColor: phase.color }}
                      />
                      <span
                        className={cn(
                          'font-medium',
                          isCurrent ? 'text-white' : 'text-white/30'
                        )}
                      >
                        Phase {phase.number}
                      </span>
                      <span className="text-white/20">{phase.name}</span>
                      {isCurrent && (
                        <Badge variant="default" size="sm">
                          CURRENT
                        </Badge>
                      )}
                      {isPast && (
                        <CheckCircle2 className="w-4 h-4 text-green-500 ml-auto" />
                      )}
                    </div>
                  );
                })}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </CardContent>
    </Card>
  );
};
