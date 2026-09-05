import React from 'react';
import { motion } from 'framer-motion';
import { TrendingUp, TrendingDown, Minus, Heart, AlertTriangle, CheckCircle } from 'lucide-react';
import { cn } from '../../utils/cn';
import { IndicatorData } from '../../types';
import { canairyMessages } from '../../content/canairy-messages';
import { formatDistanceToNow } from 'date-fns';

interface NestEggCardProps {
  indicator: IndicatorData;
  onClick?: () => void;
  compact?: boolean;
}

export const NestEggCard: React.FC<NestEggCardProps> = ({
  indicator,
  onClick,
  compact = false,
}) => {
  const { status, id, name, unit, critical } = indicator;
  
  // Get family-friendly name
  const friendlyName = canairyMessages.indicators[id as keyof typeof canairyMessages.indicators]?.new || name;
  const description = canairyMessages.indicators[id as keyof typeof canairyMessages.indicators]?.description || '';

  const getTrendIcon = () => {
    if (!status.trend) return <Minus className="w-4 h-4" />;
    return status.trend === 'up' ? (
      <TrendingUp className="w-4 h-4" />
    ) : (
      <TrendingDown className="w-4 h-4" />
    );
  };

  const getStatusIcon = () => {
    switch (status.level) {
      case 'green':
        return <CheckCircle className="w-5 h-5 text-canairy-green" />;
      case 'amber':
        return <AlertTriangle className="w-5 h-5 text-canairy-amber" />;
      case 'red':
        return <Heart className="w-5 h-5 text-canairy-red animate-pulse" />;
      default:
        return <Minus className="w-5 h-5 text-canairy-charcoal-light" />;
    }
  };

  const getEggColor = () => {
    switch (status.level) {
      case 'green':
        return 'from-canairy-green/20 to-canairy-green/10 border-canairy-green/30';
      case 'amber':
        return 'from-canairy-amber/20 to-canairy-amber/10 border-canairy-amber/30';
      case 'red':
        return 'from-canairy-red/20 to-canairy-red/10 border-canairy-red/30';
      default:
        return 'from-canairy-neutral-dark to-canairy-neutral border-canairy-neutral-dark';
    }
  };

  const cardVariants = {
    initial: { opacity: 0, scale: 0.9, y: 20 },
    animate: {
      opacity: 1,
      scale: 1,
      y: 0,
      transition: {
        type: "spring" as const,
        stiffness: 300,
        damping: 20,
      }
    },
    hover: {
      scale: 1.05,
      y: -5,
      transition: { duration: 0.2 }
    },
    tap: { scale: 0.95 }
  };

  return (
    <motion.div
      variants={cardVariants}
      initial="initial"
      animate="animate"
      whileHover="hover"
      whileTap="tap"
      className={cn(
        "nest-egg relative",
        getEggColor(),
        compact && 'p-4'
      )}
      onClick={onClick}
    >
      {/* Feather decoration */}
      <div className="absolute -top-2 -right-2 transform rotate-12">
        <svg width="30" height="30" viewBox="0 0 30 30" className="text-canairy-yellow-dark opacity-60">
          <path
            d="M15,5 Q10,10 12,20 Q15,15 18,20 Q20,10 15,5"
            fill="currentColor"
            stroke="currentColor"
            strokeWidth="0.5"
          />
        </svg>
      </div>

      {/* Critical indicator badge */}
      {critical && (
        <div className="absolute top-2 right-2">
          <span className="badge-alert text-xs">
            Important
          </span>
        </div>
      )}

      <div className="relative z-10">
        {/* Header */}
        <div className="flex items-start justify-between mb-3">
          <div className="flex-1">
            <h3 className={cn(
              "font-primary font-bold text-canairy-charcoal",
              compact ? "text-base" : "text-lg"
            )}>
              {friendlyName}
            </h3>
            {!compact && description && (
              <p className="text-sm text-canairy-charcoal-light mt-1">
                {description}
              </p>
            )}
          </div>
          <div className="ml-3">
            {getStatusIcon()}
          </div>
        </div>

        {/* Value display */}
        <div className="flex items-baseline justify-between mb-3">
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold font-mono text-canairy-charcoal">
              {typeof status.value === 'number' 
                ? status.value.toLocaleString()
                : status.value}
            </span>
            <span className="text-sm text-canairy-charcoal-light">{unit}</span>
          </div>
          {status.trend && (
            <motion.div
              className={cn(
                "flex items-center gap-1",
                status.trend === 'up' ? 'text-canairy-red' : 'text-canairy-green'
              )}
              animate={{ y: status.trend === 'up' ? -2 : 2 }}
              transition={{ duration: 0.5, repeat: Infinity, repeatType: 'reverse' }}
            >
              {getTrendIcon()}
            </motion.div>
          )}
        </div>

        {/* Status bar */}
        <div className="bg-white/50 rounded-full p-1">
          <div
            className={cn(
              "h-2 rounded-full transition-all duration-500",
              status.level === 'green' && 'bg-canairy-green',
              status.level === 'amber' && 'bg-canairy-amber',
              status.level === 'red' && 'bg-canairy-red',
              status.level === 'unknown' && 'bg-canairy-charcoal-light'
            )}
            style={{ width: `${status.level === 'unknown' ? 20 : status.level === 'green' ? 100 : status.level === 'amber' ? 60 : 30}%` }}
          />
        </div>

        {/* Last update */}
        {!compact && (
          <div className="flex items-center gap-1 text-xs text-canairy-charcoal-light mt-3">
            <span>Checked {formatDistanceToNow(new Date(status.lastUpdate), { addSuffix: true })}</span>
          </div>
        )}
      </div>

      {/* Egg shine effect */}
      <div className="absolute inset-0 rounded-egg bg-gradient-to-br from-white/20 to-transparent pointer-events-none" />
    </motion.div>
  );
};