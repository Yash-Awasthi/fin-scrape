import { describe, it, expect } from 'vitest';
import { DOMAIN_META, Domain } from '../types';

describe('DOMAIN_META', () => {
  const allDomains: Domain[] = [
    'economy', 'jobs_labor', 'rights_governance', 'security_infrastructure',
    'oil_axis', 'ai_window', 'global_conflict', 'domestic_control', 'social_cohesion',
    'supply_chain', 'energy',
  ];

  it('has entries for all 11 domains', () => {
    expect(Object.keys(DOMAIN_META)).toHaveLength(11);
    allDomains.forEach(domain => {
      expect(DOMAIN_META[domain]).toBeDefined();
    });
  });

  it('every domain has label, weight, and icon', () => {
    Object.values(DOMAIN_META).forEach(meta => {
      expect(meta.label).toBeTruthy();
      expect(typeof meta.weight).toBe('number');
      expect(meta.weight).toBeGreaterThan(0);
      expect(meta.icon).toBeTruthy();
    });
  });

  it('global_conflict has highest weight (1.5)', () => {
    expect(DOMAIN_META.global_conflict.weight).toBe(1.5);
  });

  it('security_infrastructure and domestic_control are weighted 1.25', () => {
    expect(DOMAIN_META.security_infrastructure.weight).toBe(1.25);
    expect(DOMAIN_META.domestic_control.weight).toBe(1.25);
  });

  it('social_cohesion has lowest weight (0.75)', () => {
    expect(DOMAIN_META.social_cohesion.weight).toBe(0.75);
  });

  it('standard domains are weighted 1.0', () => {
    const standardDomains: Domain[] = ['economy', 'jobs_labor', 'rights_governance', 'oil_axis', 'ai_window'];
    standardDomains.forEach(domain => {
      expect(DOMAIN_META[domain].weight).toBe(1.0);
    });
  });
});
