/**
 * Synthesis Engine for Canairy
 *
 * Detects patterns from indicator data, scores them, and optionally
 * enhances with Claude LLM for natural language synthesis.
 */

// Legacy pattern-based system (being phased out)
export { PATTERN_LIBRARY, detectPatterns, type Pattern, type PatternCondition } from './patternLibrary';
export { synthesizeCards, scoredPatternToCardData, type ScoredPattern, type SynthesisOutput } from './cardScorer';
export { synthesizePattern, synthesizeBatch, clearSynthesisCache, getCacheStats, type SynthesisResult } from './claudeService';
export { generateInsightCardWithEvidence } from './evidenceGenerator';

// New intelligence briefing system
export {
  enrichIndicator,
  enrichIndicators,
  getSystemSummary,
  getIndicatorContext,
  type EnrichedIndicator,
  type IndicatorContextEntry,
} from './indicatorContext';

export {
  BRIEFING_SYSTEM_PROMPT,
  buildBriefingPrompt,
  parseBriefingResponse,
  type BriefingResponse,
} from './domainKnowledge';

export {
  generateBriefing,
  getCachedBriefing,
  clearBriefingCache,
  needsBriefingRefresh,
} from './briefingGenerator';
