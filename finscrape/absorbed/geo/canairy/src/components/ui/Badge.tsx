import React from 'react';
import { cn } from '../../utils/cn';
import { AlertLevel } from '../../types';

interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: AlertLevel | 'default' | 'outline';
  size?: 'sm' | 'md' | 'lg';
}

export const Badge = React.forwardRef<HTMLSpanElement, BadgeProps>(
  ({ className, variant = 'default', size = 'md', ...props }, ref) => {
    const sizeClasses = {
      sm: 'px-1.5 py-0.5 text-xs',
      md: 'px-2 py-1 text-xs',
      lg: 'px-3 py-1.5 text-sm',
    };

    const variantClasses = {
      default: 'bg-bunker-dark text-bunker-primary border-bunker-border',
      outline: 'bg-transparent text-bunker-primary border-bunker-border',
      green: 'badge-success',
      amber: 'badge-warning',
      red: 'badge-danger',
      unknown: 'bg-bunker-secondary/20 text-bunker-secondary border-bunker-secondary/30',
    };

    return (
      <span
        ref={ref}
        className={cn(
          'inline-flex items-center rounded font-medium border',
          sizeClasses[size],
          variantClasses[variant],
          className
        )}
        {...props}
      />
    );
  }
);

Badge.displayName = 'Badge';

interface StatusBadgeProps {
  level: AlertLevel;
  value?: string | number;
  showIcon?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({
  level,
  value,
  showIcon = true,
  size = 'md',
}) => {
  const icons = {
    green: '✓',
    amber: '!',
    red: '✗',
    unknown: '?',
  };

  return (
    <Badge variant={level} size={size}>
      {showIcon && <span className="mr-1">{icons[level]}</span>}
      {value || level.toUpperCase()}
    </Badge>
  );
};