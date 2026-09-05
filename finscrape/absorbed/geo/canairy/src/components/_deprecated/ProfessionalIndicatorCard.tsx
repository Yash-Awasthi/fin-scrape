import React from 'react';
import { motion } from 'framer-motion';
import { TrendingUp, TrendingDown, Minus, Activity, Clock } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '../core/Card';
import { Badge, StatusBadge } from '../core/Badge';
import { cn } from '../../utils/cn';
import { IndicatorData } from '../../types';
import { formatDistanceToNow } from 'date-fns';

interface IndicatorCardProps {
  indicator: IndicatorData;
  onClick?: () => void;
  compact?: boolean;
}

export const ProfessionalIndicatorCard: React.FC<IndicatorCardProps> = ({
  indicator,
  onClick,
  compact = false,
}) => {
  const { status, name, domain, unit, dataSource, critical, greenFlag } = indicator;
  
  const getTrendIcon = () => {
    if (!status.trend) return <Minus className="w-3 h-3" />;
    return status.trend === 'up' ? (
      <TrendingUp className="w-3 h-3" />
    ) : (
      <TrendingDown className="w-3 h-3" />
    );
  };

  const getTrendColor = () => {
    if (!status.trend) return 'text-bmb-secondary';
    if (greenFlag) {
      return status.trend === 'up' ? 'text-bmb-success' : 'text-bmb-danger';
    }
    return status.trend === 'up' ? 'text-bmb-danger' : 'text-bmb-success';
  };

  const cardVariants = {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0 },
    hover: { y: -2 },
  };

  // Generate deterministic sparkline from indicator id hash
  const sparklineData = Array.from({ length: 20 }, (_, i) => {
    // Use indicator id and index for deterministic values
    const hash = indicator.id.split('').reduce((acc, char, j) => acc + char.charCodeAt(0) * (j + 1), 0);
    const baseValue = status.level === 'green' ? 30 : status.level === 'amber' ? 50 : 70;
    const variance = ((hash * (i + 1)) % 30) - 15; // -15 to +15 variance
    return Math.max(10, Math.min(90, baseValue + variance));
  });

  return (
    <motion.div
      variants={cardVariants}
      initial="initial"
      animate="animate"
      whileHover="hover"
      transition={{ duration: 0.2 }}
    >
      <Card
        hover
        onClick={onClick}
        className={cn(
          'relative overflow-hidden',
          status.level === 'red' && critical && 'border-bmb-danger/50',
          compact && 'p-4'
        )}
      >
        {/* Status bar */}
        <div
          className={cn(
            'absolute top-0 left-0 right-0 h-0.5',
            status.level === 'green' && 'bg-bmb-success',
            status.level === 'amber' && 'bg-bmb-warning',
            status.level === 'red' && 'bg-bmb-danger',
            status.level === 'unknown' && 'bg-bmb-secondary'
          )}
        />

        <CardHeader className={compact ? 'pb-3' : ''}>
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <CardTitle className={cn('flex items-center gap-2', compact && 'text-base')}>
                {name}
                {critical && (
                  <Badge variant="red" size="sm">
                    CRITICAL
                  </Badge>
                )}
              </CardTitle>
              <div className="flex items-center gap-2 mt-1">
                <Badge variant="default" size="sm">
                  {domain.replace('_', ' ').toUpperCase()}
                </Badge>
                <span className="text-2xs text-bmb-secondary">
                  {dataSource}
                </span>
              </div>
            </div>
            <StatusBadge 
              level={status.level} 
              size="sm"
              pulse={status.level === 'red' && critical}
            />
          </div>
        </CardHeader>

        <CardContent>
          {/* Value and trend */}
          <div className="flex items-end justify-between mb-3">
            <div>
              <div className="flex items-baseline gap-2">
                <span className="data-value">
                  {typeof status.value === 'number' 
                    ? status.value.toLocaleString(undefined, { maximumFractionDigits: 2 })
                    : status.value}
                </span>
                <span className="data-label">{unit}</span>
              </div>
            </div>
            {status.trend && (
              <div className={cn('flex items-center gap-1', getTrendColor())}>
                {getTrendIcon()}
                <span className="text-xs font-medium">
                  {status.trend === 'up' ? '↑' : '↓'}
                </span>
              </div>
            )}
          </div>

          {/* Mini sparkline */}
          {!compact && (
            <div className="h-8 flex items-end gap-0.5 mb-3">
              {sparklineData.map((value, i) => (
                <div
                  key={i}
                  className={cn(
                    'flex-1 rounded-sm transition-all duration-300',
                    status.level === 'green' && 'bg-bmb-success/20',
                    status.level === 'amber' && 'bg-bmb-warning/20',
                    status.level === 'red' && 'bg-bmb-danger/20',
                    status.level === 'unknown' && 'bg-bmb-secondary/20'
                  )}
                  style={{ height: `${value}%` }}
                />
              ))}
            </div>
          )}

          {/* Last update */}
          <div className="flex items-center justify-between text-2xs text-bmb-secondary">
            <div className="flex items-center gap-1">
              <Clock className="w-3 h-3" />
              <span>
                {formatDistanceToNow(new Date(status.lastUpdate), { addSuffix: true })}
              </span>
            </div>
            <div className="flex items-center gap-1">
              <Activity className="w-3 h-3" />
              <span>Live</span>
            </div>
          </div>
        </CardContent>

        {/* Glow effect for critical red indicators */}
        {status.level === 'red' && critical && (
          <div className="absolute inset-0 pointer-events-none">
            <div className="absolute inset-0 bg-bmb-danger/5 animate-pulse" />
          </div>
        )}
      </Card>
    </motion.div>
  );
};