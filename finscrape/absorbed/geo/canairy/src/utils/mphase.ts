/**
 * M-Phase (Migration Phase) Calculation
 *
 * Calculates the current M-phase level based on domestic control indicators.
 * Matches the logic from src/processors/phase_controller.py
 *
 * M-0: Domestic Control domain score ≥0.4 → passport/document review
 * M-1: ICE + 2 domestic indicators all amber for sustained period → visa research
 * M-2: 2+ Domestic Control reds sustained → trial relocation
 */

import { IndicatorData, MPhaseLevel, MPhaseInfo, M_PHASE_INFO } from '../types';

// Domestic control indicator IDs (match backend)
const DOMESTIC_INDICATOR_IDS = [
  'ice_detention_surge',
  'federal_regulations',
  'liberty_litigation_count',
  'congress_activity',
  'travel_02_border_wait',
];

// Domain weights for calculating domain score
const LEVEL_SCORES: Record<string, number> = {
  green: 0.0,
  amber: 0.5,
  red: 1.0,
  unknown: 0.0,
};

interface MPhaseResult {
  level: MPhaseLevel | null;
  info: MPhaseInfo | null;
  domesticScore: number;
  amberCount: number;
  redCount: number;
  triggered: boolean;
}

/**
 * Calculate M-phase from current indicators
 */
export function calculateMPhase(indicators: IndicatorData[]): MPhaseResult {
  // Filter to domestic control indicators
  const domesticIndicators = indicators.filter(
    ind => ind.domain === 'domestic_control' || DOMESTIC_INDICATOR_IDS.includes(ind.id)
  );

  if (domesticIndicators.length === 0) {
    return {
      level: null,
      info: null,
      domesticScore: 0,
      amberCount: 0,
      redCount: 0,
      triggered: false,
    };
  }

  // Count amber and red indicators
  let amberCount = 0;
  let redCount = 0;
  let totalScore = 0;

  for (const ind of domesticIndicators) {
    const level = ind.status?.level || 'unknown';
    totalScore += LEVEL_SCORES[level] || 0;

    if (level === 'amber') amberCount++;
    if (level === 'red') redCount++;
  }

  // Calculate domain score (0-1 scale)
  const domesticScore = totalScore / domesticIndicators.length;

  // Check ICE indicator specifically for M-1 trigger
  const iceIndicator = indicators.find(ind => ind.id === 'ice_detention_surge');
  const iceAmber = iceIndicator?.status?.level === 'amber';

  // Determine M-phase level
  let level: MPhaseLevel | null = null;
  let triggerReason = '';

  // M-2: 2+ reds in domestic control
  if (redCount >= 2) {
    level = 2;
    triggerReason = `${redCount} domestic control indicators at red level`;
  }
  // M-1: ICE amber + 2 other ambers
  else if (iceAmber && amberCount >= 3) {
    level = 1;
    triggerReason = 'ICE detention elevated with multiple domestic indicators at amber';
  }
  // M-0: Domain score ≥0.4
  else if (domesticScore >= 0.4) {
    level = 0;
    triggerReason = `Domestic control domain score elevated (${Math.round(domesticScore * 100)}%)`;
  }

  if (level === null) {
    return {
      level: null,
      info: null,
      domesticScore,
      amberCount,
      redCount,
      triggered: false,
    };
  }

  const baseInfo = M_PHASE_INFO[level];

  return {
    level,
    info: {
      level,
      ...baseInfo,
      triggerReason,
    },
    domesticScore,
    amberCount,
    redCount,
    triggered: true,
  };
}

/**
 * Get all M-phase tasks that should be visible based on current M-phase level
 * Returns tasks for the current level and all levels below
 */
export function getVisibleMPhaseLevels(currentLevel: MPhaseLevel | null): (0 | 1 | 2)[] {
  if (currentLevel === null) return [];

  const levels: (0 | 1 | 2)[] = [];
  for (let i = 0; i <= currentLevel; i++) {
    levels.push(i as 0 | 1 | 2);
  }
  return levels;
}
