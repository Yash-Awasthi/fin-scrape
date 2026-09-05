/**
 * Trust Architecture Types for Canairy
 *
 * These types support the "show your work" trust model where every
 * recommendation is backed by traceable evidence and explicit reasoning.
 */

import { EvidenceSignal } from '../data/sourceRegistry';

/**
 * Situation brief - narrative explaining what's happening
 */
export interface SituationBrief {
  /** 2-4 paragraphs explaining the current situation in plain language */
  narrative: string;
  /** Time horizon for the situation (e.g., "developing over the next 1-2 weeks") */
  timeHorizon: string;
  /** Historical comparison if applicable */
  historicalContext?: string;
  /** When this brief was generated */
  generatedAt: Date;
}

/**
 * Reasoning chain - how we connected evidence to recommendation
 */
export interface ReasoningChain {
  /** What we observe in the data */
  observation: string;
  /** How we interpret those observations */
  interpretation: string;
  /** What this means for the family */
  implication: string;
  /** Why we recommend this action */
  recommendation: string;
  /** What this reasoning depends on being true */
  assumptions: string[];
  /** What could make this analysis wrong */
  counterpoints: string[];
  /** What would change this recommendation */
  updateTriggers: string[];
}

/**
 * Action item with effort estimates
 */
export interface ActionItem {
  id: string;
  /** The specific task to do */
  task: string;
  /** Why this action matters */
  why: string;
  /** Effort level */
  effort: 'quick' | 'moderate' | 'involved';
  /** Human-readable time estimate */
  timeEstimate: string;
  /** How important this is */
  priority: 'critical' | 'recommended' | 'optional';
  /** Whether the user has completed it */
  completed?: boolean;
  /** Links to phase system if applicable */
  relatedPhase?: number;
}

/**
 * Card detail header info
 */
export interface CardDetailHeader {
  headline: string;
  urgency: 'today' | 'week' | 'knowing';
  confidence: 'high' | 'moderate' | 'low';
  lastUpdated: Date;
  domains: string[];
  signalCount: number;
}

/**
 * Full insight card with evidence trail
 * Extends the dashboard card with trust layer fields
 */
export interface InsightCardWithEvidence {
  // Dashboard display fields
  id: string;
  headline: string;
  body: string;
  urgency: 'today' | 'week' | 'knowing';
  domains: string[];
  indicatorIds: string[];
  severity: number;
  action?: {
    label: string;
    href: string;
  };

  // Trust layer fields (used in detail view)
  confidence: 'high' | 'moderate' | 'low';
  evidence: EvidenceSignal[];
  situationBrief: SituationBrief;
  reasoningChain: ReasoningChain;
  actions: ActionItem[];
  patternId: string;
  generatedAt: Date;
}

/**
 * Confidence level descriptions for display
 */
export const CONFIDENCE_DESCRIPTIONS: Record<
  'high' | 'moderate' | 'low',
  { label: string; description: string; color: string }
> = {
  high: {
    label: 'High confidence',
    description:
      '3+ corroborating sources from authoritative origins, consistent trend data',
    color: 'text-green-400',
  },
  moderate: {
    label: 'Moderate confidence',
    description:
      '1-2 sources, or sources are less authoritative, or data is preliminary',
    color: 'text-amber-400',
  },
  low: {
    label: 'Low confidence',
    description: 'Single source, unverified, or data is stale/incomplete',
    color: 'text-red-400',
  },
};

/**
 * Urgency level config
 */
export const URGENCY_CONFIG = {
  today: {
    label: 'Do this today',
    description: 'Time-sensitive action with a narrow window',
    color: 'text-red-400',
    bgColor: 'bg-red-500/10',
    borderColor: 'border-red-500/40',
  },
  week: {
    label: 'This week',
    description: 'Important but not immediately time-critical',
    color: 'text-amber-400',
    bgColor: 'bg-amber-500/10',
    borderColor: 'border-amber-500/40',
  },
  knowing: {
    label: 'Worth knowing',
    description: 'Informational - no immediate action required',
    color: 'text-olive-tertiary',
    bgColor: 'bg-white/5',
    borderColor: 'border-olive-hover',
  },
};

/**
 * Action effort config
 */
export const EFFORT_CONFIG = {
  quick: {
    label: '~15 min',
    description: 'Can be done right now',
    color: 'text-green-400',
  },
  moderate: {
    label: '~1 hour',
    description: 'Needs some dedicated time',
    color: 'text-amber-400',
  },
  involved: {
    label: '~half day',
    description: 'Significant effort required',
    color: 'text-red-400',
  },
};

/**
 * Action priority config
 */
export const PRIORITY_CONFIG = {
  critical: {
    label: 'Critical',
    description: 'Has a time window - do first',
    color: 'text-red-400',
    bgColor: 'bg-red-500/10',
  },
  recommended: {
    label: 'Recommended',
    description: 'Improves the situation',
    color: 'text-amber-400',
    bgColor: 'bg-amber-500/10',
  },
  optional: {
    label: 'Optional',
    description: 'Builds long-term resilience',
    color: 'text-olive-tertiary',
    bgColor: 'bg-white/5',
  },
};
