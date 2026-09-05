/**
 * Pattern Library for Canairy Synthesis Engine
 *
 * Patterns define multi-indicator scenarios that the synthesis engine
 * detects and ranks for display on the dashboard.
 */

import { IndicatorData } from '../../types';

export interface PatternCondition {
  indicatorId?: string;
  domain?: string;
  level: 'green' | 'amber' | 'red';
  trend?: 'improving' | 'stable' | 'worsening';
}

export interface Pattern {
  id: string;
  name: string;
  requiredConditions: PatternCondition[];
  optionalConditions?: PatternCondition[];
  baseSeverity: number; // 1-10
  outcomeTemplate: string;
  headlineTemplate: string;
  actionTemplate?: string;
  actionHref?: string;
  historicalPrecedent?: string;
  domains: string[];
}

/**
 * Pattern library - patterns covering major risk scenarios
 *
 * HEADLINE RULES (from spec):
 * 1. Lead with a verb or an outcome, never a domain name
 * 2. Include a time horizon: "this week", "before Friday", "this weekend"
 * 3. Be specific enough to act on without reading the body
 *
 * BODY RULES:
 * 1. First sentence: what's happening in the real world (with numbers)
 * 2. Second sentence: how it affects the family specifically
 * 3. Third sentence (optional): why acting now matters
 * 4. Never use: "indicators", "signals", "elevated", "metrics"
 */
export const PATTERN_LIBRARY: Pattern[] = [
  // ──────────────────────────────────────────────────────────────────────────────
  // ECONOMIC PATTERNS (AMBER-TRIGGERED)
  // ──────────────────────────────────────────────────────────────────────────────
  {
    id: 'market-watch',
    name: 'Market Volatility Alert',
    requiredConditions: [
      { indicatorId: 'market_01_intraday_swing', level: 'amber' },
    ],
    optionalConditions: [
      { indicatorId: 'econ_02_grocery_cpi', level: 'amber' },
    ],
    baseSeverity: 6,
    outcomeTemplate:
      'Markets are swinging 2-3% daily — more than usual. Your 401k balance may fluctuate, but history shows staying the course beats panic selling.',
    headlineTemplate: 'Hold steady on investments this week',
    actionTemplate: 'Review portfolio allocation',
    actionHref: '/action-plan',
    domains: ['economy'],
  },
  {
    id: 'inflation-watch',
    name: 'Inflation Pressure',
    requiredConditions: [
      { indicatorId: 'econ_02_grocery_cpi', level: 'amber' },
    ],
    baseSeverity: 5,
    outcomeTemplate:
      'Grocery prices are up 5-8% from last quarter. Your weekly food bill will be $20-40 higher. Stocking up now locks in today\'s prices.',
    headlineTemplate: 'Stock up on essentials this week',
    actionTemplate: 'Add shelf-stable staples',
    actionHref: '/action-plan',
    domains: ['economy'],
  },
  {
    id: 'multi-economic-stress',
    name: 'Multiple Economic Pressures',
    requiredConditions: [
      { domain: 'economy', level: 'amber' },
    ],
    optionalConditions: [
      { indicatorId: 'market_01_intraday_swing', level: 'amber' },
      { indicatorId: 'econ_02_grocery_cpi', level: 'amber' },
    ],
    baseSeverity: 7,
    outcomeTemplate:
      'Markets are volatile and prices are climbing — a combination that often precedes economic slowdowns. Having 2-4 weeks of cash on hand provides security if ATMs or cards have issues.',
    headlineTemplate: 'Build your cash cushion this week',
    actionTemplate: 'Withdraw 2 weeks cash',
    actionHref: '/action-plan',
    domains: ['economy'],
  },
  // ──────────────────────────────────────────────────────────────────────────────
  // GLOBAL CONFLICT PATTERNS (AMBER-TRIGGERED)
  // ──────────────────────────────────────────────────────────────────────────────
  {
    id: 'taiwan-watch',
    name: 'Taiwan Strait Activity',
    requiredConditions: [
      { indicatorId: 'taiwan_pla_activity', level: 'amber' },
    ],
    baseSeverity: 6,
    outcomeTemplate:
      'Military activity near Taiwan has increased 40% this month. If tensions escalate, chip shortages could affect phones, laptops, and vehicles within weeks.',
    headlineTemplate: 'Order electronics before potential delays',
    actionTemplate: 'Review electronics needs',
    actionHref: '/action-plan',
    domains: ['global_conflict'],
  },
  {
    id: 'geopolitical-tensions',
    name: 'Rising Geopolitical Tensions',
    requiredConditions: [
      { domain: 'global_conflict', level: 'amber' },
    ],
    baseSeverity: 5,
    outcomeTemplate:
      'State Department has issued new travel advisories for 3 regions. No direct domestic impact expected right now, but having your family\'s emergency plan fresh in everyone\'s mind matters.',
    headlineTemplate: 'Review your family emergency plan this week',
    actionTemplate: 'Confirm rally points with family',
    actionHref: '/action-plan',
    domains: ['global_conflict'],
  },
  // ──────────────────────────────────────────────────────────────────────────────
  // DOMESTIC CONTROL PATTERNS (AMBER-TRIGGERED)
  // ──────────────────────────────────────────────────────────────────────────────
  {
    id: 'enforcement-uptick',
    name: 'Immigration Enforcement Activity',
    requiredConditions: [
      { indicatorId: 'ice_detention_surge', level: 'amber' },
    ],
    baseSeverity: 5,
    outcomeTemplate:
      'DHS has expanded enforcement operations to 4 additional cities this week. If your community could be affected, ensure everyone knows their rights and has emergency contacts ready.',
    headlineTemplate: 'Know your rights this week',
    actionTemplate: 'Share know-your-rights info',
    actionHref: '/action-plan',
    domains: ['domestic_control'],
  },
  {
    id: 'surveillance-expansion',
    name: 'Surveillance Infrastructure Growth',
    requiredConditions: [
      { indicatorId: 'power_01_ai_surveillance', level: 'amber' },
    ],
    baseSeverity: 4,
    outcomeTemplate:
      'New AI surveillance programs are being deployed in 6 states. Good time to audit your digital footprint — review which apps have location access and consider encrypted messaging.',
    headlineTemplate: 'Audit your digital privacy this week',
    actionTemplate: 'Review app permissions',
    actionHref: '/settings',
    domains: ['domestic_control', 'ai_window'],
  },
  // ──────────────────────────────────────────────────────────────────────────────
  // ENERGY & OIL PATTERNS (AMBER-TRIGGERED)
  // ──────────────────────────────────────────────────────────────────────────────
  {
    id: 'oil-axis-shift',
    name: 'Oil Trade Realignment',
    requiredConditions: [
      { indicatorId: 'oil_03_ofac_designations', level: 'amber' },
    ],
    baseSeverity: 5,
    outcomeTemplate:
      'Major oil exporters are shifting away from dollar settlements. This could affect fuel prices 10-20% over the next quarter. Keeping your tank above half-full is good practice.',
    headlineTemplate: 'Keep fuel tanks topped off this month',
    actionTemplate: 'Fill vehicle tanks',
    actionHref: '/action-plan',
    domains: ['oil_axis', 'energy'],
  },
  // ──────────────────────────────────────────────────────────────────────────────
  // CYBER SECURITY PATTERNS (AMBER-TRIGGERED)
  // ──────────────────────────────────────────────────────────────────────────────
  {
    id: 'cyber-threats',
    name: 'Elevated Cyber Threat',
    requiredConditions: [
      { indicatorId: 'cyber_01_cisa_kev', level: 'amber' },
    ],
    optionalConditions: [
      { indicatorId: 'cyber_02_ai_ransomware', level: 'amber' },
    ],
    baseSeverity: 5,
    outcomeTemplate:
      'CISA is warning about 4 actively exploited software vulnerabilities this week. Update your phone, computer, and router. If you haven\'t changed passwords in 6 months, now is the time.',
    headlineTemplate: 'Update devices and passwords today',
    actionTemplate: 'Run all updates now',
    actionHref: '/action-plan',
    domains: ['security_infrastructure'],
  },
  // ──────────────────────────────────────────────────────────────────────────────
  // HIGH SEVERITY PATTERNS (RED-TRIGGERED - for escalation)
  // ──────────────────────────────────────────────────────────────────────────────
  {
    id: 'banking-crisis',
    name: 'Banking System Stress',
    requiredConditions: [
      { domain: 'economy', level: 'red' },
    ],
    baseSeverity: 9,
    outcomeTemplate:
      'Multiple banks are showing signs of stress similar to 2008. ATMs and card payments could be disrupted. Withdraw $500+ in small bills today — this is your financial go-bag.',
    headlineTemplate: 'Protect your deposits today',
    actionTemplate: 'Withdraw emergency cash',
    actionHref: '/action-plan',
    historicalPrecedent: '2008 financial crisis, 2023 SVB collapse',
    domains: ['economy'],
  },
  {
    id: 'market-crisis',
    name: 'Market Crisis',
    requiredConditions: [
      { indicatorId: 'market_01_intraday_swing', level: 'red' },
    ],
    baseSeverity: 8,
    outcomeTemplate:
      'Extreme market volatility. Circuit breakers may trigger. Avoid panic selling.',
    headlineTemplate: 'Markets in turmoil',
    actionTemplate: 'Screenshot all balances',
    actionHref: '/action-plan',
    domains: ['economy'],
  },

  // ──────────────────────────────────────────────────────────────────────────────
  // ENERGY PATTERNS
  // ──────────────────────────────────────────────────────────────────────────────
  {
    id: 'grid-stress',
    name: 'Grid Reliability Crisis',
    requiredConditions: [
      { indicatorId: 'energy_03_grid_emergency', level: 'red' },
    ],
    optionalConditions: [
      { indicatorId: 'grid_01_pjm_outages', level: 'amber' },
    ],
    baseSeverity: 8,
    outcomeTemplate:
      'Power grid under stress. Rolling blackouts possible. Charge devices and prepare backup power.',
    headlineTemplate: 'Power grid reliability concerns',
    actionTemplate: 'Charge all power banks and batteries',
    actionHref: '/action-plan',
    historicalPrecedent: 'Texas 2021 freeze, California rolling blackouts',
    domains: ['energy', 'security_infrastructure'],
  },
  {
    id: 'fuel-crisis',
    name: 'Fuel Supply Disruption',
    requiredConditions: [
      { indicatorId: 'spr_01_level', level: 'red' },
    ],
    optionalConditions: [
      { indicatorId: 'hormuz_war_risk', level: 'amber' },
      { domain: 'oil_axis', level: 'amber' },
    ],
    baseSeverity: 7,
    outcomeTemplate:
      'Strategic reserves depleted and supply chains stressed. Fuel prices may spike 30-50%.',
    headlineTemplate: 'Fuel supply under pressure',
    actionTemplate: 'Fill all vehicle fuel tanks',
    actionHref: '/action-plan',
    domains: ['energy', 'oil_axis'],
  },
  {
    id: 'nat-gas-shortage',
    name: 'Natural Gas Supply Risk',
    requiredConditions: [
      { indicatorId: 'energy_02_nat_gas_storage', level: 'red' },
    ],
    baseSeverity: 6,
    outcomeTemplate:
      'Natural gas storage below normal. Heating costs may increase significantly this winter.',
    headlineTemplate: 'Natural gas supplies tight',
    actionTemplate: 'Review heating alternatives',
    actionHref: '/action-plan',
    domains: ['energy'],
  },

  // ──────────────────────────────────────────────────────────────────────────────
  // SUPPLY CHAIN PATTERNS
  // ──────────────────────────────────────────────────────────────────────────────
  {
    id: 'supply-chain-breakdown',
    name: 'Supply Chain Disruption',
    requiredConditions: [
      { indicatorId: 'supply_01_port_congestion', level: 'red' },
      { indicatorId: 'supply_02_freight_index', level: 'amber' },
    ],
    baseSeverity: 7,
    outcomeTemplate:
      'Major port congestion causing delays. Essential goods may be scarce for 4-8 weeks.',
    headlineTemplate: 'Supply chain bottlenecks forming',
    actionTemplate: 'Stock essential supplies now',
    actionHref: '/action-plan',
    historicalPrecedent: '2021 port congestion crisis',
    domains: ['supply_chain'],
  },
  {
    id: 'chip-shortage',
    name: 'Semiconductor Shortage',
    requiredConditions: [
      { indicatorId: 'supply_03_chip_lead_time', level: 'red' },
    ],
    baseSeverity: 5,
    outcomeTemplate:
      'Chip shortages affecting vehicle and electronics availability. Lead times extended.',
    headlineTemplate: 'Chip shortage affecting production',
    domains: ['supply_chain'],
  },

  // ──────────────────────────────────────────────────────────────────────────────
  // SECURITY PATTERNS
  // ──────────────────────────────────────────────────────────────────────────────
  {
    id: 'cyber-attack',
    name: 'Critical Infrastructure Cyber Attack',
    requiredConditions: [
      { indicatorId: 'cyber_01_cisa_kev', level: 'red' },
    ],
    optionalConditions: [
      { indicatorId: 'energy_03_grid_emergency', level: 'amber' },
    ],
    baseSeverity: 8,
    outcomeTemplate:
      'Critical infrastructure under cyber attack. Banking, utilities, and communications may be affected.',
    headlineTemplate: 'Cyber threat to critical infrastructure',
    actionTemplate: 'Test offline communications',
    actionHref: '/action-plan',
    historicalPrecedent: 'Colonial Pipeline 2021, SolarWinds 2020',
    domains: ['security_infrastructure'],
  },
  {
    id: 'civil-unrest',
    name: 'Civil Unrest Risk',
    requiredConditions: [
      { indicatorId: 'civil_01_acled_protests', level: 'red' },
    ],
    optionalConditions: [
      { indicatorId: 'national_guard_metros', level: 'amber' },
    ],
    baseSeverity: 7,
    outcomeTemplate:
      'Elevated protest activity in major metros. Avoid affected areas and review family meeting points.',
    headlineTemplate: 'Civil unrest elevated',
    actionTemplate: 'Review family meeting locations',
    actionHref: '/action-plan',
    domains: ['domestic_control', 'security_infrastructure'],
  },

  // ──────────────────────────────────────────────────────────────────────────────
  // GLOBAL CONFLICT PATTERNS
  // ──────────────────────────────────────────────────────────────────────────────
  {
    id: 'taiwan-crisis',
    name: 'Taiwan Strait Crisis',
    requiredConditions: [
      { indicatorId: 'taiwan_pla_activity', level: 'red' },
    ],
    optionalConditions: [
      { indicatorId: 'supply_03_chip_lead_time', level: 'amber' },
    ],
    baseSeverity: 9,
    outcomeTemplate:
      'Military activity in Taiwan Strait elevated. Global chip supply at risk. Major economic disruption possible.',
    headlineTemplate: 'Taiwan Strait tensions escalating',
    actionTemplate: 'Review Phase 4+ preparations',
    actionHref: '/action-plan',
    historicalPrecedent: '1996 Taiwan Strait crisis',
    domains: ['global_conflict', 'supply_chain'],
  },
  {
    id: 'nato-escalation',
    name: 'NATO-Russia Escalation',
    requiredConditions: [
      { indicatorId: 'nato_high_readiness', level: 'red' },
    ],
    optionalConditions: [
      { indicatorId: 'russia_nato_escalation', level: 'amber' },
    ],
    baseSeverity: 9,
    outcomeTemplate:
      'NATO forces at high readiness. Potential for significant escalation. Energy and supply impacts likely.',
    headlineTemplate: 'NATO-Russia tensions elevated',
    actionTemplate: 'Accelerate Phase 5+ preparations',
    actionHref: '/action-plan',
    domains: ['global_conflict', 'oil_axis'],
  },
  {
    id: 'hormuz-closure',
    name: 'Hormuz Strait Risk',
    requiredConditions: [
      { indicatorId: 'hormuz_war_risk', level: 'red' },
    ],
    optionalConditions: [
      { indicatorId: 'spr_01_level', level: 'amber' },
    ],
    baseSeverity: 8,
    outcomeTemplate:
      'Persian Gulf shipping at risk. Oil prices may double if strait is blocked. Fill vehicles immediately.',
    headlineTemplate: 'Persian Gulf shipping risk elevated',
    actionTemplate: 'Fill all vehicle fuel tanks',
    actionHref: '/action-plan',
    domains: ['oil_axis', 'global_conflict'],
  },

  // ──────────────────────────────────────────────────────────────────────────────
  // HEALTH PATTERNS
  // ──────────────────────────────────────────────────────────────────────────────
  {
    id: 'pandemic-risk',
    name: 'Pandemic Alert',
    requiredConditions: [
      { indicatorId: 'bio_01_h2h_countries', level: 'red' },
    ],
    baseSeverity: 9,
    outcomeTemplate:
      'Novel pathogen with human-to-human transmission confirmed. Mask up, stock medications, limit gatherings.',
    headlineTemplate: 'Novel pathogen H2H transmission',
    actionTemplate: 'Verify N95 cache and prescriptions',
    actionHref: '/action-plan',
    historicalPrecedent: 'COVID-19, H1N1',
    domains: ['security_infrastructure'],
  },
  {
    id: 'pharma-shortage',
    name: 'Medication Shortage',
    requiredConditions: [
      { indicatorId: 'fda_drug_shortages', level: 'red' },
    ],
    baseSeverity: 7,
    outcomeTemplate:
      'Critical medication shortages reported. Refill prescriptions immediately if possible.',
    headlineTemplate: 'Critical medication shortages',
    actionTemplate: 'Refill all prescriptions (90-day)',
    actionHref: '/action-plan',
    domains: ['security_infrastructure', 'supply_chain'],
  },

  // ──────────────────────────────────────────────────────────────────────────────
  // TRAVEL & DOMESTIC PATTERNS
  // ──────────────────────────────────────────────────────────────────────────────
  {
    id: 'travel-disruption',
    name: 'Air Travel Disruption',
    requiredConditions: [
      { indicatorId: 'flight_01_ground_stops', level: 'red' },
    ],
    optionalConditions: [
      { indicatorId: 'flight_02_delay_pct', level: 'amber' },
    ],
    baseSeverity: 5,
    outcomeTemplate:
      'Widespread flight disruptions. If traveling, expect delays and consider alternatives.',
    headlineTemplate: 'Major air travel disruptions',
    actionTemplate: 'Review travel plans',
    domains: ['security_infrastructure'],
  },
  {
    id: 'border-crisis',
    name: 'Border Processing Crisis',
    requiredConditions: [
      { indicatorId: 'travel_02_border_wait', level: 'red' },
    ],
    optionalConditions: [
      { indicatorId: 'dhs_removal_expansion', level: 'amber' },
    ],
    baseSeverity: 5,
    outcomeTemplate:
      'Border wait times extremely elevated. Avoid non-essential border crossings.',
    headlineTemplate: 'Border processing delays severe',
    domains: ['domestic_control'],
  },

  // ──────────────────────────────────────────────────────────────────────────────
  // COMPOUND PATTERNS
  // ──────────────────────────────────────────────────────────────────────────────
  {
    id: 'cascade-crisis',
    name: 'Multi-Domain Crisis',
    requiredConditions: [
      { domain: 'economy', level: 'red' },
      { domain: 'energy', level: 'red' },
    ],
    baseSeverity: 10,
    outcomeTemplate:
      'Multiple critical systems under stress simultaneously. Activate full 48-hour protocol immediately.',
    headlineTemplate: 'Multi-domain crisis developing',
    actionTemplate: 'Complete full action protocol',
    actionHref: '/action-plan',
    historicalPrecedent: 'March 2020 pandemic + market crash',
    domains: ['economy', 'energy'],
  },

  // ──────────────────────────────────────────────────────────────────────────────
  // PERIPHERAL IMPACT PATTERNS (Reading Between the Lines)
  // ──────────────────────────────────────────────────────────────────────────────

  // CHILDCARE & SCHOOL IMPACTS
  {
    id: 'school-disruption-risk',
    name: 'School Disruption Signal',
    requiredConditions: [
      { domain: 'security_infrastructure', level: 'amber' },
    ],
    optionalConditions: [
      { domain: 'energy', level: 'amber' },
    ],
    baseSeverity: 5,
    outcomeTemplate:
      'Infrastructure stress often cascades to schools first — they close before businesses do. If you have kids, mentally rehearse your backup childcare plan. Who watches them if school closes with 2 hours notice?',
    headlineTemplate: 'Line up backup childcare this week',
    actionTemplate: 'Confirm 2 backup childcare contacts',
    actionHref: '/action-plan',
    domains: ['security_infrastructure'],
  },

  // MEDICATION & ELDERLY CARE
  {
    id: 'medication-supply-pressure',
    name: 'Medication Supply Concern',
    requiredConditions: [
      { domain: 'supply_chain', level: 'amber' },
    ],
    baseSeverity: 6,
    outcomeTemplate:
      'Supply chain hiccups hit pharmacies within 2-3 weeks of port slowdowns. If anyone in your household takes daily medication — blood pressure, insulin, thyroid — call your pharmacy now about a 90-day refill. Insurance often covers it.',
    headlineTemplate: 'Refill prescriptions to 90-day supply',
    actionTemplate: 'Call pharmacy for 90-day fills',
    actionHref: '/action-plan',
    domains: ['supply_chain'],
  },

  // ELDERLY PARENTS CHECK-IN
  {
    id: 'elderly-check-in-prompt',
    name: 'Elder Care Awareness',
    requiredConditions: [
      { domain: 'economy', level: 'amber' },
    ],
    optionalConditions: [
      { domain: 'energy', level: 'amber' },
    ],
    baseSeverity: 4,
    outcomeTemplate:
      'Economic stress hits fixed-income households hardest. If you have elderly parents, this is a good week to check if they\'re managing heating bills, grocery costs, or pharmacy copays. A 10-minute call can catch problems early.',
    headlineTemplate: 'Check in on elderly family members',
    actionTemplate: 'Call parents/grandparents this weekend',
    actionHref: '/action-plan',
    domains: ['economy'],
  },

  // PET SUPPLY BUFFER
  {
    id: 'pet-supply-buffer',
    name: 'Pet Supply Awareness',
    requiredConditions: [
      { domain: 'supply_chain', level: 'amber' },
    ],
    baseSeverity: 3,
    outcomeTemplate:
      'Pet food and medications often face shortages before human supplies — they\'re lower priority in logistics chains. If you have pets, grab an extra month of food and any prescription meds. Pet insulin especially can become scarce.',
    headlineTemplate: 'Stock extra pet food and meds',
    actionTemplate: 'Buy 4-week pet food buffer',
    actionHref: '/action-plan',
    domains: ['supply_chain'],
  },

  // CASH-BASED COMMERCE
  {
    id: 'cash-economy-signal',
    name: 'Cash Economy Advantage',
    requiredConditions: [
      { domain: 'economy', level: 'amber' },
      { domain: 'security_infrastructure', level: 'amber' },
    ],
    baseSeverity: 6,
    outcomeTemplate:
      'When systems get stressed, card networks and ATMs often fail first. Having $300-500 in small bills lets you buy gas, groceries, or medicine when everyone else is stuck. Keep it at home, not in your wallet.',
    headlineTemplate: 'Build your cash buffer this week',
    actionTemplate: 'Withdraw $300-500 in small bills',
    actionHref: '/action-plan',
    domains: ['economy', 'security_infrastructure'],
  },

  // COMMUTE DISRUPTION PREPARATION
  {
    id: 'commute-disruption-prep',
    name: 'Commute Resilience',
    requiredConditions: [
      { domain: 'energy', level: 'amber' },
    ],
    optionalConditions: [
      { domain: 'global_conflict', level: 'amber' },
    ],
    baseSeverity: 4,
    outcomeTemplate:
      'Energy and geopolitical stress can spike gas prices 30% in a week. If you commute, consider whether you could work remotely for a few days if prices jump. Having that conversation with your employer now is easier than asking during a crisis.',
    headlineTemplate: 'Confirm your work-from-home option',
    actionTemplate: 'Discuss remote work policy with manager',
    actionHref: '/action-plan',
    domains: ['energy'],
  },

  // LOCAL NETWORK ACTIVATION
  {
    id: 'neighbor-network-prompt',
    name: 'Community Resilience Prompt',
    requiredConditions: [
      { domain: 'security_infrastructure', level: 'amber' },
    ],
    optionalConditions: [
      { domain: 'domestic_control', level: 'amber' },
    ],
    baseSeverity: 4,
    outcomeTemplate:
      'Neighbors help neighbors when systems fail. Do you know the names of the 3-4 households closest to you? This week, find a reason to introduce yourself if you haven\'t. Exchange phone numbers. These relationships matter when the power\'s out.',
    headlineTemplate: 'Meet your closest neighbors this week',
    actionTemplate: 'Exchange numbers with 3 neighbors',
    actionHref: '/action-plan',
    domains: ['security_infrastructure'],
  },

  // INSURANCE DOCUMENTATION
  {
    id: 'insurance-documentation-check',
    name: 'Insurance Documentation',
    requiredConditions: [
      { domain: 'economy', level: 'amber' },
    ],
    optionalConditions: [
      { domain: 'security_infrastructure', level: 'amber' },
    ],
    baseSeverity: 3,
    outcomeTemplate:
      'Economic stress leads to more claims — and slower processing. Do you have photos of your home contents? Can you find your policy numbers offline? Spending 30 minutes documenting now saves days of frustration later.',
    headlineTemplate: 'Document home contents for insurance',
    actionTemplate: 'Photo inventory of valuables',
    actionHref: '/action-plan',
    domains: ['economy'],
  },

  // VEHICLE READINESS
  {
    id: 'vehicle-readiness-check',
    name: 'Vehicle Preparedness',
    requiredConditions: [
      { domain: 'energy', level: 'amber' },
    ],
    optionalConditions: [
      { domain: 'global_conflict', level: 'amber' },
    ],
    baseSeverity: 5,
    outcomeTemplate:
      'Your car is your Plan B escape pod. Check: Is the tank above half? Are tires properly inflated? Is there a phone charger? Water? A paper map? If you had to drive 300 miles tonight, could you? Fix gaps this weekend.',
    headlineTemplate: 'Prep your vehicle go-kit this weekend',
    actionTemplate: 'Stock vehicle emergency kit',
    actionHref: '/action-plan',
    domains: ['energy'],
  },

  // DIGITAL BACKUP CHECK
  {
    id: 'digital-backup-prompt',
    name: 'Digital Backup Awareness',
    requiredConditions: [
      { domain: 'security_infrastructure', level: 'amber' },
    ],
    baseSeverity: 4,
    outcomeTemplate:
      'If your phone died right now, could you call your family? Write down 5 critical numbers on paper. Export your password manager. Back up irreplaceable photos. Digital fragility is invisible until it isn\'t.',
    headlineTemplate: 'Back up critical info offline',
    actionTemplate: 'Write down 5 emergency numbers on paper',
    actionHref: '/action-plan',
    domains: ['security_infrastructure'],
  },

  // WATER BUFFER
  {
    id: 'water-buffer-check',
    name: 'Water Resilience',
    requiredConditions: [
      { domain: 'security_infrastructure', level: 'amber' },
    ],
    optionalConditions: [
      { domain: 'energy', level: 'amber' },
    ],
    baseSeverity: 5,
    outcomeTemplate:
      'Municipal water needs electricity to pump. A 48-hour outage means no tap water. Do you have 1 gallon per person per day for 3 days? That\'s 12 gallons for a family of 4. Fill some old bottles this week — it\'s free.',
    headlineTemplate: 'Check your water buffer this week',
    actionTemplate: 'Store 1 gallon per person per day (3 days)',
    actionHref: '/action-plan',
    domains: ['security_infrastructure', 'energy'],
  },

  // WORK INCOME DIVERSIFICATION
  {
    id: 'income-diversification-prompt',
    name: 'Income Resilience Signal',
    requiredConditions: [
      { domain: 'economy', level: 'amber' },
      { domain: 'jobs_labor', level: 'amber' },
    ],
    baseSeverity: 5,
    outcomeTemplate:
      'Economic uncertainty hits layoffs 3-6 months before headlines predict. Is your resume updated? Do you have a skill you could freelance? Not to panic — but having a Plan B income source in your back pocket reduces stress significantly.',
    headlineTemplate: 'Update your resume this month',
    actionTemplate: 'Refresh resume and LinkedIn',
    actionHref: '/action-plan',
    domains: ['economy', 'jobs_labor'],
  },

  // SECOND-ORDER SUPPLY EFFECTS
  {
    id: 'supply-chain-second-order',
    name: 'Hidden Supply Chain Effects',
    requiredConditions: [
      { domain: 'global_conflict', level: 'amber' },
    ],
    optionalConditions: [
      { domain: 'supply_chain', level: 'amber' },
    ],
    baseSeverity: 5,
    outcomeTemplate:
      'Conflict abroad affects more than news headlines. Components for cars, appliances, and medical devices may face 6-12 week delays. If you\'ve been putting off a repair or purchase, consider accelerating it before backlogs hit.',
    headlineTemplate: 'Accelerate delayed purchases or repairs',
    actionTemplate: 'Complete postponed equipment repairs',
    actionHref: '/action-plan',
    domains: ['global_conflict', 'supply_chain'],
  },

  // BANKING HOURS AWARENESS
  {
    id: 'banking-access-prompt',
    name: 'Banking Access Awareness',
    requiredConditions: [
      { domain: 'economy', level: 'amber' },
    ],
    baseSeverity: 4,
    outcomeTemplate:
      'Bank branches are shrinking — many areas now have only 1-2 nearby. Know where yours is and their hours. Have you tested that you can actually log in to your bank app? Do you know your password without the password manager?',
    headlineTemplate: 'Test your banking access this week',
    actionTemplate: 'Verify bank login and branch hours',
    actionHref: '/action-plan',
    domains: ['economy'],
  },

  // COMMUNICATION REDUNDANCY
  {
    id: 'communication-backup-prompt',
    name: 'Communication Backup',
    requiredConditions: [
      { domain: 'security_infrastructure', level: 'amber' },
    ],
    optionalConditions: [
      { domain: 'global_conflict', level: 'amber' },
    ],
    baseSeverity: 5,
    outcomeTemplate:
      'Cell networks fail in crises — everyone calls at once. Does your family have a Plan B contact method? A landline? A specific radio channel? An out-of-state relative everyone checks in with? Decide now, not during the emergency.',
    headlineTemplate: 'Set up family communication backup',
    actionTemplate: 'Designate out-of-area contact person',
    actionHref: '/action-plan',
    domains: ['security_infrastructure'],
  },

  // SEASONAL PREPARATION TRIGGER
  {
    id: 'seasonal-prep-economy',
    name: 'Economic Seasonal Preparedness',
    requiredConditions: [
      { domain: 'economy', level: 'amber' },
    ],
    baseSeverity: 4,
    outcomeTemplate:
      'Prices rise fastest heading into winter. If you\'re planning to buy warm clothing, heating fuel, or holiday supplies, buying now locks in current prices. Waiting typically costs 15-25% more by December.',
    headlineTemplate: 'Buy winter supplies at current prices',
    actionTemplate: 'Purchase seasonal items now',
    actionHref: '/action-plan',
    domains: ['economy'],
  },

  // MENTAL HEALTH RESOURCE PREP
  {
    id: 'mental-health-resource-prep',
    name: 'Mental Health Awareness',
    requiredConditions: [
      { domain: 'economy', level: 'amber' },
      { domain: 'global_conflict', level: 'amber' },
    ],
    baseSeverity: 4,
    outcomeTemplate:
      'Multiple stressors compound anxiety — and therapy waitlists are often 2-3 months long. If anyone in your household might benefit from support, making that call now means help is available when stress peaks, not after.',
    headlineTemplate: 'Line up mental health support now',
    actionTemplate: 'Research therapy/counseling options',
    actionHref: '/action-plan',
    domains: ['economy', 'global_conflict'],
  },

  // LOCAL FOOD NETWORK
  {
    id: 'local-food-network',
    name: 'Local Food Resilience',
    requiredConditions: [
      { domain: 'supply_chain', level: 'amber' },
    ],
    baseSeverity: 4,
    outcomeTemplate:
      'Global supply chains are fragile; local food is resilient. Do you know your nearest farmers market? Any local farms with CSA boxes? Having one local food source means fresh produce even when grocery shelves empty.',
    headlineTemplate: 'Find your local food sources',
    actionTemplate: 'Identify 2 local farms or markets',
    actionHref: '/action-plan',
    domains: ['supply_chain'],
  },

  // DOCUMENT GO-BAG
  {
    id: 'document-go-bag',
    name: 'Document Readiness',
    requiredConditions: [
      { domain: 'domestic_control', level: 'amber' },
    ],
    optionalConditions: [
      { domain: 'security_infrastructure', level: 'amber' },
    ],
    baseSeverity: 5,
    outcomeTemplate:
      'If you had to leave home in 10 minutes, could you grab passports, birth certificates, insurance cards, and medication lists? Put copies in a single folder or small bag. Knowing where they are eliminates panic.',
    headlineTemplate: 'Organize your document go-folder',
    actionTemplate: 'Assemble critical documents in one place',
    actionHref: '/action-plan',
    domains: ['domestic_control', 'security_infrastructure'],
  },

  // INFLATION PROTECTION
  {
    id: 'inflation-protection-prompt',
    name: 'Inflation Protection Strategy',
    requiredConditions: [
      { indicatorId: 'econ_02_grocery_cpi', level: 'amber' },
    ],
    optionalConditions: [
      { domain: 'energy', level: 'amber' },
    ],
    baseSeverity: 5,
    outcomeTemplate:
      'Inflation erodes savings sitting in checking accounts. If you have cash above your 3-month emergency fund, consider moving it somewhere earning interest — high-yield savings or I-bonds at least keep pace with inflation.',
    headlineTemplate: 'Move excess cash to high-yield savings',
    actionTemplate: 'Open high-yield savings account',
    actionHref: '/action-plan',
    domains: ['economy'],
  },
];

/**
 * Detect which patterns match the current indicator state
 */
export function detectPatterns(indicators: IndicatorData[]): Pattern[] {
  const matchedPatterns: Pattern[] = [];

  for (const pattern of PATTERN_LIBRARY) {
    let requiredMet = true;
    let optionalCount = 0;

    // Check required conditions
    for (const condition of pattern.requiredConditions) {
      const matches = indicators.filter(ind => {
        if (condition.indicatorId && ind.id !== condition.indicatorId) return false;
        if (condition.domain && ind.domain !== condition.domain) return false;
        if (ind.status.level !== condition.level) return false;
        if (condition.trend && ind.status.trend !== condition.trend) return false;
        return true;
      });

      if (matches.length === 0) {
        requiredMet = false;
        break;
      }
    }

    if (!requiredMet) continue;

    // Check optional conditions (boosters)
    if (pattern.optionalConditions) {
      for (const condition of pattern.optionalConditions) {
        const matches = indicators.filter(ind => {
          if (condition.indicatorId && ind.id !== condition.indicatorId) return false;
          if (condition.domain && ind.domain !== condition.domain) return false;
          // Optional: level can be same OR worse
          const levelOrder: Record<string, number> = { green: 0, amber: 1, red: 2, unknown: 0 };
          if (levelOrder[ind.status.level] < levelOrder[condition.level]) return false;
          return true;
        });

        if (matches.length > 0) {
          optionalCount++;
        }
      }
    }

    matchedPatterns.push(pattern);
  }

  return matchedPatterns;
}
