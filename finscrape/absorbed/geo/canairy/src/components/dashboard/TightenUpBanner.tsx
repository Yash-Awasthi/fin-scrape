import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { AlertCircle, ChevronDown, ChevronUp, Check, Clock } from 'lucide-react';
import { cn } from '../../utils/cn';
import { useStore, selectTightenUpActive } from '../../store';
import { ACTION_PROTOCOL_CHECKLIST } from '../../data/phaseData';

export const TightenUpBanner: React.FC = () => {
  const actionProtocolActive = useStore(selectTightenUpActive);
  const { indicators } = useStore();
  const [expanded, setExpanded] = useState(false);
  const [completed, setCompleted] = useState<Set<string>>(new Set());

  if (!actionProtocolActive) return null;

  const redIndicators = indicators.filter((i) => i.status.level === 'red');
  const completedCount = completed.size;
  const totalCount = ACTION_PROTOCOL_CHECKLIST.length;
  const progress = Math.round((completedCount / totalCount) * 100);

  const toggleItem = (id: string) => {
    setCompleted((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const categories = [...new Set(ACTION_PROTOCOL_CHECKLIST.map((c) => c.category))];

  return (
    <motion.div
      role="alert"
      aria-live="assertive"
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      className="mb-6"
    >
      <div className="rounded-2xl border-2 border-red-500/50 bg-red-500/10 overflow-hidden">
        {/* Header */}
        <button
          onClick={() => setExpanded(!expanded)}
          className="w-full px-4 sm:px-6 py-4 flex items-center justify-between text-left"
        >
          <div className="flex items-center gap-3 flex-1 min-w-0">
            <motion.div
              animate={{ scale: [1, 1.2, 1] }}
              transition={{ duration: 1.5, repeat: Infinity }}
            >
              <AlertCircle className="w-6 h-6 text-red-400 flex-shrink-0" />
            </motion.div>
            <div className="min-w-0">
              <h2 className="text-lg font-display font-bold text-red-400">
                ACTION PROTOCOL ACTIVE
              </h2>
              <p className="text-sm text-red-300/80 truncate">
                {redIndicators.length} indicators at RED — complete 48-hour checklist
              </p>
            </div>
          </div>

          <div className="flex items-center gap-4 flex-shrink-0 ml-4">
            {/* Progress ring */}
            <div className="flex items-center gap-2">
              <div className="text-sm font-mono text-red-300">
                {completedCount}/{totalCount}
              </div>
              <div className="w-16 h-2 bg-red-900/50 rounded-full overflow-hidden">
                <motion.div
                  className="h-full bg-red-400 rounded-full"
                  initial={{ width: 0 }}
                  animate={{ width: `${progress}%` }}
                />
              </div>
            </div>
            {expanded ? (
              <ChevronUp className="w-5 h-5 text-red-400" />
            ) : (
              <ChevronDown className="w-5 h-5 text-red-400" />
            )}
          </div>
        </button>

        {/* Expandable checklist */}
        <AnimatePresence>
          {expanded && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.3 }}
              className="overflow-hidden"
            >
              <div className="px-4 sm:px-6 pb-6 border-t border-red-500/20">
                {/* Timer */}
                <div className="flex items-center gap-2 py-3 text-sm text-red-300/80">
                  <Clock className="w-4 h-4" />
                  <span>Complete within 48 hours of activation</span>
                </div>

                {/* Red indicators causing activation */}
                <div className="mb-4 p-3 bg-white/[0.03] rounded-lg">
                  <div className="text-xs text-white/30 mb-2">Triggering indicators:</div>
                  <div className="flex flex-wrap gap-2">
                    {redIndicators.map((ind) => (
                      <span
                        key={ind.id}
                        className={cn(
                          'px-2 py-1 text-xs rounded-md',
                          ind.critical
                            ? 'bg-red-500/20 text-red-300 border border-red-500/30'
                            : 'bg-red-500/10 text-red-400'
                        )}
                      >
                        {ind.name}
                        {ind.critical && ' (CRITICAL)'}
                      </span>
                    ))}
                  </div>
                </div>

                {/* Checklist by category */}
                <div className="space-y-4">
                  {categories.map((cat) => (
                    <div key={cat}>
                      <h4 className="text-xs font-medium text-white/30 uppercase tracking-wider mb-2">
                        {cat}
                      </h4>
                      <div className="space-y-1">
                        {ACTION_PROTOCOL_CHECKLIST.filter((c) => c.category === cat).map(
                          (item) => {
                            const done = completed.has(item.id);
                            return (
                              <button
                                key={item.id}
                                onClick={() => toggleItem(item.id)}
                                className={cn(
                                  'w-full flex items-center gap-3 px-3 py-2 rounded-lg text-left transition-colors',
                                  done
                                    ? 'bg-green-500/10 text-green-400'
                                    : 'hover:bg-red-500/5 text-white/50'
                                )}
                              >
                                <div
                                  className={cn(
                                    'w-5 h-5 rounded border-2 flex items-center justify-center flex-shrink-0 transition-colors',
                                    done
                                      ? 'bg-green-500 border-green-500'
                                      : 'border-white/15'
                                  )}
                                >
                                  {done && <Check className="w-3 h-3 text-white" />}
                                </div>
                                <span
                                  className={cn(
                                    'text-sm',
                                    done && 'line-through opacity-60'
                                  )}
                                >
                                  {item.text}
                                </span>
                              </button>
                            );
                          }
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </motion.div>
  );
};
