import React, { useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { AlertTriangle, ChevronDown, ChevronUp, Check, Clock, Shield, ChevronRight } from 'lucide-react';
import { cn } from '../../utils/cn';
import { useStore, selectTightenUpActive } from '../../store';
import { generateActionList } from '../../data/actionGenerator';
import { getOutcomePhrase } from '../../data/indicatorTranslations';

// Storage for completed items
const STORAGE_KEY = 'canairy_threat_banner_completed';

function loadCompletedIds(): Set<string> {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    return stored ? new Set(JSON.parse(stored)) : new Set();
  } catch {
    return new Set();
  }
}

function saveCompletedIds(ids: Set<string>) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify([...ids]));
}

export const ThreatBanner: React.FC = () => {
  const actionProtocolActive = useStore(selectTightenUpActive);
  const { indicators, systemPhase } = useStore();
  const [expanded, setExpanded] = useState(false);
  const [completed, setCompleted] = useState<Set<string>>(() => loadCompletedIds());

  const redCount = indicators.filter(i => i.status.level === 'red').length;
  const amberCount = indicators.filter(i => i.status.level === 'amber').length;
  const hasElevated = redCount > 0 || amberCount >= 3;

  if (!hasElevated) return null;

  const redIndicators = indicators.filter(i => i.status.level === 'red');

  // Generate outcome sentence
  const outcomeSentence = useMemo(() => {
    if (redCount >= 2) {
      const phrases = redIndicators.slice(0, 2).map(i => getOutcomePhrase(i.id, 'red'));
      return `Multiple signals suggest ${phrases.join(' and ')}. Check your action plan now.`;
    }
    if (redCount === 1) {
      const phrase = getOutcomePhrase(redIndicators[0].id, 'red');
      return `Conditions indicate ${phrase}. Review priority actions below.`;
    }
    return 'Several indicators are elevated. Review your action plan.';
  }, [redIndicators, redCount]);

  // Get action items from the action plan generator
  const actionItems = useMemo(() => {
    const phase = typeof systemPhase === 'number' ? systemPhase : undefined;
    const tierCompleted = new Set<string>(); // Fresh set for preview
    const actions = generateActionList(indicators, tierCompleted, phase);
    // Take top 5 uncompleted items
    return actions.filter(a => !completed.has(a.id)).slice(0, 5);
  }, [indicators, systemPhase, completed]);

  const completedCount = completed.size;
  const totalVisible = actionItems.length + completedCount;
  const progress = totalVisible > 0 ? Math.round((completedCount / totalVisible) * 100) : 0;

  const toggleItem = (id: string) => {
    setCompleted(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      saveCompletedIds(next);
      return next;
    });
  };

  // Determine severity level
  const isHighPhase = redCount >= 2;

  return (
    <motion.div
      role="alert"
      aria-live="assertive"
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
    >
      <div className={cn(
        'rounded-2xl overflow-hidden',
        isHighPhase ? 'threat-banner' : 'threat-banner-amber'
      )}>
        {/* Header */}
        <button
          onClick={() => setExpanded(!expanded)}
          aria-expanded={expanded}
          aria-label={`${isHighPhase ? 'Time to Take Action' : 'Stay Alert'}: ${redCount > 0 ? `${redCount} conditions need attention` : `${amberCount} conditions worth watching`}. ${expanded ? 'Click to collapse' : 'Click to expand for actions'}`}
          className="w-full px-4 sm:px-6 py-4 flex items-center justify-between text-left"
        >
          <div className="flex items-center gap-3 flex-1 min-w-0">
            <div className={cn(
              'w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0',
              isHighPhase
                ? 'bg-red-500/20 border border-red-500/30'
                : 'bg-amber-500/15 border border-amber-500/25'
            )}>
              {isHighPhase ? (
                <motion.div
                  animate={{ scale: [1, 1.15, 1] }}
                  transition={{ duration: 2, repeat: Infinity }}
                >
                  <AlertTriangle className="w-5 h-5 text-red-400" />
                </motion.div>
              ) : (
                <Shield className="w-5 h-5 text-amber-400" />
              )}
            </div>

            <div className="min-w-0">
              <h2 className={cn(
                'text-sm sm:text-base font-display font-bold tracking-wide',
                isHighPhase ? 'text-red-300' : 'text-amber-300'
              )}>
                {isHighPhase ? 'Time to Take Action' : 'Stay Alert'}
              </h2>
              <p className={cn(
                'text-xs sm:text-sm',
                isHighPhase ? 'text-red-300/60' : 'text-amber-300/60'
              )}>
                {redCount > 0
                  ? `${redCount} condition${redCount !== 1 ? 's' : ''} need${redCount === 1 ? 's' : ''} your attention — see actions below`
                  : `${amberCount} conditions worth watching — good time to review your plans`
                }
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3 flex-shrink-0 ml-4">
            {actionItems.length > 0 && (
              <div className="hidden sm:flex items-center gap-2">
                <span className={cn(
                  'text-xs font-mono',
                  isHighPhase ? 'text-red-300/70' : 'text-amber-300/70'
                )}>
                  {actionItems.length} actions
                </span>
              </div>
            )}
            {expanded ? (
              <ChevronUp className={cn('w-4 h-4', isHighPhase ? 'text-red-400/60' : 'text-amber-400/60')} />
            ) : (
              <ChevronDown className={cn('w-4 h-4', isHighPhase ? 'text-red-400/60' : 'text-amber-400/60')} />
            )}
          </div>
        </button>

        {/* Outcome sentence - always visible */}
        <div className={cn(
          'px-4 sm:px-6 pb-4 -mt-1',
          isHighPhase ? 'text-red-200/80' : 'text-amber-200/80'
        )}>
          <p className="text-sm leading-relaxed">
            {outcomeSentence}
          </p>
        </div>

        {/* Expandable action items */}
        <AnimatePresence>
          {expanded && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.3 }}
              className="overflow-hidden"
            >
              <div className={cn(
                'px-4 sm:px-6 pb-5 border-t',
                isHighPhase ? 'border-red-500/10' : 'border-amber-500/10'
              )}>
                <div className={cn(
                  'flex items-center gap-2 py-3 text-xs',
                  isHighPhase ? 'text-red-300/50' : 'text-amber-300/50'
                )}>
                  <Clock className="w-3.5 h-3.5" />
                  <span>Priority actions for current conditions</span>
                </div>

                {/* Action items from action plan */}
                <div className="space-y-1">
                  {actionItems.map((item, idx) => {
                    const done = completed.has(item.id);
                    return (
                      <button
                        key={item.id}
                        onClick={(e) => {
                          e.stopPropagation();
                          toggleItem(item.id);
                        }}
                        className={cn(
                          'w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-left transition-colors',
                          done
                            ? 'bg-green-500/[0.08] text-green-400'
                            : 'hover:bg-white/[0.03] text-white/80'
                        )}
                      >
                        <div className={cn(
                          'w-5 h-5 rounded-full border-2 flex items-center justify-center flex-shrink-0 transition-colors',
                          done
                            ? 'bg-green-500 border-green-500'
                            : item.urgency === 'now'
                            ? 'border-red-400'
                            : item.urgency === 'today'
                            ? 'border-amber-400'
                            : 'border-olive-500'
                        )}>
                          {done ? (
                            <Check className="w-3 h-3 text-white" />
                          ) : (
                            <span className="text-[10px] font-mono text-white/40">{idx + 1}</span>
                          )}
                        </div>
                        <div className="flex-1 min-w-0">
                          <span className={cn('text-sm', done && 'line-through opacity-50')}>
                            {item.task}
                          </span>
                          {item.why && !done && (
                            <p className="text-xs text-white/30 mt-0.5 truncate">{item.why}</p>
                          )}
                        </div>
                        {!done && (
                          <span className="text-[10px] text-white/20 flex items-center gap-1">
                            <Clock className="w-3 h-3" />
                            {item.timeEstimate}
                          </span>
                        )}
                      </button>
                    );
                  })}
                </div>

                {/* Link to full action plan */}
                <Link
                  to="/action-plan"
                  className={cn(
                    'flex items-center justify-center gap-1.5 mt-4 py-2.5 rounded-lg text-sm font-medium transition-colors',
                    isHighPhase
                      ? 'bg-red-500/10 text-red-300 hover:bg-red-500/15'
                      : 'bg-amber-500/10 text-amber-300 hover:bg-amber-500/15'
                  )}
                >
                  Open full action plan
                  <ChevronRight className="w-4 h-4" />
                </Link>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </motion.div>
  );
};
