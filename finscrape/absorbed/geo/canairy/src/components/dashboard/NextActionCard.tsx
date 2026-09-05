import React from 'react';
import { motion } from 'framer-motion';
import { ArrowRight, Clock } from 'lucide-react';
import { useStore } from '../../store';
import { generateDetailedActions } from '../../utils/actions';
import { GlassCard } from '../ui/GlassCard';
import { cn } from '../../utils/cn';

export const NextActionCard: React.FC = () => {
  const { indicators, currentPhase } = useStore();
  const actions = generateDetailedActions(indicators, currentPhase);
  const nextAction = actions[0];

  if (!nextAction) {
    return (
      <GlassCard glow="green" className="relative overflow-hidden">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-green-500/10 border border-green-500/20 flex items-center justify-center flex-shrink-0">
            <span className="text-lg">&#10003;</span>
          </div>
          <div>
            <h3 className="text-white font-display font-semibold">You're in good shape</h3>
            <p className="text-sm text-white/40 mt-0.5">
              No urgent actions right now. Keep an eye on things and stay ready.
            </p>
          </div>
        </div>
      </GlassCard>
    );
  }

  const urgencyConfig = {
    immediate: { label: 'DO NOW', color: 'text-red-400', bg: 'bg-red-500/15', border: 'border-red-500/20', glow: 'red' as const },
    today: { label: 'TODAY', color: 'text-amber-400', bg: 'bg-amber-500/15', border: 'border-amber-500/20', glow: 'amber' as const },
    'this-week': { label: 'THIS WEEK', color: 'text-white/50', bg: 'bg-white/[0.08]', border: 'border-white/10', glow: 'none' as const },
  };

  const config = urgencyConfig[nextAction.urgency];
  const Icon = nextAction.icon;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.1 }}
    >
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-xs font-medium text-white/30 uppercase tracking-wider">Your Next Step</h2>
        <span className={cn('text-xs font-medium px-2 py-0.5 rounded-lg', config.bg, config.color, config.border, 'border')}>
          {config.label}
        </span>
      </div>

      <GlassCard glow={config.glow} className="relative overflow-hidden">
        <div className="flex items-start gap-4">
          <div className={cn(
            'w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0 border',
            config.bg, config.border
          )}>
            <Icon className={cn('w-5 h-5', config.color)} />
          </div>

          <div className="flex-1 min-w-0">
            <h3 className="text-white font-display font-semibold text-base sm:text-lg">
              {nextAction.title}
            </h3>
            <p className="text-sm text-white/40 mt-1 line-clamp-2">
              {nextAction.why}
            </p>

            <div className="flex flex-wrap items-center gap-3 mt-3">
              <span className="text-xs text-white/30 flex items-center gap-1">
                <Clock className="w-3 h-3" />
                {nextAction.timeRequired}
              </span>
              <span className="text-xs text-white/20">&middot;</span>
              <span className="text-xs text-white/30">{nextAction.impact}</span>
            </div>

            {/* First 2 steps preview */}
            <div className="mt-3 space-y-1">
              {nextAction.steps.slice(0, 2).map((step, i) => (
                <div key={i} className="flex items-start gap-2 text-xs text-white/30">
                  <span className="text-white/15 mt-px">{i + 1}.</span>
                  <span>{step}</span>
                </div>
              ))}
              {nextAction.steps.length > 2 && (
                <span className="text-xs text-white/20">+{nextAction.steps.length - 2} more steps</span>
              )}
            </div>
          </div>

          <button className={cn(
            'flex-shrink-0 w-10 h-10 rounded-xl flex items-center justify-center transition-colors',
            'bg-white/5 hover:bg-white/10 border border-white/[0.08]'
          )}>
            <ArrowRight className="w-4 h-4 text-white/60" />
          </button>
        </div>
      </GlassCard>
    </motion.div>
  );
};
