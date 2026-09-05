import { create } from 'zustand';
import { devtools, subscribeWithSelector } from 'zustand/middleware';
import { IndicatorData, HOPIScore, SystemStatus, Phase } from '../types';
import { apiService } from '../services/api';
import { synthesizeCards, SynthesisOutput, ScoredPattern, scoredPatternToCardData } from '../services/synthesis';
import { synthesizeBatch, SynthesisResult } from '../services/synthesis';
import { analyzeIndicators, generateFallbackInsights, AIAnalysisResult, AIInsight, getDefaultUserContext, computeSystemPhase } from '../services/synthesis/aiAnalysis';

// Track if we've logged the fallback message
let hasLoggedFallbackMessage = false;

interface ChecklistProgress {
  completedPhase: number;
  currentPhaseProgress: number;
  completedItems: string[];
}

interface AppState {
  // Data
  indicators: IndicatorData[];
  hopiScore: HOPIScore | null;
  currentPhase: Phase | null;
  systemStatus: SystemStatus | null;
  alerts: any[];

  // Phase & Checklist
  systemPhase: number | 'tighten-up';
  checklistProgress: ChecklistProgress | null;

  // Synthesis
  synthesisOutput: SynthesisOutput | null;
  synthesisResults: Map<string, SynthesisResult>;
  synthesisLoading: boolean;

  // AI Analysis (true Claude-driven insights)
  aiAnalysis: AIAnalysisResult | null;
  aiAnalysisLoading: boolean;

  // UI State
  loading: boolean;
  error: string | null;
  usingFallbackData: boolean;  // True when API failed and using mock data
  lastSuccessfulFetch: Date | null;  // Last time live data was fetched
  selectedIndicator: string | null;
  sidebarOpen: boolean;
  timeRange: '24h' | '7d' | '30d' | '90d';
  detailPanelCardId: string | null;  // Card ID shown in detail panel

  // Actions
  fetchIndicators: () => Promise<void>;
  fetchHOPIScore: () => Promise<void>;
  fetchSystemStatus: () => Promise<void>;
  refreshAll: () => Promise<void>;
  runSynthesis: () => Promise<void>;
  runAIAnalysis: () => Promise<void>;
  setSelectedIndicator: (id: string | null) => void;
  setSidebarOpen: (open: boolean) => void;
  setTimeRange: (range: '24h' | '7d' | '30d' | '90d') => void;
  setDetailPanelCardId: (id: string | null) => void;
  updateIndicator: (id: string, data: Partial<IndicatorData>) => void;
  setError: (error: string | null) => void;
  updateChecklistProgress: (itemId: string, completed: boolean) => void;
}

export const useStore = create<AppState>()(
  devtools(
    subscribeWithSelector((set, get) => ({
      // Initial state
      indicators: [],
      hopiScore: null,
      currentPhase: null,
      systemStatus: null,
      alerts: [],
      systemPhase: 1,
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
      usingFallbackData: false,
      lastSuccessfulFetch: null,
      selectedIndicator: null,
      sidebarOpen: true,
      timeRange: '7d',
      detailPanelCardId: null,

      // Actions
      fetchIndicators: async () => {
        set({ loading: true, error: null });
        try {
          const response = await apiService.getIndicators();
          set({
            indicators: response.data,
            loading: false,
            usingFallbackData: response.isUsingFallback,
            lastSuccessfulFetch: response.lastSuccessfulFetch || null
          });
        } catch (error) {
          set({
            error: 'Failed to fetch indicators',
            loading: false,
            usingFallbackData: true
          });
        }
      },

      fetchHOPIScore: async () => {
        try {
          const hopiResponse = await apiService.getHOPIScore();
          const currentPhase = await apiService.getCurrentPhase();

          // Calculate system phase using centralized logic
          const { indicators, usingFallbackData } = get();
          const systemPhase = computeSystemPhase(indicators);

          set({
            hopiScore: hopiResponse.data,
            currentPhase,
            systemPhase,
            usingFallbackData: usingFallbackData || hopiResponse.isUsingFallback
          });
        } catch (error) {
          console.error('Failed to fetch HOPI score:', error);
        }
      },

      fetchSystemStatus: async () => {
        try {
          const systemStatus = await apiService.getSystemStatus();
          set({ systemStatus });
        } catch (error) {
          console.error('Failed to fetch system status:', error);
        }
      },

      refreshAll: async () => {
        const { fetchIndicators, fetchHOPIScore, fetchSystemStatus, runSynthesis, runAIAnalysis } = get();
        await Promise.all([
          fetchIndicators(),
          fetchHOPIScore(),
          fetchSystemStatus(),
        ]);
        // Run both synthesis engines in parallel
        await Promise.all([
          runSynthesis(),
          runAIAnalysis(),
        ]);
      },

      runSynthesis: async () => {
        const { indicators, systemPhase } = get();

        if (indicators.length === 0) return;

        set({ synthesisLoading: true });

        try {
          // Convert 'tighten-up' to numeric phase for synthesis
          const phaseNum = systemPhase === 'tighten-up' ? 3 : systemPhase;
          // Run pattern detection and scoring
          const synthesisOutput = synthesizeCards(indicators, phaseNum);
          set({ synthesisOutput });

          // Optionally enhance with Claude LLM (if API key configured)
          const allPatterns = [
            synthesisOutput.leadCard,
            ...synthesisOutput.secondaryCards,
            ...synthesisOutput.compactRows.slice(0, 3),
          ].filter(Boolean) as ScoredPattern[];

          if (allPatterns.length > 0) {
            const results = await synthesizeBatch(allPatterns, indicators);
            set({ synthesisResults: results });
          }
        } catch (error) {
          console.error('Synthesis failed:', error);
        } finally {
          set({ synthesisLoading: false });
        }
      },

      runAIAnalysis: async () => {
        const { indicators, systemPhase, checklistProgress } = get();

        if (indicators.length === 0) return;

        set({ aiAnalysisLoading: true });

        try {
          // Build user context from current state
          const completedItems = checklistProgress?.completedItems?.length ?? 4;
          const totalItems = 12; // Phase 1 default
          // Convert 'tighten-up' to numeric phase for context building
          const phaseNum = systemPhase === 'tighten-up' ? 3 : systemPhase;
          const userContext = getDefaultUserContext(phaseNum, completedItems, totalItems);

          // Try to get AI-driven analysis from Claude
          const result = await analyzeIndicators(indicators, userContext);

          if (result) {
            console.log('AI Analysis complete:', result.insights.length, 'insights generated');
            set({ aiAnalysis: result });
          } else {
            // Fall back to heuristic-based insights
            if (!hasLoggedFallbackMessage) {
              console.info('Using pre-built insights');
              hasLoggedFallbackMessage = true;
            }
            const fallback = generateFallbackInsights(indicators);
            set({ aiAnalysis: fallback });
          }
        } catch (error) {
          console.error('AI Analysis failed:', error);
          // Fall back to heuristic insights on error
          const fallback = generateFallbackInsights(indicators);
          set({ aiAnalysis: fallback });
        } finally {
          set({ aiAnalysisLoading: false });
        }
      },

      setSelectedIndicator: (id) => set({ selectedIndicator: id }),
      setSidebarOpen: (open) => set({ sidebarOpen: open }),
      setTimeRange: (range) => set({ timeRange: range }),
      setDetailPanelCardId: (id) => set({ detailPanelCardId: id }),
      
      updateIndicator: (id, data) => {
        set((state) => ({
          indicators: state.indicators.map((ind) =>
            ind.id === id ? { ...ind, ...data } : ind
          ),
        }));
      },

      setError: (error) => set({ error }),

      updateChecklistProgress: (itemId, completed) => {
        set((state) => {
          const currentItems = state.checklistProgress?.completedItems ?? [];
          const newItems = completed
            ? [...currentItems, itemId]
            : currentItems.filter(id => id !== itemId);

          return {
            checklistProgress: {
              ...state.checklistProgress!,
              completedItems: newItems,
              currentPhaseProgress: Math.min(100, Math.round((newItems.length / 12) * 100)),
            },
          };
        });
      },
    }))
  )
);

// Selectors
export const selectIndicatorsByDomain = (domain: string) => (state: AppState) =>
  state.indicators.filter((ind) => ind.domain === domain);

export const selectCriticalIndicators = (state: AppState) =>
  state.indicators.filter((ind) => ind.critical && ind.status.level === 'red');

export const selectIndicatorCounts = (state: AppState) => {
  const counts = { green: 0, amber: 0, red: 0, unknown: 0 };
  state.indicators.forEach((ind) => {
    counts[ind.status.level]++;
  });
  return counts;
};

export const selectTightenUpActive = (state: AppState) => {
  return state.systemPhase === 'tighten-up';
};

export const selectSynthesisCards = (state: AppState) => {
  const { synthesisOutput, synthesisResults } = state;

  if (!synthesisOutput) return null;

  // Convert scored patterns to card data with enhanced content
  const enhanceCard = (scored: ScoredPattern | null) => {
    if (!scored) return null;

    const baseCard = scoredPatternToCardData(scored);
    const enhanced = synthesisResults.get(scored.pattern.id);

    if (enhanced) {
      const urgency: 'today' | 'week' | 'knowing' =
        enhanced.urgencyTag === 'Do this today' ? 'today' :
        enhanced.urgencyTag === 'This week' ? 'week' : 'knowing';
      return {
        ...baseCard,
        headline: enhanced.headline,
        // Map enhanced fields to card structure
        whatsHappening: enhanced.body ? `Here's what I'm seeing: ${enhanced.body}` : baseCard.whatsHappening,
        whyItMatters: enhanced.whyItMatters || baseCard.whyItMatters,
        whatToDo: enhanced.whatToDo || baseCard.whatToDo,
        urgency,
      };
    }

    return baseCard;
  };

  return {
    leadCard: enhanceCard(synthesisOutput.leadCard),
    secondaryCards: synthesisOutput.secondaryCards.map(s => enhanceCard(s)).filter(Boolean),
    compactRows: synthesisOutput.compactRows.map(s => ({
      id: s.pattern.id,
      text: s.pattern.headlineTemplate,
      domain: s.pattern.domains[0] || 'unknown',
      href: s.pattern.actionHref,
    })),
  };
};

// Select AI-generated insights
export const selectAIInsights = (state: AppState) => {
  return state.aiAnalysis;
};

// Select the lead AI insight (highest urgency)
export const selectLeadAIInsight = (state: AppState): AIInsight | null => {
  const analysis = state.aiAnalysis;
  if (!analysis || analysis.insights.length === 0) return null;

  // Priority order: today > week > knowing
  const todayInsights = analysis.insights.filter(i => i.urgency === 'today');
  if (todayInsights.length > 0) return todayInsights[0];

  const weekInsights = analysis.insights.filter(i => i.urgency === 'week');
  if (weekInsights.length > 0) return weekInsights[0];

  return analysis.insights[0];
};

// Select secondary AI insights (expanded to show more)
export const selectSecondaryAIInsights = (state: AppState): AIInsight[] => {
  const analysis = state.aiAnalysis;
  if (!analysis || analysis.insights.length <= 1) return [];

  const lead = selectLeadAIInsight(state);
  return analysis.insights.filter(i => i.id !== lead?.id).slice(0, 6);
};