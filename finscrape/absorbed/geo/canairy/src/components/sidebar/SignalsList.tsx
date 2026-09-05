import React from 'react';
import { motion } from 'framer-motion';
import { ExternalLink, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { useStore } from '../../store';
import { getSignalHeadline, INDICATOR_TRANSLATIONS } from '../../data/indicatorTranslations';

interface Signal {
  id: string;
  headline: string;
  source: string;
  url: string;  // Required - every signal must link to source
  trend?: 'up' | 'down' | 'neutral';
  timestamp?: string;
}

// Source URLs for indicators - link to specific data pages
const SOURCE_URLS: Record<string, string> = {
  // Economy
  econ_01_treasury_tail: 'https://www.treasurydirect.gov/auctions/auction-query/',
  econ_02_grocery_cpi: 'https://www.bls.gov/news.release/cpi.nr0.htm',
  market_01_intraday_swing: 'https://finance.yahoo.com/quote/%5ETNX/',
  green_g1_gdp_rates: 'https://www.bea.gov/data/gdp/gross-domestic-product',
  luxury_01_collapse: 'https://www.bloomberg.com/markets/sectors/consumer-discretionary',

  // Global Conflict
  taiwan_pla_activity: 'https://www.mnd.gov.tw/english/',
  taiwan_exclusion_zone: 'https://www.mnd.gov.tw/english/',
  global_conflict_intensity: 'https://acleddata.com/dashboard/',
  nato_high_readiness: 'https://www.nato.int/cps/en/natohq/news.htm',
  russia_nato_escalation: 'https://www.reuters.com/world/europe/',
  nuclear_01_tests: 'https://www.ctbto.org/specials/testing-times/',
  defense_spending_growth: 'https://www.sipri.org/databases/milex',
  hormuz_war_risk: 'https://www.lloyds.com/market-resources/marine',

  // Domestic Control
  ice_detention_surge: 'https://trac.syr.edu/immigration/detentionstats/',
  dhs_removal_expansion: 'https://www.federalregister.gov/agencies/homeland-security-department',
  national_guard_metros: 'https://www.nationalguard.mil/News/',
  hill_control_legislation: 'https://www.congress.gov/',

  // Security & Infrastructure
  cyber_01_cisa_kev: 'https://www.cisa.gov/known-exploited-vulnerabilities-catalog',
  cyber_02_ai_ransomware: 'https://www.cisa.gov/stopransomware/ransomware-alerts',
  grid_01_pjm_outages: 'https://www.oe.energy.gov/oe417.htm',
  bio_01_h2h_countries: 'https://www.who.int/emergencies/disease-outbreak-news',

  // Oil Axis
  oil_01_russian_brics: 'https://energyandcleanair.org/russia-fossil-tracker/',
  oil_02_mbridge_settlements: 'https://www.bis.org/about/bisih/topics/cbdc/mbridge.htm',
  oil_03_jodi_inventory: 'https://www.jodidata.org/oil/',
  oil_04_refinery_ratio: 'https://www.jodidata.org/oil/',
  spr_01_level: 'https://www.eia.gov/petroleum/supply/weekly/',
  ofac_01_designations: 'https://ofac.treasury.gov/recent-actions',

  // AI Window
  compute_01_training_cost: 'https://epochai.org/trends',
  labor_ai_01_layoffs: 'https://layoffs.fyi/',
  info_02_deepfake_shocks: 'https://www.sec.gov/news/market-alerts',

  // Jobs & Labor
  job_01_jobless_claims: 'https://www.dol.gov/ui/data.pdf',
  job_01_strike_days: 'https://striketracker.ilr.cornell.edu/',
  supply_pharmacy_shortage: 'https://www.accessdata.fda.gov/scripts/drugshortages/',

  // Rights & Governance
  power_01_ai_surveillance: 'https://legiscan.com/gaits/search',
  civil_01_acled_protests: 'https://acleddata.com/data-export-tool/',
  power_02_dod_autonomy: 'https://www.cbo.gov/topics/defense-and-national-security',
  liberty_01_litigation: 'https://www.aclu.org/court-cases',

  // Social Cohesion
  education_01_closures: 'https://nces.ed.gov/',

  // Default fallbacks by source
  BLS: 'https://www.bls.gov/news.release/',
  Treasury: 'https://www.treasury.gov/resource-center/',
  Fed: 'https://www.federalreserve.gov/newsevents.htm',
  CISA: 'https://www.cisa.gov/news-events/alerts',
  CDC: 'https://www.cdc.gov/media/',
  WHO: 'https://www.who.int/emergencies/disease-outbreak-news',
  EIA: 'https://www.eia.gov/petroleum/weekly/',
  Reuters: 'https://www.reuters.com/',
  Bloomberg: 'https://www.bloomberg.com/markets',
  AP: 'https://apnews.com/',
  NYSE: 'https://www.nyse.com/market-data',
  ACLED: 'https://acleddata.com/',
  NATO: 'https://www.nato.int/cps/en/natohq/news.htm',
  DOL: 'https://www.dol.gov/newsroom/',
  TRAC: 'https://trac.syr.edu/immigration/',
};

// Get URL for a signal based on indicator ID or source name
const getSignalUrl = (indicatorId: string, source: string): string => {
  // Try indicator-specific URL first
  if (SOURCE_URLS[indicatorId]) {
    return SOURCE_URLS[indicatorId];
  }
  // Fall back to source-based URL
  if (SOURCE_URLS[source]) {
    return SOURCE_URLS[source];
  }
  // Default fallback
  return 'https://www.reuters.com/';
};

export const SignalsList: React.FC = () => {
  const { indicators } = useStore();

  // Generate signals from indicator changes using news-style headlines
  const generateSignals = (): Signal[] => {
    const signals: Signal[] = [];

    // Get red indicators first (most urgent)
    const redIndicators = indicators.filter(i => i.status.level === 'red');
    const amberIndicators = indicators.filter(i => i.status.level === 'amber');

    // Generate news-style headlines for red indicators
    redIndicators.slice(0, 3).forEach(ind => {
      const translation = INDICATOR_TRANSLATIONS[ind.id];
      const source = translation?.sourceAbbrev || ind.domain.replace('_', ' ');
      signals.push({
        id: `red-${ind.id}`,
        headline: getSignalHeadline(ind.id, 'red'),
        source,
        url: getSignalUrl(ind.id, source),
        trend: 'up',
        timestamp: 'Now',
      });
    });

    // Generate news-style headlines for amber indicators
    amberIndicators.slice(0, 5).forEach(ind => {
      const translation = INDICATOR_TRANSLATIONS[ind.id];
      const source = translation?.sourceAbbrev || ind.domain.replace('_', ' ');
      signals.push({
        id: `amber-${ind.id}`,
        headline: getSignalHeadline(ind.id, 'amber'),
        source,
        url: getSignalUrl(ind.id, source),
        trend: ind.status.trend === 'up' ? 'up' : ind.status.trend === 'down' ? 'down' : 'neutral',
        timestamp: '2h ago',
      });
    });

    // Add contextual signals if we have space
    if (signals.length < 6 && amberIndicators.some(i => i.domain === 'economy')) {
      signals.push({
        id: 'context-economy',
        headline: 'Fed signals interest rate hold through Q2',
        source: 'Bloomberg',
        url: 'https://www.bloomberg.com/markets',
        trend: 'neutral',
        timestamp: '4h ago',
      });
    }

    if (signals.length < 7 && amberIndicators.some(i => i.domain === 'supply_chain')) {
      signals.push({
        id: 'context-supply',
        headline: 'West Coast port talks continue without resolution',
        source: 'AP',
        url: 'https://apnews.com/hub/supply-chain',
        trend: 'neutral',
        timestamp: '6h ago',
      });
    }

    return signals.slice(0, 8);
  };

  const signals = generateSignals();

  const getTrendIcon = (trend?: 'up' | 'down' | 'neutral') => {
    switch (trend) {
      case 'up':
        return <TrendingUp className="w-3 h-3 text-red-400" />;
      case 'down':
        return <TrendingDown className="w-3 h-3 text-green-400" />;
      default:
        return <Minus className="w-3 h-3 text-olive-tertiary" />;
    }
  };

  if (signals.length === 0) {
    return (
      <div className="text-center py-4 text-olive-tertiary text-sm">
        No active signals
      </div>
    );
  }

  return (
    <div className="space-y-0">
      {signals.map((signal, index) => (
        <motion.a
          key={signal.id}
          href={signal.url}
          target="_blank"
          rel="noopener noreferrer"
          initial={{ opacity: 0, x: 10 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: index * 0.05 }}
          className="block py-3 border-b border-white/5 group cursor-pointer"
        >
          <div className="flex items-start gap-2">
            <div className="mt-1 flex-shrink-0">
              {getTrendIcon(signal.trend)}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm text-olive-primary leading-snug group-hover:text-amber-400 transition-colors">
                {signal.headline}
              </p>
              <div className="flex items-center gap-2 mt-1">
                <span className="text-xs font-mono text-olive-tertiary">{signal.source}</span>
                {signal.timestamp && (
                  <>
                    <span className="text-olive-muted">·</span>
                    <span className="text-xs font-mono text-olive-muted">{signal.timestamp}</span>
                  </>
                )}
                <ExternalLink className="w-2.5 h-2.5 text-olive-muted opacity-0 group-hover:opacity-100 transition-opacity ml-auto" />
              </div>
            </div>
          </div>
        </motion.a>
      ))}
    </div>
  );
};
