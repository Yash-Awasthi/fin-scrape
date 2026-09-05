/**
 * Indicator Display Utilities
 *
 * Centralized formatting for sources, units, domains, and descriptions.
 * Converts raw system values to human-readable display text.
 */

import { IndicatorData } from '../types';

// ============================================================================
// CRITICAL INDICATORS
// ============================================================================

export const CRITICAL_INDICATORS = [
  'market_01_intraday_swing',
  'info_02_deepfake_shocks',
  'nato_high_readiness',
  'national_guard_metros',
  'dhs_removal_expansion',
  'luxury_01_collapse',
  'taiwan_pla_activity',
];

export function isCriticalIndicator(indicatorId: string): boolean {
  return CRITICAL_INDICATORS.includes(indicatorId);
}

// ============================================================================
// SOURCE DISPLAY
// ============================================================================

export const INDICATOR_SOURCES: Record<string, { name: string; abbrev: string }> = {
  // Global Conflict
  'taiwan_pla_activity': { name: 'Taiwan Ministry of National Defense', abbrev: 'Taiwan MND' },
  'global_conflict_intensity': { name: 'Armed Conflict Location & Event Data', abbrev: 'ACLED' },
  'nato_high_readiness': { name: 'NATO / SHAPE', abbrev: 'NATO' },
  'nuclear_test_activity': { name: 'News RSS / CNS', abbrev: 'News RSS' },
  'defense_spending_growth': { name: 'SIPRI Military Expenditure Database', abbrev: 'SIPRI' },
  'hormuz_war_risk': { name: "Lloyd's of London / Shipping Industry", abbrev: "Lloyd's" },
  'travel_01_advisories': { name: 'State Department Travel Advisories', abbrev: 'State Dept' },

  // Economy
  'econ_01_treasury_tail': { name: 'Treasury Direct / Bloomberg', abbrev: 'Treasury' },
  'econ_02_grocery_cpi': { name: 'Bureau of Labor Statistics', abbrev: 'BLS' },
  'market_01_intraday_swing': { name: 'Bloomberg / Treasury', abbrev: 'Bloomberg' },
  'luxury_01_collapse': { name: 'Bloomberg / S&P', abbrev: 'Bloomberg' },
  'green_g1_gdp_rates': { name: 'Bureau of Economic Analysis', abbrev: 'BEA' },
  'bank_01_failures': { name: 'FDIC Failed Bank List', abbrev: 'FDIC' },
  'bank_02_discount_window': { name: 'Federal Reserve H.4.1', abbrev: 'Fed' },
  'bank_03_deposit_flow': { name: 'Federal Reserve H.8', abbrev: 'Fed' },
  'housing_01_delinquency': { name: 'Mortgage Bankers Association', abbrev: 'MBA' },
  'housing_03_rate_shock': { name: 'Freddie Mac PMMS', abbrev: 'Freddie Mac' },

  // Jobs & Labor
  'job_01_jobless_claims': { name: 'Department of Labor', abbrev: 'DOL' },
  'job_01_strike_days': { name: 'BLS / Cornell ILR', abbrev: 'BLS' },
  'supply_pharmacy_shortage': { name: 'FDA Drug Shortage Database', abbrev: 'FDA' },

  // Rights & Governance
  'power_01_ai_surveillance': { name: 'OpenStates API', abbrev: 'OpenStates' },
  'civil_01_acled_protests': { name: 'ACLED', abbrev: 'ACLED' },
  'liberty_litigation_count': { name: 'CourtListener', abbrev: 'CourtListener' },

  // Security & Infrastructure
  'cyber_01_cisa_kev': { name: 'CISA', abbrev: 'CISA' },
  'grid_01_pjm_outages': { name: 'NWS API', abbrev: 'NWS' },
  'bio_01_h2h_countries': { name: 'WHO Disease Outbreak News', abbrev: 'WHO' },
  'cdc_health_alerts': { name: 'CDC RSS', abbrev: 'CDC' },
  'fema_disaster_declarations': { name: 'FEMA API', abbrev: 'FEMA' },
  'fda_drug_shortages': { name: 'FDA Drug Shortages', abbrev: 'FDA' },
  'supply_01_port_congestion': { name: 'Marine Exchange / Port Authorities', abbrev: 'Marine Ex' },
  'supply_02_freight_index': { name: 'Freightos Baltic Index', abbrev: 'FBX' },
  'supply_03_chip_lead_time': { name: 'News RSS / Industry Data', abbrev: 'News RSS' },
  'energy_02_nat_gas_storage': { name: 'EIA Natural Gas Weekly', abbrev: 'EIA' },
  'energy_03_grid_emergency': { name: 'EIA / NERC', abbrev: 'EIA' },
  'telecom_01_bgp_anomalies': { name: 'BGPStream / RIPE NCC', abbrev: 'BGPStream' },
  'telecom_02_cell_outages': { name: 'Downdetector / FCC', abbrev: 'FCC' },
  'telecom_03_undersea_cable': { name: 'TeleGeography / Industry', abbrev: 'TeleGeo' },
  'flight_01_ground_stops': { name: 'FAA Operations', abbrev: 'FAA' },
  'flight_02_delay_pct': { name: 'FAA / FlightAware', abbrev: 'FAA' },
  'flight_03_tfr_count': { name: 'FAA NOTAM System', abbrev: 'FAA' },
  'travel_03_tsa_throughput': { name: 'TSA Checkpoint Data', abbrev: 'TSA' },
  'water_01_reservoir_level': { name: 'USBR / State Water Resources', abbrev: 'USBR' },
  'water_02_treatment_alerts': { name: 'EPA Safe Drinking Water', abbrev: 'EPA' },

  // Domestic Control
  'ice_detention_surge': { name: 'ICE Statistics', abbrev: 'ICE' },
  'federal_regulations': { name: 'Federal Register', abbrev: 'Fed Register' },
  'congress_activity': { name: 'GovTrack', abbrev: 'GovTrack' },
  'travel_02_border_wait': { name: 'CBP Border Wait Times', abbrev: 'CBP' },

  // Oil Axis
  'spr_01_level': { name: 'EIA', abbrev: 'EIA' },
  'oil_03_ofac_designations': { name: 'Treasury OFAC', abbrev: 'OFAC' },

  // AI Window
  'labor_ai_01_layoffs': { name: 'Layoffs.fyi RSS', abbrev: 'Layoffs.fyi' },
  'cult_media_01_trends': { name: 'Google Trends', abbrev: 'Google' },
};

export function getSourceDisplay(indicatorId: string, rawSource?: string): string {
  const mapped = INDICATOR_SOURCES[indicatorId];
  if (mapped) return mapped.abbrev;
  if (rawSource && rawSource !== 'mock_data' && rawSource !== 'Unknown' && rawSource !== 'MOCK') {
    return rawSource;
  }
  return 'Pending';
}

export function getSourceFull(indicatorId: string): string {
  const mapped = INDICATOR_SOURCES[indicatorId];
  return mapped?.name || 'Data integration pending';
}

export function hasValidSource(indicatorId: string): boolean {
  return indicatorId in INDICATOR_SOURCES;
}

// ============================================================================
// UNIT FORMATTING
// ============================================================================

const UNIT_DISPLAY: Record<string, string> = {
  'incursions_per_week': '/week',
  'incursions/week': '/week',
  'events_per_day': ' events/day',
  'events/day': ' events/day',
  'basis_points': ' bp',
  'bps': ' bp',
  'percent': '%',
  '%': '%',
  'thousands': 'K',
  'index': '',
  'systems': ' systems',
  'daily_incursions': '/day',
  'milestone_score': '',
  'bills_per_month': ' bills/mo',
  'bills/month': ' bills/mo',
  'daily_average': '/day',
  'ratio': '',
  'million_barrels': 'M bbl',
  'M_barrels': 'M bbl',
  'percentage': '%',
  'countries': ' countries',
  'K_jobs': 'K jobs',
  'days': ' days',
  'weeks': ' weeks',
  'events': ' events',
  'metros': ' metros',
  'cities': ' cities',
  'cases': ' cases',
  'attacks': ' attacks',
  'incidents': ' incidents',
  'score': '',
  'index_value': '',
};

export function formatValue(value: number | string | null | undefined, unit?: string): string {
  if (value === null || value === undefined) return 'N/A';

  const numValue = typeof value === 'number' ? value : parseFloat(value);
  if (isNaN(numValue)) return String(value);

  const displayUnit = unit ? (UNIT_DISPLAY[unit] || ` ${unit.replace(/_/g, ' ')}`) : '';

  // Smart number formatting
  if (Math.abs(numValue) >= 1000000) {
    return `${(numValue / 1000000).toFixed(1)}M${displayUnit}`;
  }
  if (Math.abs(numValue) >= 1000) {
    return `${(numValue / 1000).toFixed(1)}K${displayUnit}`;
  }
  if (numValue < 1 && numValue > 0) {
    return `${numValue.toFixed(2)}${displayUnit}`;
  }
  if (Number.isInteger(numValue)) {
    return `${numValue}${displayUnit}`;
  }
  return `${numValue.toFixed(1)}${displayUnit}`;
}

export function formatUnit(unit?: string): string {
  if (!unit) return '';
  return UNIT_DISPLAY[unit] || unit.replace(/_/g, ' ');
}

// ============================================================================
// DOMAIN FORMATTING
// ============================================================================

const DOMAIN_DISPLAY: Record<string, string> = {
  'global_conflict': 'Global Conflict',
  'economy': 'Economy',
  'domestic_control': 'Domestic Control',
  'supply_chain': 'Supply Chain',
  'security_infrastructure': 'Security & Infra',
  'energy': 'Energy',
  'oil_axis': 'Oil Axis',
  'ai_window': 'AI Window',
  'jobs_labor': 'Jobs & Labor',
  'rights_governance': 'Rights & Gov',
  'social_cohesion': 'Social Cohesion',
  // Handle uppercase variants
  'GLOBAL_CONFLICT': 'Global Conflict',
  'ECONOMY': 'Economy',
  'DOMESTIC_CONTROL': 'Domestic Control',
  'SUPPLY_CHAIN': 'Supply Chain',
  'SECURITY_INFRASTRUCTURE': 'Security & Infra',
  'ENERGY': 'Energy',
  'OIL_AXIS': 'Oil Axis',
  'AI_WINDOW': 'AI Window',
  'JOBS_LABOR': 'Jobs & Labor',
  'RIGHTS_GOVERNANCE': 'Rights & Gov',
  'SOCIAL_COHESION': 'Social Cohesion',
};

export function formatDomain(raw: string): string {
  return DOMAIN_DISPLAY[raw] || raw.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}

// ============================================================================
// INDICATOR DESCRIPTIONS
// ============================================================================

export const INDICATOR_DESCRIPTIONS: Record<string, string> = {
  // Global Conflict
  'taiwan_pla_activity': 'Daily PLA aircraft and naval incursions near Taiwan. Higher numbers signal increased military pressure and potential for escalation.',
  'taiwan_exclusion_zone': 'Tracks Chinese military exclusion zones near Taiwan — a precursor to blockade or conflict that would devastate semiconductor supply chains.',
  'global_conflict_intensity': "ACLED's global armed conflict intensity. Elevated levels correlate with energy price spikes, refugee flows, and supply disruptions.",
  'nato_high_readiness': "NATO high-readiness force activations beyond routine exercises. Elevated levels haven't been seen since the Cold War.",
  'russia_nato_escalation': 'Composite escalation index tracking Russia-NATO confrontation risk across military, diplomatic, and nuclear dimensions.',
  'nuclear_01_tests': 'Nuclear and ballistic missile tests by any state. Activity here changes the global threat calculus for months.',
  'defense_spending_growth': 'Global military spending growth rate. Sustained increases signal arms race dynamics and reduced resources for civilian needs.',
  'hormuz_war_risk': "Shipping insurance premium through the Strait of Hormuz. 20% of global oil transits here — spikes mean energy price shocks.",

  // Economy
  'econ_01_treasury_tail': "Gap between expected and actual demand at Treasury auctions. Wide tails signal that investors are losing confidence in US debt.",
  'econ_02_grocery_cpi': '3-month annualized food inflation. This is the number that hits your grocery bill directly.',
  'market_01_intraday_swing': 'Intraday swings in the 10-year Treasury yield. Extreme volatility preceded both the 2008 and 2020 crises.',
  'green_g1_gdp_rates': "Real GDP growth — the one green flag. Strong growth with low rates means the economy has runway. Absence of this is a warning.",
  'luxury_01_collapse': "Luxury goods stock performance. When luxury collapses, recession follows within 3-6 months. It's the canary for consumer spending.",

  // Domestic Control
  'ice_detention_surge': 'ICE detention facility utilization. Above 85% historically correlates with expanded enforcement operations in civilian spaces.',
  'dhs_removal_expansion': 'Cities where DHS has activated expedited removal. Expansion signals reduced due process protections.',
  'national_guard_metros': 'Metropolitan areas with National Guard deployment for non-disaster reasons. A Phase 5 critical trigger.',

  // Security & Infrastructure
  'cyber_01_cisa_kev': 'Critical cybersecurity vulnerabilities tracked by CISA over 90 days. High counts mean the attack surface on infrastructure is expanding.',
  'cyber_02_ai_ransomware': 'AI-assisted ransomware attacks on infrastructure over 90 days. The intersection of AI capability and cybercrime.',
  'grid_01_pjm_outages': 'Major power outages per quarter tracked by NERC. Your PJM grid region matters — Northeast exposure.',
  'bio_01_h2h_countries': 'Countries reporting sustained human-to-human transmission of novel pathogens. The pandemic early warning.',

  // AI Window
  'compute_01_training_cost': 'AI capability milestones crossed versus projected timeline. Acceleration here reshapes job markets faster than policy can adapt.',
  'labor_ai_01_layoffs': 'Monthly layoffs where companies cite AI as the primary driver. The leading edge of the displacement wave.',
  'info_02_deepfake_shocks': 'Market-moving deepfake events per quarter. When fake content moves real markets, trust in information erodes.',

  // Jobs & Labor
  'job_01_jobless_claims': 'Weekly unemployment claims — the earliest signal of labor market stress. Spikes here precede recession announcements.',
  'job_01_strike_days': 'Worker-days lost to strikes per month. Rising strike activity signals wage pressure and supply disruption risk.',
  'supply_pharmacy_shortage': 'Critical medications in shortage per FDA tracking. Affects prescription availability for your family directly.',

  // Rights & Governance
  'power_01_ai_surveillance': 'AI surveillance bills advancing through state legislatures per month. The legislative velocity of the surveillance state.',
  'civil_01_acled_protests': 'Daily average of US protest events. Elevated levels signal social tension and potential for disruption.',
  'power_02_dod_autonomy': 'DoD autonomous weapons deployment posture. The gap between human oversight and machine decision-making in warfare.',
  'hill_control_legislation': '"Control bills" — legislation expanding executive authority — advancing in Congress over 30 days.',
  'liberty_01_litigation': 'Major constitutional cases in federal courts. The legal frontline of rights protection.',

  // Oil Axis
  'oil_01_russian_brics': 'Share of Russian oil exports going to BRICS nations. Higher = stronger sanctions-evasion infrastructure.',
  'oil_02_mbridge_settlements': 'mBridge CBDC settlement volume for oil trades. Measures de-dollarization velocity in energy markets.',
  'oil_03_jodi_inventory': 'OECD oil inventory levels. Buffer against supply shocks — low inventories mean higher price volatility.',
  'oil_04_refinery_ratio': 'Asia-to-OECD refinery capacity ratio. Measures the shift of refining power toward countries outside Western control.',
  'spr_01_level': 'US Strategic Petroleum Reserve level. Emergency buffer against supply disruptions.',
  'ofac_01_designations': 'India/China oil-related sanctions designations in 30 days. Measures how actively the US is trying to enforce oil sanctions.',

  // Social Cohesion
  'education_01_closures': "Non-weather school closures. A canary indicator — when schools close for non-obvious reasons, something systemic is usually wrong.",
};

export function getDescription(indicatorId: string, fallback?: string): string {
  return INDICATOR_DESCRIPTIONS[indicatorId] || fallback || 'Monitoring this indicator for changes.';
}

// ============================================================================
// DEDUPLICATION & SORTING
// ============================================================================

function severityRank(level: string): number {
  return { 'red': 3, 'amber': 2, 'green': 1, 'unknown': 0 }[level] || 0;
}

export function deduplicateIndicators(indicators: IndicatorData[]): IndicatorData[] {
  const seen = new Map<string, IndicatorData>();
  for (const ind of indicators) {
    const existing = seen.get(ind.id);
    if (!existing || severityRank(ind.status.level) > severityRank(existing.status.level)) {
      seen.set(ind.id, ind);
    }
  }
  return Array.from(seen.values());
}

export function sortIndicators(indicators: IndicatorData[]): IndicatorData[] {
  return [...indicators].sort((a, b) => {
    // 1. Red first, then amber, then green
    const statusOrder = severityRank(b.status.level) - severityRank(a.status.level);
    if (statusOrder !== 0) return statusOrder;

    // 2. Critical indicators first within same status
    const aCrit = isCriticalIndicator(a.id) ? 1 : 0;
    const bCrit = isCriticalIndicator(b.id) ? 1 : 0;
    if (bCrit !== aCrit) return bCrit - aCrit;

    // 3. Worsening trend first within same status + criticality
    const trendOrder: Record<string, number> = { 'worsening': 3, 'up': 3, 'stable': 2, 'improving': 1, 'down': 1 };
    const aTrend = trendOrder[a.status.trend || 'stable'] || 2;
    const bTrend = trendOrder[b.status.trend || 'stable'] || 2;
    return bTrend - aTrend;
  });
}

// ============================================================================
// TIME FORMATTING
// ============================================================================

export function formatTimeAgo(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;

  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

// ============================================================================
// HOUSEHOLD RELEVANCE
// ============================================================================

export const INDICATOR_HOUSEHOLD_RELEVANCE: Record<string, { impact: string; action: string }> = {
  // Global Conflict
  'taiwan_pla_activity': {
    impact: 'Escalation could disrupt semiconductor supply, affecting electronics, medical devices, and car availability. Energy prices would spike globally.',
    action: 'Ensure prescriptions are filled. If car shopping, don\'t delay. Keep electronics inventory stable.',
  },
  'taiwan_exclusion_zone': {
    impact: 'A military exclusion zone would immediately spike shipping costs and potentially ground flights over the Pacific.',
    action: 'Avoid booking non-refundable Asia travel. Check medication supply chains.',
  },
  'global_conflict_intensity': {
    impact: 'Elevated conflict drives oil prices, refugee migration, and defense spending (crowding out civilian programs).',
    action: 'Monitor fuel costs. Consider locking in heating oil or propane if red.',
  },
  'nato_high_readiness': {
    impact: 'Activated NATO forces signal serious escalation risk. Historically correlates with increased defense spending and reduced civilian budgets.',
    action: 'Review emergency fund adequacy. Understand your area\'s evacuation routes if near military infrastructure.',
  },
  'russia_nato_escalation': {
    impact: 'Direct NATO-Russia confrontation would reshape global trade, spike energy costs, and potentially affect food supply chains.',
    action: 'Maintain 30-day food supply. Understand natural gas heating alternatives.',
  },
  'nuclear_01_tests': {
    impact: 'Nuclear proliferation changes the geopolitical landscape for years. Immediate market volatility likely.',
    action: 'Ensure portfolio diversification. Know your local emergency alert systems.',
  },
  'hormuz_war_risk': {
    impact: '20% of global oil moves through Hormuz. Disruption means immediate gas price spikes of 20-50%.',
    action: 'Fill gas tanks when amber. Consider fuel-efficient trip consolidation.',
  },

  // Economy
  'econ_01_treasury_tail': {
    impact: 'Treasury market dysfunction signals broader financial stress. Mortgage rates and credit availability could shift rapidly.',
    action: 'Lock in favorable mortgage rates if red. Avoid large financed purchases during volatility.',
  },
  'econ_02_grocery_cpi': {
    impact: 'This directly hits your grocery bill. Elevated food inflation means prioritizing budget flexibility.',
    action: 'Stock up on non-perishables before further increases. Consider bulk buying staples.',
  },
  'market_01_intraday_swing': {
    impact: 'Extreme Treasury volatility often precedes recession. Your 401k and investment portfolio will feel this.',
    action: 'Avoid panic selling. Ensure emergency fund covers 6 months. Review bond allocations.',
  },
  'green_g1_gdp_rates': {
    impact: 'Strong GDP with low rates means economic stability. Absence is a warning for job security.',
    action: 'This is a green flag. When present, conditions favor large purchases and career moves.',
  },
  'luxury_01_collapse': {
    impact: 'Luxury sector collapse precedes recession by 3-6 months. Employment and housing markets follow.',
    action: 'Delay large discretionary purchases. Shore up emergency savings.',
  },

  // Domestic Control
  'ice_detention_surge': {
    impact: 'Elevated detention often correlates with workplace raids and community disruption in certain industries.',
    action: 'Know your rights. Ensure family emergency contacts are current. Have documentation accessible.',
  },
  'dhs_removal_expansion': {
    impact: 'Expanded enforcement changes community dynamics and can affect local businesses and services.',
    action: 'Maintain family communication plans. Know local immigrant rights organizations.',
  },
  'national_guard_metros': {
    impact: 'Guard deployment indicates civil unrest potential. May affect commutes, events, and downtown access.',
    action: 'Have alternative commute routes planned. Keep vehicle fuel above half tank.',
  },

  // Security & Infrastructure
  'cyber_01_cisa_kev': {
    impact: 'Critical vulnerabilities mean your devices, bank accounts, and infrastructure are at risk.',
    action: 'Ensure all devices are updated. Enable 2FA everywhere. Review password strength.',
  },
  'cyber_02_ai_ransomware': {
    impact: 'AI-assisted attacks target hospitals, utilities, and supply chains. Service disruptions possible.',
    action: 'Keep offline copies of critical documents. Know your utility\'s outage notification system.',
  },
  'grid_01_pjm_outages': {
    impact: 'Grid stress means potential rolling blackouts or extended outages during peak demand.',
    action: 'Maintain backup power for essentials. Know your medical device backup plans.',
  },
  'bio_01_h2h_countries': {
    impact: 'Human-to-human transmission of novel pathogens is how pandemics start. Early warning matters.',
    action: 'Stock N95 masks and sanitizer. Review remote work/school options. Keep prescriptions current.',
  },

  // AI Window
  'compute_01_training_cost': {
    impact: 'Rapid AI advancement accelerates job market disruption faster than retraining programs can adapt.',
    action: 'Assess your role\'s automation risk. Invest in complementary skills. Review career contingencies.',
  },
  'labor_ai_01_layoffs': {
    impact: 'AI-driven layoffs signal which sectors are most vulnerable. Could affect your industry.',
    action: 'Understand your industry\'s AI exposure. Maintain updated resume and network.',
  },
  'info_02_deepfake_shocks': {
    impact: 'Deepfakes that move markets mean you can\'t trust what you see. Financial decisions need verification.',
    action: 'Verify major news through multiple sources before acting. Be skeptical of viral content.',
  },

  // Jobs & Labor
  'job_01_jobless_claims': {
    impact: 'Rising claims are the earliest recession signal. Your job security depends on your industry.',
    action: 'Build emergency fund to 6+ months. Don\'t make career moves based on optimism alone.',
  },
  'job_01_strike_days': {
    impact: 'Strikes disrupt supply chains and can affect specific products and services.',
    action: 'Monitor industries affecting your regular purchases. Stock up if relevant sectors are striking.',
  },
  'supply_pharmacy_shortage': {
    impact: 'Medication shortages directly affect your family\'s health. Some substitutions may not be available.',
    action: 'Fill prescriptions before they\'re due. Ask pharmacist about therapeutic alternatives.',
  },

  // Rights & Governance
  'power_01_ai_surveillance': {
    impact: 'Surveillance expansion changes privacy expectations in public and digital spaces.',
    action: 'Review digital privacy settings. Understand your state\'s surveillance legislation.',
  },
  'civil_01_acled_protests': {
    impact: 'Elevated protest activity can disrupt downtown areas, events, and routine activities.',
    action: 'Stay informed about local protest schedules. Have alternative routes planned.',
  },
  'power_02_dod_autonomy': {
    impact: 'Autonomous weapons reduce human oversight in military decisions. Signals broader automation trends.',
    action: 'Understand your area\'s proximity to military installations. Monitor policy debates.',
  },
  'hill_control_legislation': {
    impact: 'Control legislation changes the balance of power. May affect your rights and protections.',
    action: 'Know your representatives. Engage with civic processes that matter to you.',
  },

  // Oil Axis
  'oil_01_russian_brics': {
    impact: 'Sanctions evasion weakens Western economic leverage and can destabilize energy markets.',
    action: 'Monitor energy prices. Diversify heating sources if possible.',
  },
  'oil_02_mbridge_settlements': {
    impact: 'De-dollarization in oil trades affects US economic influence and potentially the dollar\'s value.',
    action: 'Consider international diversification in investments. Monitor currency trends.',
  },
  'oil_03_jodi_inventory': {
    impact: 'Low oil inventories mean higher price volatility. Gas and heating costs become unpredictable.',
    action: 'Fill up when prices dip. Consider locking in heating oil rates.',
  },
  'spr_01_level': {
    impact: 'Low SPR means less cushion against supply shocks. Prices spike faster and higher.',
    action: 'Same as oil inventory — maintain fuel reserves when possible.',
  },

  // Social Cohesion
  'education_01_closures': {
    impact: 'Non-weather closures signal community stress — from threats to outbreaks to civil unrest.',
    action: 'Have childcare backup plans. Understand your school\'s emergency protocols.',
  },
};

export function getHouseholdRelevance(indicatorId: string): { impact: string; action: string } | null {
  return INDICATOR_HOUSEHOLD_RELEVANCE[indicatorId] || null;
}

// ============================================================================
// INDICATOR CONNECTIONS
// ============================================================================

export const INDICATOR_CONNECTIONS: Record<string, string[]> = {
  // Global Conflict cluster
  'taiwan_pla_activity': ['taiwan_exclusion_zone', 'global_conflict_intensity', 'nato_high_readiness', 'defense_spending_growth'],
  'taiwan_exclusion_zone': ['taiwan_pla_activity', 'hormuz_war_risk', 'oil_03_jodi_inventory'],
  'global_conflict_intensity': ['taiwan_pla_activity', 'russia_nato_escalation', 'defense_spending_growth', 'civil_01_acled_protests'],
  'nato_high_readiness': ['russia_nato_escalation', 'global_conflict_intensity', 'defense_spending_growth'],
  'russia_nato_escalation': ['nato_high_readiness', 'nuclear_01_tests', 'oil_01_russian_brics', 'global_conflict_intensity'],
  'nuclear_01_tests': ['russia_nato_escalation', 'defense_spending_growth', 'global_conflict_intensity'],
  'hormuz_war_risk': ['oil_03_jodi_inventory', 'spr_01_level', 'econ_02_grocery_cpi', 'taiwan_exclusion_zone'],
  'defense_spending_growth': ['nato_high_readiness', 'global_conflict_intensity', 'nuclear_01_tests'],

  // Economy cluster
  'econ_01_treasury_tail': ['market_01_intraday_swing', 'luxury_01_collapse', 'green_g1_gdp_rates'],
  'econ_02_grocery_cpi': ['job_01_jobless_claims', 'supply_pharmacy_shortage', 'hormuz_war_risk'],
  'market_01_intraday_swing': ['econ_01_treasury_tail', 'luxury_01_collapse', 'job_01_jobless_claims'],
  'green_g1_gdp_rates': ['job_01_jobless_claims', 'econ_01_treasury_tail', 'luxury_01_collapse'],
  'luxury_01_collapse': ['market_01_intraday_swing', 'job_01_jobless_claims', 'econ_01_treasury_tail'],

  // Domestic Control cluster
  'ice_detention_surge': ['dhs_removal_expansion', 'national_guard_metros'],
  'dhs_removal_expansion': ['ice_detention_surge', 'hill_control_legislation', 'national_guard_metros'],
  'national_guard_metros': ['civil_01_acled_protests', 'ice_detention_surge', 'dhs_removal_expansion'],

  // Security & Infrastructure cluster
  'cyber_01_cisa_kev': ['cyber_02_ai_ransomware', 'grid_01_pjm_outages'],
  'cyber_02_ai_ransomware': ['cyber_01_cisa_kev', 'compute_01_training_cost', 'grid_01_pjm_outages'],
  'grid_01_pjm_outages': ['cyber_01_cisa_kev', 'cyber_02_ai_ransomware', 'hormuz_war_risk'],
  'bio_01_h2h_countries': ['supply_pharmacy_shortage', 'education_01_closures'],

  // AI Window cluster
  'compute_01_training_cost': ['labor_ai_01_layoffs', 'info_02_deepfake_shocks', 'cyber_02_ai_ransomware'],
  'labor_ai_01_layoffs': ['compute_01_training_cost', 'job_01_jobless_claims', 'job_01_strike_days'],
  'info_02_deepfake_shocks': ['compute_01_training_cost', 'power_01_ai_surveillance', 'civil_01_acled_protests'],

  // Jobs & Labor cluster
  'job_01_jobless_claims': ['labor_ai_01_layoffs', 'luxury_01_collapse', 'green_g1_gdp_rates'],
  'job_01_strike_days': ['labor_ai_01_layoffs', 'supply_pharmacy_shortage', 'job_01_jobless_claims'],
  'supply_pharmacy_shortage': ['bio_01_h2h_countries', 'hormuz_war_risk', 'oil_03_jodi_inventory'],

  // Rights & Governance cluster
  'power_01_ai_surveillance': ['hill_control_legislation', 'info_02_deepfake_shocks', 'power_02_dod_autonomy'],
  'civil_01_acled_protests': ['national_guard_metros', 'education_01_closures', 'global_conflict_intensity'],
  'power_02_dod_autonomy': ['compute_01_training_cost', 'power_01_ai_surveillance', 'defense_spending_growth'],
  'hill_control_legislation': ['power_01_ai_surveillance', 'dhs_removal_expansion', 'liberty_01_litigation'],
  'liberty_01_litigation': ['hill_control_legislation', 'power_01_ai_surveillance'],

  // Oil Axis cluster
  'oil_01_russian_brics': ['oil_02_mbridge_settlements', 'ofac_01_designations', 'russia_nato_escalation'],
  'oil_02_mbridge_settlements': ['oil_01_russian_brics', 'ofac_01_designations'],
  'oil_03_jodi_inventory': ['hormuz_war_risk', 'spr_01_level', 'econ_02_grocery_cpi'],
  'oil_04_refinery_ratio': ['oil_03_jodi_inventory', 'oil_01_russian_brics'],
  'spr_01_level': ['oil_03_jodi_inventory', 'hormuz_war_risk'],
  'ofac_01_designations': ['oil_01_russian_brics', 'oil_02_mbridge_settlements'],

  // Social Cohesion cluster
  'education_01_closures': ['bio_01_h2h_countries', 'civil_01_acled_protests', 'national_guard_metros'],
};

export function getConnectedIndicators(indicatorId: string): string[] {
  return INDICATOR_CONNECTIONS[indicatorId] || [];
}

// ============================================================================
// PHASE RELEVANCE
// ============================================================================

export const PHASE_RELEVANCE: Record<string, number[]> = {
  // Which phases particularly care about this indicator
  // Phase 0-9 mapping from the household resilience system

  // Critical for early phases (0-2): economic stability
  'econ_01_treasury_tail': [0, 1, 2],
  'econ_02_grocery_cpi': [0, 1, 2, 3],
  'green_g1_gdp_rates': [0, 1, 2],
  'job_01_jobless_claims': [0, 1, 2, 3],

  // Mid phases (3-5): supply chain and infrastructure
  'supply_pharmacy_shortage': [3, 4, 5],
  'grid_01_pjm_outages': [3, 4, 5, 6],
  'cyber_01_cisa_kev': [3, 4, 5],
  'oil_03_jodi_inventory': [3, 4, 5],
  'spr_01_level': [3, 4, 5],

  // Critical triggers (Phase 5+)
  'national_guard_metros': [5, 6, 7],
  'bio_01_h2h_countries': [5, 6, 7],
  'taiwan_pla_activity': [5, 6, 7, 8],
  'taiwan_exclusion_zone': [6, 7, 8],

  // Escalation indicators (Phase 6+)
  'nato_high_readiness': [6, 7, 8],
  'russia_nato_escalation': [6, 7, 8],
  'nuclear_01_tests': [7, 8, 9],
  'hormuz_war_risk': [6, 7, 8],

  // Domestic control (Phase 4+)
  'ice_detention_surge': [4, 5, 6],
  'dhs_removal_expansion': [4, 5, 6, 7],

  // AI disruption (Phase 3+)
  'compute_01_training_cost': [3, 4, 5],
  'labor_ai_01_layoffs': [3, 4, 5],
  'info_02_deepfake_shocks': [4, 5, 6],

  // Market crash indicators (any phase but especially mid)
  'market_01_intraday_swing': [2, 3, 4, 5],
  'luxury_01_collapse': [2, 3, 4],

  // Civil stability (Phase 4+)
  'civil_01_acled_protests': [4, 5, 6],
  'education_01_closures': [4, 5, 6],

  // Governance (all phases matter)
  'power_01_ai_surveillance': [3, 4, 5, 6],
  'hill_control_legislation': [4, 5, 6, 7],
  'power_02_dod_autonomy': [5, 6, 7],
};

export function getPhaseRelevance(indicatorId: string): number[] {
  return PHASE_RELEVANCE[indicatorId] || [];
}

export function getPhaseRelevanceLabel(phases: number[]): string {
  if (phases.length === 0) return 'All phases';
  const min = Math.min(...phases);
  const max = Math.max(...phases);
  if (min === max) return `Phase ${min}`;
  return `Phases ${min}–${max}`;
}

// ============================================================================
// EXPANDED SOURCE INFO
// ============================================================================

export interface SourceInfo {
  name: string;
  abbrev: string;
  description?: string;
  url?: string;
  updateFrequency?: 'real-time' | 'hourly' | 'daily' | 'weekly' | 'monthly';
}

export const INDICATOR_SOURCES_FULL: Record<string, SourceInfo> = {
  // Global Conflict
  'taiwan_pla_activity': {
    name: 'Taiwan Ministry of National Defense',
    abbrev: 'Taiwan MND',
    description: 'Official daily reports on PLA aircraft and naval vessel incursions into Taiwan\'s ADIZ.',
    url: 'https://www.mnd.gov.tw',
    updateFrequency: 'daily',
  },
  'global_conflict_intensity': {
    name: 'Armed Conflict Location & Event Data',
    abbrev: 'ACLED',
    description: 'Academic consortium tracking conflict events globally with standardized methodology.',
    url: 'https://acleddata.com',
    updateFrequency: 'weekly',
  },
  'nato_high_readiness': {
    name: 'NATO / SHAPE',
    abbrev: 'NATO',
    description: 'NATO Supreme Headquarters Allied Powers Europe force posture updates.',
    url: 'https://shape.nato.int',
    updateFrequency: 'daily',
  },
  'hormuz_war_risk': {
    name: "Lloyd's of London",
    abbrev: "Lloyd's",
    description: 'War risk insurance premiums for vessels transiting the Strait of Hormuz.',
    url: 'https://www.lloyds.com',
    updateFrequency: 'weekly',
  },

  // Economy
  'econ_01_treasury_tail': {
    name: 'Treasury Direct / Bloomberg',
    abbrev: 'Treasury',
    description: 'Treasury auction results including bid-to-cover ratios and tail spreads.',
    url: 'https://www.treasurydirect.gov',
    updateFrequency: 'weekly',
  },
  'econ_02_grocery_cpi': {
    name: 'Bureau of Labor Statistics',
    abbrev: 'BLS',
    description: 'Consumer Price Index for food at home, seasonally adjusted.',
    url: 'https://www.bls.gov/cpi',
    updateFrequency: 'monthly',
  },
  'market_01_intraday_swing': {
    name: 'Bloomberg / Treasury',
    abbrev: 'Bloomberg',
    description: 'Intraday yield volatility on 10-year Treasury notes.',
    url: 'https://www.bloomberg.com',
    updateFrequency: 'real-time',
  },

  // Domestic Control
  'ice_detention_surge': {
    name: 'TRAC Immigration',
    abbrev: 'TRAC',
    description: 'Syracuse University research center analyzing immigration enforcement data.',
    url: 'https://trac.syr.edu',
    updateFrequency: 'monthly',
  },
  'national_guard_metros': {
    name: 'National Guard Bureau',
    abbrev: 'NGB',
    description: 'Official deployment status for National Guard units.',
    url: 'https://www.nationalguard.mil',
    updateFrequency: 'weekly',
  },

  // Security & Infrastructure
  'cyber_01_cisa_kev': {
    name: 'CISA',
    abbrev: 'CISA',
    description: 'Known Exploited Vulnerabilities catalog maintained by the Cybersecurity and Infrastructure Security Agency.',
    url: 'https://www.cisa.gov/known-exploited-vulnerabilities-catalog',
    updateFrequency: 'daily',
  },
  'grid_01_pjm_outages': {
    name: 'NERC / EIA',
    abbrev: 'NERC',
    description: 'North American Electric Reliability Corporation grid reliability reports.',
    url: 'https://www.nerc.com',
    updateFrequency: 'monthly',
  },
  'bio_01_h2h_countries': {
    name: 'WHO Disease Outbreak News',
    abbrev: 'WHO',
    description: 'World Health Organization surveillance for novel pathogen transmission.',
    url: 'https://www.who.int/emergencies/disease-outbreak-news',
    updateFrequency: 'daily',
  },

  // AI Window
  'compute_01_training_cost': {
    name: 'Epoch AI',
    abbrev: 'Epoch AI',
    description: 'Research organization tracking AI compute trends and capability milestones.',
    url: 'https://epochai.org',
    updateFrequency: 'monthly',
  },
  'labor_ai_01_layoffs': {
    name: 'Challenger Gray / BLS',
    abbrev: 'Challenger',
    description: 'Layoff announcements tracked by outplacement firm Challenger, Gray & Christmas.',
    url: 'https://www.challengergray.com',
    updateFrequency: 'monthly',
  },

  // Jobs & Labor
  'job_01_jobless_claims': {
    name: 'Department of Labor',
    abbrev: 'DOL',
    description: 'Weekly initial unemployment insurance claims.',
    url: 'https://www.dol.gov/ui/data.pdf',
    updateFrequency: 'weekly',
  },
  'supply_pharmacy_shortage': {
    name: 'FDA Drug Shortage Database',
    abbrev: 'FDA',
    description: 'Official FDA tracking of prescription drug shortages.',
    url: 'https://www.accessdata.fda.gov/scripts/drugshortages',
    updateFrequency: 'daily',
  },

  // Oil Axis
  'oil_03_jodi_inventory': {
    name: 'JODI / IEA',
    abbrev: 'JODI',
    description: 'Joint Organisations Data Initiative oil inventory statistics.',
    url: 'https://www.jodidata.org',
    updateFrequency: 'monthly',
  },
  'spr_01_level': {
    name: 'EIA',
    abbrev: 'EIA',
    description: 'Energy Information Administration Strategic Petroleum Reserve levels.',
    url: 'https://www.eia.gov/petroleum/supply/weekly',
    updateFrequency: 'weekly',
  },
};

export function getSourceInfo(indicatorId: string): SourceInfo | null {
  return INDICATOR_SOURCES_FULL[indicatorId] || null;
}

// ============================================================================
// CARD IMPACT LINES
// ============================================================================

export const CARD_IMPACT_LINES: Record<string, { green: string; amber: string; red: string }> = {
  'nato_high_readiness': {
    green: 'Routine exercise levels',
    amber: 'Above-routine activation — watch energy prices',
    red: 'Highest readiness since Cold War',
  },
  'compute_01_training_cost': {
    green: 'On projected timeline',
    amber: 'Ahead of schedule — labor market shifts accelerating',
    red: 'Major capability jump — job markets reshaping fast',
  },
  'russia_nato_escalation': {
    green: 'Tensions within normal range',
    amber: 'Escalation index climbing — energy and cyber risk rising',
    red: 'Near-peer confrontation risk at Cold War levels',
  },
  'global_conflict_intensity': {
    green: 'Conflict intensity at baseline',
    amber: 'Multiple conflicts intensifying — energy prices affected',
    red: 'Crisis-level conflict — cascading supply and price impacts',
  },
  'luxury_01_collapse': {
    green: 'Consumer confidence holding',
    amber: 'Luxury weakness — recession signal in 3-6 months',
    red: 'Luxury freefall — recession and layoffs follow historically',
  },
  'taiwan_pla_activity': {
    green: 'Normal patrol levels',
    amber: 'Elevated military pressure — electronics supply at risk',
    red: 'Blockade-level activity — semiconductor crisis imminent',
  },
  'taiwan_exclusion_zone': {
    green: 'No active exclusion zones',
    amber: 'Zones expanding — shipping routes affected',
    red: 'Major exclusion active — supply chain crisis',
  },
  'liberty_01_litigation': {
    green: 'Normal caseload',
    amber: 'Key constitutional cases in play',
    red: 'Rights protections under active legal challenge',
  },
  'ice_detention_surge': {
    green: 'Below capacity — routine operations',
    amber: 'Filling up — enforcement expanding to new areas',
    red: 'At capacity — aggressive enforcement in civilian spaces',
  },
  'cyber_01_cisa_kev': {
    green: 'Normal vulnerability levels',
    amber: 'Attack surface expanding — update all devices',
    red: 'Active infrastructure exploitation — prepare for outages',
  },
  'green_g1_gdp_rates': {
    green: 'Economy has runway — the one green flag',
    amber: 'Growth slowing — watch for downstream effects',
    red: 'Contraction — recession conditions',
  },
  'national_guard_metros': {
    green: 'No non-disaster deployments',
    amber: 'Guard active in metros — civil unrest indicator',
    red: 'Multiple cities — movement restrictions possible',
  },
  'market_01_intraday_swing': {
    green: 'Normal trading conditions',
    amber: 'Elevated swings — preceded 2008 and 2020 crises',
    red: 'Extreme volatility — banking disruption risk',
  },
  'info_02_deepfake_shocks': {
    green: 'No market-moving events',
    amber: 'Disinfo affecting markets — trust eroding',
    red: 'Fabricated content moving real markets regularly',
  },
  'econ_02_grocery_cpi': {
    green: 'Food prices stable',
    amber: 'Grocery bills climbing — stock shelf-stable essentials',
    red: 'Food inflation spiking — buy 30-day buffer now',
  },
  'econ_01_treasury_tail': {
    green: 'Strong auction demand',
    amber: 'Weak demand — borrowing costs rising across the economy',
    red: 'Auction stress severe — banking system risk',
  },
  'hormuz_war_risk': {
    green: 'Normal shipping insurance rates',
    amber: 'Risk premium climbing — energy prices will follow',
    red: 'Strait restricted — fill your oil tank immediately',
  },
  'supply_pharmacy_shortage': {
    green: 'Normal supply levels',
    amber: 'Shortages growing — refill prescriptions to 90-day',
    red: 'Widespread shortages — fill everything now',
  },
  'job_01_jobless_claims': {
    green: 'Labor market healthy',
    amber: 'Claims rising — recession warning in 2-4 months',
    red: 'Spike — layoffs accelerating across sectors',
  },
  'labor_ai_01_layoffs': {
    green: 'Normal attrition levels',
    amber: 'AI-driven layoffs rising — update your positioning',
    red: 'Mass displacement — diversify income streams',
  },
  'cyber_02_ai_ransomware': {
    green: 'Baseline threat level',
    amber: 'AI-enhanced attacks increasing — update security',
    red: 'Critical infrastructure under active AI-assisted attack',
  },
  'bio_01_h2h_countries': {
    green: 'No novel transmission',
    amber: 'Novel pathogen spreading — review health supplies',
    red: 'Pandemic conditions — activate health phase protocols',
  },
  'grid_01_pjm_outages': {
    green: 'Grid operating normally',
    amber: 'Outage frequency rising — test backup power',
    red: 'Major grid instability — generator becomes critical',
  },
  'job_01_strike_days': {
    green: 'Normal labor activity',
    amber: 'Strike activity rising — supply disruptions possible',
    red: 'Major strikes — shortages similar to supply chain crises',
  },
  'power_01_ai_surveillance': {
    green: 'Normal legislative pace',
    amber: 'Surveillance bills accelerating through legislatures',
    red: 'Privacy protections eroding rapidly across states',
  },
  'civil_01_acled_protests': {
    green: 'Baseline protest levels',
    amber: 'Elevated social tension — plan around disruptions',
    red: 'Sustained unrest — avoid affected areas, review safety',
  },
  'oil_02_mbridge_settlements': {
    green: 'Minimal non-dollar settlement',
    amber: 'De-dollarization accelerating — Treasury demand weakens',
    red: 'Significant oil trade leaving dollar system',
  },
  'oil_01_russian_brics': {
    green: 'Sanctions holding',
    amber: 'Russia building BRICS oil infrastructure — sanctions weakening',
    red: 'Sanctions evasion mature — geopolitical leverage shifts',
  },
  'ofac_01_designations': {
    green: 'Routine enforcement',
    amber: 'Sanctions enforcement intensifying — retaliation risk',
    red: 'Aggressive enforcement — energy market disruption likely',
  },
  'oil_04_refinery_ratio': {
    green: 'OECD refining capacity stable',
    amber: 'Refining power shifting to Asia — less Western control',
    red: 'Structural shift — energy pricing outside Western influence',
  },
  'oil_03_jodi_inventory': {
    green: 'Inventory levels healthy',
    amber: 'Inventories declining — price volatility increasing',
    red: 'Low buffer — energy shocks hit harder',
  },
  'spr_01_level': {
    green: 'SPR at comfortable levels',
    amber: 'SPR declining — emergency cushion thinning',
    red: 'SPR critically low — no buffer for supply shocks',
  },
  'nuclear_01_tests': {
    green: 'No recent tests',
    amber: 'Testing activity — global threat calculus shifting',
    red: 'Sustained testing — prolonged elevated risk environment',
  },
  'defense_spending_growth': {
    green: 'Stable spending levels',
    amber: 'Arms race dynamics — domestic programs face pressure',
    red: 'Spending surge — resources diverted from civilian needs',
  },
  'hill_control_legislation': {
    green: 'Normal legislative pace',
    amber: 'Executive authority bills advancing — monitor closely',
    red: 'Control legislation passing — structural governance shifts',
  },
  'education_01_closures': {
    green: 'Normal operations',
    amber: 'Non-weather closures appearing — investigate causes',
    red: 'Systemic closures — something deeper is wrong',
  },
  'power_02_dod_autonomy': {
    green: 'Human oversight maintained',
    amber: 'Autonomy expanding in military systems — oversight thinning',
    red: 'Machine decision-making without human veto',
  },
  'dhs_removal_expansion': {
    green: 'Routine enforcement',
    amber: 'Expedited removal expanding — due process weakening',
    red: 'Wide expansion — significant civil liberties impact',
  },
};

export function getCardImpactLine(indicatorId: string, status: 'green' | 'amber' | 'red'): string {
  return CARD_IMPACT_LINES[indicatorId]?.[status] || '';
}
