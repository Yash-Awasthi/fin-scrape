/**
 * Sparkline Component
 *
 * Minimal line chart - no axes, no labels, just the trend shape.
 * Designed for indicator cards where space is limited.
 */

import React from 'react';

interface SparklineProps {
  data?: Array<{ value: number; timestamp: string }>;
  color?: string;
  height?: number;
  className?: string;
}

export const Sparkline: React.FC<SparklineProps> = ({
  data,
  color = '#9B9990',
  height = 40,
  className = '',
}) => {
  if (!data || data.length < 2) {
    return (
      <div className={`w-full ${className}`} style={{ height }}>
        <div className="w-full h-full flex items-center justify-center text-[10px] text-olive-muted">
          No data
        </div>
      </div>
    );
  }

  const values = data.map(d => d.value);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;

  const width = 200;
  const padding = 2;
  const effectiveHeight = height - padding * 2;

  const points = values.map((v, i) => ({
    x: (i / (values.length - 1)) * width,
    y: padding + effectiveHeight - ((v - min) / range) * effectiveHeight,
  }));

  const pathD = points
    .map((p, i) => (i === 0 ? `M ${p.x} ${p.y}` : `L ${p.x} ${p.y}`))
    .join(' ');

  return (
    <div className={`w-full ${className}`} style={{ height }}>
      <svg
        viewBox={`0 0 ${width} ${height}`}
        className="w-full h-full"
        preserveAspectRatio="none"
      >
        <path
          d={pathD}
          fill="none"
          stroke={color}
          strokeWidth={1.5}
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    </div>
  );
};

/**
 * Get sparkline color based on status
 */
export function getSparklineColor(status: string): string {
  switch (status) {
    case 'red':
      return '#EF4444';
    case 'amber':
      return '#F59E0B';
    case 'green':
      return '#10B981';
    default:
      return '#9B9990';
  }
}
