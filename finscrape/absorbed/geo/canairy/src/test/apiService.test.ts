import { describe, it, expect } from 'vitest';
import { mockIndicators, mockHOPIScore, mockSystemStatus } from '../mock/mockData';
import { DOMAIN_META, Domain } from '../types';

/**
 * Tests that mock data matches the expected shape for the API service.
 * When the real API is unavailable, the frontend falls back to this data.
 */
describe('Mock Data Shape', () => {
  describe('mockIndicators', () => {
    it('has 49 indicators', () => {
      expect(mockIndicators).toHaveLength(49);
    });

    it('every indicator has required fields', () => {
      mockIndicators.forEach(ind => {
        expect(ind.id).toBeTruthy();
        expect(ind.name).toBeTruthy();
        expect(ind.domain).toBeTruthy();
        expect(ind.description).toBeTruthy();
        expect(ind.unit).toBeTruthy();
        expect(ind.dataSource).toBeTruthy();
        expect(ind.updateFrequency).toBeTruthy();

        // Status
        expect(ind.status).toBeDefined();
        expect(['green', 'amber', 'red', 'unknown']).toContain(ind.status.level);
        expect(ind.status.value).toBeDefined();
        expect(['up', 'down', 'stable']).toContain(ind.status.trend);
        expect(ind.status.lastUpdate).toBeTruthy();
        expect(['LIVE', 'MANUAL', 'MOCK']).toContain(ind.status.dataSource);

        // Thresholds
        expect(ind.thresholds).toBeDefined();
      });
    });

    it('every indicator domain is valid', () => {
      const validDomains = Object.keys(DOMAIN_META);
      mockIndicators.forEach(ind => {
        expect(validDomains).toContain(ind.domain);
      });
    });

    it('covers all 11 domains', () => {
      const domains = new Set(mockIndicators.map(i => i.domain));
      expect(domains.size).toBe(11);
    });

    it('has unique IDs', () => {
      const ids = mockIndicators.map(i => i.id);
      expect(new Set(ids).size).toBe(ids.length);
    });

    it('critical indicators have expected IDs', () => {
      const criticalIds = mockIndicators
        .filter(i => i.critical)
        .map(i => i.id);
      expect(criticalIds).toContain('market_01_intraday_swing');
      expect(criticalIds).toContain('info_02_deepfake_shocks');
      expect(criticalIds).toContain('nato_high_readiness');
      expect(criticalIds).toContain('national_guard_metros');
      expect(criticalIds).toContain('dhs_removal_expansion');
    });

    it('green flag indicators are marked correctly', () => {
      const greenFlags = mockIndicators.filter(i => i.greenFlag);
      expect(greenFlags.length).toBeGreaterThanOrEqual(2);
      expect(greenFlags.map(i => i.id)).toContain('green_g1_gdp_rates');
      expect(greenFlags.map(i => i.id)).toContain('compute_01_training_cost');
    });

    it('disabled indicators have enabled=false', () => {
      const disabled = mockIndicators.filter(i => i.enabled === false);
      expect(disabled.length).toBeGreaterThan(0);
      // Cult indicators should all be disabled
      const cultDisabled = disabled.filter(i => i.domain === 'social_cohesion');
      expect(cultDisabled.length).toBe(4);
    });

    it('status levels match threshold values', () => {
      mockIndicators.forEach(ind => {
        const { value } = ind.status;
        const amber = ind.thresholds.threshold_amber;
        const red = ind.thresholds.threshold_red;
        if (typeof value !== 'number' || amber === undefined || red === undefined) return;

        // For green flags and inverted thresholds, skip validation
        if (ind.greenFlag) return;
        // For inverted thresholds (lower is worse), skip
        if (red < amber) return;

        // Standard: higher is worse
        if (ind.status.level === 'green') {
          expect(value).toBeLessThanOrEqual(amber);
        }
        if (ind.status.level === 'red') {
          expect(value).toBeGreaterThanOrEqual(red);
        }
      });
    });
  });

  describe('mockHOPIScore', () => {
    it('has required fields', () => {
      expect(mockHOPIScore.score).toBeDefined();
      expect(mockHOPIScore.confidence).toBeDefined();
      expect(mockHOPIScore.phase).toBeDefined();
      expect(mockHOPIScore.targetPhase).toBeDefined();
      expect(mockHOPIScore.domains).toBeDefined();
      expect(mockHOPIScore.timestamp).toBeTruthy();
    });

    it('covers all 11 domains', () => {
      const domainKeys = Object.keys(mockHOPIScore.domains);
      expect(domainKeys).toHaveLength(11);
    });

    it('domain scores are between 0 and 1', () => {
      Object.values(mockHOPIScore.domains).forEach(domain => {
        expect(domain.score).toBeGreaterThanOrEqual(0);
        expect(domain.score).toBeLessThanOrEqual(1);
      });
    });

    it('domain weights match DOMAIN_META', () => {
      Object.entries(mockHOPIScore.domains).forEach(([key, domain]) => {
        const meta = DOMAIN_META[key as Domain];
        if (meta) {
          expect(domain.weight).toBe(meta.weight);
        }
      });
    });
  });

  describe('mockSystemStatus', () => {
    it('has required fields', () => {
      expect(mockSystemStatus.operational).toBe(true);
      expect(mockSystemStatus.lastUpdate).toBeTruthy();
      expect(typeof mockSystemStatus.activeAlerts).toBe('number');
      expect(typeof mockSystemStatus.dataQuality).toBe('number');
    });
  });
});
