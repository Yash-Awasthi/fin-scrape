import React from 'react';
import { motion } from 'framer-motion';
import { cn } from '../../utils/cn';
import { HOPIScore } from '../../types';

interface HOPIGaugeProps {
  score: HOPIScore | null;
  size?: 'sm' | 'md' | 'lg';
  showDetails?: boolean;
}

export const HOPIGauge: React.FC<HOPIGaugeProps> = ({
  score,
  size = 'md',
  showDetails = true,
}) => {
  const sizeConfig = {
    sm: { width: 200, height: 200, strokeWidth: 20 },
    md: { width: 300, height: 300, strokeWidth: 30 },
    lg: { width: 400, height: 400, strokeWidth: 40 },
  };

  const { width, height, strokeWidth } = sizeConfig[size];
  const radius = (Math.min(width, height) - strokeWidth) / 2;
  const center = width / 2;

  const normalizedScore = score ? Math.min(1, Math.max(0, score.score)) : 0;
  const angle = normalizedScore * 270 - 135; // -135 to 135 degrees
  const confidence = score?.confidence || 0;

  // Calculate arc path
  const startAngle = -135;
  const endAngle = 135;
  const angleInRadians = (angle: number) => (angle * Math.PI) / 180;

  const arcPath = (start: number, end: number, r: number) => {
    const startRad = angleInRadians(start);
    const endRad = angleInRadians(end);
    const largeArcFlag = end - start > 180 ? 1 : 0;

    const x1 = center + r * Math.cos(startRad);
    const y1 = center + r * Math.sin(startRad);
    const x2 = center + r * Math.cos(endRad);
    const y2 = center + r * Math.sin(endRad);

    return `M ${x1} ${y1} A ${r} ${r} 0 ${largeArcFlag} 1 ${x2} ${y2}`;
  };

  const getPhaseColor = (phase: number) => {
    if (phase <= 2) return '#10B981'; // Green
    if (phase <= 5) return '#F59E0B'; // Amber
    return '#EF4444'; // Red
  };

  const getScoreLabel = (score: number) => {
    if (score < 0.3) return 'LOW RISK';
    if (score < 0.6) return 'MODERATE';
    if (score < 0.8) return 'ELEVATED';
    return 'CRITICAL';
  };

  return (
    <div className="flex flex-col items-center">
      <svg width={width} height={height} className="transform -rotate-90">
        {/* Background arc */}
        <path
          d={arcPath(startAngle, endAngle, radius)}
          fill="none"
          stroke="rgba(255,255,255,0.06)"
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        />

        {/* Gradient definitions */}
        <defs>
          <linearGradient id="gauge-gradient" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#10B981" />
            <stop offset="50%" stopColor="#F59E0B" />
            <stop offset="100%" stopColor="#EF4444" />
          </linearGradient>
        </defs>

        {/* Value arc */}
        <motion.path
          d={arcPath(startAngle, angle, radius)}
          fill="none"
          stroke="url(#gauge-gradient)"
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          initial={{ pathLength: 0 }}
          animate={{ pathLength: 1 }}
          transition={{ duration: 1.5, ease: "easeInOut" }}
        />

        {/* Needle */}
        <motion.line
          x1={center}
          y1={center}
          x2={center + radius * Math.cos(angleInRadians(angle))}
          y2={center + radius * Math.sin(angleInRadians(angle))}
          stroke="#F9FAFB"
          strokeWidth={3}
          strokeLinecap="round"
          initial={{ rotate: -135 }}
          animate={{ rotate: angle }}
          transition={{ duration: 1.5, ease: "easeInOut", delay: 0.2 }}
          style={{ transformOrigin: `${center}px ${center}px` }}
        />

        {/* Center dot */}
        <circle
          cx={center}
          cy={center}
          r={strokeWidth / 2}
          fill="#1A1A1A"
          stroke="rgba(255,255,255,0.06)"
          strokeWidth={2}
        />
      </svg>

      {/* Text display */}
      <div className="text-center mt-6 transform rotate-90">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
        >
          <div className="text-5xl font-bold text-bmb-primary font-mono">
            {(normalizedScore * 100).toFixed(0)}
          </div>
          <div className="text-sm text-bmb-secondary mt-1">
            HOPI SCORE
          </div>
        </motion.div>

        {showDetails && score && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.8 }}
            className="mt-4 space-y-2"
          >
            <div className="flex items-center justify-center gap-4">
              <div className="text-center">
                <div 
                  className="text-2xl font-bold"
                  style={{ color: getPhaseColor(score.phase) }}
                >
                  PHASE {score.phase}
                </div>
                <div className="text-xs text-bmb-secondary">Current</div>
              </div>
              <div className="w-px h-8 bg-bmb-border" />
              <div className="text-center">
                <div className="text-2xl font-bold text-bmb-primary">
                  {confidence.toFixed(0)}%
                </div>
                <div className="text-xs text-bmb-secondary">Confidence</div>
              </div>
            </div>
            
            <div className={cn(
              "text-xs font-medium px-3 py-1 rounded-full inline-block",
              normalizedScore < 0.3 && "bg-bmb-success/10 text-bmb-success",
              normalizedScore >= 0.3 && normalizedScore < 0.6 && "bg-bmb-warning/10 text-bmb-warning",
              normalizedScore >= 0.6 && "bg-bmb-danger/10 text-bmb-danger"
            )}>
              {getScoreLabel(normalizedScore)}
            </div>
          </motion.div>
        )}
      </div>
    </div>
  );
};