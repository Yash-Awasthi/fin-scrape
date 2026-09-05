/**
 * ThresholdBar Component
 *
 * Visual indicator showing where the current value sits relative to
 * amber and red thresholds. Instantly answers "how bad is it?" and
 * "how close to the next level?" without reading numbers.
 */

import React from 'react';
import { motion } from 'framer-motion';

interface ThresholdBarProps {
  value: number;
  min?: number;
  max?: number;
  amberThreshold?: number;
  redThreshold?: number;
  inverted?: boolean; // For indicators where LOWER is worse (e.g., GDP growth)
  height?: number;
}

export const ThresholdBar: React.FC<ThresholdBarProps> = ({
  value,
  min = 0,
  max,
  amberThreshold,
  redThreshold,
  inverted = false,
  height = 8,
}) => {
  // If no thresholds provided, show a simple progress bar
  if (amberThreshold === undefined || redThreshold === undefined) {
    const autoMax = max || Math.max(value * 1.5, 100);
    const pct = Math.min((value / autoMax) * 100, 100);

    return (
      <div className="relative rounded-full overflow-hidden bg-white/5" style={{ height }}>
        <motion.div
          className="absolute h-full bg-olive-secondary/50 rounded-full"
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.5, ease: 'easeOut' }}
        />
      </div>
    );
  }

  // Calculate scale max
  const scaleMax = max || Math.max(redThreshold * 1.5, value * 1.2);
  const range = scaleMax - min;

  // Calculate zone positions
  const amberPct = ((amberThreshold - min) / range) * 100;
  const redPct = ((redThreshold - min) / range) * 100;
  const valuePct = Math.min(Math.max(((value - min) / range) * 100, 0), 100);

  // Determine current status color
  const getStatusColor = () => {
    if (inverted) {
      if (value <= redThreshold) return '#EF4444'; // red
      if (value <= amberThreshold) return '#F59E0B'; // amber
      return '#10B981'; // green
    }
    if (value >= redThreshold) return '#EF4444';
    if (value >= amberThreshold) return '#F59E0B';
    return '#10B981';
  };

  if (inverted) {
    // Inverted: Green on right, Red on left
    return (
      <div className="relative rounded-full overflow-hidden bg-white/5" style={{ height }}>
        {/* Red zone (left) */}
        <div
          className="absolute h-full bg-red-500/20"
          style={{ left: 0, width: `${100 - redPct}%` }}
        />
        {/* Amber zone (middle) */}
        <div
          className="absolute h-full bg-amber-500/20"
          style={{
            left: `${100 - redPct}%`,
            width: `${redPct - amberPct}%`
          }}
        />
        {/* Green zone (right) */}
        <div
          className="absolute h-full bg-emerald-500/20"
          style={{ left: `${100 - amberPct}%`, width: `${amberPct}%` }}
        />
        {/* Current value marker */}
        <motion.div
          className="absolute top-1/2 -translate-y-1/2 rounded-full border-2 border-white shadow-md"
          style={{
            width: height * 1.25,
            height: height * 1.25,
            backgroundColor: getStatusColor(),
          }}
          initial={{ left: '0%' }}
          animate={{ left: `${valuePct}%` }}
          transition={{ duration: 0.5, ease: 'easeOut' }}
        />
      </div>
    );
  }

  // Normal: Green on left, Red on right
  return (
    <div className="relative rounded-full overflow-hidden bg-white/5" style={{ height }}>
      {/* Green zone */}
      <div
        className="absolute h-full bg-emerald-500/20"
        style={{ left: 0, width: `${amberPct}%` }}
      />
      {/* Amber zone */}
      <div
        className="absolute h-full bg-amber-500/20"
        style={{
          left: `${amberPct}%`,
          width: `${redPct - amberPct}%`
        }}
      />
      {/* Red zone */}
      <div
        className="absolute h-full bg-red-500/20"
        style={{ left: `${redPct}%`, width: `${100 - redPct}%` }}
      />
      {/* Current value marker */}
      <motion.div
        className="absolute top-1/2 -translate-y-1/2 rounded-full border-2 border-white shadow-md"
        style={{
          width: height * 1.25,
          height: height * 1.25,
          backgroundColor: getStatusColor(),
        }}
        initial={{ left: '0%' }}
        animate={{ left: `calc(${valuePct}% - ${height * 0.625}px)` }}
        transition={{ duration: 0.5, ease: 'easeOut' }}
      />
    </div>
  );
};

/**
 * Compact threshold display showing threshold values
 */
interface ThresholdLabelsProps {
  amberThreshold?: number;
  redThreshold?: number;
  unit?: string;
}

export const ThresholdLabels: React.FC<ThresholdLabelsProps> = ({
  amberThreshold,
  redThreshold,
  unit = '',
}) => {
  if (amberThreshold === undefined && redThreshold === undefined) {
    return null;
  }

  return (
    <div className="flex items-center gap-3 text-[10px] text-olive-muted mt-1">
      {amberThreshold !== undefined && (
        <span className="flex items-center gap-1">
          <span className="w-1.5 h-1.5 rounded-full bg-amber-500/50" />
          Amber: {amberThreshold}{unit}
        </span>
      )}
      {redThreshold !== undefined && (
        <span className="flex items-center gap-1">
          <span className="w-1.5 h-1.5 rounded-full bg-red-500/50" />
          Red: {redThreshold}{unit}
        </span>
      )}
    </div>
  );
};
