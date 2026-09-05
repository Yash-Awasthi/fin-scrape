/**
 * DataSourceBanner - Shows warning when using fallback/mock data
 *
 * Displays an amber banner informing users that live data is unavailable
 * and they're seeing cached/fallback values.
 */

import React from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { cn } from '../../utils/cn';

interface DataSourceBannerProps {
  isUsingFallback: boolean;
  onRetry?: () => void;
  isRetrying?: boolean;
  className?: string;
}

export const DataSourceBanner: React.FC<DataSourceBannerProps> = ({
  isUsingFallback,
  onRetry,
  isRetrying = false,
  className,
}) => {
  if (!isUsingFallback) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -10 }}
        role="alert"
        aria-live="polite"
        className={cn(
          'flex items-center gap-3 px-4 py-3 rounded-xl',
          'bg-amber-500/10 border border-amber-500/20',
          className
        )}
      >
        <AlertTriangle className="w-5 h-5 text-amber-400 flex-shrink-0" aria-hidden="true" />

        <div className="flex-1 min-w-0">
          <p className="text-sm text-amber-200">
            <span className="font-medium">Live data unavailable</span>
            <span className="text-amber-200/70"> — showing cached values</span>
          </p>
        </div>

        {onRetry && (
          <button
            onClick={onRetry}
            disabled={isRetrying}
            className={cn(
              'flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium',
              'bg-amber-500/20 text-amber-300 hover:bg-amber-500/30',
              'transition-colors focus-visible:ring-2 focus-visible:ring-amber-400',
              isRetrying && 'opacity-50 cursor-not-allowed'
            )}
            aria-label={isRetrying ? 'Retrying...' : 'Retry loading live data'}
          >
            <RefreshCw
              className={cn('w-4 h-4', isRetrying && 'animate-spin')}
              aria-hidden="true"
            />
            {isRetrying ? 'Retrying...' : 'Retry'}
          </button>
        )}
      </motion.div>
    </AnimatePresence>
  );
};

export default DataSourceBanner;
