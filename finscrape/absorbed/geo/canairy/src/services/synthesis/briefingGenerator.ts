/**
 * Briefing Generator Service
 *
 * Generates AI-powered intelligence briefings by combining:
 * - Enriched indicator data
 * - Domain knowledge system prompt
 * - Claude API for synthesis
 *
 * This is the core of the "intelligence briefing" approach vs. traditional dashboard.
 */

import { IndicatorData } from '../../types';
import { enrichIndicators, getSystemSummary, EnrichedIndicator } from './indicatorContext';
import { BRIEFING_SYSTEM_PROMPT, buildBriefingPrompt, parseBriefingResponse, BriefingResponse } from './domainKnowledge';

// Cache for briefings (15-minute TTL)
interface BriefingCache {
  briefing: BriefingResponse;
  timestamp: number;
  indicatorHash: string;
}

let briefingCache: BriefingCache | null = null;
const CACHE_TTL = 15 * 60 * 1000; // 15 minutes

/**
 * Generate a hash of current indicator states for cache invalidation
 */
function getIndicatorHash(indicators: IndicatorData[]): string {
  return indicators
    .map(i => `${i.id}:${i.status.level}:${i.status.value}`)
    .sort()
    .join('|');
}

/**
 * Check if cached briefing is still valid
 */
function isCacheValid(hash: string): boolean {
  if (!briefingCache) return false;
  if (Date.now() - briefingCache.timestamp > CACHE_TTL) return false;
  if (briefingCache.indicatorHash !== hash) return false;
  return true;
}

/**
 * Call Claude API for briefing generation
 */
async function callClaudeForBriefing(
  systemPrompt: string,
  userPrompt: string
): Promise<string | null> {
  // Canairy AI synthesis is disabled to stop Anthropic token usage.
  // Re-enable by setting VITE_CANAIRY_AI_ENABLED=true at build time.
  if (import.meta.env.VITE_CANAIRY_AI_ENABLED !== 'true') {
    return null;
  }

  const apiKey = import.meta.env.VITE_ANTHROPIC_API_KEY;

  if (!apiKey) {
    console.warn('[Briefing] No API key configured, using fallback');
    return null;
  }

  console.log('[Briefing] Calling Claude API for synthesis...');

  try {
    const response = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': apiKey,
        'anthropic-version': '2023-06-01',
        'anthropic-dangerous-direct-browser-access': 'true',
      },
      body: JSON.stringify({
        model: 'claude-3-haiku-20240307',
        max_tokens: 4000,
        system: systemPrompt,
        messages: [
          {
            role: 'user',
            content: userPrompt,
          },
        ],
      }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('[Briefing] Claude API error:', response.status, errorText);
      return null;
    }

    const data = await response.json();
    const result = data.content?.[0]?.text || null;
    console.log('[Briefing] Claude response received:', result?.substring(0, 200) + '...');
    return result;
  } catch (error) {
    console.error('[Briefing] Claude API call failed:', error);
    return null;
  }
}

/**
 * Generate a fallback briefing when Claude is unavailable
 */
function generateFallbackBriefing(
  indicators: IndicatorData[],
  summary: ReturnType<typeof getSystemSummary>
): BriefingResponse {
  const { overallStatus, redCount, amberCount, criticalIndicators, elevatedIndicators, affectedDomains } = summary;

  let headline: string;
  let whatsHappening: string;
  let whyItMatters: string;
  let whereItsHeading: string;

  if (overallStatus === 'red') {
    headline = `ACTION REQUIRED — ${redCount} Critical Indicator${redCount > 1 ? 's' : ''} Detected`;
    whatsHappening = criticalIndicators
      .map(i => `${i.name}: ${i.meaning}`)
      .join('\n\n');
    whyItMatters = criticalIndicators
      .map(i => i.householdImpact)
      .filter((v, i, a) => a.indexOf(v) === i) // unique
      .join(' ');
    whereItsHeading = 'If current trends continue, expect these conditions to intensify. Monitor closely for escalation signs.';
  } else if (overallStatus === 'amber') {
    headline = `ELEVATED WATCH — ${amberCount} Indicator${amberCount > 1 ? 's' : ''} Showing Stress`;
    whatsHappening = elevatedIndicators
      .slice(0, 3)
      .map(i => `${i.name}: ${i.meaning}`)
      .join('\n\n');
    whyItMatters = elevatedIndicators
      .slice(0, 3)
      .map(i => i.householdImpact)
      .filter((v, i, a) => a.indexOf(v) === i)
      .join(' ');
    whereItsHeading = 'Conditions bear watching. These indicators could escalate to red status if trends continue.';
  } else {
    headline = 'ALL SYSTEMS NORMAL — No Significant Threats Detected';
    whatsHappening = 'All monitored indicators are operating within normal parameters. No immediate concerns identified.';
    whyItMatters = 'Your household faces no elevated risks from the indicators we monitor. Maintain normal preparedness levels.';
    whereItsHeading = 'Conditions are stable. Continue monitoring for changes.';
  }

  const whatToWatch: string[] = [];
  if (criticalIndicators.length > 0) {
    criticalIndicators.forEach(i => {
      whatToWatch.push(`${i.name}: Watch for further deterioration`);
    });
  }
  if (elevatedIndicators.length > 0) {
    elevatedIndicators.slice(0, 3).forEach(i => {
      whatToWatch.push(`${i.name}: May escalate to red`);
    });
  }
  if (whatToWatch.length === 0) {
    whatToWatch.push('Continue routine monitoring');
  }

  const recommendedActions: BriefingResponse['recommendedActions'] = [];

  // Add actions based on critical indicators
  criticalIndicators.forEach(i => {
    if (i.recommendedAction && i.recommendedAction !== 'Monitor situation') {
      recommendedActions.push({
        action: i.recommendedAction,
        reasoning: `Triggered by: ${i.name} at ${i.status} level`,
        urgency: 'now',
      });
    }
  });

  // Add actions based on elevated indicators (limit to avoid overwhelm)
  elevatedIndicators.slice(0, 2).forEach(i => {
    if (i.recommendedAction && i.recommendedAction !== 'Monitor situation' && !recommendedActions.some(a => a.action === i.recommendedAction)) {
      recommendedActions.push({
        action: i.recommendedAction,
        reasoning: `Triggered by: ${i.name} at ${i.status} level`,
        urgency: 'soon',
      });
    }
  });

  if (recommendedActions.length === 0) {
    recommendedActions.push({
      action: 'Maintain current preparedness level',
      reasoning: 'No elevated indicators require immediate action',
      urgency: 'when-ready',
    });
  }

  // Build topic cards from elevated indicators
  const topics: BriefingResponse['topics'] = [];

  // Group by domain for topic cards
  const domainGroups = new Map<string, typeof criticalIndicators>();
  [...criticalIndicators, ...elevatedIndicators].forEach(i => {
    const existing = domainGroups.get(i.domain) || [];
    existing.push(i);
    domainGroups.set(i.domain, existing);
  });

  domainGroups.forEach((domainIndicators, domain) => {
    const hasCritical = domainIndicators.some(i => i.status === 'red');

    // Build actions from all indicators in this domain
    const actions: BriefingResponse['topics'][0]['actions'] = [];
    domainIndicators.forEach(ind => {
      if (ind.recommendedAction && ind.recommendedAction !== 'Monitor situation') {
        actions.push({
          action: ind.recommendedAction,
          reasoning: `Triggered by ${ind.name}`,
          urgency: ind.status === 'red' ? 'now' as const : 'soon' as const,
        });
      }
    });

    topics.push({
      topic: domain.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
      status: hasCritical ? 'red' : 'amber',
      headline: domainIndicators.map(i => i.name).join(', ') + ' showing stress',
      whatsHappening: domainIndicators.map(i => `${i.name}: ${i.meaning}`).join('\n\n'),
      whyItMatters: domainIndicators.map(i => i.householdImpact).filter(Boolean).join(' '),
      whereItsHeading: 'If current trends continue, conditions may escalate. Monitor closely.',
      whatToWatch: domainIndicators.map(i => `${i.name} crossing into red territory`),
      actions,
      keyIndicators: domainIndicators.map(i => i.id),
    });
  });

  return {
    status: overallStatus,
    headline,
    topics,
    whatsHappening,
    whyItMatters,
    whereItsHeading,
    whatToWatch,
    recommendedActions,
    keyIndicators: [...criticalIndicators, ...elevatedIndicators].map(i => i.id),
    confidence: overallStatus === 'red' ? 'high' : 'moderate',
    generatedAt: new Date().toISOString(),
  };
}

/**
 * Main entry point: Generate an intelligence briefing
 */
export async function generateBriefing(
  indicators: IndicatorData[],
  options: {
    userPhase?: number;
    focusAreas?: string[];
    forceRefresh?: boolean;
  } = {}
): Promise<BriefingResponse> {
  const { userPhase = 1, focusAreas = [], forceRefresh = false } = options;

  // Check cache
  const indicatorHash = getIndicatorHash(indicators);
  if (!forceRefresh && isCacheValid(indicatorHash) && briefingCache) {
    console.log('Using cached briefing');
    return briefingCache.briefing;
  }

  // Get system summary and enriched indicators
  const summary = getSystemSummary(indicators);
  const enriched = enrichIndicators(indicators, { includeGreen: false, sortByPriority: true });

  console.log('[Briefing] Status:', summary.overallStatus, '| Red:', summary.redCount, '| Amber:', summary.amberCount);

  // If all green, return a simple "all clear" briefing
  if (summary.overallStatus === 'green') {
    console.log('[Briefing] All green, using simple all-clear briefing');
    const allClearBriefing = generateFallbackBriefing(indicators, summary);
    briefingCache = {
      briefing: allClearBriefing,
      timestamp: Date.now(),
      indicatorHash,
    };
    return allClearBriefing;
  }

  // Build the prompt
  const userPrompt = buildBriefingPrompt(enriched, { userPhase, focusAreas });
  console.log('[Briefing] Built prompt with', enriched.length, 'enriched indicators');

  // Call Claude
  const claudeResponse = await callClaudeForBriefing(BRIEFING_SYSTEM_PROMPT, userPrompt);

  let briefing: BriefingResponse;

  if (claudeResponse) {
    console.log('[Briefing] Claude synthesis successful, parsing response');
    // Parse Claude's response
    const keyIndicators = enriched.slice(0, 5).map(i => i.id);
    briefing = parseBriefingResponse(claudeResponse, keyIndicators);
    briefing.status = summary.overallStatus;
  } else {
    console.log('[Briefing] Claude failed, using fallback briefing');
    // Fallback to generated briefing
    briefing = generateFallbackBriefing(indicators, summary);
  }

  // Cache the result
  briefingCache = {
    briefing,
    timestamp: Date.now(),
    indicatorHash,
  };

  return briefing;
}

/**
 * Get the current briefing from cache without regenerating
 */
export function getCachedBriefing(): BriefingResponse | null {
  if (!briefingCache) return null;
  if (Date.now() - briefingCache.timestamp > CACHE_TTL) return null;
  return briefingCache.briefing;
}

/**
 * Clear the briefing cache
 */
export function clearBriefingCache(): void {
  briefingCache = null;
}

/**
 * Check if a briefing refresh is needed
 */
export function needsBriefingRefresh(indicators: IndicatorData[]): boolean {
  const hash = getIndicatorHash(indicators);
  return !isCacheValid(hash);
}

/**
 * Export types for consumers
 */
export type { BriefingResponse, EnrichedIndicator };
