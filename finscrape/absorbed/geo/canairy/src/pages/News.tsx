import React, { useState, useMemo } from 'react';
import { motion } from 'framer-motion';
import {
  Newspaper,
  Filter,
  Globe,
  TrendingUp,
  AlertTriangle,
  Shield,
  Zap
} from 'lucide-react';
import { NewsFeed } from '../components/news/NewsFeed';
import { Card, CardHeader, CardTitle, CardContent } from '../components/core/Card';
import { Button } from '../components/core/Button';
import { Badge } from '../components/core/Badge';
import { cn } from '../utils/cn';
import { useStore } from '../store';

type NewsFilter = 'all' | 'high' | 'medium' | 'low' | 'indicators';
type DomainFilter = 'all' | 'economy' | 'jobs_labor' | 'rights_governance' | 'security_infrastructure' | 'oil_axis' | 'ai_window' | 'global_conflict' | 'domestic_control' | 'social_cohesion';

const indicatorOptions = [
  { id: 'econ_01_treasury_tail', name: '10Y Auction Tail', icon: TrendingUp },
  { id: 'market_01_intraday_swing', name: '10Y Intraday Swing', icon: TrendingUp },
  { id: 'taiwan_pla_activity', name: 'Taiwan PLA Incursions', icon: Shield },
  { id: 'nato_high_readiness', name: 'NATO High Readiness', icon: Globe },
  { id: 'national_guard_metros', name: 'Guard Deployments', icon: AlertTriangle },
  { id: 'oil_01_russian_brics', name: 'Russian Crude to BRICS', icon: Zap },
  { id: 'info_02_deepfake_shocks', name: 'Deepfake Shocks', icon: AlertTriangle },
  { id: 'ice_detention_surge', name: 'ICE Detention', icon: AlertTriangle },
];

export const News: React.FC = () => {
  const [urgencyFilter, setUrgencyFilter] = useState<NewsFilter>('all');
  const [domainFilter, setDomainFilter] = useState<DomainFilter>('all');
  const [selectedIndicator, setSelectedIndicator] = useState<string | null>(null);
  const [showIndicatorFilter, setShowIndicatorFilter] = useState(false);

  // Get real indicator counts from store
  const indicators = useStore(s => s.indicators);
  const statusCounts = useMemo(() => ({
    red: indicators.filter(i => i.status.level === 'red').length,
    amber: indicators.filter(i => i.status.level === 'amber').length,
    green: indicators.filter(i => i.status.level === 'green').length,
  }), [indicators]);

  const getFilteredView = () => {
    if (selectedIndicator) {
      return (
        <NewsFeed
          key={`indicator-${selectedIndicator}`}
          indicatorId={selectedIndicator}
          limit={20}
          showGlobal={false}
        />
      );
    }

    return (
      <NewsFeed
        key="global-feed"
        showGlobal={true}
        limit={20}
      />
    );
  };

  const clearFilters = () => {
    setSelectedIndicator(null);
    setUrgencyFilter('all');
    setDomainFilter('all');
    setShowIndicatorFilter(false);
  };

  return (
    <>
      {/* Page Header */}
      <div className="border-b border-white/[0.04]">
        <div className="px-4 sm:px-6 lg:px-8 py-4 sm:py-6">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
            <div>
              <h1 className="text-2xl sm:text-3xl font-semibold text-white">News</h1>
              <p className="text-white/30 mt-1">What's happening in the world, filtered for what matters to your family</p>
            </div>
            <div className="flex items-center gap-2">
              <Button
                onClick={() => setShowIndicatorFilter(!showIndicatorFilter)}
                variant={showIndicatorFilter ? 'primary' : 'ghost'}
                size="sm"
              >
                <Filter className="w-4 h-4 mr-2" />
                Filter by Indicator
              </Button>

              {(selectedIndicator || urgencyFilter !== 'all' || domainFilter !== 'all') && (
                <Button
                  onClick={clearFilters}
                  variant="ghost"
                  size="sm"
                >
                  Clear Filters
                </Button>
              )}
            </div>
          </div>

          {/* Indicator Filter Panel */}
          {showIndicatorFilter && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="mb-6 p-4 bg-white/[0.03] rounded-lg border border-white/[0.04]"
            >
              <h3 className="text-white font-medium mb-3">Filter by Risk Indicator</h3>
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
                <button
                  onClick={() => setSelectedIndicator(null)}
                  className={cn(
                    "p-3 rounded-lg text-sm font-medium transition-all text-left",
                    !selectedIndicator
                      ? "bg-white text-[#0A0A0A]"
                      : "bg-white/5 text-white/50 hover:bg-white/10 hover:text-white"
                  )}
                >
                  <div className="flex items-center gap-2">
                    <Globe className="w-4 h-4" />
                    All News
                  </div>
                </button>

                {indicatorOptions.map((indicator) => (
                  <button
                    key={indicator.id}
                    onClick={() => setSelectedIndicator(indicator.id)}
                    className={cn(
                      "p-3 rounded-lg text-sm font-medium transition-all text-left",
                      selectedIndicator === indicator.id
                        ? "bg-white text-[#0A0A0A]"
                        : "bg-white/5 text-white/50 hover:bg-white/10 hover:text-white"
                    )}
                  >
                    <div className="flex items-center gap-2">
                      <indicator.icon className="w-4 h-4" />
                      {indicator.name}
                    </div>
                  </button>
                ))}
              </div>
            </motion.div>
          )}

          {/* Active Filters */}
          {(selectedIndicator || urgencyFilter !== 'all' || domainFilter !== 'all') && (
            <div className="flex items-center gap-2 mb-4">
              <span className="text-sm text-white/30">Active filters:</span>

              {selectedIndicator && (
                <Badge variant="accent">
                  {indicatorOptions.find(i => i.id === selectedIndicator)?.name || selectedIndicator}
                </Badge>
              )}

              {urgencyFilter !== 'all' && (
                <Badge variant="amber">
                  {urgencyFilter.charAt(0).toUpperCase() + urgencyFilter.slice(1)} Urgency
                </Badge>
              )}

              {domainFilter !== 'all' && (
                <Badge variant="accent">
                  {domainFilter.replace('_', ' ')} Domain
                </Badge>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Content */}
      <div className="px-4 sm:px-6 lg:px-8 py-4 sm:py-8">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* Main News Feed */}
          <div className="lg:col-span-3">
            {getFilteredView()}
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Shield className="w-5 h-5 text-blue-400" />
                  Current Risk Status
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-white/50">High Priority</span>
                    <Badge variant="red" size="sm">{statusCounts.red} indicator{statusCounts.red !== 1 ? 's' : ''}</Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-white/50">Monitoring</span>
                    <Badge variant="amber" size="sm">{statusCounts.amber} indicator{statusCounts.amber !== 1 ? 's' : ''}</Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-white/50">Normal</span>
                    <Badge variant="green" size="sm">{statusCounts.green} indicator{statusCounts.green !== 1 ? 's' : ''}</Badge>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Newspaper className="w-5 h-5 text-purple-400" />
                  News Sources
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 text-sm">
                  <div className="flex items-center justify-between">
                    <span className="text-white/50">Wall Street Journal</span>
                    <Badge variant="green" size="sm">95/100</Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-white/50">Reuters</span>
                    <Badge variant="green" size="sm">92/100</Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-white/50">Bloomberg</span>
                    <Badge variant="green" size="sm">90/100</Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-white/50">Financial Times</span>
                    <Badge variant="green" size="sm">88/100</Badge>
                  </div>
                </div>
                <div className="mt-4 pt-4 border-t border-white/[0.04]">
                  <p className="text-xs text-white/30">
                    Sources rated by credibility and bias assessment
                  </p>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </>
  );
};
