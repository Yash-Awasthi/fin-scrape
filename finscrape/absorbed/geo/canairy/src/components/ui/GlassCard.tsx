import React from 'react';
import { cn } from '../../utils/cn';

interface GlassCardProps {
  children: React.ReactNode;
  className?: string;
  glow?: 'red' | 'amber' | 'green' | 'none';
  padding?: 'none' | 'sm' | 'md' | 'lg';
  interactive?: boolean;
}

const glowClasses = {
  red: 'glow-border-red',
  amber: 'glow-border-amber',
  green: 'glow-border-green',
  none: '',
};

const paddingClasses = {
  none: '',
  sm: 'p-3 sm:p-4',
  md: 'p-4 sm:p-6',
  lg: 'p-6 sm:p-8',
};

export const GlassCard: React.FC<GlassCardProps> = ({
  children,
  className,
  glow = 'none',
  padding = 'md',
  interactive = false,
}) => {
  return (
    <div
      className={cn(
        interactive ? 'glass-card-interactive' : 'glass-card',
        paddingClasses[padding],
        glowClasses[glow],
        className
      )}
    >
      {children}
    </div>
  );
};
