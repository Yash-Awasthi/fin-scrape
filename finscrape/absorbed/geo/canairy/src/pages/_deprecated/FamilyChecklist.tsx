import React, { useState, useMemo } from 'react';
import {
  ChevronDown,
  Check,
  Shield,
  Printer,
  Eye,
  EyeOff,
} from 'lucide-react';
import { Link } from 'react-router-dom';
import { useStore } from '../store';
import { PHASES } from '../data/phaseData';
import { ScoreRing } from '../components/ui/ScoreRing';
import { GlassCard } from '../components/ui/GlassCard';
import { cn } from '../utils/cn';

export const FamilyChecklist: React.FC = () => {
  const { currentPhase } = useStore();
  const phaseNumber = currentPhase?.number ?? 0;
  const [showAllPhases, setShowAllPhases] = useState(false);

  const relevantPhases = useMemo(() => {
    if (showAllPhases) return PHASES;
    return PHASES.filter(p => p.number <= phaseNumber + 1);
  }, [phaseNumber, showAllPhases]);

  const [completedItems, setCompletedItems] = useState<Set<string>>(() => {
    try {
      const stored = localStorage.getItem('canairy_checklist');
      return stored ? new Set(JSON.parse(stored)) : new Set();
    } catch {
      return new Set();
    }
  });

  const [expandedPhase, setExpandedPhase] = useState<number | null>(phaseNumber);

  const toggleItem = (id: string) => {
    setCompletedItems(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      localStorage.setItem('canairy_checklist', JSON.stringify([...next]));
      return next;
    });
  };

  const totalActions = relevantPhases.reduce((sum, p) => sum + p.actions.length, 0);
  const completedCount = relevantPhases.reduce((sum, p) => {
    return sum + p.actions.filter((_, i) => completedItems.has(`${p.number}-${i}`)).length;
  }, 0);
  const overallProgress = totalActions > 0 ? Math.round((completedCount / totalActions) * 100) : 0;

  return (
    <>
      {/* Header */}
      <div className="border-b border-white/[0.04]">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8">
          <div className="flex items-center gap-3 mb-1 text-sm">
            <Link to="/dashboard" className="text-white/20 hover:text-white/40 transition-colors">Dashboard</Link>
            <ChevronDown className="w-3 h-3 text-white/10 rotate-[-90deg]" />
            <span className="text-white/50">Family Actions</span>
          </div>

          <div className="flex items-center justify-between mt-4 gap-4">
            <div className="flex items-center gap-5">
              {/* Score Ring for completion */}
              <ScoreRing
                value={overallProgress}
                max={100}
                size="sm"
                color={overallProgress === 100 ? '#10B981' : overallProgress > 50 ? '#F59E0B' : '#64748B'}
                label="%"
              />
              <div>
                <h1 className="text-2xl font-display font-bold text-white">Family Actions</h1>
                <p className="text-white/30 text-sm">Practical steps to keep your family ready</p>
              </div>
            </div>
            <div className="hidden sm:flex items-center gap-2">
              <button
                onClick={() => setShowAllPhases(!showAllPhases)}
                className={cn(
                  "btn text-sm",
                  showAllPhases ? "btn-primary" : "btn-secondary"
                )}
              >
                {showAllPhases ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                {showAllPhases ? 'Show Relevant' : 'Show All Phases'}
              </button>
              <button
                onClick={() => window.print()}
                className="btn btn-secondary text-sm"
              >
                <Printer className="w-4 h-4" />
                Print
              </button>
            </div>
          </div>

          {/* Progress microcopy */}
          <div className="mt-4">
            {overallProgress === 100 && (
              <p className="text-green-400 text-sm font-medium">Fully prepared for this phase. Amazing work!</p>
            )}
            {overallProgress > 0 && overallProgress < 100 && (
              <p className="text-xs text-white/20">{completedCount}/{totalActions} complete — every step makes your family more resilient</p>
            )}
            {overallProgress === 0 && (
              <p className="text-xs text-white/20">Tap any item to get started. Even one step makes a difference.</p>
            )}
          </div>
        </div>
      </div>

      {/* Checklist */}
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-3">
        {relevantPhases.map((phase) => {
          const isExpanded = expandedPhase === phase.number;
          const isCurrent = phase.number === phaseNumber;
          const phaseCompleted = phase.actions.filter((_, i) => completedItems.has(`${phase.number}-${i}`)).length;
          const phaseTotal = phase.actions.length;
          const phasePct = phaseTotal > 0 ? Math.round((phaseCompleted / phaseTotal) * 100) : 0;

          return (
            <GlassCard
              key={phase.number}
              padding="none"
              glow={isCurrent && phasePct < 100 ? 'amber' : phasePct === 100 ? 'green' : 'none'}
            >
              <button
                onClick={() => setExpandedPhase(isExpanded ? null : phase.number)}
                className="w-full px-5 py-4 flex items-center gap-4 text-left"
              >
                <div
                  className="w-10 h-10 rounded-xl flex items-center justify-center border flex-shrink-0"
                  style={{
                    backgroundColor: `${phase.color}10`,
                    borderColor: `${phase.color}30`,
                  }}
                >
                  {phasePct === 100 ? (
                    <Check className="w-5 h-5 text-green-400" />
                  ) : (
                    <span className="text-sm font-bold" style={{ color: phase.color }}>{phase.number}</span>
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <h3 className={cn('font-semibold', isCurrent ? 'text-white' : 'text-white/40')}>
                      {phase.name}
                    </h3>
                    {isCurrent && (
                      <span className="px-2 py-0.5 text-xs rounded-lg bg-white/[0.08] text-white/50 font-medium">CURRENT</span>
                    )}
                  </div>
                  <p className="text-sm text-white/20 truncate">{phase.description}</p>
                </div>
                <div className="flex items-center gap-3 flex-shrink-0">
                  <span className="text-xs text-white/20">{phaseCompleted}/{phaseTotal}</span>
                  <ChevronDown className={cn('w-5 h-5 text-white/15 transition-transform', isExpanded && 'rotate-180')} />
                </div>
              </button>

              {isExpanded && (
                <div className="px-5 pb-5 border-t border-white/[0.04] pt-4 space-y-1">
                  {phase.actions.map((action, i) => {
                    const itemId = `${phase.number}-${i}`;
                    const done = completedItems.has(itemId);
                    return (
                      <button
                        key={itemId}
                        onClick={() => toggleItem(itemId)}
                        className={cn(
                          'w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-left transition-colors',
                          done ? 'bg-green-500/8 text-green-400' : 'hover:bg-white/[0.03] text-white/50'
                        )}
                      >
                        <div
                          className={cn(
                            'w-5 h-5 rounded border-2 flex items-center justify-center flex-shrink-0 transition-colors',
                            done ? 'bg-green-500 border-green-500' : 'border-white/15'
                          )}
                        >
                          {done && <Check className="w-3 h-3 text-white" />}
                        </div>
                        <span className={cn('text-sm', done && 'line-through opacity-50')}>{action}</span>
                      </button>
                    );
                  })}
                </div>
              )}
            </GlassCard>
          );
        })}

        <div className="text-center py-8">
          <Link
            to="/playbook"
            className="inline-flex items-center gap-2 text-white/30 hover:text-white/50 transition-colors text-sm font-medium"
          >
            <Shield className="w-4 h-4" />
            View Full Resilience Playbook (Phases 0-9)
          </Link>
        </div>
      </div>
    </>
  );
};
