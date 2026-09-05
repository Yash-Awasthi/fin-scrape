import React from 'react';
import { 
  TrendingUp, 
  TrendingDown, 
  Minus, 
  AlertTriangle,
  Info,
  ExternalLink,
  Calendar,
  Database,
  Clock
} from 'lucide-react';
import { Modal } from '../core/Modal';
import { Badge, StatusBadge } from '../core/Badge';
import { cn } from '../../utils/cn';
import { IndicatorData } from '../../types';
import { getIndicatorDescription } from '../../data/indicatorDescriptions';
import { NewsFeed } from '../news/NewsFeed';
import { formatDistanceToNow } from 'date-fns';

interface IndicatorModalProps {
  isOpen: boolean;
  onClose: () => void;
  indicator: IndicatorData;
}

export const IndicatorModal: React.FC<IndicatorModalProps> = ({
  isOpen,
  onClose,
  indicator
}) => {
  const description = getIndicatorDescription(indicator.id);
  
  const getTrendIcon = () => {
    if (!indicator.status.trend) return <Minus className="w-4 h-4" />;
    return indicator.status.trend === 'up' ? (
      <TrendingUp className="w-4 h-4" />
    ) : (
      <TrendingDown className="w-4 h-4" />
    );
  };

  const getTrendColor = () => {
    if (!indicator.status.trend) return 'text-white/30';
    if (indicator.greenFlag) {
      return indicator.status.trend === 'up' ? 'text-green-400' : 'text-red-400';
    }
    return indicator.status.trend === 'up' ? 'text-red-400' : 'text-green-400';
  };

  const getStatusDescription = () => {
    switch (indicator.status.level) {
      case 'green':
        return 'Operating within normal parameters';
      case 'amber':
        return 'Approaching threshold levels - monitor closely';
      case 'red':
        return 'Critical levels detected - action may be required';
      default:
        return 'Status unknown or data unavailable';
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={indicator.name}
      size="lg"
    >
      <div className="space-y-6">
        {/* Current Status */}
        <div className="bg-white/[0.03] rounded-xl p-6">
          <div className="flex items-start justify-between mb-4">
            <div>
              <h3 className="text-lg font-medium text-white mb-2">Current Status</h3>
              <div className="flex items-center gap-4">
                <StatusBadge 
                  level={indicator.status.level}
                  pulse={indicator.status.level === 'red' && indicator.critical}
                />
                {indicator.critical && (
                  <Badge variant="red" size="sm">CRITICAL</Badge>
                )}
              </div>
            </div>
            <div className="text-right">
              <div className="flex items-baseline gap-2 mb-1">
                <span className="text-2xl font-bold text-white">
                  {typeof indicator.status.value === 'number' 
                    ? indicator.status.value.toLocaleString(undefined, { maximumFractionDigits: 2 })
                    : indicator.status.value}
                </span>
                <span className="text-white/30">{indicator.unit}</span>
              </div>
              {indicator.status.trend && (
                <div className={cn('flex items-center gap-1 justify-end', getTrendColor())}>
                  {getTrendIcon()}
                  <span className="text-sm font-medium">
                    {indicator.status.trend === 'up' ? 'Rising' : 'Falling'}
                  </span>
                </div>
              )}
            </div>
          </div>
          
          <p className="text-white/30 text-sm">{getStatusDescription()}</p>
          
          <div className="flex items-center gap-4 mt-4 pt-4 border-t border-white/[0.04] text-sm text-white/30">
            <div className="flex items-center gap-1">
              <Calendar className="w-4 h-4" />
              <span>Updated {formatDistanceToNow(new Date(indicator.status.lastUpdate), { addSuffix: true })}</span>
            </div>
            <div className="flex items-center gap-1">
              <Database className="w-4 h-4" />
              <span>{indicator.dataSource}</span>
            </div>
          </div>
        </div>

        {/* Description */}
        {description && (
          <>
            {/* What We're Tracking */}
            <div>
              <h3 className="text-lg font-medium text-white mb-3 flex items-center gap-2">
                <Info className="w-5 h-5 text-blue-400" />
                What We're Tracking
              </h3>
              <p className="text-white/50 leading-relaxed">{description.whatWeTrack}</p>
            </div>

            {/* Why It Matters */}
            <div>
              <h3 className="text-lg font-medium text-white mb-3 flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-amber-400" />
                Why It Matters
              </h3>
              <p className="text-white/50 leading-relaxed">{description.whyItMatters}</p>
            </div>

            {/* Real World Impact */}
            {description.realWorldImpact && (
              <div className="bg-amber-500/10 border border-amber-500/20 rounded-lg p-4">
                <h3 className="text-lg font-medium text-amber-400 mb-3 flex items-center gap-2">
                  <AlertTriangle className="w-5 h-5" />
                  Real World Impact
                </h3>
                <p className="text-white/50 leading-relaxed">{description.realWorldImpact}</p>
              </div>
            )}

            {/* Threshold Levels */}
            <div>
              <h3 className="text-lg font-medium text-white mb-3">Alert Thresholds</h3>
              <div className="space-y-3">
                <div className="flex items-start gap-3 p-3 bg-green-500/10 border border-green-500/20 rounded-lg">
                  <div className="w-3 h-3 bg-green-400 rounded-full mt-1.5 flex-shrink-0" />
                  <div className="flex-1">
                    <div className="font-medium text-green-400 mb-1">Normal (Green)</div>
                    <p className="text-white/50 text-sm mb-2">{description.thresholds.green}</p>
                    {description.actionGuidance && (
                      <p className="text-white/30 text-xs italic">Action: {description.actionGuidance.green}</p>
                    )}
                  </div>
                </div>
                
                <div className="flex items-start gap-3 p-3 bg-amber-500/10 border border-amber-500/20 rounded-lg">
                  <div className="w-3 h-3 bg-amber-400 rounded-full mt-1.5 flex-shrink-0" />
                  <div className="flex-1">
                    <div className="font-medium text-amber-400 mb-1">Elevated (Amber)</div>
                    <p className="text-white/50 text-sm mb-2">{description.thresholds.amber}</p>
                    {description.actionGuidance && (
                      <p className="text-white/30 text-xs italic">Action: {description.actionGuidance.amber}</p>
                    )}
                  </div>
                </div>
                
                <div className="flex items-start gap-3 p-3 bg-red-500/10 border border-red-500/20 rounded-lg">
                  <div className="w-3 h-3 bg-red-400 rounded-full mt-1.5 flex-shrink-0" />
                  <div className="flex-1">
                    <div className="font-medium text-red-400 mb-1">Critical (Red)</div>
                    <p className="text-white/50 text-sm mb-2">{description.thresholds.red}</p>
                    {description.actionGuidance && (
                      <p className="text-white/30 text-xs italic">Action: {description.actionGuidance.red}</p>
                    )}
                  </div>
                </div>
              </div>
            </div>

            {/* Historical Context */}
            {description.historicalContext && (
              <div className="bg-white/[0.03] rounded-lg p-4 border border-white/[0.08]">
                <h3 className="text-lg font-medium text-white mb-3 flex items-center gap-2">
                  <Clock className="w-5 h-5 text-white/30" />
                  Historical Context
                </h3>
                <p className="text-white/50 text-sm leading-relaxed">{description.historicalContext}</p>
              </div>
            )}

            {/* Methodology */}
            {description.methodology && (
              <div>
                <h3 className="text-lg font-medium text-white mb-3">Methodology</h3>
                <p className="text-white/50 text-sm leading-relaxed">{description.methodology}</p>
              </div>
            )}

            {/* References */}
            {description.references && description.references.length > 0 && (
              <div>
                <h3 className="text-lg font-medium text-white mb-3">References & Sources</h3>
                <div className="space-y-2">
                  {description.references.map((reference, index) => (
                    <div key={index} className="flex items-center gap-2 text-sm text-white/50">
                      <ExternalLink className="w-3 h-3 flex-shrink-0" />
                      <span>{reference}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Related News */}
            <div>
              <NewsFeed 
                indicatorId={indicator.id} 
                limit={5}
                showGlobal={false}
              />
            </div>
          </>
        )}

        {/* Fallback if no description */}
        {!description && (
          <div className="text-center py-8">
            <Info className="w-12 h-12 text-white/20 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-white mb-2">Detailed Information</h3>
            <p className="text-white/30">
              Comprehensive analysis and thresholds for this indicator are being prepared.
            </p>
          </div>
        )}
      </div>
    </Modal>
  );
};