import React from 'react';
import { motion } from 'framer-motion';
import { cn } from '../../utils/cn';

interface ScoreRingProps {
  value: number;
  max?: number;
  size?: 'sm' | 'md' | 'lg';
  color?: string;
  label?: string;
  sublabel?: string;
  showValue?: boolean;
}

const sizeConfig = {
  sm: { diameter: 80, stroke: 6, fontSize: 'text-xl', subSize: 'text-2xs' },
  md: { diameter: 140, stroke: 8, fontSize: 'text-4xl', subSize: 'text-xs' },
  lg: { diameter: 180, stroke: 10, fontSize: 'text-5xl', subSize: 'text-sm' },
};

export const ScoreRing: React.FC<ScoreRingProps> = ({
  value,
  max = 100,
  size = 'md',
  color,
  label,
  sublabel,
  showValue = true,
}) => {
  const config = sizeConfig[size];
  const radius = (config.diameter - config.stroke) / 2;
  const circumference = 2 * Math.PI * radius;
  const normalizedValue = Math.min(1, Math.max(0, value / max));
  const offset = circumference - normalizedValue * circumference;

  const autoColor = color ?? (
    normalizedValue < 0.3 ? '#10B981' :
    normalizedValue < 0.6 ? '#F59E0B' :
    '#EF4444'
  );

  return (
    <div className="relative flex flex-col items-center">
      <div className="relative" style={{ width: config.diameter, height: config.diameter }}>
        <svg
          width={config.diameter}
          height={config.diameter}
          className="transform -rotate-90"
        >
          {/* Background ring */}
          <circle
            cx={config.diameter / 2}
            cy={config.diameter / 2}
            r={radius}
            fill="none"
            stroke="rgba(255,255,255,0.06)"
            strokeWidth={config.stroke}
          />
          {/* Value ring */}
          <motion.circle
            cx={config.diameter / 2}
            cy={config.diameter / 2}
            r={radius}
            fill="none"
            stroke={autoColor}
            strokeWidth={config.stroke}
            strokeLinecap="round"
            strokeDasharray={circumference}
            initial={{ strokeDashoffset: circumference }}
            animate={{ strokeDashoffset: offset }}
            transition={{ duration: 1.2, ease: 'easeOut' }}
            style={{
              filter: `drop-shadow(0 0 8px ${autoColor}40)`,
            }}
          />
        </svg>

        {/* Center content */}
        {showValue && (
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <motion.span
              className={cn('score-display', config.fontSize)}
              style={{ color: autoColor }}
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.3, duration: 0.5 }}
            >
              {Math.round(value)}
            </motion.span>
            {label && (
              <span className={cn('text-white/40 uppercase tracking-wider mt-0.5', config.subSize)}>
                {label}
              </span>
            )}
          </div>
        )}
      </div>

      {sublabel && (
        <span className="text-xs text-white/30 mt-2">{sublabel}</span>
      )}
    </div>
  );
};
