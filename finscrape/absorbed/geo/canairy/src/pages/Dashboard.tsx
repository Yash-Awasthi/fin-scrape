/**
 * Dashboard Page
 *
 * Streamlined layout:
 * 1. Welcome banner (first visit)
 * 2. Threat/Phase banner with actions (main CTA)
 * 3. What's happening (signals driving the plan)
 * 4. Also monitoring (low priority tracking with detail)
 */

import React, { useState, useEffect, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { RefreshCw, Eye, ChevronDown, ChevronRight, Clock } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { useStore, selectSynthesisCards, selectAIInsights, selectLeadAIInsight, selectSecondaryAIInsights } from '../store';
import { IndicatorData, DOMAIN_META } from '../types';
import { IndicatorModal } from '../components/indicators/IndicatorModal';
import { DashboardLoader } from '../components/dashboard/DashboardLoader';
import { ThreatBanner } from '../components/dashboard/ThreatBanner';
import { WelcomeBanner } from '../components/dashboard/WelcomeBanner';
import { LeadCard, LeadCardData } from '../components/dashboard/LeadCard';
import { SecondaryCardsGrid, CompactRowData } from '../components/dashboard/SecondaryCard';
import { AIAnalysisSummary } from '../components/dashboard/AIInsightCard';
import { ErrorBoundary } from '../components/ErrorBoundary';
import { DataSourceBanner } from '../components/common/DataSourceBanner';
import { getDisplayName, getImpact, getAction } from '../data/indicatorTranslations';
import { cn } from '../utils/cn';

export const Dashboard: React.FC = () => {
  const [selectedIndicator, setSelectedIndicator] = useState<IndicatorData | null>(null);
  const [showLegacyInsights, setShowLegacyInsights] = useState(false);

  const {
    indicators,
    loading,
    usingFallbackData,
    refreshAll,
    runSynthesis,
  } = useStore();

  const [isRetrying, setIsRetrying] = useState(false);

  const handleRetry = async () => {
    setIsRetrying(true);
    await refreshAll();
    setIsRetrying(false);
  };

  const synthesisCards = useStore(selectSynthesisCards);
  const aiAnalysis = useStore(selectAIInsights);
  const leadAIInsight = useStore(selectLeadAIInsight);
  const secondaryAIInsights = useStore(selectSecondaryAIInsights);

  // Count indicators by level
  const redCount = indicators.filter(i => i.status.level === 'red').length;
  const amberCount = indicators.filter(i => i.status.level === 'amber').length;
  const elevatedCount = redCount + amberCount;

  // Calculate last update time from indicators
  const lastUpdate = useMemo(() => {
    if (indicators.length === 0) return null;
    const mostRecent = indicators.reduce((latest, ind) =>
      new Date(ind.status.lastUpdate) > new Date(latest.status.lastUpdate) ? ind : latest
    );
    return mostRecent.status.lastUpdate;
  }, [indicators]);

  // Run synthesis when indicators change
  useEffect(() => {
    if (indicators.length > 0 && !synthesisCards) {
      runSynthesis();
    }
  }, [indicators.length]);

  // Fallback card data when synthesis hasn't run yet
  const getFallbackCards = () => {
    const redIndicators = indicators.filter(i => i.status.level === 'red');
    const amberIndicators = indicators.filter(i => i.status.level === 'amber');

    let leadCard: LeadCardData | null = null;

    if (redIndicators.length >= 2) {
      const impacts = redIndicators.slice(0, 2).map(i => getImpact(i.id, 'red'));
      leadCard = {
        id: 'fallback-action-protocol',
        headline: 'Multiple signals need your attention',
        whatsHappening: `Here's what I'm seeing: ${impacts.join('. ')} When multiple indicators go red at once, it's worth taking a closer look at your household's readiness.`,
        whyItMatters: "Having cash, fuel, and supplies ready protects your family when things move quickly. This is a good time to make sure your basics are covered.",
        whatToDo: "Review your action plan and check your supplies.",
        actions: [
          { id: 'fallback-1', text: 'Open your action plan and review top priorities', estimateMinutes: 10 },
          { id: 'fallback-2', text: 'Check cash on hand and essential supplies', estimateMinutes: 15 },
        ],
        urgency: 'today',
        indicatorIds: redIndicators.map(i => i.id),
        severity: 9,
      };
    } else if (redIndicators.length === 1) {
      const ind = redIndicators[0];
      const impact = getImpact(ind.id, 'red');
      const action = getAction(ind.id, 'red');
      leadCard = {
        id: `fallback-${ind.id}`,
        headline: action,
        whatsHappening: `Here's what happened: ${impact}`,
        whyItMatters: "When an indicator goes red, it's worth paying attention. This may affect your daily routine or require some preparation.",
        whatToDo: "Review the action plan for this indicator.",
        actions: [
          { id: 'fallback-single-1', text: 'Review the recommended actions for this signal', estimateMinutes: 5 },
        ],
        urgency: 'today',
        indicatorIds: [ind.id],
        severity: 7,
      };
    } else if (amberIndicators.length >= 3) {
      const topIndicator = amberIndicators[0];
      const action = getAction(topIndicator.id, 'amber');
      const impact = getImpact(topIndicator.id, 'amber');
      leadCard = {
        id: 'fallback-elevated',
        headline: action,
        whatsHappening: `Here's what I'm tracking: ${impact}. Several indicators are showing elevated readings right now.`,
        whyItMatters: "Nothing urgent, but now is a good time to review your supplies and ensure everything is current. A little preparation goes a long way.",
        whatToDo: "Take a few minutes to review your action plan.",
        actions: [
          { id: 'fallback-amber-1', text: 'Review your action plan and priorities', estimateMinutes: 10 },
          { id: 'fallback-amber-2', text: 'Check that supplies and documents are current', estimateMinutes: 15 },
        ],
        urgency: 'week',
        indicatorIds: amberIndicators.map(i => i.id),
        severity: 5,
      };
    }

    const compactRows: CompactRowData[] = amberIndicators.slice(0, 5).map(ind => ({
      id: `fallback-compact-${ind.id}`,
      text: getDisplayName(ind.id),
      domain: ind.domain,
      href: `/indicators?highlight=${ind.id}`,
    }));

    return { leadCard, secondaryCards: [], compactRows };
  };

  // Convert AI insights to card format (prioritized)
  const aiInsightToCard = (insight: typeof leadAIInsight): LeadCardData | null => {
    if (!insight) return null;

    const urgency: 'today' | 'week' | 'knowing' = insight.urgency;
    const actions = insight.actionItems?.map((a, i) => ({
      id: `${insight.id}-action-${i}`,
      text: a.task,
      estimateMinutes: a.effort === 'quick' ? 10 : a.effort === 'moderate' ? 30 : 60,
    })) || [];

    return {
      id: insight.id,
      headline: insight.headline,
      whatsHappening: insight.situationBrief || insight.body,
      whyItMatters: insight.reasoning?.familyImplication || "This may affect your household's daily routine.",
      whatToDo: insight.actionItems?.[0]?.task || insight.reasoning?.recommendation || "Review your action plan.",
      actions,
      urgency,
      indicatorIds: insight.domains,
      severity: urgency === 'today' ? 8 : urgency === 'week' ? 5 : 3,
      confidence: insight.confidence,
      signalCount: insight.evidenceSources?.length,
    };
  };

  // Combine AI insights with pattern-based synthesis for maximum coverage
  const getCards = () => {
    const aiCards: ReturnType<typeof aiInsightToCard>[] = [];
    let leadCard = null;

    // Get AI-generated cards if available
    if (leadAIInsight) {
      leadCard = aiInsightToCard(leadAIInsight);
      aiCards.push(...secondaryAIInsights.map(aiInsightToCard).filter(Boolean));
    }

    // Get pattern-based synthesis cards
    const patternCards = synthesisCards || getFallbackCards();

    // If no AI lead card, use pattern-based lead
    if (!leadCard && patternCards.leadCard) {
      leadCard = patternCards.leadCard;
    }

    // Combine secondary cards from both sources, avoiding duplicates
    const allSecondaryCards = [
      ...aiCards,
      ...(patternCards.secondaryCards || []),
    ].filter(Boolean);

    // Deduplicate by id (AI insights take priority)
    const seenIds = new Set<string>();
    const uniqueSecondaryCards = allSecondaryCards.filter(card => {
      if (!card || seenIds.has(card.id)) return false;
      seenIds.add(card.id);
      return true;
    });

    return {
      leadCard,
      secondaryCards: uniqueSecondaryCards.slice(0, 8), // Show up to 8 secondary cards
      compactRows: patternCards.compactRows || [],
    };
  };

  const cards = getCards();

  return (
    <>
      <div className="p-4 sm:p-6 lg:p-8 space-y-5 w-full">
        {/* Loading state */}
        {loading && indicators.length === 0 && (
          <DashboardLoader message="Loading indicator data..." />
        )}

        {/* Empty state */}
        {!loading && indicators.length === 0 && (
          <div className="text-center py-24">
            <div className="w-16 h-16 rounded-2xl bg-white/5 flex items-center justify-center mx-auto mb-4">
              <Eye className="w-8 h-8 text-olive-tertiary" />
            </div>
            <h3 className="text-xl font-display font-semibold text-olive-primary mb-2">
              Setting things up...
            </h3>
            <p className="text-olive-secondary mb-6 max-w-md mx-auto">
              Canairy is connecting to data sources. This usually takes just a moment.
            </p>
            <button onClick={refreshAll} className="btn btn-primary">
              <RefreshCw className="w-4 h-4" />
              Try Again
            </button>
          </div>
        )}

        {indicators.length > 0 && (
          <>
            {/* ──── 1. WELCOME BANNER (First visit only) ──── */}
            <ErrorBoundary isolate>
              <WelcomeBanner />
            </ErrorBoundary>

            {/* ──── DATA SOURCE WARNING (when using fallback data) ──── */}
            <DataSourceBanner
              isUsingFallback={usingFallbackData}
              onRetry={handleRetry}
              isRetrying={isRetrying}
            />

            {/* ──── DATA FRESHNESS INDICATOR ──── */}
            {lastUpdate && (
              <div className="flex items-center justify-end gap-1.5 text-xs text-olive-muted -mt-2 mb-2">
                <Clock className="w-3 h-3" />
                <span>
                  Last updated: {formatDistanceToNow(new Date(lastUpdate), { addSuffix: true })}
                  {usingFallbackData && <span className="text-amber-400 ml-1">· Using cached data</span>}
                </span>
              </div>
            )}

            {/* ──── 2. THREAT/PHASE BANNER (main CTA with actions) ──── */}
            <ErrorBoundary isolate>
              <ThreatBanner />
            </ErrorBoundary>

            {/* ──── 3. WHAT'S HAPPENING (Signals) ──── */}
            {(cards.leadCard || (cards.secondaryCards && cards.secondaryCards.length > 0)) && (
              <ErrorBoundary isolate>
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.1 }}
                  className="pt-2"
                >
                  <h3 className="text-xs font-medium text-olive-tertiary uppercase tracking-wider mb-3">
                    What's happening — {elevatedCount} signal{elevatedCount !== 1 ? 's' : ''} elevated
                  </h3>

                  <div className="space-y-4">
                    {cards.leadCard && (
                      <LeadCard data={cards.leadCard} />
                    )}
                    {cards.secondaryCards && cards.secondaryCards.length > 0 && (
                      <SecondaryCardsGrid cards={cards.secondaryCards.filter(Boolean) as any} />
                    )}
                    {/* Compact rows for additional signals */}
                    {cards.compactRows && cards.compactRows.length > 0 && (
                      <div className="mt-4 pt-4 border-t border-white/[0.06]">
                        <h4 className="text-[11px] font-medium text-olive-tertiary uppercase tracking-wider mb-1">
                          Also worth noting
                        </h4>
                        <p className="text-[10px] text-olive-muted mb-3">
                          Additional recommendations based on current conditions — important but not as time-sensitive.
                        </p>
                        <div className="grid gap-1">
                          {cards.compactRows.slice(0, 6).map((row, idx) => (
                            <Link
                              key={row.id}
                              to={row.href || '/action-plan'}
                              className="flex items-center gap-3 py-2 px-3 rounded-lg hover:bg-white/[0.03] transition-colors group"
                            >
                              <span className="text-xs text-olive-muted font-mono w-4">{idx + 1}</span>
                              <span className="text-sm text-olive-secondary group-hover:text-olive-primary flex-1">
                                {row.text}
                              </span>
                              <span className="text-[10px] text-olive-muted capitalize">
                                {row.domain.replace(/_/g, ' ')}
                              </span>
                            </Link>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </motion.div>
              </ErrorBoundary>
            )}

            {/* ──── 4. ALSO MONITORING (Enhanced with domain grouping) ──── */}
            <ErrorBoundary isolate>
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.15 }}
              >
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-xs font-medium text-olive-tertiary uppercase tracking-wider">
                    Also monitoring
                  </h3>
                  <Link
                    to="/indicators"
                    className="text-xs text-olive-400 hover:text-olive-300 transition-colors flex items-center gap-1"
                  >
                    View all
                    <ChevronRight className="w-3 h-3" />
                  </Link>
                </div>
                <div className="glass-card p-4">
                  {/* Group by domain with counts */}
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                    {Object.entries(
                      indicators.reduce((acc, ind) => {
                        const domain = ind.domain;
                        if (!acc[domain]) {
                          acc[domain] = { green: 0, amber: 0, red: 0 };
                        }
                        acc[domain][ind.status.level === 'unknown' ? 'green' : ind.status.level]++;
                        return acc;
                      }, {} as Record<string, { green: number; amber: number; red: number }>)
                    )
                      .filter(([domain]) => DOMAIN_META[domain as keyof typeof DOMAIN_META])
                      .sort((a, b) => {
                        // Sort by severity (red first, then amber)
                        const aScore = a[1].red * 10 + a[1].amber;
                        const bScore = b[1].red * 10 + b[1].amber;
                        return bScore - aScore;
                      })
                      .slice(0, 9)
                      .map(([domain, counts]) => {
                        const meta = DOMAIN_META[domain as keyof typeof DOMAIN_META];
                        const hasRed = counts.red > 0;
                        const hasAmber = counts.amber > 0;
                        return (
                          <Link
                            key={domain}
                            to={`/indicators?domain=${encodeURIComponent(domain)}`}
                            className={cn(
                              'flex items-center justify-between px-3 py-2 rounded-lg transition-colors',
                              'hover:bg-white/5',
                              hasRed ? 'bg-red-500/5' : hasAmber ? 'bg-amber-500/5' : 'bg-white/[0.02]'
                            )}
                          >
                            <span className={cn(
                              'text-sm truncate',
                              hasRed ? 'text-red-300' : hasAmber ? 'text-amber-300' : 'text-olive-300'
                            )}>
                              {meta?.label || domain}
                            </span>
                            <div className="flex items-center gap-1.5 flex-shrink-0">
                              {counts.red > 0 && (
                                <span className="text-[10px] font-mono text-red-400 bg-red-500/15 px-1.5 py-0.5 rounded">
                                  {counts.red}
                                </span>
                              )}
                              {counts.amber > 0 && (
                                <span className="text-[10px] font-mono text-amber-400 bg-amber-500/15 px-1.5 py-0.5 rounded">
                                  {counts.amber}
                                </span>
                              )}
                              {counts.red === 0 && counts.amber === 0 && (
                                <span className="w-2 h-2 rounded-full bg-green-500/60" />
                              )}
                            </div>
                          </Link>
                        );
                      })}
                  </div>
                </div>
              </motion.div>
            </ErrorBoundary>

            {/* ──── 5. DEEPER ANALYSIS (Hidden connections, phase relevance) ──── */}
            {aiAnalysis && (aiAnalysis.hiddenConnections?.length > 0 || aiAnalysis.phaseRelevance) && (
              <ErrorBoundary isolate>
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 0.2 }}
                >
                  <button
                    onClick={() => setShowLegacyInsights(!showLegacyInsights)}
                    className="w-full flex items-center justify-between py-2 text-left hover:text-olive-secondary transition-colors"
                  >
                    <div>
                      <span className="text-xs font-medium text-olive-tertiary uppercase tracking-wider">Deeper Analysis</span>
                      <p className="text-[10px] text-olive-muted mt-0.5">AI-generated briefing connecting current signals</p>
                    </div>
                    <ChevronDown className={`w-4 h-4 text-olive-tertiary transition-transform ${showLegacyInsights ? 'rotate-180' : ''}`} />
                  </button>
                  {showLegacyInsights && (
                    <div className="space-y-4 mt-2">
                      <AIAnalysisSummary
                        overallAssessment={aiAnalysis.outcomeSentence}
                        hiddenConnections={aiAnalysis.hiddenConnections}
                        familyFocusedSummary={aiAnalysis.familyFocusedSummary}
                        phaseRelevance={aiAnalysis.phaseRelevance}
                      />
                    </div>
                  )}
                </motion.div>
              </ErrorBoundary>
            )}

            {/* ──── BOTTOM MICROCOPY ──── */}
            <div className="text-center py-8">
              <p className="text-xs text-olive-muted">
                Intelligence briefing powered by Canairy
              </p>
            </div>
          </>
        )}
      </div>

      {/* Indicator Modal */}
      {selectedIndicator && (
        <IndicatorModal
          isOpen={!!selectedIndicator}
          onClose={() => setSelectedIndicator(null)}
          indicator={selectedIndicator}
        />
      )}
    </>
  );
};
