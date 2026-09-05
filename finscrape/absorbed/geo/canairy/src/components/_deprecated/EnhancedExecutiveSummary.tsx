import React from 'react';
import { motion } from 'framer-motion';
import {
  AlertCircle,
  CheckCircle,
  AlertTriangle,
  Clock,
  TrendingUp,
  Shield,
  Info
} from 'lucide-react';
import { cn } from '../../utils/cn';
import { useStore } from '../../store';
import { Badge } from '../core/Badge';

type SystemStatus = 'stable' | 'monitoring' | 'action-required';
type ImpactTimeframe = 'immediate' | 'this-week' | 'this-month' | 'long-term';

export const EnhancedExecutiveSummary: React.FC = () => {
  const { indicators, hopiScore, currentPhase } = useStore();
  
  const getSystemAnalysis = () => {
    const redIndicators = indicators.filter(i => i.status.level === 'red');
    const criticalReds = redIndicators.filter(i => i.critical);
    const amberIndicators = indicators.filter(i => i.status.level === 'amber');
    
    // Build situation narrative
    const threats: string[] = [];
    let status: SystemStatus = 'stable';
    let confidence = 85; // Base confidence
    
    // Analyze critical threats by domain
    if (redIndicators.some(i => i.id === 'econ_01_treasury_tail' || i.id === 'market_01_intraday_swing')) {
      threats.push('Treasury/market stress detected — banking system under pressure');
      confidence -= 10;
    }

    if (redIndicators.some(i => i.id === 'taiwan_pla_activity')) {
      threats.push('Taiwan PLA incursions escalating — semiconductor supply at risk');
      confidence -= 15;
    }

    if (redIndicators.some(i => i.id === 'nato_high_readiness')) {
      threats.push('NATO high-readiness forces activated — conflict proximity elevated');
      confidence -= 15;
    }

    if (redIndicators.some(i => i.id === 'national_guard_metros')) {
      threats.push('National Guard deployed to major metros — civil order stressed');
      confidence -= 10;
    }

    if (redIndicators.some(i => i.id === 'dhs_removal_expansion')) {
      threats.push('DHS expedited removal expanded — civil liberties eroding');
      confidence -= 5;
    }

    if (redIndicators.some(i => i.id === 'info_02_deepfake_shocks')) {
      threats.push('Deepfake market shocks detected — information warfare active');
      confidence -= 10;
    }

    // Add amber warnings from key indicators
    amberIndicators.forEach(indicator => {
      if (indicator.id === 'econ_02_grocery_cpi') {
        threats.push('Grocery prices rising faster than wages');
        confidence -= 3;
      }
      if (indicator.id === 'oil_01_russian_brics') {
        threats.push('De-dollarization accelerating via Russian oil trade');
        confidence -= 5;
      }
      if (indicator.id === 'ice_detention_surge') {
        threats.push('ICE detention population elevated — enforcement surge active');
        confidence -= 3;
      }
    });
    
    // Determine status
    if (criticalReds.length > 0 || redIndicators.length >= 2) {
      status = 'action-required';
    } else if (redIndicators.length > 0 || amberIndicators.length >= 3) {
      status = 'monitoring';
    }
    
    // Generate main message
    let mainMessage = '';
    let subMessage = '';
    
    if (status === 'action-required') {
      if (criticalReds.length > 0 && redIndicators.length >= 2) {
        mainMessage = 'Multiple Critical Systems Failing';
        subMessage = 'Immediate protective actions required - this pattern preceded the March 2023 banking crisis';
      } else if (criticalReds.length > 0) {
        mainMessage = 'Critical Threat Detected';
        subMessage = `${criticalReds[0].name} has crossed into dangerous territory`;
      } else {
        mainMessage = 'System-Wide Stress Building';
        subMessage = 'Multiple indicators showing red - coordinated response needed';
      }
    } else if (status === 'monitoring') {
      mainMessage = 'Emerging Risks Detected';
      subMessage = threats.length > 0 ? threats[0] : 'Some indicators showing elevated levels';
    } else {
      mainMessage = 'All Systems Operating Normally';
      subMessage = 'No significant threats detected - maintain normal preparedness';
    }
    
    return {
      status,
      mainMessage,
      subMessage,
      threats: threats.slice(0, 3),
      confidence: Math.max(confidence, 20)
    };
  };
  
  const getImpactTimeline = (): { timeframe: ImpactTimeframe; description: string }[] => {
    const timeline: { timeframe: ImpactTimeframe; description: string }[] = [];
    const redIndicators = indicators.filter(i => i.status.level === 'red');
    
    // Immediate impacts (24-48 hours)
    if (redIndicators.some(i => i.id === 'market_01_intraday_swing')) {
      timeline.push({
        timeframe: 'immediate',
        description: 'Bank lending may freeze, ATM limits possible'
      });
    }

    if (redIndicators.some(i => i.id === 'national_guard_metros')) {
      timeline.push({
        timeframe: 'immediate',
        description: 'Movement restrictions likely in affected metros'
      });
    }

    // This week impacts
    if (redIndicators.some(i => i.id === 'taiwan_pla_activity')) {
      timeline.push({
        timeframe: 'this-week',
        description: 'Electronics and semiconductor prices to spike 10-20%'
      });
    }

    if (redIndicators.some(i => i.id === 'econ_01_treasury_tail')) {
      timeline.push({
        timeframe: 'this-week',
        description: 'Stock market correction likely, tighten financial positions'
      });
    }

    // This month impacts
    if (redIndicators.some(i => i.id === 'oil_01_russian_brics' || i.id === 'ofac_01_designations')) {
      timeline.push({
        timeframe: 'this-month',
        description: 'Energy prices rising as oil trade shifts away from USD'
      });
    }

    // Long-term impacts
    if (redIndicators.some(i => i.id === 'oil_02_mbridge_settlements')) {
      timeline.push({
        timeframe: 'long-term',
        description: 'Dollar purchasing power erosion accelerating'
      });
    }
    
    return timeline.slice(0, 4);
  };
  
  const { status, mainMessage, subMessage, threats, confidence } = getSystemAnalysis();
  const impactTimeline = getImpactTimeline();
  
  const getStatusIcon = () => {
    switch (status) {
      case 'stable':
        return <CheckCircle className="w-6 h-6" />;
      case 'monitoring':
        return <AlertTriangle className="w-6 h-6" />;
      case 'action-required':
        return <AlertCircle className="w-6 h-6 animate-pulse" />;
    }
  };
  
  const getStatusColor = () => {
    switch (status) {
      case 'stable':
        return 'text-green-400 border-green-500/20 bg-green-500/5';
      case 'monitoring':
        return 'text-amber-400 border-amber-500/20 bg-amber-500/5';
      case 'action-required':
        return 'text-red-400 border-red-500/20 bg-red-500/5';
    }
  };
  
  const getTimeframeIcon = (timeframe: ImpactTimeframe) => {
    switch (timeframe) {
      case 'immediate':
        return '⚡';
      case 'this-week':
        return '📅';
      case 'this-month':
        return '📆';
      case 'long-term':
        return '🔮';
    }
  };
  
  return (
    <motion.div
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      className="mb-8"
    >
      <div className={cn(
        'rounded-2xl border-2 p-4 sm:p-6',
        getStatusColor()
      )}>
        {/* Main Status */}
        <div className="flex flex-col sm:flex-row sm:items-start gap-4 mb-6">
          <div className="flex items-start gap-4 flex-1">
            <div className="flex-shrink-0 mt-1">
              {getStatusIcon()}
            </div>
            <div className="flex-1">
              <h2 className="text-xl sm:text-2xl font-display font-semibold text-white mb-1">
                {mainMessage}
              </h2>
              <p className="font-body text-white/50 text-sm sm:text-base">
                {subMessage}
              </p>
            </div>
          </div>
          <div className="text-left sm:text-right">
            <div className="text-sm text-white/30 mb-1">Confidence</div>
            <div className="text-xl font-bold text-white">{confidence}%</div>
          </div>
        </div>
        
        {/* Threat Summary */}
        {threats.length > 0 && (
          <div className="mb-6 p-4 bg-white/[0.03] rounded-xl">
            <h3 className="text-sm font-display font-medium text-white/50 mb-3 flex items-center gap-2">
              <Info className="w-4 h-4" />
              Current Situation
            </h3>
            <ul className="space-y-2">
              {threats.map((threat, i) => (
                <li key={i} className="flex items-start gap-2 text-sm">
                  <span className="text-amber-400 mt-0.5">•</span>
                  <span className="font-body text-white/50">{threat}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
        
        {/* Impact Timeline */}
        {impactTimeline.length > 0 && (
          <div className="mb-6">
            <h3 className="text-sm font-display font-medium text-white/50 mb-3 flex items-center gap-2">
              <Clock className="w-4 h-4" />
              Expected Impact Timeline
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {impactTimeline.map((impact, i) => (
                <div key={i} className="bg-white/[0.03] rounded-lg p-3">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-lg">{getTimeframeIcon(impact.timeframe)}</span>
                    <span className="text-xs font-display font-medium text-white/30">
                      {impact.timeframe.replace('-', ' ').toUpperCase()}
                    </span>
                  </div>
                  <p className="text-sm font-body text-white/50">{impact.description}</p>
                </div>
              ))}
            </div>
          </div>
        )}
        
        {/* Bottom Stats Bar */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pt-4 border-t border-white/10">
          <div className="flex flex-wrap items-center gap-4">
            <div className="flex items-center gap-2">
              <Shield className="w-4 h-4 text-white/30" />
              <span className="text-sm text-white/30">
                Phase {currentPhase?.number || 0} Active
              </span>
            </div>
            <div className="flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-white/30" />
              <span className="text-sm text-white/30">
                HOPI: {hopiScore?.score.toFixed(1) || 'N/A'}
              </span>
            </div>
          </div>
          
          {status !== 'stable' && (
            <Badge 
              variant={status === 'action-required' ? 'red' : 'amber'} 
              size="sm"
            >
              {indicators.filter(i => i.status.level === 'red').length} RED ALERTS
            </Badge>
          )}
        </div>
      </div>
    </motion.div>
  );
};