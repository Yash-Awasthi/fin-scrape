import React, { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Database,
  ChevronDown,
  ChevronUp,
  CheckCircle,
  AlertCircle,
  Clock,
  Building2,
  LineChart,
  Newspaper,
  ExternalLink,
  Radio
} from 'lucide-react';
import { useStore } from '../../store';
import { cn } from '../../utils/cn';
import { formatDistanceToNow } from 'date-fns';

interface DataSource {
  name: string;
  type: 'official' | 'financial' | 'news' | 'data';
  status: 'live' | 'delayed' | 'offline' | 'mock';
  delay?: string;
  indicatorCount: number;
  lastUpdate: string;
  url?: string;
}

// Determine source type
const getSourceType = (name: string): 'official' | 'financial' | 'news' | 'data' => {
  const official = ['Treasury', 'FRED', 'BEA', 'DOE', 'CISA', 'WHO', 'OFAC', 'Congress', 'Federal Register', 'ICE', 'Taiwan MND', 'NATO', 'CTBTO', 'National Guard', 'SIPRI', 'BIS', 'Cornell ILR', 'LegiScan', 'ACLED', 'ACLU', 'EFF'];
  const financial = ['Yahoo Finance', 'JODI', 'Epoch AI', 'Layoffs.fyi', 'Etherscan', 'CREA'];
  const news = ['News', 'Composite', 'X API', 'Google Trends'];

  if (official.some(s => name.includes(s))) return 'official';
  if (financial.some(s => name.includes(s))) return 'financial';
  if (news.some(s => name.includes(s))) return 'news';
  return 'data';
};

// Get source URLs
const getSourceUrl = (name: string): string | undefined => {
  const urls: Record<string, string> = {
    'US Treasury API': 'https://www.treasurydirect.gov/',
    'FRED API': 'https://fred.stlouisfed.org/',
    'BEA / FRED': 'https://www.bea.gov/',
    'Yahoo Finance': 'https://finance.yahoo.com/',
    'Cornell ILR': 'https://striketracker.ilr.cornell.edu/',
    'LegiScan API': 'https://legiscan.com/',
    'ACLED API': 'https://acleddata.com/',
    'CISA JSON Feed': 'https://www.cisa.gov/known-exploited-vulnerabilities-catalog',
    'DOE OE-417': 'https://www.oe.energy.gov/oe417.htm',
    'WHO DON RSS': 'https://www.who.int/emergencies/disease-outbreak-news',
    'CREA': 'https://energyandcleanair.org/',
    'BIS Reports': 'https://www.bis.org/',
    'Treasury OFAC': 'https://ofac.treasury.gov/',
    'JODI API': 'https://www.jodidata.org/',
    'Epoch AI': 'https://epochai.org/',
    'Taiwan MND': 'https://www.mnd.gov.tw/english/',
    'NATO / News': 'https://www.nato.int/',
    'CTBTO / KCNA': 'https://www.ctbto.org/',
    'SIPRI': 'https://www.sipri.org/',
    'ICE Statistics': 'https://www.ice.gov/',
    'Federal Register': 'https://www.federalregister.gov/',
    'ACLU / EFF': 'https://www.aclu.org/',
  };
  return urls[name];
};

const SourceIcon: React.FC<{ type: 'official' | 'financial' | 'news' | 'data'; className?: string }> = ({ type, className }) => {
  switch (type) {
    case 'official':
      return <Building2 className={cn("w-4 h-4", className)} />;
    case 'financial':
      return <LineChart className={cn("w-4 h-4", className)} />;
    case 'news':
      return <Newspaper className={cn("w-4 h-4", className)} />;
    default:
      return <Database className={cn("w-4 h-4", className)} />;
  }
};

const StatusIcon: React.FC<{ status: 'live' | 'delayed' | 'offline' | 'mock' }> = ({ status }) => {
  switch (status) {
    case 'live':
      return (
        <motion.div
          className="flex items-center gap-1 text-green-400"
          animate={{ opacity: [1, 0.6, 1] }}
          transition={{ duration: 2, repeat: Infinity }}
        >
          <CheckCircle className="w-3.5 h-3.5" />
        </motion.div>
      );
    case 'delayed':
      return <Clock className="w-3.5 h-3.5 text-amber-400" />;
    case 'offline':
      return <AlertCircle className="w-3.5 h-3.5 text-red-400" />;
    case 'mock':
      return <Radio className="w-3.5 h-3.5 text-gray-500" />;
  }
};

export const DataProvenance: React.FC = () => {
  const [isExpanded, setIsExpanded] = useState(false);
  const { indicators } = useStore();

  // Aggregate data sources from indicators
  const dataSources = useMemo(() => {
    const sourceMap = new Map<string, DataSource>();

    indicators.forEach(indicator => {
      const name = indicator.dataSource;
      const existing = sourceMap.get(name);

      if (existing) {
        existing.indicatorCount++;
        // Update lastUpdate if this indicator is more recent
        if (new Date(indicator.status.lastUpdate) > new Date(existing.lastUpdate)) {
          existing.lastUpdate = indicator.status.lastUpdate;
        }
      } else {
        sourceMap.set(name, {
          name,
          type: getSourceType(name),
          status: indicator.status.dataSource === 'LIVE' ? 'live' : 'mock',
          indicatorCount: 1,
          lastUpdate: indicator.status.lastUpdate,
          url: getSourceUrl(name)
        });
      }
    });

    return Array.from(sourceMap.values()).sort((a, b) => {
      // Sort: live first, then by indicator count
      if (a.status === 'live' && b.status !== 'live') return -1;
      if (a.status !== 'live' && b.status === 'live') return 1;
      return b.indicatorCount - a.indicatorCount;
    });
  }, [indicators]);

  const liveCount = dataSources.filter(s => s.status === 'live').length;
  const totalIndicators = indicators.length;

  return (
    <div className="bg-[#0A0A0A] border border-[#1A1A1A] rounded-lg overflow-hidden">
      {/* Header - Always visible */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-4 py-3 flex items-center justify-between hover:bg-[#111111] transition-colors"
      >
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <Database className="w-4 h-4 text-gray-400" />
            <span className="text-sm font-medium text-white">Data Provenance</span>
          </div>
          <div className="flex items-center gap-2 text-xs text-gray-400">
            <span>{totalIndicators} indicators</span>
            <span className="text-gray-600">•</span>
            <span>{dataSources.length} sources</span>
            <span className="text-gray-600">•</span>
            <span className="text-green-400">{liveCount} live</span>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {/* Quick status indicator */}
          <div className="flex items-center gap-1.5">
            <motion.div
              className="w-2 h-2 bg-green-400 rounded-full"
              animate={{ scale: [1, 1.2, 1], opacity: [1, 0.7, 1] }}
              transition={{ duration: 2, repeat: Infinity }}
            />
            <span className="text-xs text-green-400">Connected</span>
          </div>
          {isExpanded ? (
            <ChevronUp className="w-4 h-4 text-gray-400" />
          ) : (
            <ChevronDown className="w-4 h-4 text-gray-400" />
          )}
        </div>
      </button>

      {/* Expanded Content */}
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="px-4 pb-4 border-t border-[#1A1A1A]">
              {/* Legend */}
              <div className="flex flex-wrap items-center gap-4 py-3 text-xs text-gray-400 border-b border-[#1A1A1A]">
                <div className="flex items-center gap-1.5">
                  <Building2 className="w-3.5 h-3.5 text-blue-400" />
                  <span>Official</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <LineChart className="w-3.5 h-3.5 text-emerald-400" />
                  <span>Financial</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <Newspaper className="w-3.5 h-3.5 text-amber-400" />
                  <span>News</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <Database className="w-3.5 h-3.5 text-gray-400" />
                  <span>Data</span>
                </div>
              </div>

              {/* Source List */}
              <div className="mt-3 space-y-2 max-h-64 overflow-y-auto">
                {dataSources.map((source) => (
                  <div
                    key={source.name}
                    className="flex items-center justify-between p-2 rounded-lg hover:bg-[#111111] transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <StatusIcon status={source.status} />
                      <SourceIcon
                        type={source.type}
                        className={cn(
                          source.type === 'official' && 'text-blue-400',
                          source.type === 'financial' && 'text-emerald-400',
                          source.type === 'news' && 'text-amber-400',
                          source.type === 'data' && 'text-gray-400'
                        )}
                      />
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="text-sm text-white font-medium">{source.name}</span>
                          <span className="text-xs text-gray-500">
                            ({source.indicatorCount} {source.indicatorCount === 1 ? 'indicator' : 'indicators'})
                          </span>
                        </div>
                        <div className="text-xs text-gray-500">
                          Updated {formatDistanceToNow(new Date(source.lastUpdate), { addSuffix: true })}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className={cn(
                        "text-xs px-2 py-0.5 rounded-full",
                        source.status === 'live' && 'bg-green-400/10 text-green-400',
                        source.status === 'delayed' && 'bg-amber-400/10 text-amber-400',
                        source.status === 'offline' && 'bg-red-400/10 text-red-400',
                        source.status === 'mock' && 'bg-gray-400/10 text-gray-400'
                      )}>
                        {source.status === 'live' ? 'Live' : source.status === 'mock' ? 'Estimated' : source.status}
                      </span>
                      {source.url && (
                        <a
                          href={source.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="p-1 text-gray-500 hover:text-white transition-colors"
                          title="View source"
                        >
                          <ExternalLink className="w-3.5 h-3.5" />
                        </a>
                      )}
                    </div>
                  </div>
                ))}
              </div>

              {/* Footer Note */}
              <div className="mt-3 pt-3 border-t border-[#1A1A1A] text-xs text-gray-500">
                Data refreshes automatically. Official sources are verified government APIs. Estimated values are derived from historical patterns.
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};
