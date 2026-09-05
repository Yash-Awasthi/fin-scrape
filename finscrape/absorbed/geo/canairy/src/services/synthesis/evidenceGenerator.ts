/**
 * Evidence Generator for Trust Layer
 *
 * Generates evidence trails, situation briefs, and reasoning chains
 * for synthesis cards based on matched indicators and patterns.
 */

import { IndicatorData } from '../../types';
import { ScoredPattern } from './cardScorer';
import {
  EvidenceSignal,
  getSource,
  computeConfidence,
} from '../../data/sourceRegistry';
import {
  InsightCardWithEvidence,
  SituationBrief,
  ReasoningChain,
  ActionItem,
} from '../../types/trust';
import { INDICATOR_TRANSLATIONS, getImpact } from '../../data/indicatorTranslations';

/**
 * Map indicator IDs to their data sources
 */
const INDICATOR_SOURCE_MAP: Record<string, string> = {
  econ_01_treasury_tail: 'treasury',
  econ_02_grocery_cpi: 'bls',
  market_01_intraday_swing: 'yahoo_finance',
  green_g1_gdp_rates: 'fred',
  job_01_strike_days: 'cornell_ilr',
  power_01_ai_surveillance: 'legiscan',
  civil_01_acled_protests: 'acled',
  cyber_01_cisa_kev: 'cisa',
  grid_01_pjm_outages: 'pjm',
  bio_01_h2h_countries: 'who',
  oil_01_russian_brics: 'crea',
  oil_02_mbridge_settlements: 'bis',
  ofac_01_designations: 'treasury',
  oil_04_refinery_ratio: 'eia',
  labor_ai_01_layoffs: 'bloomberg',
  cyber_02_ai_ransomware: 'cisa',
  info_02_deepfake_shocks: 'reuters',
  compute_01_training_cost: 'epoch_ai',
  global_conflict_intensity: 'acled',
  taiwan_pla_activity: 'taiwan_mnd',
  nato_high_readiness: 'nato',
  nuclear_01_tests: 'sipri',
  russia_nato_escalation: 'nato',
  defense_spending_growth: 'sipri',
  dc_control_countdown: 'legiscan',
  national_guard_metros: 'ap',
  ice_detention_surge: 'ice',
  dhs_removal_expansion: 'dhs',
  hill_control_legislation: 'legiscan',
  liberty_litigation_count: 'trac',
  supply_01_port_congestion: 'marine_traffic',
  supply_02_freight_index: 'freightos',
  supply_03_chip_lead_time: 'bloomberg',
  spr_01_level: 'eia',
  energy_02_nat_gas_storage: 'eia',
  energy_03_grid_emergency: 'doe',
  bank_01_failures: 'fdic',
  bank_02_discount_window: 'fed',
  bank_03_deposit_flow: 'fed',
  flight_01_ground_stops: 'faa',
  flight_02_delay_pct: 'faa',
  flight_03_tfr_count: 'faa',
  travel_01_advisories: 'state_dept',
  travel_02_border_wait: 'dhs',
  travel_03_tsa_throughput: 'dhs',
};

/**
 * Generate an evidence signal from an indicator
 */
function generateEvidenceFromIndicator(indicator: IndicatorData): EvidenceSignal {
  const translation = INDICATOR_TRANSLATIONS[indicator.id];
  const sourceId = INDICATOR_SOURCE_MAP[indicator.id] || 'reuters';
  const source = getSource(sourceId);

  // Generate headline based on indicator status
  const headline =
    translation?.redHeadline && indicator.status.level === 'red'
      ? translation.redHeadline
      : translation?.amberHeadline && indicator.status.level === 'amber'
      ? translation.amberHeadline
      : `${indicator.name} at ${indicator.status.level} level`;

  // Generate data point
  const dataPoint = indicator.status.value !== undefined
    ? `${indicator.status.value}${indicator.unit ? ` ${indicator.unit}` : ''}`
    : undefined;

  // Determine reliability based on source type
  const reliability =
    source.type === 'government-official' || source.type === 'international-org'
      ? 'official'
      : source.type === 'academic-research'
      ? 'authoritative'
      : source.type === 'wire-service' || source.type === 'industry-data'
      ? 'reporting'
      : 'preliminary';

  // Generate relevance text
  const relevance =
    translation
      ? `${translation.displayName} is a key measure of ${indicator.domain.replace(/_/g, ' ')} conditions that directly affects household resilience.`
      : `This indicator tracks ${indicator.domain.replace(/_/g, ' ')} conditions.`;

  return {
    id: `evidence-${indicator.id}`,
    headline,
    source,
    date: new Date(indicator.status.lastUpdate),
    url: indicator.sourceUrl,
    dataPoint,
    reliability,
    relevance,
    indicatorId: indicator.id,
  };
}

/**
 * Situation brief templates by pattern type
 */
const SITUATION_TEMPLATES: Record<string, (indicators: IndicatorData[]) => SituationBrief> = {
  'inflation-watch': (indicators) => {
    const cpi = indicators.find(i => i.id === 'econ_02_grocery_cpi');
    const value = cpi?.status.value || 5;
    return {
      narrative: `Grocery prices have been climbing steadily over the past quarter, with the most recent data showing a ${value}% annualized increase. This is above the Federal Reserve's 2% target and reflects persistent inflation pressure in food categories.

This shows up at checkout. Families are seeing $20-40 more per weekly grocery trip compared to last year, with staples like eggs, meat, and dairy leading the increases. Imported foods and those requiring significant transportation are hit hardest.

The pattern is consistent with supply chain normalization taking longer than expected, combined with elevated energy costs that affect food production and distribution.`,
      timeHorizon: 'This trend is likely to persist for the next 2-3 months based on current data.',
      historicalContext: 'Grocery inflation last hit these levels in mid-2022, when it peaked at 13.5% before gradually declining.',
      generatedAt: new Date(),
    };
  },

  'market-watch': (indicators) => {
    const swing = indicators.find(i => i.id === 'market_01_intraday_swing');
    const value = swing?.status.value || 25;
    return {
      narrative: `Financial markets are experiencing elevated volatility, with Treasury yields swinging ${value} basis points intraday — roughly 3x normal levels. This kind of movement often precedes broader market uncertainty.

For households with retirement accounts or investment portfolios, this means your balance will fluctuate more than usual day-to-day. History shows that staying the course during volatility outperforms panic selling, but it can be uncomfortable to watch.

The underlying drivers appear to be uncertainty about Federal Reserve policy and global economic conditions.`,
      timeHorizon: 'Market volatility typically persists for 2-4 weeks during adjustment periods.',
      historicalContext: 'Similar volatility levels were seen during the March 2023 banking stress and the August 2024 carry trade unwind.',
      generatedAt: new Date(),
    };
  },

  'multi-economic-stress': (indicators) => {
    const redCount = indicators.filter(i => i.status.level === 'red').length;
    const amberCount = indicators.filter(i => i.status.level === 'amber').length;
    return {
      narrative: `Multiple economic indicators are showing stress simultaneously — ${amberCount} at caution level and ${redCount} at critical. This combination suggests broader economic friction that goes beyond any single issue.

When market volatility, inflation, and other stressors align, the effects compound. ATMs can have issues during banking stress, credit card networks can slow, and cash becomes more valuable as a buffer.

The last time this many economic indicators aligned was during the early pandemic period in 2020, though the causes and likely outcomes differ.`,
      timeHorizon: 'Multi-factor economic stress typically takes 4-8 weeks to resolve or escalate.',
      historicalContext: 'Similar indicator patterns preceded the 2008 financial crisis by approximately 6 weeks.',
      generatedAt: new Date(),
    };
  },

  'taiwan-watch': (indicators) => {
    const pla = indicators.find(i => i.id === 'taiwan_pla_activity');
    const value = pla?.status.value || 28;
    return {
      narrative: `Military activity in the Taiwan Strait has increased, with PLA aircraft incursions averaging ${value} per day over the past two weeks. This is above the normal baseline but below crisis levels seen during past tensions.

Taiwan manufactures over 90% of the world's advanced semiconductors. If tensions escalate, chip shortages could affect everything from phones to cars to medical devices within weeks. The 2021 chip shortage caused 6-month delays for vehicle purchases.

Current activity appears to be signaling and posturing rather than preparation for military action, but the situation warrants monitoring.`,
      timeHorizon: 'Taiwan Strait tensions typically ebb and flow over 2-4 week cycles.',
      historicalContext: 'The 1996 Taiwan Strait crisis and 2022 Pelosi visit both saw similar activity spikes that resolved without escalation.',
      generatedAt: new Date(),
    };
  },

  'cyber-threats': (indicators) => {
    const kev = indicators.find(i => i.id === 'cyber_01_cisa_kev');
    const value = kev?.status.value || 4;
    return {
      narrative: `CISA has added ${value} new vulnerabilities to its Known Exploited Vulnerabilities catalog this month, indicating active exploitation by threat actors. These affect common software that many households use.

Unpatched devices are the primary entry point for ransomware and identity theft. Your phone, computer, router, and smart home devices all need regular updates. If you haven't updated in the past month, you're likely vulnerable.

This is a good time to audit your digital security: run updates, change passwords that haven't been touched in 6+ months, and enable two-factor authentication where available.`,
      timeHorizon: 'Active exploitation windows typically last 2-6 weeks before patches are widely deployed.',
      historicalContext: 'The Log4j vulnerability in December 2021 followed a similar pattern — rapid exploitation followed by gradual patching.',
      generatedAt: new Date(),
    };
  },

  'enforcement-uptick': (indicators) => {
    const ice = indicators.find(i => i.id === 'ice_detention_surge');
    const value = ice?.status.value || 62000;
    return {
      narrative: `ICE detention population has reached ${value.toLocaleString()}, indicating increased immigration enforcement activity. This affects communities unevenly — some areas see little change while others experience significant disruption.

For affected communities, this means ensuring everyone knows their rights, has emergency contacts memorized (not just in their phone), and has documentation accessible. Schools and workplaces may see increased anxiety.

Enforcement patterns tend to focus on specific regions and workplace categories. Local immigrant rights organizations have the most current information about your area.`,
      timeHorizon: 'Enforcement campaigns typically run in 3-6 month cycles.',
      historicalContext: 'Similar detention levels were seen in 2019, preceding policy changes that affected detention practices.',
      generatedAt: new Date(),
    };
  },

  'oil-axis-shift': (indicators) => {
    const brics = indicators.find(i => i.id === 'oil_01_russian_brics');
    const value = brics?.status.value || 68;
    return {
      narrative: `${value}% of Russian crude oil is now flowing to BRICS nations rather than traditional Western markets. This represents a significant shift in global energy trade patterns that has implications for the dollar and fuel prices.

For households, this primarily shows up at the gas pump. When oil trade moves away from dollar settlement, it can create currency pressure that eventually affects domestic fuel prices. The effect is gradual — typically 3-6 months lag.

Keeping your vehicle tank above half-full is good practice during energy market shifts. It provides buffer against sudden price spikes and potential supply disruptions.`,
      timeHorizon: 'Energy market realignments typically play out over 6-12 months.',
      historicalContext: 'Previous petrodollar challenges in the 1970s caused the oil shocks that defined that era.',
      generatedAt: new Date(),
    };
  },
};

/**
 * Generate a situation brief for a pattern
 */
function generateSituationBrief(
  patternId: string,
  indicators: IndicatorData[]
): SituationBrief {
  const template = SITUATION_TEMPLATES[patternId];
  if (template) {
    return template(indicators);
  }

  // Default situation brief
  const domains = [...new Set(indicators.map(i => i.domain))];
  const levels = indicators.map(i => i.status.level);
  const hasRed = levels.includes('red');

  return {
    narrative: `Multiple indicators in the ${domains.join(' and ').replace(/_/g, ' ')} domain${domains.length > 1 ? 's' : ''} are showing ${hasRed ? 'elevated' : 'cautionary'} signals. This pattern suggests conditions that warrant attention and potential preparation.

The specific combination of signals indicates this isn't a random fluctuation — there's a coherent pattern that historically has preceded household-level impacts.

We're watching this situation closely and will update if conditions change significantly.`,
    timeHorizon: 'Situation timeline depends on underlying factors.',
    generatedAt: new Date(),
  };
}

/**
 * Generate reasoning chain for a pattern
 */
function generateReasoningChain(
  pattern: ScoredPattern,
  indicators: IndicatorData[]
): ReasoningChain {
  const indicatorNames = indicators
    .map(i => INDICATOR_TRANSLATIONS[i.id]?.displayName || i.name)
    .join(', ');

  const impacts = indicators
    .map(i => getImpact(i.id, i.status.level as 'amber' | 'red'))
    .filter(Boolean);

  return {
    observation: `${indicatorNames} ${indicators.length > 1 ? 'are' : 'is'} showing ${indicators[0]?.status.level} status. ${pattern.pattern.outcomeTemplate.split('.')[0]}.`,

    interpretation: `When these indicators align, it historically indicates conditions that affect household budgets, supply availability, or safety. The pattern matches scenarios we've studied from past events.`,

    implication: impacts.length > 0
      ? impacts.join(' ')
      : `Your household may experience impacts related to ${indicators[0]?.domain.replace(/_/g, ' ')} in the coming weeks.`,

    recommendation: pattern.pattern.actionTemplate
      ? `${pattern.pattern.actionTemplate} now because timing matters. Acting before conditions worsen locks in current prices/availability and provides buffer if things escalate.`
      : 'Taking preparatory action now provides optionality regardless of how the situation develops.',

    assumptions: [
      'Current trends continue at similar pace',
      'No major policy interventions change the trajectory',
      'Historical patterns remain predictive of outcomes',
    ],

    counterpoints: [
      'Conditions may improve faster than expected if underlying causes resolve',
      'Buffer inventories (retail, supply chain) may delay consumer impact',
      'Our historical comparisons may not fully apply to current circumstances',
    ],

    updateTriggers: [
      `If indicator levels improve to green → recommendation downgrades`,
      `If additional indicators turn red → recommendation escalates to "do this today"`,
      `If 48 hours pass without change → situation is stabilizing`,
    ],
  };
}

/**
 * Generate action items for a pattern
 */
function generateActionItems(
  pattern: ScoredPattern,
  indicators: IndicatorData[]
): ActionItem[] {
  const actions: ActionItem[] = [];
  const severity = pattern.pattern.baseSeverity;

  // Primary action from pattern
  if (pattern.pattern.actionTemplate) {
    actions.push({
      id: `action-${pattern.pattern.id}-primary`,
      task: pattern.pattern.actionTemplate,
      why: 'Primary recommended action based on current conditions',
      effort: severity >= 7 ? 'moderate' : 'quick',
      timeEstimate: severity >= 7 ? '1-2 hours' : '30 minutes',
      priority: severity >= 7 ? 'critical' : 'recommended',
    });
  }

  // Add domain-specific secondary actions
  const domains = [...new Set(indicators.map(i => i.domain))];

  if (domains.includes('economy')) {
    actions.push({
      id: `action-${pattern.pattern.id}-cash`,
      task: 'Verify cash on hand (2 weeks minimum)',
      why: 'Cash provides buffer if card systems have issues',
      effort: 'quick',
      timeEstimate: '15 minutes',
      priority: severity >= 7 ? 'critical' : 'recommended',
    });
  }

  if (domains.includes('supply_chain') || domains.includes('energy')) {
    actions.push({
      id: `action-${pattern.pattern.id}-supplies`,
      task: 'Check shelf-stable supply levels',
      why: 'Stocking up at current prices beats paying peak prices later',
      effort: 'moderate',
      timeEstimate: '1 hour + shopping trip',
      priority: 'recommended',
    });
  }

  if (domains.includes('security_infrastructure')) {
    actions.push({
      id: `action-${pattern.pattern.id}-security`,
      task: 'Run software updates on all devices',
      why: 'Unpatched devices are primary entry points for attacks',
      effort: 'quick',
      timeEstimate: '20 minutes',
      priority: 'recommended',
    });
  }

  // Always add a planning action
  actions.push({
    id: `action-${pattern.pattern.id}-plan`,
    task: 'Review family emergency communication plan',
    why: 'Ensure everyone knows rally points and emergency contacts',
    effort: 'quick',
    timeEstimate: '15 minutes',
    priority: 'optional',
  });

  return actions;
}

/**
 * Generate a full InsightCardWithEvidence from a scored pattern
 */
export function generateInsightCardWithEvidence(
  scored: ScoredPattern,
  _indicators: IndicatorData[]  // Available for future use (e.g., broader context)
): InsightCardWithEvidence {
  // Get matched indicators
  const matchedIndicators = scored.matchedIndicators;

  // Generate evidence signals
  const evidence = matchedIndicators.map(generateEvidenceFromIndicator);

  // Compute confidence
  const confidence = computeConfidence(evidence);

  // Generate trust layer content
  const situationBrief = generateSituationBrief(scored.pattern.id, matchedIndicators);
  const reasoningChain = generateReasoningChain(scored, matchedIndicators);
  const actions = generateActionItems(scored, matchedIndicators);

  // Determine urgency
  const urgency: 'today' | 'week' | 'knowing' =
    scored.severityScore >= 70 ? 'today' :
    scored.severityScore >= 40 ? 'week' : 'knowing';

  return {
    id: scored.pattern.id,
    headline: scored.pattern.headlineTemplate,
    body: scored.pattern.outcomeTemplate,
    urgency,
    domains: scored.pattern.domains,
    indicatorIds: matchedIndicators.map(i => i.id),
    severity: scored.pattern.baseSeverity,
    action: scored.pattern.actionTemplate
      ? {
          label: scored.pattern.actionTemplate,
          href: scored.pattern.actionHref || '/action-plan',
        }
      : undefined,
    confidence,
    evidence,
    situationBrief,
    reasoningChain,
    actions,
    patternId: scored.pattern.id,
    generatedAt: new Date(),
  };
}
