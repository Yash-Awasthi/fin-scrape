/**
 * Card Scorer for Canairy Synthesis Engine
 *
 * Scores and ranks detected patterns to determine which cards
 * should be displayed and in what order.
 */

import { IndicatorData } from '../../types';
import { Pattern, detectPatterns } from './patternLibrary';

export interface ScoredPattern {
  pattern: Pattern;
  totalScore: number;
  severityScore: number;
  recencyScore: number;
  trendScore: number;
  phaseRelevanceScore: number;
  actionabilityScore: number;
  matchedIndicators: IndicatorData[];
}

export interface SynthesisOutput {
  leadCard: ScoredPattern | null;
  secondaryCards: ScoredPattern[];
  compactRows: ScoredPattern[];
  omitted: ScoredPattern[];
}

/**
 * Score weights for ranking algorithm
 */
const WEIGHTS = {
  severity: 0.35,
  recency: 0.20,
  trend: 0.20,
  phaseRelevance: 0.10,
  actionability: 0.15,
};

/**
 * Calculate severity score (0-100)
 */
function calculateSeverityScore(pattern: Pattern, matchedIndicators: IndicatorData[]): number {
  let score = pattern.baseSeverity * 10; // Base: 10-100

  // Bonus for critical indicators
  const criticalCount = matchedIndicators.filter(i => i.critical).length;
  score += criticalCount * 5;

  // Bonus for multiple indicators matching
  if (matchedIndicators.length > 2) {
    score += (matchedIndicators.length - 2) * 3;
  }

  // Bonus for red indicators
  const redCount = matchedIndicators.filter(i => i.status.level === 'red').length;
  score += redCount * 5;

  return Math.min(100, score);
}

/**
 * Calculate recency score (0-100)
 * Higher score for more recent status changes
 */
function calculateRecencyScore(matchedIndicators: IndicatorData[]): number {
  if (matchedIndicators.length === 0) return 0;

  const now = Date.now();
  let recentScore = 0;

  for (const ind of matchedIndicators) {
    const updatedAt = new Date(ind.status.lastUpdate).getTime();
    const hoursSinceUpdate = (now - updatedAt) / (1000 * 60 * 60);

    if (hoursSinceUpdate < 1) {
      recentScore += 100;
    } else if (hoursSinceUpdate < 6) {
      recentScore += 80;
    } else if (hoursSinceUpdate < 24) {
      recentScore += 60;
    } else if (hoursSinceUpdate < 48) {
      recentScore += 40;
    } else {
      recentScore += 20;
    }
  }

  return Math.min(100, recentScore / matchedIndicators.length);
}

/**
 * Calculate trend score (0-100)
 * Higher score for worsening trends (up = worsening, down = improving)
 */
function calculateTrendScore(matchedIndicators: IndicatorData[]): number {
  if (matchedIndicators.length === 0) return 50;

  let trendScore = 0;

  for (const ind of matchedIndicators) {
    switch (ind.status.trend) {
      case 'up': // up = worsening
        trendScore += 100;
        break;
      case 'stable':
        trendScore += 50;
        break;
      case 'down': // down = improving
        trendScore += 25;
        break;
      default:
        trendScore += 50;
    }
  }

  return trendScore / matchedIndicators.length;
}

/**
 * Calculate phase relevance score (0-100)
 * Higher score for patterns relevant to current system phase
 */
function calculatePhaseRelevanceScore(pattern: Pattern, _systemPhase: number): number {
  // Patterns with actionable steps are more relevant
  if (pattern.actionTemplate) {
    return 80;
  }

  // Higher severity patterns are generally relevant
  if (pattern.baseSeverity >= 8) {
    return 70;
  }

  return 50;
}

/**
 * Calculate actionability score (0-100)
 * Higher score for patterns with clear actions
 */
function calculateActionabilityScore(pattern: Pattern): number {
  let score = 50;

  if (pattern.actionTemplate) {
    score += 30;
  }

  if (pattern.actionHref) {
    score += 20;
  }

  return score;
}

/**
 * Score a single pattern
 */
function scorePattern(
  pattern: Pattern,
  matchedIndicators: IndicatorData[],
  systemPhase: number
): ScoredPattern {
  const severityScore = calculateSeverityScore(pattern, matchedIndicators);
  const recencyScore = calculateRecencyScore(matchedIndicators);
  const trendScore = calculateTrendScore(matchedIndicators);
  const phaseRelevanceScore = calculatePhaseRelevanceScore(pattern, systemPhase);
  const actionabilityScore = calculateActionabilityScore(pattern);

  const totalScore =
    severityScore * WEIGHTS.severity +
    recencyScore * WEIGHTS.recency +
    trendScore * WEIGHTS.trend +
    phaseRelevanceScore * WEIGHTS.phaseRelevance +
    actionabilityScore * WEIGHTS.actionability;

  return {
    pattern,
    totalScore,
    severityScore,
    recencyScore,
    trendScore,
    phaseRelevanceScore,
    actionabilityScore,
    matchedIndicators,
  };
}

/**
 * Get indicators that triggered a pattern
 */
function getMatchedIndicators(pattern: Pattern, indicators: IndicatorData[]): IndicatorData[] {
  const matched: IndicatorData[] = [];

  for (const condition of pattern.requiredConditions) {
    for (const ind of indicators) {
      if (condition.indicatorId && ind.id !== condition.indicatorId) continue;
      if (condition.domain && ind.domain !== condition.domain) continue;
      if (ind.status.level !== condition.level) continue;

      if (!matched.find(m => m.id === ind.id)) {
        matched.push(ind);
      }
    }
  }

  // Also include optional condition matches
  if (pattern.optionalConditions) {
    for (const condition of pattern.optionalConditions) {
      for (const ind of indicators) {
        if (condition.indicatorId && ind.id !== condition.indicatorId) continue;
        if (condition.domain && ind.domain !== condition.domain) continue;

        const levelOrder: Record<string, number> = { green: 0, amber: 1, red: 2, unknown: 0 };
        if (levelOrder[ind.status.level] >= levelOrder[condition.level]) {
          if (!matched.find(m => m.id === ind.id)) {
            matched.push(ind);
          }
        }
      }
    }
  }

  return matched;
}

/**
 * Main synthesis function
 * Detects patterns, scores them, and returns ranked output
 */
export function synthesizeCards(
  indicators: IndicatorData[],
  systemPhase: number
): SynthesisOutput {
  // Detect matching patterns
  const matchedPatterns = detectPatterns(indicators);

  // Score each pattern
  const scoredPatterns: ScoredPattern[] = matchedPatterns.map(pattern => {
    const matchedIndicators = getMatchedIndicators(pattern, indicators);
    return scorePattern(pattern, matchedIndicators, systemPhase);
  });

  // Sort by total score (highest first)
  scoredPatterns.sort((a, b) => b.totalScore - a.totalScore);

  // Allocate to card types
  const output: SynthesisOutput = {
    leadCard: null,
    secondaryCards: [],
    compactRows: [],
    omitted: [],
  };

  scoredPatterns.forEach((scored, index) => {
    if (index === 0 && scored.totalScore >= 35) {
      // Highest score becomes lead card
      output.leadCard = scored;
    } else if (index <= 5 && scored.totalScore >= 25) {
      // Next 5 become secondary cards (expanded from 3)
      output.secondaryCards.push(scored);
    } else if (index <= 12 && scored.totalScore >= 15) {
      // Next 7 become compact rows (expanded from 5)
      output.compactRows.push(scored);
    } else {
      // Rest are omitted
      output.omitted.push(scored);
    }
  });

  return output;
}

/**
 * Convert scored pattern to card data for UI
 */
export function scoredPatternToCardData(scored: ScoredPattern) {
  const urgency: 'today' | 'week' | 'knowing' =
    scored.severityScore >= 70 ? 'today' : scored.severityScore >= 40 ? 'week' : 'knowing';

  // Generate whatToDo summary from action template
  const whatToDoSummary = scored.pattern.actionTemplate
    ? scored.pattern.actionTemplate
    : urgency === 'today'
      ? 'Review your action plan and check supplies.'
      : urgency === 'week'
        ? 'Take some time to review your preparedness.'
        : 'Stay informed and monitor the situation.';

  // Generate household impact based on urgency
  const whyItMatters = urgency === 'today'
    ? "This may require immediate attention. Having cash, supplies, and your action plan ready helps protect your family."
    : urgency === 'week'
      ? "This may affect your daily routine or require some preparation. Now is a good time to review your readiness."
      : "Worth keeping an eye on. No action needed right now, but good to be aware.";

  return {
    id: scored.pattern.id,
    headline: scored.pattern.headlineTemplate,
    whatsHappening: `Here's what I'm seeing: ${scored.pattern.outcomeTemplate}`,
    whyItMatters,
    whatToDo: whatToDoSummary,
    actions: scored.pattern.actionTemplate
      ? [{ id: `${scored.pattern.id}-action-1`, text: scored.pattern.actionTemplate, estimateMinutes: 15 }]
      : [],
    urgency,
    indicatorIds: scored.matchedIndicators.map(i => i.id),
    severity: scored.pattern.baseSeverity,
  };
}
