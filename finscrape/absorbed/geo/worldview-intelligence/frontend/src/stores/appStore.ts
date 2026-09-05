import { create } from 'zustand';
import type {
  LayerData,
  LayerVisibility,
  SelectedEntity,
  VisualMode,
  AnomalyAlert,
  SituationReport,
} from '../types';

interface AppState {
  layers: LayerData;
  layerVisibility: LayerVisibility;
  selectedEntity: SelectedEntity | null;
  visualMode: VisualMode;
  searchQuery: string;
  timelinePosition: number;
  isPlaying: boolean;
  anomalies: AnomalyAlert[];
  situationReport: SituationReport | null;
  leftPanelOpen: boolean;
  rightPanelOpen: boolean;

  setLayerData: (layer: keyof LayerData, data: LayerData[keyof LayerData]) => void;
  toggleLayer: (layer: keyof LayerVisibility) => void;
  setSelectedEntity: (entity: SelectedEntity | null) => void;
  setVisualMode: (mode: VisualMode) => void;
  setSearchQuery: (query: string) => void;
  setTimelinePosition: (position: number) => void;
  setIsPlaying: (playing: boolean) => void;
  addAnomaly: (anomaly: AnomalyAlert) => void;
  setSituationReport: (report: SituationReport | null) => void;
  toggleLeftPanel: () => void;
  toggleRightPanel: () => void;
}

export const useAppStore = create<AppState>((set) => ({
  layers: {
    aircraft: [],
    satellites: [],
    ships: [],
    earthquakes: [],
    conflicts: [],
    missiles: [],
    news: [],
    traffic: [],
    weather: [],
  },

  layerVisibility: {
    aircraft: true,
    satellites: true,
    ships: true,
    earthquakes: true,
    conflicts: true,
    missiles: true,
    news: true,
    traffic: true,
    weather: true,
  },

  selectedEntity: null,
  visualMode: 'tactical',
  searchQuery: '',
  timelinePosition: 1,
  isPlaying: true,
  anomalies: [],
  situationReport: null,
  leftPanelOpen: true,
  rightPanelOpen: false,

  setLayerData: (layer, data) =>
    set((state) => ({
      layers: { ...state.layers, [layer]: data },
    })),

  toggleLayer: (layer) =>
    set((state) => ({
      layerVisibility: {
        ...state.layerVisibility,
        [layer]: !state.layerVisibility[layer],
      },
    })),

  setSelectedEntity: (entity) =>
    set((state) => ({
      selectedEntity: entity,
      rightPanelOpen: entity ? true : state.rightPanelOpen,
    })),

  setVisualMode: (mode) => set({ visualMode: mode }),
  setSearchQuery: (query) => set({ searchQuery: query }),
  setTimelinePosition: (position) => set({ timelinePosition: position }),
  setIsPlaying: (playing) => set({ isPlaying: playing }),

  addAnomaly: (anomaly) =>
    set((state) => ({
      anomalies: [anomaly, ...state.anomalies].slice(0, 50),
    })),

  setSituationReport: (report) => set({ situationReport: report }),
  toggleLeftPanel: () => set((state) => ({ leftPanelOpen: !state.leftPanelOpen })),
  toggleRightPanel: () => set((state) => ({ rightPanelOpen: !state.rightPanelOpen })),
}));
