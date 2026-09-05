import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  AlertCircle, 
  TrendingUp, 
  TrendingDown, 
  ChevronRight,
  Info,
  AlertTriangle,
  Activity
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '../core/Card';
import { Badge, StatusBadge } from '../core/Badge';
import { cn } from '../../utils/cn';
import { IndicatorData } from '../../types';
import { IndicatorChart } from '../charts/IndicatorChart';
import { formatDistanceToNow } from 'date-fns';
import { getIndicatorDescription } from '../../data/indicatorDescriptions';

interface CriticalIndicatorsProps {
  indicators: IndicatorData[];
  onIndicatorClick?: (indicator: IndicatorData) => void;
  maxItems?: number;
  hideGreen?: boolean;
}

export const CriticalIndicators: React.FC<CriticalIndicatorsProps> = ({
  indicators,
  onIndicatorClick,
  maxItems = 5,
  hideGreen = false
}) => {
  const [expandedId, setExpandedId] = useState<string | null>(null);

  // Get critical indicators sorted by priority
  const getCriticalIndicators = () => {
    // First get all red indicators
    const redIndicators = indicators.filter(i => i.status.level === 'red');
    const criticalReds = redIndicators.filter(i => i.critical);
    const normalReds = redIndicators.filter(i => !i.critical);

    // Then get amber indicators
    const amberIndicators = indicators.filter(i => i.status.level === 'amber');

    // Build priority list: critical reds first, then regular reds, then amber
    const priorityList = [
      ...criticalReds,
      ...normalReds,
      ...amberIndicators
    ];

    // If hideGreen is false and we have room, add green indicators
    if (!hideGreen) {
      const greenIndicators = indicators.filter(i => i.status.level === 'green');
      priorityList.push(...greenIndicators);
    }

    return priorityList.slice(0, maxItems);
  };

  const criticalIndicators = getCriticalIndicators();

  if (criticalIndicators.length === 0) {
    return null;
  }

  const getImpactSummary = (indicator: IndicatorData): string => {
    const descriptions: Record<string, string> = {
      econ_01_treasury_tail: 'Bank lending may tighten, mortgage rates rise',
      econ_02_grocery_cpi: 'Food prices outpacing wages — budget impact',
      market_01_intraday_swing: 'Systemic market stress — protect deposits NOW',
      green_g1_gdp_rates: 'Economy not meeting green-flag conditions',
      job_01_strike_days: 'Labor disruptions affecting supply chains',
      power_01_ai_surveillance: 'Surveillance legislation accelerating',
      civil_01_acled_protests: 'Social unrest rising — avoid protest zones',
      cyber_01_cisa_kev: 'Critical infrastructure under cyber attack',
      grid_01_pjm_outages: 'Power grid showing fragility — test backups',
      bio_01_h2h_countries: 'Novel pathogen transmission detected',
      oil_01_russian_brics: 'Oil trade de-dollarization accelerating',
      oil_02_mbridge_settlements: 'CBDC oil settlement bypassing USD',
      ofac_01_designations: 'Sanctions escalation — fuel price risk',
      oil_04_refinery_ratio: 'Refining shifting East — domestic supply risk',
      labor_ai_01_layoffs: 'AI displacement hitting multiple industries',
      cyber_02_ai_ransomware: 'AI-enhanced ransomware targeting infrastructure',
      info_02_deepfake_shocks: 'Information warfare — verify all breaking news',
      compute_01_training_cost: 'AI cost trends shifting',
      global_conflict_intensity: 'Multiple conflicts escalating globally',
      taiwan_pla_activity: 'Semiconductor supply at risk from PLA activity',
      nato_high_readiness: 'NATO forces activated — conflict proximity HIGH',
      nuclear_01_tests: 'Nuclear deterrence under pressure',
      russia_nato_escalation: 'Russia-NATO tensions at dangerous levels',
      defense_spending_growth: 'Arms race dynamics emerging globally',
      dc_control_countdown: 'Federal control consolidation advancing',
      national_guard_metros: 'Guard deployed — movement restrictions likely',
      ice_detention_surge: 'Mass enforcement operations active',
      dhs_removal_expansion: 'Due process curtailed — civil liberties at risk',
      hill_control_legislation: 'Control legislation advancing rapidly',
      liberty_litigation_count: 'Civil rights under broad legal assault',
    };

    return descriptions[indicator.id] || 'Monitoring for changes';
  };

  const getTrendIcon = (trend?: 'up' | 'down' | 'stable', greenFlag?: boolean) => {
    if (!trend || trend === 'stable') return null;
    
    const Icon = trend === 'up' ? TrendingUp : TrendingDown;
    const isGood = greenFlag ? trend === 'up' : trend === 'down';
    
    return (
      <Icon className={cn(
        "w-4 h-4",
        isGood ? "text-green-400" : "text-red-400"
      )} />
    );
  };

  return (
    <Card className="mb-8">
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-5 h-5 text-red-400" />
            <span>Critical Indicators</span>
            <Badge variant="red" size="sm">
              {criticalIndicators.filter(i => i.status.level === 'red').length} RED
            </Badge>
          </div>
          <button
            onClick={() => onIndicatorClick?.(criticalIndicators[0])}
            className="text-sm text-white/30 hover:text-white transition-colors flex items-center gap-1"
          >
            View all
            <ChevronRight className="w-4 h-4" />
          </button>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <AnimatePresence>
            {criticalIndicators.map((indicator, index) => {
              const isExpanded = expandedId === indicator.id;
              const description = getIndicatorDescription(indicator.id);
              
              return (
                <motion.div
                  key={indicator.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  transition={{ delay: index * 0.05 }}
                  className={cn(
                    "border rounded-lg transition-all cursor-pointer",
                    indicator.status.level === 'red' && indicator.critical 
                      ? "border-red-500/50 bg-red-500/5" 
                      : "border-white/[0.04] hover:border-white/[0.08]"
                  )}
                  onClick={() => setExpandedId(isExpanded ? null : indicator.id)}
                >
                  <div className="p-4">
                    {/* Header */}
                    <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3 mb-3">
                      <div className="flex-1">
                        <div className="flex flex-wrap items-center gap-2 mb-1">
                          <h4 className="font-display font-medium text-white">{indicator.name}</h4>
                          <StatusBadge 
                            level={indicator.status.level} 
                            size="sm"
                            pulse={indicator.status.level === 'red' && indicator.critical}
                          />
                          {indicator.critical && (
                            <Badge variant="red" size="sm">CRITICAL</Badge>
                          )}
                        </div>
                        <p className="text-sm font-body text-white/30">
                          {getImpactSummary(indicator)}
                        </p>
                      </div>
                      
                      {/* Value and Trend */}
                      <div className="text-left sm:text-right sm:ml-4">
                        <div className="flex items-center gap-2 sm:justify-end">
                          <span className="text-xl font-bold text-white">
                            {typeof indicator.status.value === 'number' 
                              ? indicator.status.value.toLocaleString(undefined, { maximumFractionDigits: 2 })
                              : indicator.status.value}
                          </span>
                          <span className="text-sm text-white/30">{indicator.unit}</span>
                          {getTrendIcon(indicator.status.trend, indicator.greenFlag)}
                        </div>
                        <div className="text-xs text-white/20 mt-1">
                          Updated {formatDistanceToNow(new Date(indicator.status.lastUpdate), { addSuffix: true })}
                        </div>
                      </div>
                    </div>

                    {/* Mini Chart */}
                    <div className="h-12 -mx-4 px-4">
                      <IndicatorChart 
                        indicator={indicator}
                        timeRange="24h"
                        height={48}
                      />
                    </div>

                    {/* Expanded Content */}
                    <AnimatePresence>
                      {isExpanded && description && (
                        <motion.div
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: 'auto', opacity: 1 }}
                          exit={{ height: 0, opacity: 0 }}
                          transition={{ duration: 0.2 }}
                          className="overflow-hidden"
                        >
                          <div className="pt-4 mt-4 border-t border-white/[0.04] space-y-3">
                            {/* Why It Matters */}
                            <div>
                              <h5 className="text-sm font-medium text-white mb-1 flex items-center gap-1">
                                <AlertTriangle className="w-3 h-3 text-amber-400" />
                                Why This Matters Now
                              </h5>
                              <p className="text-sm text-white/50">
                                {description.whyItMatters}
                              </p>
                            </div>

                            {/* Current Threshold */}
                            <div className="bg-white/[0.03] rounded-lg p-3">
                              <div className="text-xs text-white/30 mb-1">Current Status</div>
                              <p className="text-sm text-white/50">
                                {indicator.status.level === 'red' && description.thresholds.red}
                                {indicator.status.level === 'amber' && description.thresholds.amber}
                                {indicator.status.level === 'green' && description.thresholds.green}
                              </p>
                            </div>

                            {/* Action Button */}
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                onIndicatorClick?.(indicator);
                              }}
                              className="w-full py-2 bg-white/5 hover:bg-white/10 rounded-lg text-sm text-white transition-colors flex items-center justify-center gap-2"
                            >
                              <Info className="w-4 h-4" />
                              View Details & Actions
                            </button>
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>
                </motion.div>
              );
            })}
          </AnimatePresence>
        </div>

        {/* Summary Stats */}
        <div className="mt-6 pt-6 border-t border-white/[0.04] flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 text-sm">
          <div className="flex flex-wrap items-center gap-4">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-red-500 rounded-full" />
              <span className="text-white/30">
                {indicators.filter(i => i.status.level === 'red').length} Critical
              </span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-amber-500 rounded-full" />
              <span className="text-white/30">
                {indicators.filter(i => i.status.level === 'amber').length} Elevated
              </span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-green-500 rounded-full" />
              <span className="text-white/30">
                {indicators.filter(i => i.status.level === 'green').length} Normal
              </span>
            </div>
          </div>
          <Activity className="w-4 h-4 text-white/20" />
        </div>
      </CardContent>
    </Card>
  );
};