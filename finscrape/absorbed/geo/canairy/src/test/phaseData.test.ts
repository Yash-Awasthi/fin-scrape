import { describe, it, expect } from 'vitest';
import { PHASES, getPhaseByNumber, getPhaseColor, ACTION_PROTOCOL_CHECKLIST, CRITICAL_JUMP_RULES } from '../data/phaseData';

describe('PHASES', () => {
  it('has 11 phases (0–9 including 2.5)', () => {
    expect(PHASES).toHaveLength(11);
  });

  it('starts at phase 0 and ends at phase 9', () => {
    expect(PHASES[0].number).toBe(0);
    expect(PHASES[PHASES.length - 1].number).toBe(9);
  });

  it('includes phase 2.5', () => {
    const half = PHASES.find(p => p.number === 2.5);
    expect(half).toBeDefined();
    expect(half?.name).toBe('Liquidity & Docs');
  });

  it('phases are in ascending order', () => {
    for (let i = 1; i < PHASES.length; i++) {
      expect(PHASES[i].number).toBeGreaterThan(PHASES[i - 1].number);
    }
  });

  it('every phase has name, description, triggers, actions, and color', () => {
    PHASES.forEach(phase => {
      expect(phase.name).toBeTruthy();
      expect(phase.description).toBeTruthy();
      expect(phase.triggers.length).toBeGreaterThan(0);
      expect(phase.actions.length).toBeGreaterThan(0);
      expect(phase.color).toMatch(/^#[0-9A-Fa-f]{6}$/);
    });
  });

  it('lower phases are green/amber, higher phases are orange/red', () => {
    const phase0 = PHASES.find(p => p.number === 0)!;
    const phase7 = PHASES.find(p => p.number === 7)!;
    expect(phase0.color).toBe('#10B981'); // green
    expect(phase7.color).toBe('#EF4444'); // red
  });
});

describe('getPhaseByNumber', () => {
  it('returns correct phase for valid numbers', () => {
    expect(getPhaseByNumber(0)?.name).toBe('Foundations');
    expect(getPhaseByNumber(3)?.name).toBe('Air, Health, Mobile');
    expect(getPhaseByNumber(9)?.name).toBe('Optional Safe-Room');
  });

  it('returns correct phase for 2.5', () => {
    expect(getPhaseByNumber(2.5)?.name).toBe('Liquidity & Docs');
  });

  it('returns undefined for invalid phase number', () => {
    expect(getPhaseByNumber(10)).toBeUndefined();
    expect(getPhaseByNumber(-1)).toBeUndefined();
    expect(getPhaseByNumber(1.5)).toBeUndefined();
  });
});

describe('getPhaseColor', () => {
  it('returns correct color for valid phase', () => {
    expect(getPhaseColor(0)).toBe('#10B981');
    expect(getPhaseColor(7)).toBe('#EF4444');
  });

  it('returns fallback gray for invalid phase', () => {
    expect(getPhaseColor(99)).toBe('#6B7280');
  });
});

describe('ACTION_PROTOCOL_CHECKLIST', () => {
  it('has 12 checklist items', () => {
    expect(ACTION_PROTOCOL_CHECKLIST).toHaveLength(12);
  });

  it('each item has id, text, and category', () => {
    ACTION_PROTOCOL_CHECKLIST.forEach(item => {
      expect(item.id).toBeTruthy();
      expect(item.text).toBeTruthy();
      expect(item.category).toBeTruthy();
    });
  });

  it('covers all required categories', () => {
    const categories = new Set(ACTION_PROTOCOL_CHECKLIST.map(i => i.category));
    expect(categories).toContain('Financial');
    expect(categories).toContain('Supplies');
    expect(categories).toContain('Health');
    expect(categories).toContain('Comms');
    expect(categories).toContain('Docs');
    expect(categories).toContain('Family');
    expect(categories).toContain('Power');
  });

  it('has unique ids', () => {
    const ids = ACTION_PROTOCOL_CHECKLIST.map(i => i.id);
    expect(new Set(ids).size).toBe(ids.length);
  });
});

describe('CRITICAL_JUMP_RULES', () => {
  it('has 4 jump rules', () => {
    expect(CRITICAL_JUMP_RULES).toHaveLength(4);
  });

  it('each rule has required fields', () => {
    CRITICAL_JUMP_RULES.forEach(rule => {
      expect(rule.id).toBeTruthy();
      expect(rule.condition).toBeTruthy();
      expect(rule.indicatorIds.length).toBeGreaterThan(0);
      expect(rule.minPhase).toBeGreaterThanOrEqual(5);
      expect(rule.timeLimit).toBeTruthy();
    });
  });

  it('market + deepfake rule jumps to phase 7', () => {
    const rule = CRITICAL_JUMP_RULES.find(r => r.id === 'jump-1');
    expect(rule?.minPhase).toBe(7);
    expect(rule?.indicatorIds).toContain('market_01_intraday_swing');
    expect(rule?.indicatorIds).toContain('info_02_deepfake_shocks');
  });

  it('national guard rule is immediate to phase 5', () => {
    const rule = CRITICAL_JUMP_RULES.find(r => r.id === 'jump-3');
    expect(rule?.minPhase).toBe(5);
    expect(rule?.timeLimit).toBe('Immediate');
  });
});
