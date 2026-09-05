import React, { useState, useMemo, useEffect, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Filter, Search, X, RefreshCw } from 'lucide-react';
import { useStore } from '../store';
import { IndicatorData } from '../types';
import { IndicatorCard } from '../components/indicators/IndicatorCard';
import { IndicatorDetailPanel } from '../components/indicators/IndicatorDetailPanel';
import { DataSourceBanner } from '../components/common/DataSourceBanner';
import { cn } from '../utils/cn';
import {
  deduplicateIndicators,
  sortIndicators,
  formatDomain,
  formatTimeAgo,
  hasValidSource,
} from '../data/indicatorDisplay';

type FilterStatus = 'all' | 'green' | 'amber' | 'red';
type FilterDomain = 'all' | 'economy' | 'jobs_labor' | 'rights_governance' | 'security_infrastructure' | 'oil_axis' | 'ai_window' | 'global_conflict' | 'domestic_control' | 'social_cohesion';

const VALID_DOMAINS: FilterDomain[] = ['all', 'economy', 'jobs_labor', 'rights_governance', 'security_infrastructure', 'oil_axis', 'ai_window', 'global_conflict', 'domestic_control', 'social_cohesion'];

export const Indicators: React.FC = () => {
  const { indicators, loading, usingFallbackData, refreshAll } = useStore();
  const [searchParams, setSearchParams] = useSearchParams();
  const [statusFilter, setStatusFilter] = useState<FilterStatus>('all');
  const [selectedIndicator, setSelectedIndicator] = useState<IndicatorData | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [isRetrying, setIsRetrying] = useState(false);

  const handleRetry = async () => {
    setIsRetrying(true);
    await refreshAll();
    setIsRetrying(false);
  };

  // Initialize domain filter from URL params
  const domainParam = searchParams.get('domain');
  const initialDomain = domainParam && VALID_DOMAINS.includes(domainParam as FilterDomain)
    ? (domainParam as FilterDomain)
    : 'all';
  const [domainFilter, setDomainFilter] = useState<FilterDomain>(initialDomain);

  // Update domain filter when URL changes
  useEffect(() => {
    const domain = searchParams.get('domain');
    if (domain && VALID_DOMAINS.includes(domain as FilterDomain)) {
      setDomainFilter(domain as FilterDomain);
    }
  }, [searchParams]);

  // Update URL when domain filter changes
  const handleDomainChange = (domain: FilterDomain) => {
    setDomainFilter(domain);
    if (domain === 'all') {
      searchParams.delete('domain');
    } else {
      searchParams.set('domain', domain);
    }
    setSearchParams(searchParams);
  };

  // Deduplicate indicators first, then apply filters and sort
  // Also filter out indicators without valid sources (data integration pending)
  const processedIndicators = useMemo(() => {
    const deduped = deduplicateIndicators(indicators);
    const searchLower = searchQuery.toLowerCase().trim();
    const filtered = deduped.filter(indicator => {
      // Hide indicators without valid sources
      if (!hasValidSource(indicator.id)) return false;
      if (statusFilter !== 'all' && indicator.status.level !== statusFilter) return false;
      if (domainFilter !== 'all' && indicator.domain !== domainFilter) return false;
      // Search by name or description
      if (searchLower && !indicator.name.toLowerCase().includes(searchLower) &&
          !indicator.description?.toLowerCase().includes(searchLower)) return false;
      return true;
    });
    return sortIndicators(filtered);
  }, [indicators, statusFilter, domainFilter, searchQuery]);

  const filteredIndicators = processedIndicators;
  // Only count indicators with valid sources
  const dedupedIndicators = useMemo(() =>
    deduplicateIndicators(indicators).filter(i => hasValidSource(i.id)),
    [indicators]
  );

  const statusCounts = useMemo(() => ({
    all: dedupedIndicators.length,
    green: dedupedIndicators.filter(i => i.status.level === 'green').length,
    amber: dedupedIndicators.filter(i => i.status.level === 'amber').length,
    red: dedupedIndicators.filter(i => i.status.level === 'red').length,
  }), [dedupedIndicators]);

  const lastRefresh = useMemo(() => {
    if (dedupedIndicators.length === 0) return null;
    const mostRecent = dedupedIndicators.reduce((latest, ind) =>
      new Date(ind.status.lastUpdate) > new Date(latest.status.lastUpdate) ? ind : latest
    );
    return mostRecent.status.lastUpdate;
  }, [dedupedIndicators]);

  const domainLabels: Record<string, string> = {
    economy: formatDomain('economy'),
    jobs_labor: formatDomain('jobs_labor'),
    rights_governance: formatDomain('rights_governance'),
    security_infrastructure: formatDomain('security_infrastructure'),
    oil_axis: formatDomain('oil_axis'),
    ai_window: formatDomain('ai_window'),
    global_conflict: formatDomain('global_conflict'),
    domestic_control: formatDomain('domestic_control'),
    social_cohesion: formatDomain('social_cohesion'),
  };

  // Navigate to a different indicator (for connected indicator clicks)
  const handleNavigate = useCallback((indicatorId: string) => {
    const indicator = filteredIndicators.find(i => i.id === indicatorId)
      || processedIndicators.find(i => i.id === indicatorId);
    if (indicator) {
      setSelectedIndicator(indicator);
    }
  }, [filteredIndicators, processedIndicators]);

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!selectedIndicator) return;

      if (e.key === 'Escape') {
        setSelectedIndicator(null);
        return;
      }

      const currentIndex = filteredIndicators.findIndex(i => i.id === selectedIndicator.id);
      if (currentIndex === -1) return;

      if (e.key === 'ArrowUp' || e.key === 'ArrowLeft') {
        e.preventDefault();
        const prevIndex = currentIndex > 0 ? currentIndex - 1 : filteredIndicators.length - 1;
        setSelectedIndicator(filteredIndicators[prevIndex]);
      } else if (e.key === 'ArrowDown' || e.key === 'ArrowRight') {
        e.preventDefault();
        const nextIndex = currentIndex < filteredIndicators.length - 1 ? currentIndex + 1 : 0;
        setSelectedIndicator(filteredIndicators[nextIndex]);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [selectedIndicator, filteredIndicators]);

  // Filter pill component
  const FilterPill = ({
    label,
    count,
    color,
    active,
    onClick,
  }: {
    label: string;
    count: number;
    color?: 'red' | 'amber' | 'green';
    active: boolean;
    onClick: () => void;
  }) => {
    const colorClasses = {
      red: active ? 'bg-red-500/20 text-red-400 border-red-500/30' : 'text-red-400/60 hover:text-red-400',
      amber: active ? 'bg-amber-500/20 text-amber-400 border-amber-500/30' : 'text-amber-400/60 hover:text-amber-400',
      green: active ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30' : 'text-emerald-400/60 hover:text-emerald-400',
    };

    return (
      <button
        onClick={onClick}
        className={cn(
          'px-3 py-1.5 rounded-lg text-xs font-medium transition-all border',
          color
            ? colorClasses[color]
            : active
            ? 'bg-white/10 text-white border-white/10'
            : 'text-olive-muted border-transparent hover:text-olive-secondary',
          !active && 'border-transparent'
        )}
      >
        {label}
        <span className="ml-1.5 opacity-60">{count}</span>
      </button>
    );
  };

  return (
    <div className="flex h-full">
      {/* Main content area */}
      <div className={cn(
        'flex-1 transition-all duration-300',
        selectedIndicator && 'lg:mr-[560px]'
      )}>
        {/* Header */}
        <div className="px-4 py-4 border-b border-white/5">
          {/* Title row */}
          <div className="flex items-center justify-between">
            <h1 className="text-xl font-display font-semibold text-olive-primary">
              What We Watch
            </h1>
            {lastRefresh && (
              <span className="text-xs font-mono text-olive-data">
                Last refresh: {formatTimeAgo(lastRefresh)}
              </span>
            )}
          </div>

          {/* Filter row */}
          <div className="flex items-center gap-3 mt-3 flex-wrap">
            {/* Search input */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-olive-muted" />
              <input
                type="text"
                placeholder="Search indicators..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9 pr-8 py-1.5 w-48 rounded-lg bg-white/5 border border-white/10 text-sm text-olive-primary placeholder:text-olive-muted focus:outline-none focus:border-white/20 transition-colors"
              />
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery('')}
                  className="absolute right-2 top-1/2 -translate-y-1/2 text-olive-muted hover:text-olive-secondary"
                >
                  <X className="w-4 h-4" />
                </button>
              )}
            </div>

            {/* Divider */}
            <div className="w-px h-4 bg-white/10" />

            {/* Status filters */}
            <FilterPill
              label="All"
              count={statusCounts.all}
              active={statusFilter === 'all'}
              onClick={() => setStatusFilter('all')}
            />
            <FilterPill
              label="Red"
              count={statusCounts.red}
              color="red"
              active={statusFilter === 'red'}
              onClick={() => setStatusFilter('red')}
            />
            <FilterPill
              label="Amber"
              count={statusCounts.amber}
              color="amber"
              active={statusFilter === 'amber'}
              onClick={() => setStatusFilter('amber')}
            />
            <FilterPill
              label="Green"
              count={statusCounts.green}
              color="green"
              active={statusFilter === 'green'}
              onClick={() => setStatusFilter('green')}
            />

            {/* Divider */}
            <div className="w-px h-4 bg-white/10" />

            {/* Domain filter */}
            <select
              value={domainFilter}
              onChange={(e) => handleDomainChange(e.target.value as FilterDomain)}
              className="bg-transparent text-xs text-olive-secondary border border-white/10 rounded-lg px-3 py-1.5 focus:outline-none focus:border-white/20"
            >
              <option value="all">All Domains</option>
              {Object.entries(domainLabels).map(([value, label]) => (
                <option key={value} value={value}>{label}</option>
              ))}
            </select>

            {/* Status summary (right aligned) */}
            <div className="ml-auto flex items-center gap-3 text-xs text-olive-data">
              {statusCounts.red > 0 && (
                <span className="flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-red-400" />
                  <span className="text-red-400">{statusCounts.red} red</span>
                </span>
              )}
              {statusCounts.amber > 0 && (
                <span className="flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
                  <span className="text-amber-400">{statusCounts.amber} amber</span>
                </span>
              )}
              <span className="flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                <span className="text-emerald-400">{statusCounts.green} green</span>
              </span>
            </div>
          </div>
        </div>

        {/* Data Source Warning */}
        <div className="px-4 pt-4">
          <DataSourceBanner
            isUsingFallback={usingFallbackData}
            onRetry={handleRetry}
            isRetrying={isRetrying}
          />
        </div>

        {/* Grid */}
        <div className="p-4">
          {/* Loading state */}
          {loading && indicators.length === 0 && (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
              {[...Array(8)].map((_, i) => (
                <div key={i} className="rounded-xl bg-olive-card border border-white/[0.06] p-4 animate-pulse">
                  <div className="flex items-center gap-2 mb-3">
                    <div className="w-2 h-2 rounded-full bg-olive-muted" />
                    <div className="h-4 bg-olive-muted/30 rounded w-2/3" />
                  </div>
                  <div className="h-8 bg-olive-muted/20 rounded w-1/2 mb-2" />
                  <div className="h-1 bg-olive-muted/20 rounded w-full mb-3" />
                  <div className="h-3 bg-olive-muted/10 rounded w-full" />
                </div>
              ))}
            </div>
          )}

          {!loading && filteredIndicators.length > 0 ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
              {filteredIndicators.map((indicator) => (
                <IndicatorCard
                  key={indicator.id}
                  indicator={indicator}
                  onClick={() => setSelectedIndicator(indicator)}
                  isSelected={selectedIndicator?.id === indicator.id}
                />
              ))}
            </div>
          ) : !loading && filteredIndicators.length === 0 ? (
            <div className="text-center py-16">
              <div className="w-16 h-16 bg-white/5 flex items-center justify-center mx-auto mb-4 rounded-full">
                <Filter className="w-8 h-8 text-olive-muted" />
              </div>
              <h3 className="text-lg font-display font-medium text-olive-primary mb-2">
                No indicators found
              </h3>
              <p className="text-olive-secondary text-sm">
                {usingFallbackData
                  ? 'Unable to load live data. Try refreshing.'
                  : 'Try adjusting your filters'}
              </p>
              {usingFallbackData && (
                <button
                  onClick={handleRetry}
                  disabled={isRetrying}
                  className="mt-4 flex items-center gap-2 px-4 py-2 mx-auto rounded-lg bg-amber-500/20 text-amber-300 hover:bg-amber-500/30 transition-colors"
                >
                  <RefreshCw className={cn('w-4 h-4', isRetrying && 'animate-spin')} />
                  {isRetrying ? 'Retrying...' : 'Retry'}
                </button>
              )}
            </div>
          ) : null}
        </div>
      </div>

      {/* Detail Panel with Backdrop */}
      <AnimatePresence>
        {selectedIndicator && (
          <>
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.15 }}
              className="fixed inset-0 bg-black/30 z-40 lg:hidden"
              onClick={() => setSelectedIndicator(null)}
            />

            {/* Panel */}
            <IndicatorDetailPanel
              indicator={selectedIndicator}
              onClose={() => setSelectedIndicator(null)}
              onNavigate={handleNavigate}
            />
          </>
        )}
      </AnimatePresence>
    </div>
  );
};
