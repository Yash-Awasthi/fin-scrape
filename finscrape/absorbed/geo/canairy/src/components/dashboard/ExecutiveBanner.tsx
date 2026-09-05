import React from 'react';
import { motion } from 'framer-motion';
import { AlertCircle, CheckCircle, AlertTriangle, TrendingUp, Clock } from 'lucide-react';
import { cn } from '../../utils/cn';
import { useStore } from '../../store';
import { formatDistanceToNow } from 'date-fns';

type SystemStatus = 'stable' | 'monitoring' | 'action-required';

interface ExecutiveSummary {
  status: SystemStatus;
  headline: string;
  summary: string;
  confidence: number;
  criticalCount: number;
  changes: string[];
}

export const ExecutiveBanner: React.FC = () => {
  const { indicators, systemStatus } = useStore();
  
  // Generate executive summary based on current data
  const generateSummary = (): ExecutiveSummary => {
    const redCount = indicators.filter(i => i.status.level === 'red').length;
    const criticalReds = indicators.filter(i => i.status.level === 'red' && i.critical).length;
    const amberCount = indicators.filter(i => i.status.level === 'amber').length;
    
    // Calculate 24h changes
    const significantChanges = indicators
      .filter(i => {
        // In real implementation, would compare with historical data
        return i.status.trend === 'up' && (i.status.level === 'red' || i.status.level === 'amber');
      })
      .map(i => `${i.name} ${i.status.trend === 'up' ? 'rising' : 'falling'}`);
    
    let status: SystemStatus = 'stable';
    let headline = 'All Systems Normal';
    let summary = 'All indicators are within normal ranges. Continue routine monitoring.';
    
    if (redCount >= 2 || criticalReds > 0) {
      status = 'action-required';
      headline = `${redCount} Critical Changes Detected`;
      summary = `${criticalReds > 0 ? 'Critical indicators require immediate attention. ' : ''}${
        redCount >= 2 ? 'Multiple systems showing stress. Action recommended within 48-72 hours.' : ''
      }`;
    } else if (redCount > 0 || amberCount >= 3) {
      status = 'monitoring';
      headline = `${redCount + amberCount} Areas Need Attention`;
      summary = 'Some indicators showing elevated levels. Enhanced monitoring recommended. No immediate action required.';
    }
    
    const confidence = systemStatus?.dataQuality || 94.5;
    
    return {
      status,
      headline,
      summary,
      confidence,
      criticalCount: criticalReds,
      changes: significantChanges.slice(0, 3),
    };
  };
  
  const summary = generateSummary();
  
  const getStatusIcon = () => {
    switch (summary.status) {
      case 'stable':
        return <CheckCircle className="w-6 h-6" />;
      case 'monitoring':
        return <AlertTriangle className="w-6 h-6" />;
      case 'action-required':
        return <AlertCircle className="w-6 h-6" />;
    }
  };
  
  const getStatusColor = () => {
    switch (summary.status) {
      case 'stable':
        return 'from-bmb-success/20 to-bmb-success/10 border-bmb-success/30 text-bmb-success';
      case 'monitoring':
        return 'from-bmb-warning/20 to-bmb-warning/10 border-bmb-warning/30 text-bmb-warning';
      case 'action-required':
        return 'from-bmb-danger/20 to-bmb-danger/10 border-bmb-danger/30 text-bmb-danger';
    }
  };
  
  const getBgPattern = () => {
    switch (summary.status) {
      case 'stable':
        return 'bg-gradient-to-r from-bmb-success/5 to-transparent';
      case 'monitoring':
        return 'bg-gradient-to-r from-bmb-warning/5 to-transparent';
      case 'action-required':
        return 'bg-gradient-to-r from-bmb-danger/5 to-transparent';
    }
  };
  
  return (
    <motion.div
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      className="mb-6"
    >
      <div className={cn(
        'relative overflow-hidden rounded-lg border-2 bg-gradient-to-r p-6',
        getStatusColor()
      )}>
        {/* Background pattern */}
        <div className={cn('absolute inset-0', getBgPattern())} />
        
        {/* Content */}
        <div className="relative z-10">
          <div className="flex items-start gap-4">
            {/* Status Icon */}
            <motion.div
              animate={summary.status === 'action-required' ? {
                scale: [1, 1.1, 1],
                transition: { duration: 2, repeat: Infinity }
              } : {}}
              className="flex-shrink-0"
            >
              {getStatusIcon()}
            </motion.div>
            
            {/* Main Content */}
            <div className="flex-1">
              <h2 className="text-2xl font-bold mb-2">
                {summary.headline}
              </h2>
              <p className="text-bmb-primary/90 mb-4">
                {summary.summary}
              </p>
              
              {/* Key Changes */}
              {summary.changes.length > 0 && (
                <div className="flex flex-wrap gap-2 mb-4">
                  {summary.changes.map((change, i) => (
                    <span
                      key={i}
                      className="inline-flex items-center gap-1 px-3 py-1 bg-bmb-black/20 rounded-full text-sm"
                    >
                      <TrendingUp className="w-3 h-3" />
                      {change}
                    </span>
                  ))}
                </div>
              )}
              
              {/* Metadata */}
              <div className="flex items-center gap-4 text-sm opacity-80">
                <span className="flex items-center gap-1">
                  <Clock className="w-4 h-4" />
                  Updated {formatDistanceToNow(new Date(systemStatus?.lastUpdate || new Date()), { addSuffix: true })}
                </span>
                <span>
                  {summary.confidence.toFixed(0)}% confidence
                </span>
              </div>
            </div>
            
            {/* Action Buttons */}
            {summary.status !== 'stable' && (
              <div className="flex flex-col gap-2">
                {summary.status === 'action-required' && (
                  <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    className="px-6 py-2 bg-bmb-danger text-white rounded-md font-medium hover:bg-bmb-danger/90"
                  >
                    Take Action
                  </motion.button>
                )}
                <button className="px-6 py-2 bg-bmb-black/20 rounded-md text-sm hover:bg-bmb-black/30">
                  View Details
                </button>
              </div>
            )}
          </div>
        </div>
        
        {/* Animated border effect for critical status */}
        {summary.status === 'action-required' && (
          <motion.div
            className="absolute inset-0 border-2 border-bmb-danger/50 rounded-lg pointer-events-none"
            animate={{
              opacity: [0.5, 1, 0.5],
            }}
            transition={{
              duration: 2,
              repeat: Infinity,
              ease: "easeInOut"
            }}
          />
        )}
      </div>
    </motion.div>
  );
};