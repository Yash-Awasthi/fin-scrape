/**
 * Family Action Plan
 *
 * Redesigned page that educates while guiding through preparedness.
 * Works like a good doctor's visit: here's what's going on, here's what
 * it means, here's what to do, here's how it fits the bigger picture.
 *
 * Structure:
 * 1. Header with adaptive subtitle based on threat state
 * 2. Current Conditions Summary (why this phase)
 * 3. Phase Progress Map (where am I in the journey)
 * 4. Condition-Driven Actions (This Week)
 * 5. Phase Sections (the tasks, organized by tier)
 * 6. Educational Footer (How this works)
 */

import React, { useState, useMemo, useCallback, useRef } from 'react';
import { Link } from 'react-router-dom';
import { ChevronRight, ClipboardList, X } from 'lucide-react';
import { useStore, selectLeadAIInsight, selectSecondaryAIInsights } from '../store';
import { getVisibleTiers, getTierProgress, computeReadinessFromTiers, getMPhaseTier } from '../data/phaseTasks';
import { generateActionList } from '../data/actionGenerator';
import { calculateMPhase, getVisibleMPhaseLevels } from '../utils/mphase';
import {
  ConditionsSummary,
  PhaseProgressMap,
  PhaseSection,
  ConditionActions,
  HowItWorks,
  MPhaseSection,
} from '../components/action-plan';

// ============================================================================
// TYPES
// ============================================================================

type ThreatState = 'normal' | 'elevated' | 'critical';

// ============================================================================
// PERSISTENCE HELPERS
// ============================================================================

const STORAGE_KEYS = {
  thisWeek: 'canairy_action_plan_this_week',
  tiers: 'canairy_action_plan_tiers',
  mphase: 'canairy_action_plan_mphase',
  introDismissed: 'canairy_action_plan_intro_dismissed',
};

function loadCompletedIds(key: string): Set<string> {
  try {
    const stored = localStorage.getItem(key);
    return stored ? new Set(JSON.parse(stored)) : new Set();
  } catch {
    return new Set();
  }
}

function saveCompletedIds(key: string, ids: Set<string>) {
  localStorage.setItem(key, JSON.stringify([...ids]));
}

function loadIntroDismissed(): boolean {
  try {
    return localStorage.getItem(STORAGE_KEYS.introDismissed) === 'true';
  } catch {
    return false;
  }
}

function saveIntroDismissed(dismissed: boolean) {
  localStorage.setItem(STORAGE_KEYS.introDismissed, String(dismissed));
}

// ============================================================================
// SUBTITLE LOGIC
// ============================================================================

function getAdaptiveSubtitle(threatState: ThreatState, incompleteActionCount: number): string {
  switch (threatState) {
    case 'critical':
      return 'Conditions are elevated. Focus on the priority items first.';
    case 'elevated':
      return 'A few things need attention. Here\'s your plan for the week.';
    case 'normal':
    default:
      return incompleteActionCount > 0
        ? 'Everything looks calm. Here\'s what to work on to stay ahead.'
        : 'All caught up. Keep building your readiness when you have time.';
  }
}

// ============================================================================
// MAIN COMPONENT
// ============================================================================

export const FamilyActionPlan: React.FC = () => {
  const { indicators, systemPhase } = useStore();
  const leadInsight = useStore(selectLeadAIInsight);
  const secondaryInsights = useStore(selectSecondaryAIInsights);

  // Refs for scrolling to sections
  const sectionRefs = useRef<Record<string, HTMLElement | null>>({});

  // Compute threat state based on red indicator count
  const redCount = indicators.filter(i => i.status.level === 'red').length;
  const threatState: ThreatState = redCount >= 2 ? 'critical' : redCount === 1 ? 'elevated' : 'normal';

  // Intro paragraph visibility
  const [introDismissed, setIntroDismissed] = useState(loadIntroDismissed);

  // Completion state
  const [completedThisWeek, setCompletedThisWeek] = useState<Set<string>>(
    () => loadCompletedIds(STORAGE_KEYS.thisWeek)
  );
  const [completedTiers, setCompletedTiers] = useState<Set<string>>(
    () => loadCompletedIds(STORAGE_KEYS.tiers)
  );
  const [completedMPhase, setCompletedMPhase] = useState<Set<string>>(
    () => loadCompletedIds(STORAGE_KEYS.mphase)
  );

  // Calculate M-phase from indicators
  const mPhaseResult = useMemo(() => {
    return calculateMPhase(indicators);
  }, [indicators]);

  // Get visible M-phase levels (current + all below)
  const visibleMPhaseLevels = useMemo(() => {
    return getVisibleMPhaseLevels(mPhaseResult.level);
  }, [mPhaseResult.level]);

  // Generate "This Week" actions - prioritize AI insights, fall back to static
  const thisWeekActions = useMemo(() => {
    const phase = typeof systemPhase === 'number' ? systemPhase : undefined;
    const actions: ReturnType<typeof generateActionList> = [];

    // Source 1: AI-generated actions from insights (highest priority)
    const allInsights = [leadInsight, ...secondaryInsights].filter(Boolean);
    for (const insight of allInsights) {
      if (!insight) continue;

      for (const actionItem of insight.actionItems || []) {
        const actionId = `ai-${insight.id}-${actionItem.task.slice(0, 20).replace(/\s/g, '-')}`;
        if (completedThisWeek.has(actionId)) continue;

        const urgency: 'now' | 'today' | 'this-week' =
          insight.urgency === 'today' ? 'today' :
          insight.urgency === 'week' ? 'this-week' : 'this-week';

        actions.push({
          id: actionId,
          task: actionItem.task,
          why: actionItem.why,
          timeEstimate: actionItem.timeEstimate,
          urgency,
          priority: actionItem.priority === 'critical' ? 1 : actionItem.priority === 'recommended' ? 2 : 3,
          effort: actionItem.effort,
          completed: false,
          sourceInsightId: insight.id,
          sourceDomains: insight.domains,
          context: {
            dataPoints: insight.dataPoint ? [insight.dataPoint] : [],
            sources: insight.evidenceSources?.map(s => s.source) || [],
            indicators: insight.domains,
            historicalNote: insight.reasoning?.observation,
            consequence: insight.reasoning?.familyImplication,
          },
        });
      }
    }

    // Source 2: Static indicator-driven actions (fill in gaps)
    const staticActions = generateActionList(indicators, completedTiers, phase);
    for (const action of staticActions) {
      // Skip if we already have a similar AI-generated action
      const aiCoveredDomains = new Set(actions.flatMap(a => a.sourceDomains));
      const hasOverlap = action.sourceDomains.some(d => aiCoveredDomains.has(d));
      if (hasOverlap && !action.phaseTask) continue;

      actions.push(action);
    }

    // Sort: now > today > this-week, then by priority
    return actions.sort((a, b) => {
      const urgencyOrder = { 'now': 0, 'today': 1, 'this-week': 2 };
      const urgencyDiff = urgencyOrder[a.urgency] - urgencyOrder[b.urgency];
      if (urgencyDiff !== 0) return urgencyDiff;
      return a.priority - b.priority;
    });
  }, [indicators, completedTiers, systemPhase, leadInsight, secondaryInsights, completedThisWeek]);

  // Visible tiers based on phase
  const visibleTiers = useMemo(() => {
    const phase = typeof systemPhase === 'number' ? systemPhase : 5;
    return getVisibleTiers(phase);
  }, [systemPhase]);

  // Readiness computation
  const readiness = useMemo(() => {
    return computeReadinessFromTiers(completedTiers);
  }, [completedTiers]);

  // Find the first incomplete tier (for default expansion)
  const firstIncompleteTierId = useMemo(() => {
    for (const tier of visibleTiers) {
      const progress = getTierProgress(tier, completedTiers);
      if (progress.percentage < 100) return tier.id;
    }
    return visibleTiers[0]?.id ?? null;
  }, [visibleTiers, completedTiers]);

  // Toggle handlers
  const toggleThisWeek = useCallback((id: string) => {
    setCompletedThisWeek(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      saveCompletedIds(STORAGE_KEYS.thisWeek, next);
      return next;
    });
  }, []);

  const toggleTier = useCallback((id: string) => {
    setCompletedTiers(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      saveCompletedIds(STORAGE_KEYS.tiers, next);
      return next;
    });
  }, []);

  const toggleMPhase = useCallback((id: string) => {
    setCompletedMPhase(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      saveCompletedIds(STORAGE_KEYS.mphase, next);
      return next;
    });
  }, []);

  const dismissIntro = useCallback(() => {
    setIntroDismissed(true);
    saveIntroDismissed(true);
  }, []);

  // Scroll to tier section
  const scrollToTier = useCallback((tierId: string) => {
    const el = sectionRefs.current[tierId];
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }, []);

  // Count incomplete condition-driven actions
  const incompleteConditionActions = thisWeekActions.filter(
    a => !a.phaseTask && !completedThisWeek.has(a.id)
  ).length;

  const subtitle = getAdaptiveSubtitle(threatState, incompleteConditionActions);

  return (
    <div className="min-h-screen bg-olive-950">
      {/* ─────────────────────────────────────────────────────────────────────
          Section 1: Header + Orientation
      ───────────────────────────────────────────────────────────────────── */}
      <header className="border-b border-olive-700/30">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          {/* Breadcrumb */}
          <nav className="flex items-center gap-2 text-sm text-olive-400 mb-4">
            <Link to="/dashboard" className="hover:text-olive-200 transition-colors">
              Dashboard
            </Link>
            <ChevronRight className="w-3 h-3" />
            <span className="text-olive-200">Action Plan</span>
          </nav>

          {/* Title and subtitle */}
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 rounded-xl bg-olive-800/50 border border-olive-700/50 flex items-center justify-center flex-shrink-0">
              <ClipboardList className="w-6 h-6 text-olive-400" />
            </div>
            <div>
              <h1 className="text-2xl font-display font-bold text-olive-100">
                Family Action Plan
              </h1>
              <p className="text-olive-300 mt-1">{subtitle}</p>
            </div>
          </div>

          {/* Collapsible intro paragraph */}
          {!introDismissed && (
            <div className="mt-4 p-4 rounded-xl bg-olive-900/40 border border-olive-700/30 relative">
              <button
                onClick={dismissIntro}
                className="absolute top-3 right-3 text-olive-500 hover:text-olive-300 transition-colors"
                aria-label="Dismiss"
              >
                <X className="w-4 h-4" />
              </button>
              <p className="text-sm text-olive-300 leading-relaxed pr-8">
                This page helps you prepare for whatever comes. The tasks below are organized
                by how serious conditions are — when everything's calm, focus on the basics.
                When indicators turn amber or red, you'll see time-sensitive actions at the top.
                Check things off as you go; your progress is saved automatically.
              </p>
            </div>
          )}
        </div>
      </header>

      {/* ─────────────────────────────────────────────────────────────────────
          Main Content
      ───────────────────────────────────────────────────────────────────── */}
      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        {/* Section 2: Current Conditions Summary */}
        <ConditionsSummary indicators={indicators} systemPhase={systemPhase} />

        {/* Section 3: Phase Progress Map */}
        <PhaseProgressMap
          tiers={visibleTiers}
          completedTasks={completedTiers}
          onTierClick={scrollToTier}
        />

        {/* Section 4: Condition-Driven Actions (This Week) */}
        <ConditionActions
          actions={thisWeekActions}
          completedIds={completedThisWeek}
          onToggle={toggleThisWeek}
        />

        {/* Section 5: M-Phase (Migration) Sections - if triggered */}
        {mPhaseResult.triggered && mPhaseResult.info && (
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <h2 className="text-lg font-semibold text-indigo-200">Mobility Options</h2>
              <span className="text-xs bg-indigo-500/20 text-indigo-300 px-2 py-0.5 rounded-full border border-indigo-500/30">
                M-{mPhaseResult.level}
              </span>
            </div>
            <p className="text-sm text-indigo-300/70 -mt-2">
              Domestic control conditions suggest reviewing your mobility options
            </p>

            <div className="space-y-4">
              {visibleMPhaseLevels.map((level) => {
                const tier = getMPhaseTier(level);
                // Use the info for the current level, or create one for lower levels
                const info = level === mPhaseResult.level
                  ? mPhaseResult.info!
                  : {
                      level,
                      name: tier.title,
                      description: tier.description,
                      triggerReason: 'Foundation for higher M-phase preparedness',
                    };
                return (
                  <MPhaseSection
                    key={`mphase-${level}`}
                    tier={tier}
                    mPhaseInfo={info}
                    completedTasks={completedMPhase}
                    onToggleTask={toggleMPhase}
                    defaultExpanded={level === mPhaseResult.level}
                  />
                );
              })}
            </div>
          </div>
        )}

        {/* Section 6: Phase Sections */}
        <div className="space-y-4">
          <h2 className="text-lg font-semibold text-olive-100">Building Readiness</h2>
          <p className="text-sm text-olive-400 -mt-2">
            {readiness.description} — work through these at your own pace
          </p>

          <div className="space-y-4">
            {visibleTiers.map((tier) => (
              <div
                key={tier.id}
                ref={el => {
                  sectionRefs.current[tier.id] = el;
                }}
              >
                <PhaseSection
                  tier={tier}
                  completedTasks={completedTiers}
                  onToggleTask={toggleTier}
                  defaultExpanded={tier.id === firstIncompleteTierId}
                  id={`tier-${tier.id}`}
                />
              </div>
            ))}
          </div>
        </div>

        {/* Section 7: Educational Footer */}
        <HowItWorks />
      </main>
    </div>
  );
};

export default FamilyActionPlan;
