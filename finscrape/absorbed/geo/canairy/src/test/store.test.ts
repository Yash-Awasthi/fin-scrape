import { describe, it, expect, beforeEach } from 'vitest';
import { useStore, selectIndicatorsByDomain, selectCriticalIndicators, selectIndicatorCounts, selectTightenUpActive } from '../store';
import { IndicatorData } from '../types';

function makeIndicator(overrides: Partial<IndicatorData> & { id: string }): IndicatorData {
  return {
    name: overrides.id,
    domain: 'economy',
    description: '',
    unit: 'bps',
    thresholds: { green: {}, amber: {}, red: {} },
    dataSource: 'MOCK',
    updateFrequency: 'daily',
    status: {
      level: 'green',
      value: 0,
      lastUpdate: new Date().toISOString(),
      dataSource: 'MOCK',
    },
    ...overrides,
  };
}

describe('Store', () => {
  beforeEach(() => {
    useStore.setState({
      indicators: [],
      hopiScore: null,
      currentPhase: null,
      systemStatus: null,
      alerts: [],
      loading: false,
      error: null,
      selectedIndicator: null,
      sidebarOpen: true,
      timeRange: '7d',
    });
  });

  describe('basic state', () => {
    it('initializes with empty indicators', () => {
      expect(useStore.getState().indicators).toEqual([]);
    });

    it('initializes with no loading and no error', () => {
      const state = useStore.getState();
      expect(state.loading).toBe(false);
      expect(state.error).toBeNull();
    });
  });

  describe('setSelectedIndicator', () => {
    it('sets the selected indicator', () => {
      useStore.getState().setSelectedIndicator('econ_01_treasury_tail');
      expect(useStore.getState().selectedIndicator).toBe('econ_01_treasury_tail');
    });

    it('clears the selected indicator with null', () => {
      useStore.getState().setSelectedIndicator('econ_01_treasury_tail');
      useStore.getState().setSelectedIndicator(null);
      expect(useStore.getState().selectedIndicator).toBeNull();
    });
  });

  describe('setTimeRange', () => {
    it('updates time range', () => {
      useStore.getState().setTimeRange('30d');
      expect(useStore.getState().timeRange).toBe('30d');
    });
  });

  describe('updateIndicator', () => {
    it('updates a specific indicator by id', () => {
      const indicators = [
        makeIndicator({ id: 'ind1', status: { level: 'green', value: 10, lastUpdate: '', dataSource: 'MOCK' } }),
        makeIndicator({ id: 'ind2', status: { level: 'amber', value: 20, lastUpdate: '', dataSource: 'MOCK' } }),
      ];
      useStore.setState({ indicators });

      useStore.getState().updateIndicator('ind1', {
        status: { level: 'red', value: 50, lastUpdate: '', dataSource: 'LIVE' },
      });

      const updated = useStore.getState().indicators.find(i => i.id === 'ind1');
      expect(updated?.status.level).toBe('red');
      expect(updated?.status.value).toBe(50);
    });

    it('does not modify other indicators', () => {
      const indicators = [
        makeIndicator({ id: 'ind1' }),
        makeIndicator({ id: 'ind2', status: { level: 'amber', value: 20, lastUpdate: '', dataSource: 'MOCK' } }),
      ];
      useStore.setState({ indicators });

      useStore.getState().updateIndicator('ind1', { name: 'Updated' });

      const other = useStore.getState().indicators.find(i => i.id === 'ind2');
      expect(other?.status.level).toBe('amber');
    });
  });

  describe('setError', () => {
    it('sets and clears error', () => {
      useStore.getState().setError('Something broke');
      expect(useStore.getState().error).toBe('Something broke');

      useStore.getState().setError(null);
      expect(useStore.getState().error).toBeNull();
    });
  });
});

describe('Selectors', () => {
  const indicators: IndicatorData[] = [
    makeIndicator({ id: 'econ1', domain: 'economy', status: { level: 'green', value: 1, lastUpdate: '', dataSource: 'MOCK' } }),
    makeIndicator({ id: 'econ2', domain: 'economy', status: { level: 'red', value: 5, lastUpdate: '', dataSource: 'MOCK' }, critical: true }),
    makeIndicator({ id: 'conf1', domain: 'global_conflict', status: { level: 'red', value: 80, lastUpdate: '', dataSource: 'MOCK' }, critical: true }),
    makeIndicator({ id: 'oil1', domain: 'oil_axis', status: { level: 'amber', value: 40, lastUpdate: '', dataSource: 'MOCK' } }),
    makeIndicator({ id: 'ai1', domain: 'ai_window', status: { level: 'green', value: 10, lastUpdate: '', dataSource: 'MOCK' } }),
  ];

  const state = {
    indicators,
    hopiScore: null,
    currentPhase: null,
    systemStatus: null,
    alerts: [],
    systemPhase: 1 as number | 'tighten-up',
    checklistProgress: {
      completedPhase: 1,
      currentPhaseProgress: 65,
      completedItems: [],
    },
    synthesisOutput: null,
    synthesisResults: new Map(),
    synthesisLoading: false,
    aiAnalysis: null,
    aiAnalysisLoading: false,
    loading: false,
    error: null,
    selectedIndicator: null,
    sidebarOpen: true,
    timeRange: '7d' as const,
    detailPanelCardId: null,
    fetchIndicators: async () => {},
    fetchHOPIScore: async () => {},
    fetchSystemStatus: async () => {},
    refreshAll: async () => {},
    runSynthesis: async () => {},
    runAIAnalysis: async () => {},
    setSelectedIndicator: () => {},
    setSidebarOpen: () => {},
    setTimeRange: () => {},
    setDetailPanelCardId: () => {},
    updateIndicator: () => {},
    setError: () => {},
    updateChecklistProgress: () => {},
  };

  describe('selectIndicatorsByDomain', () => {
    it('filters indicators by domain', () => {
      const result = selectIndicatorsByDomain('economy')(state);
      expect(result).toHaveLength(2);
      expect(result.every(i => i.domain === 'economy')).toBe(true);
    });

    it('returns empty for domain with no indicators', () => {
      const result = selectIndicatorsByDomain('social_cohesion')(state);
      expect(result).toHaveLength(0);
    });
  });

  describe('selectCriticalIndicators', () => {
    it('returns only critical indicators that are red', () => {
      const result = selectCriticalIndicators(state);
      expect(result).toHaveLength(2);
      expect(result.every(i => i.critical && i.status.level === 'red')).toBe(true);
    });
  });

  describe('selectIndicatorCounts', () => {
    it('counts indicators by level', () => {
      const counts = selectIndicatorCounts(state);
      expect(counts.green).toBe(2);
      expect(counts.amber).toBe(1);
      expect(counts.red).toBe(2);
      expect(counts.unknown).toBe(0);
    });
  });

  describe('selectTightenUpActive', () => {
    it('returns true when systemPhase is tighten-up', () => {
      const tightenState = { ...state, systemPhase: 'tighten-up' as const };
      expect(selectTightenUpActive(tightenState)).toBe(true);
    });

    it('returns false when systemPhase is a number', () => {
      const normalState = {
        ...state,
        systemPhase: 2 as number | 'tighten-up',
        indicators: [
          makeIndicator({ id: 'a', status: { level: 'red', value: 1, lastUpdate: '', dataSource: 'MOCK' } }),
          makeIndicator({ id: 'b', status: { level: 'amber', value: 2, lastUpdate: '', dataSource: 'MOCK' } }),
        ],
      };
      expect(selectTightenUpActive(normalState)).toBe(false);
    });

    it('returns false when no indicators are red', () => {
      const greenState = {
        ...state,
        indicators: [
          makeIndicator({ id: 'a', status: { level: 'green', value: 1, lastUpdate: '', dataSource: 'MOCK' } }),
        ],
      };
      expect(selectTightenUpActive(greenState)).toBe(false);
    });
  });
});
