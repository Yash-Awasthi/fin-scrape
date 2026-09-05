import React from 'react';
import { cn } from '../../utils/cn';
import { AlertLevel } from '../../types';

interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: AlertLevel | 'default' | 'outline' | 'accent';
  size?: 'sm' | 'md' | 'lg';
  dot?: boolean;
}

export const Badge = React.forwardRef<HTMLSpanElement, BadgeProps>(
  ({ className, variant = 'default', size = 'md', dot = false, children, ...props }, ref) => {
    const sizeClasses = {
      sm: 'px-2 py-0.5 text-2xs',
      md: 'px-2.5 py-0.5 text-xs',
      lg: 'px-3 py-1 text-sm',
    };

    const variantClasses = {
      default: 'badge-default',
      outline: 'bg-transparent text-olive-secondary border border-olive',
      accent: 'bg-amber-400/10 text-amber-400 border border-amber-400/20',
      green: 'badge-success',
      amber: 'badge-warning',
      red: 'badge-danger',
      unknown: 'bg-white/10 text-olive-secondary border border-white/20',
    };

    return (
      <span
        ref={ref}
        className={cn(
          'badge',
          sizeClasses[size],
          variantClasses[variant],
          className
        )}
        {...props}
      >
        {dot && (
          <span
            className={cn(
              'w-1.5 h-1.5 rounded-full mr-1.5',
              variant === 'green' && 'bg-emerald-400',
              variant === 'amber' && 'bg-amber-400',
              variant === 'red' && 'bg-red-400',
              variant === 'accent' && 'bg-amber-400',
              (variant === 'default' || variant === 'outline' || variant === 'unknown') && 'bg-olive-secondary'
            )}
          />
        )}
        {children}
      </span>
    );
  }
);

Badge.displayName = 'Badge';

interface StatusBadgeProps {
  level: AlertLevel;
  value?: string | number;
  showIcon?: boolean;
  size?: 'sm' | 'md' | 'lg';
  pulse?: boolean;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({
  level,
  value,
  showIcon = true,
  size = 'md',
  pulse = false,
}) => {
  return (
    <Badge 
      variant={level} 
      size={size} 
      dot={showIcon}
      className={cn(pulse && level === 'red' && 'animate-pulse')}
    >
      {value || level.toUpperCase()}
    </Badge>
  );
};