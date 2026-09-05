// Core types for Canairy resilience monitoring system

export type AlertLevel = 'green' | 'amber' | 'red' | 'unknown';

export type IndicatorStatus = {
  level: AlertLevel;
  value: number | string | null;
  trend?: 'up' | 'down' | 'stable' | 'unknown';
  lastUpdate: string;
  dataSource: 'LIVE' | 'MANUAL' | 'MOCK' | 'UNAVAILABLE';
  daysSustained?: number;  // How many days at current level
};

// Baseline data for comparison
export interface IndicatorBaseline {
  value: number;
  period: string;  // e.g., "Jan 2026" or "12-month avg"
}

export type Domain =
  | 'economy'
  | 'jobs_labor'
  | 'rights_governance'
  | 'security_infrastructure'
  | 'oil_axis'
  | 'ai_window'
  | 'global_conflict'
  | 'domestic_control'
  | 'supply_chain'
  | 'energy'
  | 'social_cohesion'
  | 'water_infrastructure'
  | 'telecommunications'
  | 'housing_mortgage'
  | 'travel_mobility'
  | 'aviation'
  | 'cult_meta';

export const DOMAIN_META: Record<Domain, { label: string; weight: number; icon: string }> = {
  economy:                 { label: 'Economy',          weight: 1.0,  icon: 'DollarSign' },
  jobs_labor:              { label: 'Jobs & Labor',     weight: 1.0,  icon: 'Briefcase' },
  rights_governance:       { label: 'Rights & Gov',     weight: 1.1,  icon: 'Scale' },
  security_infrastructure: { label: 'Security & Infra', weight: 1.25, icon: 'ShieldAlert' },
  oil_axis:                { label: 'Oil Axis',         weight: 1.0,  icon: 'Fuel' },
  ai_window:               { label: 'AI Window',        weight: 1.0,  icon: 'Brain' },
  global_conflict:         { label: 'Global Conflict',  weight: 1.25, icon: 'Globe' },
  domestic_control:        { label: 'Domestic Control', weight: 1.2,  icon: 'Landmark' },
  supply_chain:            { label: 'Supply Chain',     weight: 1.0,  icon: 'Truck' },
  energy:                  { label: 'Energy',           weight: 1.1,  icon: 'Zap' },
  social_cohesion:         { label: 'Social Cohesion',  weight: 0.75, icon: 'Users' },
  water_infrastructure:    { label: 'Water',            weight: 0.9,  icon: 'Droplets' },
  telecommunications:      { label: 'Telecom',          weight: 0.9,  icon: 'Radio' },
  housing_mortgage:        { label: 'Housing',          weight: 0.9,  icon: 'Home' },
  travel_mobility:         { label: 'Travel',           weight: 0.8,  icon: 'Plane' },
  aviation:                { label: 'Aviation',         weight: 0.8,  icon: 'PlaneTakeoff' },
  cult_meta:               { label: 'Social Signals',   weight: 0.7,  icon: 'TrendingUp' },
};

export interface Indicator {
  id: string;
  name: string;
  domain: Domain;
  description: string;
  unit: string;
  thresholds: {
    green: { min?: number; max?: number };
    amber: { min?: number; max?: number };
    red: { min?: number; max?: number };
    threshold_amber?: number;
    threshold_red?: number;
  };
  critical?: boolean;
  greenFlag?: boolean;
  enabled?: boolean;
  unavailable?: boolean; // Data source temporarily unavailable - gray out in UI
  dataSource: string;
  sourceUrl?: string; // Link to the official data source for transparency
  updateFrequency: string;
  metadata?: Record<string, any>;
}

export interface IndicatorData extends Indicator {
  status: IndicatorStatus;
  history?: DataPoint[];

  // Extended context for AI analysis
  baseline?: IndicatorBaseline;
  previousStatus?: AlertLevel;
  statusChangedDate?: string;  // ISO date string
  source?: string;  // Human-readable source name (e.g., "BLS", "NERC")
}

export interface DataPoint {
  timestamp: string;
  value: number;
  level: AlertLevel;
}

export interface HOPIScore {
  score: number;
  confidence: number;
  phase: number;
  targetPhase: number;
  domains: Record<Domain, DomainScore>;
  timestamp: string;
}

export interface DomainScore {
  score: number;
  weight: number;
  indicators: string[];
  criticalAlerts: string[];
}

export interface Phase {
  number: number;
  name: string;
  description: string;
  triggers: string[];
  actions: string[];
  color: string;
}

export interface SystemStatus {
  operational: boolean;
  lastUpdate: string;
  activeAlerts: number;
  dataQuality: number;
  message?: string;
}

export interface EmergencyProcedure {
  id: string;
  title: string;
  phase: number;
  steps: string[];
  priority: 'immediate' | 'urgent' | 'standard';
  completed?: boolean;
}

export interface ChartConfig {
  type: 'line' | 'bar' | 'area' | 'doughnut';
  timeRange: '24h' | '7d' | '30d' | '90d';
  showThresholds: boolean;
  animated: boolean;
}

/**
 * User/household context for personalized AI analysis
 */
export interface UserContext {
  region: string;                    // "Central New Jersey"
  state: string;                     // "NJ"
  gridOperator: string;              // "PJM Interconnection"
  nearestMetro: string;              // "New York metro area"
  currentPhase: number;
  phaseTasksCompleted: number;
  phaseTasksTotal: number;
  householdDescription?: string;     // "Family with toddler"
}

/**
 * M-Phase (Migration Phase) for relocation task surfacing
 * Triggered by domestic control indicator conditions
 */
export type MPhaseLevel = 0 | 1 | 2;

export interface MPhaseInfo {
  level: MPhaseLevel;
  name: string;
  description: string;
  triggerReason: string;
}

export const M_PHASE_INFO: Record<MPhaseLevel, Omit<MPhaseInfo, 'level' | 'triggerReason'>> = {
  0: {
    name: 'Document Review',
    description: 'Passport and vital document review tasks surface',
  },
  1: {
    name: 'Visa Research',
    description: 'Begin researching relocation options',
  },
  2: {
    name: 'Trial Relocation',
    description: 'Test relocation logistics',
  },
};