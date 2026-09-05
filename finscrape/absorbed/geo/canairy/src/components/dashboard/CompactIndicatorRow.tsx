import React from 'react';
import { motion } from 'framer-motion';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { useStore } from '../../store';
import { IndicatorData } from '../../types';
import { cn } from '../../utils/cn';

interface CompactIndicatorRowProps {
  onIndicatorClick?: (indicator: IndicatorData) => void;
  max?: number;
}

export const CompactIndicatorRow: React.FC<CompactIndicatorRowProps> = ({
  onIndicatorClick,
  max = 6,
}) => {
  const { indicators } = useStore();

  // Pick top indicators: all reds first, then critical ambers, then top ambers
  const topIndicators = [...indicators]
    .filter(i => i.status.level === 'red' || i.status.level === 'amber')
    .sort((a, b) => {
      if (a.status.level === 'red' && b.status.level !== 'red') return -1;
      if (a.status.level !== 'red' && b.status.level === 'red') return 1;
      if (a.critical && !b.critical) return -1;
      if (!a.critical && b.critical) return 1;
      return 0;
    })
    .slice(0, max);

  if (topIndicators.length === 0) return null;

  const TrendIcon = ({ trend }: { trend?: string }) => {
    if (trend === 'up') return <TrendingUp className="w-3 h-3" />;
    if (trend === 'down') return <TrendingDown className="w-3 h-3" />;
    return <Minus className="w-2.5 h-2.5" />;
  };

  const statusColors = {
    red: { dot: 'bg-red-500', text: 'text-red-400', border: 'border-red-500/15 hover:border-red-500/30' },
    amber: { dot: 'bg-amber-500', text: 'text-amber-400', border: 'border-amber-500/10 hover:border-amber-500/25' },
    green: { dot: 'bg-green-500', text: 'text-green-400', border: 'border-green-500/10' },
    unknown: { dot: 'bg-white/20', text: 'text-white/30', border: 'border-white/5' },
  };

  return (
    <div>
      <h2 className="text-xs font-medium text-white/30 uppercase tracking-wider mb-3">Key Indicators</h2>
      <div className="flex flex-wrap gap-2">
        {topIndicators.map((ind, idx) => {
          const colors = statusColors[ind.status.level];
          return (
            <motion.button
              key={ind.id}
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.2 + idx * 0.03 }}
              onClick={() => onIndicatorClick?.(ind)}
              className={cn(
                'inline-flex items-center gap-2 px-3 py-1.5 rounded-xl',
                'bg-white/[0.03] border transition-all duration-200 cursor-pointer',
                colors.border
              )}
            >
              <span className={cn('w-1.5 h-1.5 rounded-full flex-shrink-0', colors.dot,
                ind.status.level === 'red' && ind.critical && 'animate-pulse'
              )} />
              <span className="text-xs text-white/60 truncate max-w-[120px]">{ind.name}</span>
              <span className={cn('text-xs font-mono', colors.text)}>
                {typeof ind.status.value === 'number' ? ind.status.value.toFixed(1) : ind.status.value}
              </span>
              <span className={cn('text-white/20')}>
                <TrendIcon trend={ind.status.trend} />
              </span>
            </motion.button>
          );
        })}
      </div>
    </div>
  );
};
