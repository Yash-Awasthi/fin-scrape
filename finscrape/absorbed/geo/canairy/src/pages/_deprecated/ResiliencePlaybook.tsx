import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Shield,
  ChevronDown,
  ChevronUp,
  Check,
  AlertTriangle,
  ArrowRight,
  Clock,
  Zap,
  CheckCircle2,
  Circle,
  Printer,
} from 'lucide-react';
import { Link } from 'react-router-dom';
import { useStore } from '../store';
import { PHASES, ACTION_PROTOCOL_CHECKLIST, CRITICAL_JUMP_RULES } from '../data/phaseData';
import { cn } from '../utils/cn';

export const ResiliencePlaybook: React.FC = () => {
  const { currentPhase, indicators } = useStore();
  const [expandedPhase, setExpandedPhase] = useState<number | null>(
    currentPhase?.number ?? null
  );
  const [completedChecklist, setCompletedChecklist] = useState<Set<string>>(new Set());

  const phaseNumber = currentPhase?.number ?? 0;
  const redCount = indicators?.filter((i) => i.status.level === 'red').length || 0;
  const tightenUpActive = redCount >= 2;

  const toggleChecklist = (id: string) => {
    setCompletedChecklist((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const categories = [...new Set(ACTION_PROTOCOL_CHECKLIST.map((c: { category: string }) => c.category))];

  return (
    <>
      {/* Header */}
      <div className="border-b border-white/[0.04]">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8">
          <div className="flex items-center gap-3 mb-1">
            <Link
              to="/dashboard"
              className="text-white/20 hover:text-white/50 text-sm transition-colors"
            >
              Dashboard
            </Link>
            <ChevronDown className="w-3 h-3 text-white/15 rotate-[-90deg]" />
            <span className="text-white/50 text-sm">Playbook</span>
          </div>
          <div className="flex items-center justify-between gap-4 mt-4">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-white/5 border border-white/10 flex items-center justify-center">
                <Shield className="w-6 h-6 text-white/40" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-white">Your Family's Plan</h1>
                <p className="text-white/30">
                  Step-by-step guide for every level of preparedness — from basics to full resilience
                </p>
              </div>
            </div>
            <button
              onClick={() => window.print()}
              className="hidden sm:flex btn btn-secondary text-sm"
            >
              <Printer className="w-4 h-4" />
              Print
            </button>
          </div>

          {/* Current phase badge */}
          <div className="mt-6 flex items-center gap-4">
            <div
              className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium"
              style={{
                backgroundColor: `${PHASES.find((p) => p.number === phaseNumber)?.color ?? '#6B7280'}15`,
                borderColor: `${PHASES.find((p) => p.number === phaseNumber)?.color ?? '#6B7280'}30`,
                borderWidth: 1,
                color: PHASES.find((p) => p.number === phaseNumber)?.color ?? '#6B7280',
              }}
            >
              <Circle className="w-3 h-3 fill-current" />
              Current: Phase {phaseNumber} —{' '}
              {PHASES.find((p) => p.number === phaseNumber)?.name ?? 'Unknown'}
            </div>
            {tightenUpActive && (
              <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm font-medium">
                <AlertTriangle className="w-3.5 h-3.5" />
                TIGHTEN-UP ACTIVE
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* ── TIGHTEN-UP 48-Hour Checklist ── */}
        {tightenUpActive && (
          <section>
            <div className="flex items-center gap-3 mb-4">
              <div className="w-8 h-8 rounded-lg bg-red-500/10 flex items-center justify-center">
                <Zap className="w-4 h-4 text-red-400" />
              </div>
              <h2 className="text-lg font-bold text-white">48-Hour Tighten-Up Checklist</h2>
              <span className="text-sm text-white/20 ml-auto">
                {completedChecklist.size}/{ACTION_PROTOCOL_CHECKLIST.length} complete
              </span>
            </div>

            <div className="glass-card border border-red-500/20 overflow-hidden">
              {/* Progress bar */}
              <div className="h-1 bg-red-900/30">
                <motion.div
                  className="h-full bg-red-500"
                  initial={{ width: 0 }}
                  animate={{
                    width: `${Math.round((completedChecklist.size / ACTION_PROTOCOL_CHECKLIST.length) * 100)}%`,
                  }}
                />
              </div>

              <div className="p-4 sm:p-6 space-y-5">
                <div className="flex items-center gap-2 text-sm text-red-300/70">
                  <Clock className="w-4 h-4" />
                  <span>Complete within 48 hours of protocol activation</span>
                </div>

                {categories.map((cat) => (
                  <div key={cat}>
                    <h4 className="text-xs font-medium text-white/20 uppercase tracking-wider mb-2">
                      {cat}
                    </h4>
                    <div className="space-y-1">
                      {ACTION_PROTOCOL_CHECKLIST.filter((c: { category: string }) => c.category === cat).map((item: { id: string; text: string }) => {
                        const done = completedChecklist.has(item.id);
                        return (
                          <button
                            key={item.id}
                            onClick={() => toggleChecklist(item.id)}
                            className={cn(
                              'w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-left transition-colors',
                              done
                                ? 'bg-green-500/10 text-green-400'
                                : 'hover:bg-white/5 text-white/50'
                            )}
                          >
                            <div
                              className={cn(
                                'w-5 h-5 rounded border-2 flex items-center justify-center flex-shrink-0 transition-colors',
                                done ? 'bg-green-500 border-green-500' : 'border-gray-600'
                              )}
                            >
                              {done && <Check className="w-3 h-3 text-white" />}
                            </div>
                            <span className={cn('text-sm', done && 'line-through opacity-60')}>
                              {item.text}
                            </span>
                          </button>
                        );
                      })}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </section>
        )}

        {/* ── Phase Ladder ── */}
        <section>
          <div className="flex items-center gap-3 mb-4">
            <div className="w-8 h-8 rounded-lg bg-white/5 flex items-center justify-center">
              <Shield className="w-4 h-4 text-white/30" />
            </div>
            <h2 className="text-lg font-bold text-white">Phase Ladder</h2>
            <span className="text-sm text-white/20">0 → 9</span>
          </div>

          <div className="space-y-3">
            {PHASES.map((phase, idx) => {
              const isCurrent = phase.number === phaseNumber;
              const isCompleted = phase.number < phaseNumber;
              const isExpanded = expandedPhase === phase.number;

              return (
                <motion.div
                  key={phase.number}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: idx * 0.03 }}
                >
                  <div
                    className={cn(
                      'rounded-2xl border overflow-hidden transition-colors',
                      isCurrent
                        ? 'border-white/10 bg-white/[0.04]'
                        : 'border-white/[0.06] glass-card'
                    )}
                  >
                    {/* Phase header */}
                    <button
                      onClick={() => setExpandedPhase(isExpanded ? null : phase.number)}
                      className="w-full px-4 sm:px-6 py-4 flex items-center gap-4 text-left"
                    >
                      {/* Phase status icon */}
                      <div
                        className={cn(
                          'w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 border',
                          isCompleted
                            ? 'bg-green-500/10 border-green-500/20'
                            : isCurrent
                              ? 'bg-white/[0.06] border-white/10'
                              : 'bg-white/[0.03] border-white/[0.04]'
                        )}
                      >
                        {isCompleted ? (
                          <CheckCircle2 className="w-5 h-5 text-green-400" />
                        ) : (
                          <span
                            className={cn(
                              'text-sm font-bold',
                              isCurrent ? 'text-white/40' : 'text-white/20'
                            )}
                          >
                            {phase.number}
                          </span>
                        )}
                      </div>

                      {/* Phase info */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <h3
                            className={cn(
                              'font-semibold',
                              isCurrent ? 'text-white' : isCompleted ? 'text-white/50' : 'text-white/30'
                            )}
                          >
                            {phase.name}
                          </h3>
                          {isCurrent && (
                            <span className="px-2 py-0.5 text-xs rounded-full bg-white/[0.08] text-white/50 font-medium">
                              CURRENT
                            </span>
                          )}
                        </div>
                        <p className="text-sm text-white/20 truncate">{phase.description}</p>
                      </div>

                      {/* Color dot + chevron */}
                      <div className="flex items-center gap-3 flex-shrink-0">
                        <div
                          className="w-3 h-3 rounded-full"
                          style={{ backgroundColor: phase.color }}
                        />
                        {isExpanded ? (
                          <ChevronUp className="w-5 h-5 text-white/20" />
                        ) : (
                          <ChevronDown className="w-5 h-5 text-white/20" />
                        )}
                      </div>
                    </button>

                    {/* Expanded details */}
                    <AnimatePresence>
                      {isExpanded && (
                        <motion.div
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: 'auto', opacity: 1 }}
                          exit={{ height: 0, opacity: 0 }}
                          transition={{ duration: 0.2 }}
                          className="overflow-hidden"
                        >
                          <div className="px-4 sm:px-6 pb-5 border-t border-white/[0.04] pt-4">
                            {/* Triggers */}
                            <div className="mb-4">
                              <h4 className="text-xs font-medium text-white/20 uppercase tracking-wider mb-2">
                                Triggers
                              </h4>
                              {phase.triggers.map((trigger, i) => (
                                <div
                                  key={i}
                                  className="flex items-start gap-2 text-sm text-white/30 mb-1"
                                >
                                  <ArrowRight className="w-3.5 h-3.5 mt-0.5 text-white/15 flex-shrink-0" />
                                  <span>{trigger}</span>
                                </div>
                              ))}
                            </div>

                            {/* Actions */}
                            <h4 className="text-xs font-medium text-white/20 uppercase tracking-wider mb-2">
                              Actions
                            </h4>
                            <div className="space-y-1.5">
                              {phase.actions.map((action, i) => (
                                <div
                                  key={i}
                                  className={cn(
                                    'flex items-start gap-3 px-3 py-2 rounded-lg text-sm',
                                    isCompleted
                                      ? 'text-green-400/70 bg-green-500/5'
                                      : 'text-white/50 bg-white/[0.03]'
                                  )}
                                >
                                  {isCompleted ? (
                                    <Check className="w-4 h-4 mt-0.5 flex-shrink-0" />
                                  ) : (
                                    <Circle className="w-4 h-4 mt-0.5 text-white/15 flex-shrink-0" />
                                  )}
                                  <span>{action}</span>
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
            })}
          </div>
        </section>

        {/* ── Critical Jump Rules ── */}
        <section>
          <div className="flex items-center gap-3 mb-4">
            <div className="w-8 h-8 rounded-lg bg-amber-500/10 flex items-center justify-center">
              <AlertTriangle className="w-4 h-4 text-amber-400" />
            </div>
            <h2 className="text-lg font-bold text-white">Critical Jump Rules</h2>
          </div>
          <p className="text-sm text-white/20 mb-4">
            These rules bypass normal phase progression and force immediate escalation.
          </p>

          <div className="grid gap-3 sm:grid-cols-2">
            {CRITICAL_JUMP_RULES.map((rule) => (
              <div
                key={rule.id}
                className="glass-card p-4"
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-mono text-amber-400/70 uppercase">
                    {rule.id}
                  </span>
                  <span className="text-xs text-white/20 flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {rule.timeLimit}
                  </span>
                </div>
                <p className="text-sm text-white/50 mb-3">{rule.condition}</p>
                <div className="flex items-center gap-2">
                  <ArrowRight className="w-3.5 h-3.5 text-red-400" />
                  <span className="text-sm font-medium text-red-400">
                    Jump to Phase {rule.minPhase}+
                  </span>
                </div>
              </div>
            ))}
          </div>
        </section>
      </div>
    </>
  );
};
