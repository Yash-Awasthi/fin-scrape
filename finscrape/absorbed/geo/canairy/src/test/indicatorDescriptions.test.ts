import { describe, it, expect } from 'vitest';
import { getIndicatorDescription } from '../data/indicatorDescriptions';

describe('getIndicatorDescription', () => {
  it('returns description for known indicator', () => {
    const desc = getIndicatorDescription('econ_01_treasury_tail');
    expect(desc).toBeDefined();
    expect(desc?.name).toBe('10Y Auction Tail');
    expect(desc?.whyItMatters).toBeTruthy();
    expect(desc?.thresholds.green).toBeTruthy();
    expect(desc?.thresholds.amber).toBeTruthy();
    expect(desc?.thresholds.red).toBeTruthy();
  });

  it('returns undefined for unknown indicator', () => {
    expect(getIndicatorDescription('nonexistent_indicator')).toBeNull();
  });

  it('has descriptions for critical indicators', () => {
    const criticalIds = [
      'market_01_intraday_swing',
      'info_02_deepfake_shocks',
      'nato_high_readiness',
      'national_guard_metros',
      'dhs_removal_expansion',
    ];
    criticalIds.forEach(id => {
      const desc = getIndicatorDescription(id);
      expect(desc, `Missing description for critical indicator: ${id}`).toBeDefined();
    });
  });

  it('every description has required fields', () => {
    // Test a sampling of indicators
    const sampleIds = [
      'econ_01_treasury_tail',
      'econ_02_grocery_cpi',
      'taiwan_pla_activity',
      'ice_detention_surge',
      'oil_01_russian_brics',
    ];
    sampleIds.forEach(id => {
      const desc = getIndicatorDescription(id);
      expect(desc?.id).toBe(id);
      expect(desc?.name).toBeTruthy();
      expect(desc?.whyItMatters.length).toBeGreaterThan(20);
      expect(desc?.thresholds.green).toBeTruthy();
      expect(desc?.thresholds.amber).toBeTruthy();
      expect(desc?.thresholds.red).toBeTruthy();
    });
  });
});
