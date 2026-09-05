/**
 * Source Registry for Canairy Trust Architecture
 *
 * Every data source used by Canairy is catalogued here with full
 * provenance information. This enables the "show your work" trust model.
 */

export type SourceType =
  | 'government-official'    // BLS, NERC, CISA, State Dept
  | 'international-org'      // UN, WHO, IMF, NATO
  | 'academic-research'      // Epoch AI, ACLED, university research
  | 'wire-service'           // Reuters, AP, AFP
  | 'industry-data'          // MarineTraffic, FreightWaves, Bloomberg
  | 'investigative-journalism' // TRAC, ProPublica, OCCRP
  | 'community-reporting';   // Local reports, social media verification

export interface SourceInfo {
  id: string;
  name: string;
  abbreviation: string;
  type: SourceType;
  description: string;
  url: string;
  methodology?: string;
}

export type SignalReliability = 'official' | 'authoritative' | 'reporting' | 'preliminary';

export interface EvidenceSignal {
  id: string;
  headline: string;
  source: SourceInfo;
  date: Date;
  url?: string;
  dataPoint?: string;
  reliability: SignalReliability;
  relevance: string;
  indicatorId: string;
}

/**
 * Canonical source registry - all data sources Canairy uses
 */
export const SOURCE_REGISTRY: Record<string, SourceInfo> = {
  bls: {
    id: 'bls',
    name: 'Bureau of Labor Statistics',
    abbreviation: 'BLS',
    type: 'government-official',
    description: 'U.S. federal agency responsible for measuring labor market activity, working conditions, and price changes in the economy.',
    url: 'https://www.bls.gov',
    methodology: 'https://www.bls.gov/cpi/questions-and-answers.htm',
  },
  fred: {
    id: 'fred',
    name: 'Federal Reserve Economic Data',
    abbreviation: 'FRED',
    type: 'government-official',
    description: 'Database maintained by the Federal Reserve Bank of St. Louis with over 800,000 economic time series.',
    url: 'https://fred.stlouisfed.org',
  },
  treasury: {
    id: 'treasury',
    name: 'U.S. Department of the Treasury',
    abbreviation: 'Treasury',
    type: 'government-official',
    description: 'Federal department managing government revenue and producing currency, coin, and Treasury securities.',
    url: 'https://www.treasury.gov',
  },
  cisa: {
    id: 'cisa',
    name: 'Cybersecurity & Infrastructure Security Agency',
    abbreviation: 'CISA',
    type: 'government-official',
    description: 'U.S. federal agency responsible for cybersecurity and critical infrastructure protection.',
    url: 'https://www.cisa.gov',
  },
  state_dept: {
    id: 'state_dept',
    name: 'U.S. Department of State',
    abbreviation: 'State Dept',
    type: 'government-official',
    description: 'Federal department handling international affairs, including travel advisories and diplomatic communications.',
    url: 'https://www.state.gov',
  },
  dhs: {
    id: 'dhs',
    name: 'Department of Homeland Security',
    abbreviation: 'DHS',
    type: 'government-official',
    description: 'Federal department responsible for public security, including immigration enforcement and border protection.',
    url: 'https://www.dhs.gov',
  },
  ice: {
    id: 'ice',
    name: 'Immigration and Customs Enforcement',
    abbreviation: 'ICE',
    type: 'government-official',
    description: 'Federal agency enforcing immigration laws and investigating cross-border criminal activity.',
    url: 'https://www.ice.gov',
  },
  doe: {
    id: 'doe',
    name: 'Department of Energy',
    abbreviation: 'DOE',
    type: 'government-official',
    description: 'Federal department responsible for energy policy and nuclear safety, including grid reliability monitoring.',
    url: 'https://www.energy.gov',
  },
  eia: {
    id: 'eia',
    name: 'Energy Information Administration',
    abbreviation: 'EIA',
    type: 'government-official',
    description: 'Statistical agency collecting and analyzing energy information including petroleum, natural gas, and electricity.',
    url: 'https://www.eia.gov',
  },
  fda: {
    id: 'fda',
    name: 'Food and Drug Administration',
    abbreviation: 'FDA',
    type: 'government-official',
    description: 'Federal agency responsible for protecting public health through regulation of food, drugs, and medical devices.',
    url: 'https://www.fda.gov',
  },
  faa: {
    id: 'faa',
    name: 'Federal Aviation Administration',
    abbreviation: 'FAA',
    type: 'government-official',
    description: 'Agency regulating civil aviation, including air traffic control and flight safety.',
    url: 'https://www.faa.gov',
  },
  fdic: {
    id: 'fdic',
    name: 'Federal Deposit Insurance Corporation',
    abbreviation: 'FDIC',
    type: 'government-official',
    description: 'Independent agency providing deposit insurance and supervising financial institutions.',
    url: 'https://www.fdic.gov',
  },
  fed: {
    id: 'fed',
    name: 'Federal Reserve',
    abbreviation: 'Fed',
    type: 'government-official',
    description: 'Central banking system of the United States, responsible for monetary policy and financial stability.',
    url: 'https://www.federalreserve.gov',
  },
  pjm: {
    id: 'pjm',
    name: 'PJM Interconnection',
    abbreviation: 'PJM',
    type: 'government-official',
    description: 'Regional transmission organization coordinating wholesale electricity in 13 states + DC, serving 65 million people.',
    url: 'https://www.pjm.com',
  },
  nerc: {
    id: 'nerc',
    name: 'North American Electric Reliability Corporation',
    abbreviation: 'NERC',
    type: 'government-official',
    description: 'International regulatory authority ensuring reliability of the bulk power system in North America.',
    url: 'https://www.nerc.com',
  },
  taiwan_mnd: {
    id: 'taiwan_mnd',
    name: 'Taiwan Ministry of National Defense',
    abbreviation: 'Taiwan MND',
    type: 'government-official',
    description: 'Official defense ministry of Taiwan, publishing regular reports on PLA military activity near Taiwan.',
    url: 'https://www.mnd.gov.tw',
  },
  // International Organizations
  who: {
    id: 'who',
    name: 'World Health Organization',
    abbreviation: 'WHO',
    type: 'international-org',
    description: 'United Nations agency responsible for international public health, including disease outbreak monitoring.',
    url: 'https://www.who.int',
  },
  nato: {
    id: 'nato',
    name: 'North Atlantic Treaty Organization',
    abbreviation: 'NATO',
    type: 'international-org',
    description: 'Intergovernmental military alliance of 32 member states across North America and Europe.',
    url: 'https://www.nato.int',
  },
  bis: {
    id: 'bis',
    name: 'Bank for International Settlements',
    abbreviation: 'BIS',
    type: 'international-org',
    description: 'International financial institution serving central banks, including mBridge CBDC project oversight.',
    url: 'https://www.bis.org',
  },
  // Academic/Research
  acled: {
    id: 'acled',
    name: 'Armed Conflict Location & Event Data',
    abbreviation: 'ACLED',
    type: 'academic-research',
    description: 'Independent research organization collecting real-time data on political violence and protests in over 200 countries.',
    url: 'https://acleddata.com',
    methodology: 'https://acleddata.com/resources/methodology/',
  },
  epoch_ai: {
    id: 'epoch_ai',
    name: 'Epoch AI',
    abbreviation: 'Epoch AI',
    type: 'academic-research',
    description: 'Research institute tracking key trends in AI development including compute, capabilities, and safety.',
    url: 'https://epochai.org',
  },
  cornell_ilr: {
    id: 'cornell_ilr',
    name: 'Cornell ILR School',
    abbreviation: 'Cornell ILR',
    type: 'academic-research',
    description: 'Industrial and Labor Relations school at Cornell University, operating the Labor Action Tracker.',
    url: 'https://striketracker.ilr.cornell.edu',
  },
  sipri: {
    id: 'sipri',
    name: 'Stockholm International Peace Research Institute',
    abbreviation: 'SIPRI',
    type: 'academic-research',
    description: 'Independent international institute dedicated to research into conflict, armaments, arms control and disarmament.',
    url: 'https://www.sipri.org',
  },
  // Wire Services
  reuters: {
    id: 'reuters',
    name: 'Reuters',
    abbreviation: 'Reuters',
    type: 'wire-service',
    description: 'International wire service providing breaking news and analysis to media organizations worldwide.',
    url: 'https://www.reuters.com',
  },
  ap: {
    id: 'ap',
    name: 'Associated Press',
    abbreviation: 'AP',
    type: 'wire-service',
    description: 'American nonprofit news agency providing content to newspapers, radio, and television stations.',
    url: 'https://apnews.com',
  },
  // Industry Data
  bloomberg: {
    id: 'bloomberg',
    name: 'Bloomberg',
    abbreviation: 'Bloomberg',
    type: 'industry-data',
    description: 'Financial data and media company providing real-time market data, analytics, and financial news.',
    url: 'https://www.bloomberg.com',
  },
  yahoo_finance: {
    id: 'yahoo_finance',
    name: 'Yahoo Finance',
    abbreviation: 'Yahoo Finance',
    type: 'industry-data',
    description: 'Financial data platform providing stock quotes, market data, and financial news.',
    url: 'https://finance.yahoo.com',
  },
  marine_traffic: {
    id: 'marine_traffic',
    name: 'MarineTraffic',
    abbreviation: 'MarineTraffic',
    type: 'industry-data',
    description: 'Global vessel tracking platform monitoring 95%+ of commercial shipping through AIS data.',
    url: 'https://www.marinetraffic.com',
  },
  freight_waves: {
    id: 'freight_waves',
    name: 'FreightWaves',
    abbreviation: 'FreightWaves',
    type: 'industry-data',
    description: 'Supply chain intelligence platform providing real-time freight market data and analytics.',
    url: 'https://www.freightwaves.com',
  },
  freightos: {
    id: 'freightos',
    name: 'Freightos Baltic Index',
    abbreviation: 'FBX',
    type: 'industry-data',
    description: 'Global container freight index tracking ocean shipping rates across major trade routes.',
    url: 'https://fbx.freightos.com',
  },
  crea: {
    id: 'crea',
    name: 'Centre for Research on Energy and Clean Air',
    abbreviation: 'CREA',
    type: 'academic-research',
    description: 'Independent research organization tracking fossil fuel trade flows and energy transitions.',
    url: 'https://energyandcleanair.org',
  },
  // Investigative Journalism
  trac: {
    id: 'trac',
    name: 'Transactional Records Access Clearinghouse',
    abbreviation: 'TRAC',
    type: 'investigative-journalism',
    description: 'Syracuse University research center providing comprehensive data on federal enforcement through FOIA requests.',
    url: 'https://trac.syr.edu',
  },
  legiscan: {
    id: 'legiscan',
    name: 'LegiScan',
    abbreviation: 'LegiScan',
    type: 'industry-data',
    description: 'Legislative tracking service monitoring bills across all 50 state legislatures and Congress.',
    url: 'https://legiscan.com',
  },
};

/**
 * Get source info by ID with fallback
 */
export function getSource(sourceId: string): SourceInfo {
  return SOURCE_REGISTRY[sourceId] || {
    id: sourceId,
    name: sourceId,
    abbreviation: sourceId,
    type: 'community-reporting' as SourceType,
    description: 'Source information not available',
    url: '',
  };
}

/**
 * Get trust weight for source type (used in confidence calculation)
 */
export function getSourceWeight(type: SourceType): number {
  const weights: Record<SourceType, number> = {
    'government-official': 5,
    'international-org': 5,
    'academic-research': 4,
    'wire-service': 3,
    'industry-data': 3,
    'investigative-journalism': 3,
    'community-reporting': 1,
  };
  return weights[type];
}

/**
 * Get reliability weight for confidence calculation
 */
export function getReliabilityWeight(reliability: SignalReliability): number {
  const weights: Record<SignalReliability, number> = {
    official: 5,
    authoritative: 4,
    reporting: 3,
    preliminary: 1,
  };
  return weights[reliability];
}

/**
 * Compute confidence level from evidence signals
 */
export function computeConfidence(
  signals: EvidenceSignal[]
): 'high' | 'moderate' | 'low' {
  if (signals.length === 0) return 'low';

  const signalCount = signals.length;

  // Factor 1: Source authority
  const authorityScore =
    signals.reduce((sum, s) => sum + getSourceWeight(s.source.type), 0) /
    signalCount;

  // Factor 2: Recency (signals older than 48h degrade confidence)
  const avgAgeHours =
    signals.reduce((sum, s) => {
      const age = (Date.now() - new Date(s.date).getTime()) / (1000 * 60 * 60);
      return sum + age;
    }, 0) / signalCount;
  const recencyPenalty = avgAgeHours > 48 ? -1 : avgAgeHours > 24 ? -0.5 : 0;

  // Factor 3: Signal reliability
  const reliabilityScore =
    signals.reduce((sum, s) => sum + getReliabilityWeight(s.reliability), 0) /
    signalCount;

  // Composite score
  const composite =
    (signalCount >= 3 ? 2 : signalCount >= 2 ? 1 : 0) +
    authorityScore +
    reliabilityScore +
    recencyPenalty;

  if (composite >= 8) return 'high';
  if (composite >= 5) return 'moderate';
  return 'low';
}
