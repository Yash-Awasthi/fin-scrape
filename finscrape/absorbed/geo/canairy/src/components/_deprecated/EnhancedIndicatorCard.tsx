import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import {
  TrendingUp,
  TrendingDown,
  Minus,
  Clock,
  ExternalLink,
  Building2,
  LineChart,
  Newspaper,
  Database,
  Star,
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '../core/Card';
import { cn } from '../../utils/cn';
import { IndicatorData } from '../../types';
import { IndicatorChart } from '../charts/IndicatorChart';
import { generateHistoricalData } from '../../utils/historicalDataGenerator';
import { ThresholdBar, ThresholdLabels } from './ThresholdBar';
import {
  formatValue,
  formatDomain,
  getSourceDisplay,
  getDescription,
  isCriticalIndicator,
  formatTimeAgo,
} from '../../data/indicatorDisplay';

// Source type detection for verification badges
type SourceType = 'official' | 'financial' | 'news' | 'data';

const getSourceType = (dataSource: string): SourceType => {
  const officialSources = ['Treasury', 'FRED', 'BEA', 'DOE', 'CISA', 'WHO', 'OFAC', 'Congress', 'Federal Register', 'ICE', 'Taiwan MND', 'NATO', 'CTBTO', 'National Guard', 'SIPRI', 'BIS', 'DOL', 'BLS', 'FDA', 'NGB', 'DHS', 'TRAC', 'NERC'];
  const financialSources = ['Yahoo Finance', 'JODI', 'Epoch AI', 'Layoffs.fyi', 'Etherscan', 'Bloomberg', 'CREA', 'Kpler'];
  const newsSources = ['News', 'Composite', 'Aggregator', 'X API', 'Google Trends', 'Reuters', 'ACLED', 'DFRLab'];

  if (officialSources.some(s => dataSource.includes(s))) return 'official';
  if (financialSources.some(s => dataSource.includes(s))) return 'financial';
  if (newsSources.some(s => dataSource.includes(s))) return 'news';
  return 'data';
};

const SourceBadgeIcon: React.FC<{ sourceType: SourceType; className?: string }> = ({ sourceType, className }) => {
  switch (sourceType) {
    case 'official':
      return <Building2 className={cn("w-3 h-3", className)} />;
    case 'financial':
      return <LineChart className={cn("w-3 h-3", className)} />;
    case 'news':
      return <Newspaper className={cn("w-3 h-3", className)} />;
    default:
      return <Database className={cn("w-3 h-3", className)} />;
  }
};

const getSourceBadgeColor = (sourceType: SourceType): string => {
  switch (sourceType) {
    case 'official':
      return 'text-blue-400 bg-blue-400/10 border-blue-400/20';
    case 'financial':
      return 'text-emerald-400 bg-emerald-400/10 border-emerald-400/20';
    case 'news':
      return 'text-amber-400 bg-amber-400/10 border-amber-400/20';
    default:
      return 'text-gray-400 bg-gray-400/10 border-gray-400/20';
  }
};

const getSourceLabel = (sourceType: SourceType): string => {
  switch (sourceType) {
    case 'official':
      return 'Official';
    case 'financial':
      return 'Financial';
    case 'news':
      return 'News';
    default:
      return 'Data';
  }
};

interface IndicatorCardProps {
  indicator: IndicatorData;
  onClick?: () => void;
  showInsights?: boolean;
}

export const EnhancedIndicatorCard: React.FC<IndicatorCardProps> = ({
  indicator,
  onClick,
}) => {
  const navigate = useNavigate();
  const { status, name, domain, unit, sourceUrl, description } = indicator;
  const [timeRange, setTimeRange] = useState<'24h' | '7d' | '30d' | '90d'>('7d');

  // Get formatted values
  const sourceDisplay = getSourceDisplay(indicator.id, indicator.dataSource);
  const domainDisplay = formatDomain(domain);
  const descriptionDisplay = getDescription(indicator.id, description);
  const isKeyIndicator = isCriticalIndicator(indicator.id);
  const currentValue = typeof status.value === 'number' ? status.value : 0;

  const handleViewDetails = (e: React.MouseEvent) => {
    e.stopPropagation();
    navigate(`/indicator/${indicator.id}`);
  };

  // Generate historical data if not provided
  useEffect(() => {
    if (!indicator.history) {
      indicator.history = generateHistoricalData(indicator, timeRange);
    }
  }, [indicator, timeRange]);

  const getTrendIcon = () => {
    if (!status.trend) return <Minus className="w-3.5 h-3.5" />;
    return status.trend === 'up' ? (
      <TrendingUp className="w-3.5 h-3.5" />
    ) : (
      <TrendingDown className="w-3.5 h-3.5" />
    );
  };

  const getTrendColor = () => {
    if (!status.trend) return 'text-olive-muted';
    // For most indicators, up = worse (red), down = better (green)
    // greenFlag indicators are inverted
    const isGreenFlag = indicator.greenFlag;
    if (isGreenFlag) {
      return status.trend === 'up' ? 'text-emerald-400' : 'text-red-400';
    }
    return status.trend === 'up' ? 'text-red-400' : 'text-emerald-400';
  };

  const getStatusColor = () => {
    switch (status.level) {
      case 'green': return 'text-emerald-400';
      case 'amber': return 'text-amber-400';
      case 'red': return 'text-red-400';
      default: return 'text-olive-muted';
    }
  };

  const getStatusDotColor = () => {
    switch (status.level) {
      case 'green': return 'bg-emerald-400';
      case 'amber': return 'bg-amber-400';
      case 'red': return 'bg-red-400';
      default: return 'bg-olive-muted';
    }
  };

  const getStatusBgColor = () => {
    switch (status.level) {
      case 'green': return 'bg-emerald-500/10 border-emerald-500/20';
      case 'amber': return 'bg-amber-500/10 border-amber-500/20';
      case 'red': return 'bg-red-500/10 border-red-500/20';
      default: return 'bg-white/5 border-white/10';
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -2 }}
      transition={{ duration: 0.2 }}
    >
      <Card
        hover
        onClick={onClick}
        className={cn(
          'relative overflow-hidden group',
          status.level === 'red' && 'border-red-500/30'
        )}
      >
        {/* Status bar at top */}
        <div
          className={cn(
            'absolute top-0 left-0 right-0 h-0.5',
            status.level === 'green' && 'bg-emerald-500',
            status.level === 'amber' && 'bg-amber-500',
            status.level === 'red' && 'bg-red-500',
            status.level === 'unknown' && 'bg-olive-muted'
          )}
        />

        <CardHeader className="pb-2">
          <div className="flex items-start justify-between gap-2">
            <div className="flex-1 min-w-0">
              {/* Status dot + Name row */}
              <div className="flex items-center gap-2 mb-1">
                <span className={cn('w-2 h-2 rounded-full shrink-0', getStatusDotColor())} />
                <CardTitle className="truncate text-base">{name}</CardTitle>
              </div>

              {/* Domain + Source row */}
              <div className="flex items-center gap-2 text-xs text-olive-muted">
                <span>{domainDisplay}</span>
                <span className="opacity-30">·</span>
                <span>{sourceDisplay}</span>
              </div>
            </div>

            {/* Status badge */}
            <div className="flex flex-col items-end gap-1">
              <span className={cn(
                'px-2 py-0.5 text-xs font-medium rounded border',
                getStatusBgColor(),
                getStatusColor()
              )}>
                {status.level.toUpperCase()}
              </span>
              {isKeyIndicator && (
                <span className="flex items-center gap-1 text-[10px] text-amber-400/70">
                  <Star className="w-3 h-3" />
                  Key indicator
                </span>
              )}
            </div>
          </div>
        </CardHeader>

        <CardContent className="pt-0">
          {/* Value and trend */}
          <div className="flex items-end justify-between mb-3">
            <div>
              <div className="flex items-baseline gap-1.5">
                <span className="text-xl font-semibold text-white">
                  {formatValue(currentValue, unit)}
                </span>
                {status.trend && (
                  <span className={cn('flex items-center', getTrendColor())}>
                    {getTrendIcon()}
                  </span>
                )}
              </div>
            </div>
          </div>

          {/* Threshold bar */}
          <div className="mb-3">
            <ThresholdBar
              value={currentValue}
              amberThreshold={indicator.thresholds?.threshold_amber}
              redThreshold={indicator.thresholds?.threshold_red}
              inverted={indicator.greenFlag}
              height={6}
            />
            <ThresholdLabels
              amberThreshold={indicator.thresholds?.threshold_amber}
              redThreshold={indicator.thresholds?.threshold_red}
            />
          </div>

          {/* Description */}
          <p className="text-xs text-olive-secondary leading-relaxed mb-3 line-clamp-2">
            {descriptionDisplay}
          </p>

          {/* Chart with time range selector */}
          <div className="mb-3">
            <div className="flex items-center justify-between gap-2 mb-2">
              <span className="text-[10px] text-olive-muted font-medium uppercase tracking-wider">History</span>
              <div className="flex bg-white/[0.03] rounded-md p-0.5">
                {(['24h', '7d', '30d'] as const).map((range) => (
                  <button
                    key={range}
                    onClick={(e) => {
                      e.stopPropagation();
                      setTimeRange(range);
                    }}
                    className={cn(
                      'px-2 py-0.5 text-[10px] font-medium rounded transition-all',
                      timeRange === range
                        ? 'bg-white/10 text-white'
                        : 'text-olive-muted hover:text-white'
                    )}
                  >
                    {range}
                  </button>
                ))}
              </div>
            </div>
            <IndicatorChart
              indicator={indicator}
              timeRange={timeRange}
              height={70}
              className="w-full"
            />
          </div>

          {/* Source Badge */}
          <div className="flex items-center justify-between p-2 bg-white/[0.02] rounded-lg mb-3">
            <div className="flex items-center gap-2">
              {(() => {
                const sourceType = getSourceType(sourceDisplay);
                return (
                  <div className={cn(
                    "flex items-center gap-1 px-1.5 py-0.5 rounded border text-[10px] font-medium",
                    getSourceBadgeColor(sourceType)
                  )}>
                    <SourceBadgeIcon sourceType={sourceType} className="w-2.5 h-2.5" />
                    <span>{getSourceLabel(sourceType)}</span>
                  </div>
                );
              })()}
              <span className="text-[10px] text-olive-muted">{sourceDisplay}</span>
            </div>
            {sourceUrl && (
              <a
                href={sourceUrl}
                target="_blank"
                rel="noopener noreferrer"
                onClick={(e) => e.stopPropagation()}
                className="flex items-center gap-1 text-[10px] text-amber-400/70 hover:text-amber-400 transition-colors"
              >
                <span>Source</span>
                <ExternalLink className="w-2.5 h-2.5" />
              </a>
            )}
          </div>

          {/* Footer */}
          <div className="flex items-center justify-between text-[10px] text-olive-muted">
            <div className="flex items-center gap-1">
              <Clock className="w-3 h-3" />
              <span>Updated {formatTimeAgo(status.lastUpdate)}</span>
            </div>
            <button
              onClick={handleViewDetails}
              className="flex items-center gap-1 text-amber-400/70 hover:text-amber-400 transition-colors font-medium"
            >
              <span>View details</span>
              <ExternalLink className="w-3 h-3" />
            </button>
          </div>
        </CardContent>

        {/* Glow effect for red indicators */}
        {status.level === 'red' && (
          <div className="absolute inset-0 pointer-events-none">
            <div className="absolute inset-0 bg-red-500/5" />
          </div>
        )}
      </Card>
    </motion.div>
  );
};
