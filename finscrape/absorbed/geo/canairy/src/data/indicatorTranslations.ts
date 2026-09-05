/**
 * Indicator Translation Map
 *
 * This is the key data structure that translates raw indicator data into
 * family-friendly language. Every indicator needs these fields to pass
 * the "kitchen table test" - if you can't say it to your partner over
 * coffee and have it make sense, it's wrong.
 */

export interface IndicatorTranslation {
  // System fields (never rendered directly)
  id: string;
  systemName: string;

  // Translation fields (used by synthesis engine)
  displayName: string;              // "Grocery Price Index"

  // What the user experiences when this indicator moves
  amberImpact: string;              // "Grocery prices are rising faster than usual"
  redImpact: string;                // "Grocery prices are spiking — expect 15-20% higher costs"

  // What to do about it
  amberAction: string;              // "Good time to stock up on shelf-stable essentials"
  redAction: string;                // "Buy 2-4 weeks of essentials now before prices climb further"

  // Sentence fragments for composing the outcome sentence
  amberOutcomePhrase: string;       // "higher prices at the store"
  redOutcomePhrase: string;         // "significantly higher grocery costs"

  // Specific data point template
  dataPointTemplate: string;        // "Avg. grocery bill: ${value} (was ${baseline} in ${baselineDate})"

  // News-style headlines for signals
  amberHeadline: string;
  redHeadline: string;

  // Source for credibility
  source: string;                   // "Bureau of Labor Statistics"
  sourceAbbrev: string;             // "BLS"
}

export const INDICATOR_TRANSLATIONS: Record<string, IndicatorTranslation> = {
  // ═══════════════════════════════════════════════════════════════════════════
  // ECONOMY DOMAIN
  // ═══════════════════════════════════════════════════════════════════════════
  'econ_01_treasury_tail': {
    id: 'econ_01_treasury_tail',
    systemName: 'TreasuryTail',
    displayName: 'Treasury Market Stress',
    amberImpact: 'Bond market showing unusual stress patterns',
    redImpact: 'Treasury auction failures signal severe funding stress',
    amberAction: 'Review investment allocations and cash positions',
    redAction: 'Verify FDIC coverage on all deposits. Hold extra cash',
    amberOutcomePhrase: 'financial market volatility',
    redOutcomePhrase: 'severe stress in government bond markets',
    dataPointTemplate: 'Auction tail: {value} bps (normal: under 3)',
    amberHeadline: 'Treasury auction sees weak demand amid market uncertainty',
    redHeadline: 'Treasury auction fails as investors flee to cash',
    source: 'Treasury Direct',
    sourceAbbrev: 'Treasury',
  },

  'econ_02_grocery_cpi': {
    id: 'econ_02_grocery_cpi',
    systemName: 'GroceryCPI',
    displayName: 'Grocery Prices',
    amberImpact: 'Grocery prices are climbing above normal seasonal patterns',
    redImpact: 'Grocery prices are spiking across most categories',
    amberAction: 'Good time to stock up on shelf-stable essentials',
    redAction: 'Buy 2-4 weeks of essentials now — prices unlikely to drop soon',
    amberOutcomePhrase: 'higher prices at the store',
    redOutcomePhrase: 'significantly higher grocery costs',
    dataPointTemplate: 'Food prices: up {value}% this quarter',
    amberHeadline: 'Consumer price index rises as grocery costs climb',
    redHeadline: 'Grocery prices surge 8% in worst spike since 2022',
    source: 'Bureau of Labor Statistics',
    sourceAbbrev: 'BLS',
  },

  'market_01_intraday_swing': {
    id: 'market_01_intraday_swing',
    systemName: 'IntradaySwing',
    displayName: 'Market Volatility',
    amberImpact: 'Stock markets are swinging more than usual',
    redImpact: 'Extreme market volatility — circuit breakers may trigger',
    amberAction: 'Avoid checking your 401k obsessively, stay the course',
    redAction: 'Screenshot all investment balances for records',
    amberOutcomePhrase: 'volatile investment markets',
    redOutcomePhrase: 'extreme market swings affecting retirement accounts',
    dataPointTemplate: 'Intraday swing: {value}% (normal: under 1%)',
    amberHeadline: 'Markets see elevated volatility amid economic uncertainty',
    redHeadline: 'Stocks plunge in worst trading session since pandemic',
    source: 'NYSE',
    sourceAbbrev: 'NYSE',
  },

  'green_g1_gdp_rates': {
    id: 'green_g1_gdp_rates',
    systemName: 'GDPRates',
    displayName: 'Economic Growth',
    amberImpact: 'Economic growth is slowing — potential recession signals',
    redImpact: 'GDP contracting — recession confirmed',
    amberAction: 'Build emergency fund, reduce discretionary spending',
    redAction: 'Prepare for job market disruptions, maximize cash reserves',
    amberOutcomePhrase: 'slowing economic growth',
    redOutcomePhrase: 'recession conditions affecting jobs and income',
    dataPointTemplate: 'GDP growth: {value}% (negative = contraction)',
    amberHeadline: 'Fed signals concern over slowing economic growth',
    redHeadline: 'Economy enters recession as GDP contracts second quarter',
    source: 'Bureau of Economic Analysis',
    sourceAbbrev: 'BEA',
  },

  'luxury_01_collapse': {
    id: 'luxury_01_collapse',
    systemName: 'LuxuryCollapse',
    displayName: 'Luxury Sector',
    amberImpact: 'Luxury goods sector weakening — often precedes broader recession',
    redImpact: 'Luxury sector collapsing — recession typically follows in 3-6 months',
    amberAction: 'Shore up emergency savings. Delay major discretionary purchases',
    redAction: 'Maximize cash reserves. Prepare for potential job market disruption',
    amberOutcomePhrase: 'early recession signals in consumer spending',
    redOutcomePhrase: 'recession warning signs in luxury sector collapse',
    dataPointTemplate: 'Luxury index: down {value}% (normal: +/- 5%)',
    amberHeadline: 'Luxury goods stocks decline as consumer confidence wavers',
    redHeadline: 'Luxury sector crashes in worst decline since 2008',
    source: 'Bloomberg / S&P',
    sourceAbbrev: 'Bloomberg',
  },

  // ═══════════════════════════════════════════════════════════════════════════
  // GLOBAL CONFLICT DOMAIN
  // ═══════════════════════════════════════════════════════════════════════════
  'taiwan_pla_activity': {
    id: 'taiwan_pla_activity',
    systemName: 'TaiwanPLA',
    displayName: 'Taiwan Strait Activity',
    amberImpact: 'Military activity near Taiwan is elevated',
    redImpact: 'Major military operations in Taiwan Strait — supply chain disruption likely',
    amberAction: 'Consider ordering electronics before potential shortages',
    redAction: 'Stock critical electronics and medications manufactured in Asia',
    amberOutcomePhrase: 'elevated military activity in the Pacific',
    redOutcomePhrase: 'serious risk to global chip supply from Taiwan tensions',
    dataPointTemplate: 'PLA sorties: {value} this week (avg: 15)',
    amberHeadline: 'Taiwan reports increased military activity in strait',
    redHeadline: 'US warns nationals to leave as Taiwan tensions escalate',
    source: 'Taiwan Ministry of Defense',
    sourceAbbrev: 'Taiwan MND',
  },

  'global_conflict_intensity': {
    id: 'global_conflict_intensity',
    systemName: 'ConflictIntensity',
    displayName: 'Global Conflict Level',
    amberImpact: 'Conflict activity elevated across multiple regions',
    redImpact: 'Multiple active conflicts with risk of escalation',
    amberAction: 'Review family emergency communication plans',
    redAction: 'Ensure go-bags packed, confirm family rally points',
    amberOutcomePhrase: 'rising geopolitical tensions',
    redOutcomePhrase: 'serious geopolitical instability',
    dataPointTemplate: 'Conflict events: {value} this week',
    amberHeadline: 'State Department issues travel advisories for 3 regions',
    redHeadline: 'US nationals told to leave Mideast amid escalating tensions',
    source: 'ACLED',
    sourceAbbrev: 'ACLED',
  },

  'nato_high_readiness': {
    id: 'nato_high_readiness',
    systemName: 'NATOReadiness',
    displayName: 'NATO Alert Level',
    amberImpact: 'NATO allies raising readiness levels',
    redImpact: 'NATO forces at high alert — significant escalation risk',
    amberAction: 'Stay informed on international developments',
    redAction: 'Accelerate Phase 5+ preparations immediately',
    amberOutcomePhrase: 'increased military readiness in Europe',
    redOutcomePhrase: 'NATO forces on high alert with escalation risk',
    dataPointTemplate: 'NATO readiness: {value}/100',
    amberHeadline: 'NATO allies announce increased military exercises',
    redHeadline: 'NATO activates rapid response force amid Russia tensions',
    source: 'NATO',
    sourceAbbrev: 'NATO',
  },

  'russia_nato_escalation': {
    id: 'russia_nato_escalation',
    systemName: 'RussiaNATO',
    displayName: 'Russia-NATO Tensions',
    amberImpact: 'Russia-NATO relations deteriorating',
    redImpact: 'Direct confrontation risk between Russia and NATO',
    amberAction: 'Monitor for energy supply impacts',
    redAction: 'Prepare for potential energy disruptions and supply shocks',
    amberOutcomePhrase: 'worsening Russia-NATO relations',
    redOutcomePhrase: 'dangerous escalation between Russia and NATO',
    dataPointTemplate: 'Escalation index: {value}/100',
    amberHeadline: 'Russia-NATO tensions rise over military buildup',
    redHeadline: 'Russia warns of military response to NATO expansion',
    source: 'IISS',
    sourceAbbrev: 'IISS',
  },

  // ═══════════════════════════════════════════════════════════════════════════
  // DOMESTIC CONTROL DOMAIN
  // ═══════════════════════════════════════════════════════════════════════════
  'ice_detention_surge': {
    id: 'ice_detention_surge',
    systemName: 'ICEDetention',
    displayName: 'Immigration Enforcement',
    amberImpact: 'Immigration enforcement operations expanding',
    redImpact: 'Aggressive enforcement reported in community spaces',
    amberAction: 'Know your rights. Share info with affected communities',
    redAction: 'Ensure all family documents accessible. Review legal contacts',
    amberOutcomePhrase: 'expanded enforcement operations',
    redOutcomePhrase: 'aggressive enforcement activity in your area',
    dataPointTemplate: 'Detentions: {value} this week',
    amberHeadline: 'DHS announces expanded enforcement in 4 new cities',
    redHeadline: 'Reports of enforcement operations at schools and hospitals',
    source: 'TRAC Immigration',
    sourceAbbrev: 'TRAC',
  },

  'national_guard_metros': {
    id: 'national_guard_metros',
    systemName: 'NationalGuard',
    displayName: 'National Guard Deployment',
    amberImpact: 'National Guard units deployed to metropolitan areas',
    redImpact: 'Major National Guard presence in civilian areas',
    amberAction: 'Note deployment locations and avoid if possible',
    redAction: 'Limit travel to essential trips only. Know alternate routes',
    amberOutcomePhrase: 'increased security presence in cities',
    redOutcomePhrase: 'significant National Guard deployments affecting daily routines',
    dataPointTemplate: 'Metros with NG presence: {value}',
    amberHeadline: 'National Guard units deployed to 3 major cities',
    redHeadline: 'Governors activate National Guard in 8 metropolitan areas',
    source: 'National Guard Bureau',
    sourceAbbrev: 'NGB',
  },

  'power_01_ai_surveillance': {
    id: 'power_01_ai_surveillance',
    systemName: 'AISurveillance',
    displayName: 'AI Surveillance Expansion',
    amberImpact: 'AI surveillance legislation advancing',
    redImpact: 'Major AI surveillance programs being deployed',
    amberAction: 'Review your digital privacy practices',
    redAction: 'Audit digital footprint. Consider privacy tools',
    amberOutcomePhrase: 'expanding surveillance infrastructure',
    redOutcomePhrase: 'significant new surveillance capabilities coming online',
    dataPointTemplate: 'Surveillance bills: {value} advancing',
    amberHeadline: 'AI surveillance bills advance in 6 state legislatures',
    redHeadline: 'Federal AI surveillance program launches nationwide',
    source: 'EFF',
    sourceAbbrev: 'EFF',
  },

  'hill_control_legislation': {
    id: 'hill_control_legislation',
    systemName: 'HillControl',
    displayName: 'Legislative Activity',
    amberImpact: 'Significant legislation affecting civil liberties advancing',
    redImpact: 'Major restrictions on rights being enacted',
    amberAction: 'Contact representatives. Document concerns',
    redAction: 'Review legal protections. Update emergency plans',
    amberOutcomePhrase: 'legislative changes to watch',
    redOutcomePhrase: 'significant changes to rights and protections',
    dataPointTemplate: 'Bills passed: {value} this session',
    amberHeadline: 'Congress advances controversial security legislation',
    redHeadline: 'President signs sweeping security powers into law',
    source: 'Congress.gov',
    sourceAbbrev: 'Congress',
  },

  // ═══════════════════════════════════════════════════════════════════════════
  // SECURITY & INFRASTRUCTURE DOMAIN
  // ═══════════════════════════════════════════════════════════════════════════
  'cyber_01_cisa_kev': {
    id: 'cyber_01_cisa_kev',
    systemName: 'CISAKEV',
    displayName: 'Cyber Threat Level',
    amberImpact: 'Critical vulnerabilities being actively exploited',
    redImpact: 'Cyberattacks on critical infrastructure reported',
    amberAction: 'Update passwords on banking and email. Enable 2FA',
    redAction: 'Screenshot financial balances. Prepare for service disruptions',
    amberOutcomePhrase: 'elevated cyber threats',
    redOutcomePhrase: 'active cyber threats against infrastructure',
    dataPointTemplate: 'Active exploits: {value} this week',
    amberHeadline: 'CISA warns of critical vulnerabilities in common software',
    redHeadline: 'Active cyberattack reported against Northeast utilities',
    source: 'CISA',
    sourceAbbrev: 'CISA',
  },

  'cyber_02_ai_ransomware': {
    id: 'cyber_02_ai_ransomware',
    systemName: 'AIRansomware',
    displayName: 'AI-Enhanced Cyber Attacks',
    amberImpact: 'Sophisticated AI-powered attacks increasing',
    redImpact: 'Major AI-enhanced ransomware campaign affecting critical services',
    amberAction: 'Verify backups of important files. Update security software',
    redAction: 'Disconnect sensitive devices. Use cash for critical purchases',
    amberOutcomePhrase: 'increasing cyber attack sophistication',
    redOutcomePhrase: 'AI-powered attacks disrupting services',
    dataPointTemplate: 'AI-enhanced attacks: {value} reported',
    amberHeadline: 'Security firms warn of AI-enhanced phishing campaigns',
    redHeadline: 'AI ransomware takes down hospital networks across 3 states',
    source: 'CISA',
    sourceAbbrev: 'CISA',
  },

  'grid_01_pjm_outages': {
    id: 'grid_01_pjm_outages',
    systemName: 'PJMOutages',
    displayName: 'Power Grid Reliability',
    amberImpact: 'Grid operators flagging reduced capacity margins',
    redImpact: 'Rolling blackouts possible in your region',
    amberAction: 'Charge backup devices, check flashlight batteries',
    redAction: 'Test generator, fill fuel, charge all power banks',
    amberOutcomePhrase: 'potential power reliability issues',
    redOutcomePhrase: 'risk of power outages in your area',
    dataPointTemplate: 'Grid margin: {value}% (warning under 15%)',
    amberHeadline: 'Grid operators issue capacity warnings ahead of cold snap',
    redHeadline: 'Utilities implement rolling blackouts as grid strains',
    source: 'PJM / NERC',
    sourceAbbrev: 'NERC',
  },

  'bio_01_h2h_countries': {
    id: 'bio_01_h2h_countries',
    systemName: 'H2HCountries',
    displayName: 'Novel Pathogen Risk',
    amberImpact: 'Novel pathogen with potential human-to-human transmission detected',
    redImpact: 'Confirmed human-to-human transmission of novel pathogen',
    amberAction: 'Verify N95 cache and medication supply',
    redAction: 'Mask up in public, limit gatherings, stock medications',
    amberOutcomePhrase: 'emerging infectious disease concerns',
    redOutcomePhrase: 'new human-transmissible pathogen requiring precautions',
    dataPointTemplate: 'Countries reporting: {value}',
    amberHeadline: 'WHO monitoring novel respiratory pathogen in 3 countries',
    redHeadline: 'CDC confirms human-to-human transmission of novel virus',
    source: 'WHO',
    sourceAbbrev: 'WHO',
  },

  // ═══════════════════════════════════════════════════════════════════════════
  // OIL AXIS DOMAIN
  // ═══════════════════════════════════════════════════════════════════════════
  'oil_01_russian_brics': {
    id: 'oil_01_russian_brics',
    systemName: 'RussianBRICS',
    displayName: 'Oil Trade Realignment',
    amberImpact: 'Oil trade patterns shifting away from Western systems',
    redImpact: 'Major disruption to global oil trading systems',
    amberAction: 'Monitor for fuel price volatility',
    redAction: 'Fill all vehicle tanks. Consider fuel storage',
    amberOutcomePhrase: 'shifting global oil trade patterns',
    redOutcomePhrase: 'major disruptions to oil supply chains',
    dataPointTemplate: 'BRICS oil share: {value}%',
    amberHeadline: 'Russia expands oil trade with BRICS partners',
    redHeadline: 'Gulf states announce shift to non-dollar oil settlements',
    source: 'CREA',
    sourceAbbrev: 'CREA',
  },

  'spr_01_level': {
    id: 'spr_01_level',
    systemName: 'SPRLevel',
    displayName: 'Strategic Oil Reserves',
    amberImpact: 'US strategic petroleum reserves running low',
    redImpact: 'Strategic reserves at critically low levels',
    amberAction: 'Keep vehicle tanks above half full',
    redAction: 'Fill all vehicles. Stock emergency fuel safely',
    amberOutcomePhrase: 'declining emergency oil reserves',
    redOutcomePhrase: 'dangerously low fuel reserves',
    dataPointTemplate: 'SPR level: {value}M barrels (historic low: 350M)',
    amberHeadline: 'Strategic petroleum reserve falls to 30-year low',
    redHeadline: 'US fuel reserves hit critical levels amid global tensions',
    source: 'EIA',
    sourceAbbrev: 'EIA',
  },

  // ═══════════════════════════════════════════════════════════════════════════
  // AI WINDOW DOMAIN
  // ═══════════════════════════════════════════════════════════════════════════
  'labor_ai_01_layoffs': {
    id: 'labor_ai_01_layoffs',
    systemName: 'AILayoffs',
    displayName: 'AI Job Displacement',
    amberImpact: 'AI-driven layoffs increasing across industries',
    redImpact: 'Major wave of AI-related job losses announced',
    amberAction: 'Review your skill positioning. Explore AI-proof roles',
    redAction: 'Accelerate reskilling. Diversify income sources',
    amberOutcomePhrase: 'increasing AI-related job changes',
    redOutcomePhrase: 'significant job market disruption from AI',
    dataPointTemplate: 'AI-cited layoffs: {value}K this quarter',
    amberHeadline: 'Tech giants cite AI as factor in workforce reductions',
    redHeadline: 'AI automation triggers largest tech layoff wave since 2020',
    source: 'BLS',
    sourceAbbrev: 'BLS',
  },

  'info_02_deepfake_shocks': {
    id: 'info_02_deepfake_shocks',
    systemName: 'DeepfakeShocks',
    displayName: 'AI Disinformation',
    amberImpact: 'AI-generated disinformation affecting public discourse',
    redImpact: 'Major deepfake incident causing market or political chaos',
    amberAction: 'Verify news through multiple trusted sources',
    redAction: 'Wait 24 hours before acting on breaking news. Cross-reference',
    amberOutcomePhrase: 'increased AI disinformation online',
    redOutcomePhrase: 'AI-generated fake news causing real-world impacts',
    dataPointTemplate: 'Deepfake incidents: {value} this month',
    amberHeadline: 'Social platforms struggle to contain AI-generated content',
    redHeadline: 'Deepfake video of world leader triggers market panic',
    source: 'Reuters',
    sourceAbbrev: 'Reuters',
  },

  'compute_01_training_cost': {
    id: 'compute_01_training_cost',
    systemName: 'TrainingCost',
    displayName: 'AI Capability Acceleration',
    amberImpact: 'AI capabilities advancing faster than expected',
    redImpact: 'Major AI capability milestone crossed ahead of schedule',
    amberAction: 'Stay informed on AI developments in your industry',
    redAction: 'Review career contingency plans. Consider AI-resistant roles',
    amberOutcomePhrase: 'accelerating AI capabilities',
    redOutcomePhrase: 'rapid AI advances that could reshape industries quickly',
    dataPointTemplate: 'Training efficiency: {value}x improvement',
    amberHeadline: 'AI labs report faster-than-expected capability gains',
    redHeadline: 'Major AI lab announces autonomous agent breakthrough',
    source: 'Epoch AI',
    sourceAbbrev: 'Epoch AI',
  },

  // ═══════════════════════════════════════════════════════════════════════════
  // SUPPLY CHAIN DOMAIN
  // ═══════════════════════════════════════════════════════════════════════════
  'supply_01_chip_lead_time': {
    id: 'supply_01_chip_lead_time',
    systemName: 'ChipLeadTime',
    displayName: 'Semiconductor Supply',
    amberImpact: 'Chip shortages extending delivery times',
    redImpact: 'Severe semiconductor shortage affecting multiple industries',
    amberAction: 'Consider ordering electronics before delays worsen',
    redAction: 'Purchase critical electronics now. Expect long waits',
    amberOutcomePhrase: 'longer waits for electronics',
    redOutcomePhrase: 'significant delays on electronics and vehicles',
    dataPointTemplate: 'Chip lead time: {value} weeks (normal: 12)',
    amberHeadline: 'Semiconductor lead times extend to 18 weeks',
    redHeadline: 'Automakers halt production amid worst chip shortage in years',
    source: 'Industry Reports',
    sourceAbbrev: 'Semi',
  },

};

/**
 * Get translation for an indicator, with fallback for unknown indicators
 */
export function getTranslation(indicatorId: string): IndicatorTranslation | null {
  return INDICATOR_TRANSLATIONS[indicatorId] || null;
}

/**
 * Get display name for an indicator (never show system ID to users)
 */
export function getDisplayName(indicatorId: string): string {
  const translation = INDICATOR_TRANSLATIONS[indicatorId];
  if (translation) return translation.displayName;

  // Fallback: Convert ID to readable name
  return indicatorId
    .replace(/_/g, ' ')
    .replace(/\d+/g, '')
    .replace(/\b\w/g, c => c.toUpperCase())
    .trim();
}

/**
 * Generate a news-style headline for a signal based on indicator status
 */
export function getSignalHeadline(indicatorId: string, status: 'amber' | 'red'): string {
  const translation = INDICATOR_TRANSLATIONS[indicatorId];
  if (!translation) {
    return `${getDisplayName(indicatorId)} at ${status} level`;
  }
  return status === 'red' ? translation.redHeadline : translation.amberHeadline;
}

/**
 * Get impact description for an indicator at a given status
 */
export function getImpact(indicatorId: string, status: 'amber' | 'red'): string {
  const translation = INDICATOR_TRANSLATIONS[indicatorId];
  if (!translation) {
    return `${getDisplayName(indicatorId)} showing elevated activity`;
  }
  return status === 'red' ? translation.redImpact : translation.amberImpact;
}

/**
 * Get action recommendation for an indicator at a given status
 */
export function getAction(indicatorId: string, status: 'amber' | 'red'): string {
  const translation = INDICATOR_TRANSLATIONS[indicatorId];
  if (!translation) {
    return 'Monitor the situation and review your preparedness';
  }
  return status === 'red' ? translation.redAction : translation.amberAction;
}

/**
 * Get outcome phrase for composing the outcome sentence
 */
export function getOutcomePhrase(indicatorId: string, status: 'amber' | 'red'): string {
  const translation = INDICATOR_TRANSLATIONS[indicatorId];
  if (!translation) {
    return `changes in ${getDisplayName(indicatorId).toLowerCase()}`;
  }
  return status === 'red' ? translation.redOutcomePhrase : translation.amberOutcomePhrase;
}
