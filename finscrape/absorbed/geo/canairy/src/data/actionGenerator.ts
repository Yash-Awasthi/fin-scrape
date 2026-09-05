/**
 * Action Generator
 *
 * Generates a prioritized action list from indicators, AI insights, and phase tasks.
 * Actions are deduplicated and sorted by urgency.
 */

import { IndicatorData } from '../types';
import { PhaseTask, TASK_TIERS, getVisibleTiers } from './phaseTasks';
import { getCardImpactLine } from './indicatorDisplay';

// ============================================================================
// TYPES
// ============================================================================

export type ActionUrgency = 'now' | 'today' | 'this-week';
export type ActionEffort = 'quick' | 'moderate' | 'involved';

export interface ActionContext {
  dataPoints?: string[];      // Specific metrics/numbers backing the action
  sources?: string[];         // Source names (e.g., "BLS", "Treasury")
  indicators?: string[];      // Indicator IDs that triggered this action
  historicalNote?: string;    // "Last time this happened..."
  consequence?: string;       // What happens if you don't act
}

export interface ActionItem {
  id: string;
  task: string;
  why: string;
  timeEstimate: string;
  urgency: ActionUrgency;
  priority: number; // 1 = most urgent
  effort: ActionEffort;
  completed: boolean;
  sourceInsightId?: string;
  sourceDomains: string[];
  phaseTask?: boolean;
  phaseTaskId?: string;
  tierName?: string;
  context?: ActionContext;    // Rich context for expansion
}

// ============================================================================
// INDICATOR-DRIVEN FALLBACK ACTIONS
// ============================================================================

// Maps indicator IDs to specific actions when that indicator is elevated
interface IndicatorAction {
  task: string;
  why: string;
  timeEstimate: string;
  effort: ActionEffort;
  context: ActionContext;
}

const INDICATOR_ACTIONS: Record<string, {
  amber: IndicatorAction;
  red: IndicatorAction;
}> = {
  'econ_02_grocery_cpi': {
    amber: {
      task: 'Add extra staples to your next grocery run',
      why: 'Prices trending up — good time to stock pantry basics',
      timeEstimate: '10 min extra',
      effort: 'quick',
      context: {
        dataPoints: ['Food prices up 4-6% from last year'],
        sources: ['Bureau of Labor Statistics'],
        historicalNote: 'In 2022, families who stocked up early saved $150-200/month.',
        consequence: 'Same groceries cost 10-15% more next month.',
      },
    },
    red: {
      task: 'Stock up on kids\' snacks and pantry staples this week',
      why: 'Food prices spiking — grab what you need before prices jump again',
      timeEstimate: '~45 min',
      effort: 'moderate',
      context: {
        dataPoints: ['Food prices up 8%+ from last year', 'Prices rising week over week'],
        sources: ['Bureau of Labor Statistics', 'USDA'],
        historicalNote: 'During 2022 spike, pasta and cereal prices jumped 15% in a month.',
        consequence: 'Your usual grocery bill could be $50-75 higher next month.',
      },
    },
  },
  'market_01_intraday_swing': {
    amber: {
      task: 'Keep $300-500 cash at home just in case',
      why: 'Markets choppy — good to have cash if card systems glitch',
      timeEstimate: '~15 min',
      effort: 'quick',
      context: {
        dataPoints: ['Stock market swinging more than usual'],
        sources: ['NYSE'],
        historicalNote: 'Remember when Venmo and card readers went down? Cash saved the day.',
        consequence: 'If your bank app goes down, you\'ll need cash for gas and groceries.',
      },
    },
    red: {
      task: 'Get some extra cash from ATM this week',
      why: 'Markets really stressed — cash is king if banks have issues',
      timeEstimate: '~15 min',
      effort: 'quick',
      context: {
        dataPoints: ['Market swings bigger than 2008 levels some days'],
        sources: ['NYSE', 'Federal Reserve'],
        historicalNote: 'During the 2023 bank scare, ATM lines got long fast.',
        consequence: 'If your bank has problems, digital payments might not work for days.',
      },
    },
  },
  'econ_01_treasury_tail': {
    amber: {
      task: 'Review and rebalance any bond holdings',
      why: 'Treasury auction stress signals rising rates',
      timeEstimate: '~30 min',
      effort: 'moderate',
      context: {
        dataPoints: ['Auction tail exceeding 3 bps', 'Dealer takedown elevated'],
        sources: ['Treasury Direct', 'Federal Reserve'],
        historicalNote: 'Large tails preceded the 2023 regional bank failures by weeks.',
        consequence: 'Bond values may drop 5-10% as rates adjust upward.',
      },
    },
    red: {
      task: 'Withdraw cash and avoid major purchases this week',
      why: 'Severe auction stress — banking system under pressure',
      timeEstimate: '~1 hr',
      effort: 'moderate',
      context: {
        dataPoints: ['Auction tail exceeding 7 bps', 'Primary dealer stress visible'],
        sources: ['Treasury Direct', 'Federal Reserve'],
        historicalNote: 'Severe auction failures have preceded every major banking crisis.',
        consequence: 'Credit tightening could freeze lending and cause bank runs.',
      },
    },
  },
  'supply_pharmacy_shortage': {
    amber: {
      task: 'Refill kids\' prescriptions and grab extra OTC meds',
      why: 'Some medications harder to find — good to have backups',
      timeEstimate: '~15 min',
      effort: 'quick',
      context: {
        dataPoints: ['More medications on FDA shortage list'],
        sources: ['FDA Drug Shortages Database'],
        historicalNote: 'Remember the kids\' Tylenol shortage in 2022? Had to check 4 stores.',
        consequence: 'Your pharmacy might be out when your kid spikes a fever at 2am.',
      },
    },
    red: {
      task: 'Call pharmacy and pediatrician about getting ahead on meds',
      why: 'Shortages getting serious — ask about 90-day supplies or alternatives',
      timeEstimate: '~30 min on phone',
      effort: 'moderate',
      context: {
        dataPoints: ['Major shortage affecting common medications'],
        sources: ['FDA', 'ASHP'],
        historicalNote: 'During COVID, some families drove to 5+ pharmacies for kids\' meds.',
        consequence: 'Really stressful when your kid needs Amoxicillin and nobody has it.',
      },
    },
  },
  'hormuz_war_risk': {
    amber: {
      task: 'Fill up the car next time you\'re at half tank',
      why: 'Oil shipping getting riskier — gas prices might jump soon',
      timeEstimate: '~10 min',
      effort: 'quick',
      context: {
        dataPoints: ['Shipping insurance costs up in the Gulf region'],
        sources: ['Energy Information Administration'],
        historicalNote: 'When tankers got attacked in 2019, gas jumped 25 cents overnight.',
        consequence: 'Could be paying 30-50 cents more per gallon next week.',
      },
    },
    red: {
      task: 'Fill up both cars this weekend',
      why: 'Oil supply seriously at risk — prices about to spike',
      timeEstimate: '~20 min',
      effort: 'quick',
      context: {
        dataPoints: ['Major oil shipping route at risk of closure'],
        sources: ['Energy Information Administration', 'Reuters'],
        historicalNote: 'The 1973 oil crisis had people waiting in line for hours for gas.',
        consequence: 'Your commute could cost 50% more by next month.',
      },
    },
  },
  'oil_01_russian_brics': {
    amber: {
      task: 'Lock in energy prices if possible',
      why: 'De-dollarization accelerating — energy prices less stable',
      timeEstimate: '~30 min',
      effort: 'moderate',
      context: {
        dataPoints: ['BRICS+ settling 30%+ of crude in non-USD', 'Dollar index volatile'],
        sources: ['BIS', 'Energy & Clean Air Research'],
        historicalNote: 'Currency shifts historically precede commodity price restructuring.',
        consequence: 'Energy costs become unpredictable as dollar loses pricing power.',
      },
    },
    red: {
      task: 'Fill heating oil tank and consider backup heating',
      why: 'Oil markets restructuring — supply volatility increasing',
      timeEstimate: '~1 hr',
      effort: 'moderate',
      context: {
        dataPoints: ['50%+ of crude now non-USD settled', 'Supply chain bifurcation'],
        sources: ['BIS', 'Reuters'],
        historicalNote: 'Market restructuring in the 1970s caused decade-long instability.',
        consequence: 'Your heating costs could become unpredictable season to season.',
      },
    },
  },
  'taiwan_pla_activity': {
    amber: {
      task: 'If you need a new laptop or phone soon, maybe don\'t wait',
      why: 'Taiwan chip supply could get disrupted — electronics might get pricier',
      timeEstimate: '~30 min research',
      effort: 'moderate',
      context: {
        dataPoints: ['More Chinese military flights near Taiwan than usual'],
        sources: ['Taiwan Defense Ministry'],
        historicalNote: 'The 2021 chip shortage meant 6-month waits for cars and PS5s.',
        consequence: 'Prices on laptops, phones, even appliances could jump 20-30%.',
      },
    },
    red: {
      task: 'Buy that laptop/tablet/phone you\'ve been putting off',
      why: 'Chip supply seriously at risk — prices will spike if things escalate',
      timeEstimate: '~1 hr',
      effort: 'moderate',
      context: {
        dataPoints: ['Military activity near Taiwan at crisis levels'],
        sources: ['Taiwan Defense Ministry', 'Reuters'],
        historicalNote: 'Taiwan makes 90% of advanced chips. When supply drops, prices double.',
        consequence: 'That laptop could cost $500 more in a few months, if you can find one.',
      },
    },
  },
  'ice_detention_surge': {
    amber: {
      task: 'Ensure all documents are accessible and organized',
      why: 'Enforcement expanding — documentation matters more',
      timeEstimate: '~45 min',
      effort: 'moderate',
      context: {
        dataPoints: ['Detention capacity expanding', 'Field operations increasing'],
        sources: ['TRAC Immigration', 'DHS'],
        historicalNote: 'Document preparation has prevented wrongful detention in past surges.',
        consequence: 'Delays proving status can mean extended detention.',
      },
    },
    red: {
      task: 'Know your rights and have lawyer contact ready',
      why: 'Aggressive enforcement — be prepared for encounters',
      timeEstimate: '~30 min',
      effort: 'moderate',
      context: {
        dataPoints: ['Detention at capacity', 'Workplace raids reported'],
        sources: ['TRAC Immigration', 'ACLU'],
        historicalNote: 'During 2018-2019 surges, having legal contacts prevented many issues.',
        consequence: 'Encounters without preparation can lead to extended detention.',
      },
    },
  },
  'grid_01_pjm_outages': {
    amber: {
      task: 'Charge phones and tablets, know where flashlights are',
      why: 'Power outages more likely than usual — be ready for a few hours without',
      timeEstimate: '~10 min',
      effort: 'quick',
      context: {
        dataPoints: ['More grid emergencies than last year'],
        sources: ['Dept of Energy'],
        historicalNote: 'Even short outages are rough with kids — no screens, no fridge.',
        consequence: 'Phones die, kids melt down, frozen food starts to thaw.',
      },
    },
    red: {
      task: 'Prep for a possible day or two without power',
      why: 'Major grid stress — stock up on easy meals and activities for kids',
      timeEstimate: '~30 min',
      effort: 'moderate',
      context: {
        dataPoints: ['Rolling blackouts possible in your area'],
        sources: ['Dept of Energy', 'Your utility company'],
        historicalNote: 'Texas 2021: families without prep suffered for days.',
        consequence: 'No heat/AC, spoiled food, cranky kids with dead iPads.',
      },
    },
  },
  'bio_01_h2h_countries': {
    amber: {
      task: 'Review health supplies and N95 stock',
      why: 'Novel pathogen spreading — prepare for health measures',
      timeEstimate: '~30 min',
      effort: 'quick',
      context: {
        dataPoints: ['H2H transmission confirmed', '3+ countries affected'],
        sources: ['WHO Disease Outbreak News', 'CDC'],
        historicalNote: 'COVID N95 masks sold out for months after initial spread.',
        consequence: 'PPE shortages leave you exposed during peak transmission.',
      },
    },
    red: {
      task: 'Activate health phase protocols',
      why: 'Pandemic conditions — stock up and prepare to isolate',
      timeEstimate: '~2 hrs',
      effort: 'involved',
      context: {
        dataPoints: ['Sustained community spread', 'WHO emergency declared'],
        sources: ['WHO', 'CDC'],
        historicalNote: 'COVID lockdowns happened within weeks of sustained spread.',
        consequence: 'Isolation without supplies means dependence on disrupted supply chains.',
      },
    },
  },
  'cyber_01_cisa_kev': {
    amber: {
      task: 'Update all devices and review security',
      why: 'Attack surface expanding — patch everything',
      timeEstimate: '~45 min',
      effort: 'moderate',
      context: {
        dataPoints: ['10+ new KEVs this month', 'Active exploitation confirmed'],
        sources: ['CISA KEV Catalog'],
        historicalNote: 'Colonial Pipeline was hit through a single unpatched vulnerability.',
        consequence: 'Ransomware can lock all your files, demand thousands in payment.',
      },
    },
    red: {
      task: 'Update everything, enable 2FA everywhere',
      why: 'Active infrastructure exploitation — secure your accounts',
      timeEstimate: '~1 hr',
      effort: 'moderate',
      context: {
        dataPoints: ['Critical infrastructure targeted', 'Mass exploitation underway'],
        sources: ['CISA', 'FBI'],
        historicalNote: 'NotPetya caused $10B in damages in a single day globally.',
        consequence: 'Account takeover, identity theft, or ransomware attack.',
      },
    },
  },
  'national_guard_metros': {
    amber: {
      task: 'Review and update emergency rally points',
      why: 'Guard active in metros — plan around disruptions',
      timeEstimate: '~20 min',
      effort: 'quick',
      context: {
        dataPoints: ['Guard activated in 2+ metros', 'Movement restrictions possible'],
        sources: ['National Guard Bureau', 'Local news'],
        historicalNote: '2020 activations caused curfews and closed businesses for weeks.',
        consequence: 'Getting home or to work could become complicated.',
      },
    },
    red: {
      task: 'Avoid affected areas, have go-bags ready',
      why: 'Multiple cities affected — movement may be restricted',
      timeEstimate: '~1 hr',
      effort: 'moderate',
      context: {
        dataPoints: ['5+ metro areas affected', 'Federal coordination active'],
        sources: ['National Guard', 'DHS'],
        historicalNote: 'Extended deployments in 2020 affected daily life for months.',
        consequence: 'Curfews, checkpoints, and closed roads disrupt normal routines.',
      },
    },
  },
  'luxury_01_collapse': {
    amber: {
      task: 'Reduce discretionary spending and build cash reserve',
      why: 'Luxury sector decline signals consumer stress ahead',
      timeEstimate: '~30 min',
      effort: 'moderate',
      context: {
        dataPoints: ['Luxury retail down 10-15%', 'High-end layoffs starting'],
        sources: ['Bloomberg Consumer', 'Retail analytics'],
        historicalNote: 'Luxury declines preceded both 2008 and 2020 recessions by 3-6 months.',
        consequence: 'Recession typically follows — job losses spread to all sectors.',
      },
    },
    red: {
      task: 'Pause major purchases and maximize emergency fund',
      why: 'Luxury collapse indicates recession is here or imminent',
      timeEstimate: '~1 hr',
      effort: 'moderate',
      context: {
        dataPoints: ['Luxury sector down 25%+', 'Mass layoffs in discretionary retail'],
        sources: ['Bloomberg', 'BLS'],
        historicalNote: 'In 2008, recession was officially declared 6 months after luxury peaked.',
        consequence: 'Job losses accelerate; those without savings face severe hardship.',
      },
    },
  },
};

// ============================================================================
// ACTION GENERATION
// ============================================================================

export function generateActionList(
  indicators: IndicatorData[],
  completedIds: Set<string>,
  systemPhase: number = 2,
): ActionItem[] {
  const actions: ActionItem[] = [];

  // SOURCE 1: Phase tasks that should be visible
  const visibleTiers = getVisibleTiers(systemPhase);
  for (const tier of visibleTiers) {
    // Only add incomplete tasks from the first incomplete tier (focus)
    const incompleteTasks = tier.tasks.filter(t => !completedIds.has(t.id));
    if (incompleteTasks.length > 0) {
      // Add up to 3 tasks from this tier
      for (const task of incompleteTasks.slice(0, 3)) {
        actions.push({
          id: `phase-${task.id}`,
          task: task.title,
          why: task.description.split('.')[0], // First sentence
          timeEstimate: task.timeEstimate,
          urgency: 'this-week',
          priority: 3,
          effort: task.effort === 'weekend' || task.effort === 'project' ? 'involved' : task.effort === 'afternoon' ? 'moderate' : 'quick',
          completed: false,
          phaseTask: true,
          phaseTaskId: task.id,
          tierName: tier.title,
          sourceDomains: task.domains,
        });
      }
      // Stop after first incomplete tier to maintain focus
      break;
    }
  }

  // SOURCE 2: Indicator-driven actions (higher priority for elevated indicators)
  const elevatedIndicators = indicators.filter(i => i.status.level !== 'green');
  const sortedIndicators = [...elevatedIndicators].sort((a, b) => {
    const levelPriority: Record<string, number> = { red: 0, amber: 1, green: 2, unknown: 3 };
    return (levelPriority[a.status.level] ?? 3) - (levelPriority[b.status.level] ?? 3);
  });

  for (const indicator of sortedIndicators.slice(0, 5)) {
    const actionDef = INDICATOR_ACTIONS[indicator.id];
    if (!actionDef) continue;

    const level = indicator.status.level as 'amber' | 'red';
    const action = actionDef[level];
    if (!action) continue;

    // Skip if similar task already exists
    const similarExists = actions.some(a =>
      a.task.toLowerCase().includes(action.task.toLowerCase().split(' ').slice(0, 3).join(' '))
    );
    if (similarExists) continue;

    const actionId = `indicator-${indicator.id}-${level}`;
    if (completedIds.has(actionId)) continue;

    actions.push({
      id: actionId,
      task: action.task,
      why: action.why,
      timeEstimate: action.timeEstimate,
      urgency: level === 'red' ? 'today' : 'this-week',
      priority: level === 'red' ? 1 : 2,
      effort: action.effort,
      completed: false,
      sourceDomains: [indicator.domain],
      context: {
        ...action.context,
        indicators: [indicator.id],
      },
    });
  }

  // Deduplicate by similar task text
  const deduplicated = deduplicateActions(actions);

  // Sort: now > today > this-week, then by priority
  return deduplicated.sort((a, b) => {
    const urgencyOrder = { 'now': 0, 'today': 1, 'this-week': 2 };
    const urgencyDiff = urgencyOrder[a.urgency] - urgencyOrder[b.urgency];
    if (urgencyDiff !== 0) return urgencyDiff;
    return a.priority - b.priority;
  });
}

function deduplicateActions(actions: ActionItem[]): ActionItem[] {
  const seen = new Set<string>();
  const result: ActionItem[] = [];

  for (const action of actions) {
    // Create a normalized key from first 3 significant words
    const words = action.task.toLowerCase()
      .replace(/[^\w\s]/g, '')
      .split(/\s+/)
      .filter(w => w.length > 3)
      .slice(0, 3)
      .join(' ');

    if (!seen.has(words)) {
      seen.add(words);
      result.push(action);
    }
  }

  return result;
}

// ============================================================================
// URGENCY HELPERS
// ============================================================================

export function getUrgencyLabel(urgency: ActionUrgency): string {
  switch (urgency) {
    case 'now': return 'Now';
    case 'today': return 'Today';
    case 'this-week': return 'This week';
  }
}

export function getUrgencyStyles(urgency: ActionUrgency): string {
  switch (urgency) {
    case 'now': return 'text-red-400 bg-red-500/10';
    case 'today': return 'text-amber-400 bg-amber-500/10';
    case 'this-week': return 'text-emerald-400 bg-emerald-500/10';
  }
}

// ============================================================================
// STATUS-BASED OUTCOME SENTENCE
// ============================================================================

export function generateOutcomeSentence(
  indicators: IndicatorData[],
  systemPhase: number,
): string {
  const redCount = indicators.filter(i => i.status.level === 'red').length;
  const amberCount = indicators.filter(i => i.status.level === 'amber').length;

  if (redCount >= 2) {
    return 'Multiple systems under stress. Focus on the checklist below — these are your priorities for today.';
  }

  if (redCount === 1) {
    const redIndicator = indicators.find(i => i.status.level === 'red');
    const impact = redIndicator ? getCardImpactLine(redIndicator.id, 'red') : '';
    return impact
      ? `${impact}. Complete the high-priority actions today.`
      : 'One system in critical state. Handle the urgent items first.';
  }

  if (amberCount >= 10) {
    return 'Elevated conditions across multiple systems. Good time to work through your preparation checklist.';
  }

  if (amberCount >= 5) {
    return 'Some systems showing stress. A good week to stock up on essentials and check your preparedness.';
  }

  if (amberCount > 0) {
    return 'Things are mostly stable. A few items worth attention this week — see the list below.';
  }

  return 'All systems green. A good time to work ahead on your preparedness checklist.';
}

// ============================================================================
// STATUS HEADING
// ============================================================================

export function getStatusHeading(indicators: IndicatorData[]): {
  heading: string;
  color: string;
} {
  const redCount = indicators.filter(i => i.status.level === 'red').length;
  const amberCount = indicators.filter(i => i.status.level === 'amber').length;

  if (redCount >= 2) {
    return { heading: 'Phase 7', color: 'text-red-400' };
  }
  if (redCount === 1) {
    return { heading: 'Phase 5', color: 'text-red-400' };
  }
  if (amberCount >= 10) {
    return { heading: 'Caution', color: 'text-amber-400' };
  }
  if (amberCount > 0) {
    return { heading: 'Watch', color: 'text-amber-400' };
  }
  return { heading: 'All Clear', color: 'text-emerald-400' };
}
