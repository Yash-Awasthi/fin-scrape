import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Link } from 'react-router-dom';
import { AlertTriangle, Clock, ChevronDown } from 'lucide-react';
import { cn } from '../../utils/cn';
import { useStore } from '../../store';
import { getDisplayName } from '../../data/indicatorTranslations';

export interface ActionItem {
  id: string;
  text: string;
  estimateMinutes: number;
}

export interface LeadCardData {
  id: string;
  headline: string;
  whatsHappening: string;         // The situation (conversational)
  whyItMatters: string;           // Impact on your family
  whatToDo: string;               // Quick 1-sentence summary
  actions: ActionItem[];          // Detailed expandable actions
  urgency: 'today' | 'week' | 'knowing';
  indicatorIds: string[];
  severity: number;
  confidence?: 'high' | 'moderate' | 'low';
  signalCount?: number;
}

interface LeadCardProps {
  data: LeadCardData;
  onClick?: () => void;
  isSelected?: boolean;
}

const URGENCY_CONFIG = {
  today: {
    label: 'Do this today',
    className: 'urgency-today',
    borderColor: 'border-red-500/40',
  },
  week: {
    label: 'This week',
    className: 'urgency-week',
    borderColor: 'border-amber-500/40',
  },
  knowing: {
    label: 'Worth knowing',
    className: 'urgency-knowing',
    borderColor: 'border-olive-hover',
  },
};

const CONFIDENCE_COLORS = {
  high: 'text-green-400',
  moderate: 'text-amber-400',
  low: 'text-red-400',
};

export const LeadCard: React.FC<LeadCardProps> = ({ data, isSelected }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const urgencyConfig = URGENCY_CONFIG[data.urgency];
  const indicators = useStore((s) => s.indicators);

  // Resolve indicator names with data sources from IDs
  const sourceIndicatorsWithSources = data.indicatorIds
    .map((id) => {
      const indicator = indicators.find((i) => i.id === id);
      if (!indicator) return null;
      return {
        id,
        name: getDisplayName(id) || indicator.name,
        dataSource: indicator.dataSource || '',
      };
    })
    .filter(Boolean) as { id: string; name: string; dataSource: string }[];

  // Clean up data source display (e.g., "BLS API" -> "BLS", "CISA JSON Feed" -> "CISA")
  const cleanDataSource = (source: string): string => {
    if (!source) return '';
    return source
      .replace(/ API$/i, '')
      .replace(/ JSON Feed$/i, '')
      .replace(/ Feed$/i, '')
      .replace(/^US /i, '')
      .trim();
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.2 }}
      onClick={() => setIsExpanded(!isExpanded)}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          setIsExpanded(!isExpanded);
        }
      }}
      role="button"
      tabIndex={0}
      aria-expanded={isExpanded}
      aria-label={`${data.headline}. ${isExpanded ? 'Click to collapse' : 'Click to expand for details'}`}
      className={cn(
        'lead-card p-5 cursor-pointer hover:bg-white/[0.02] transition-colors',
        data.urgency === 'today' && 'lead-card-red',
        data.urgency === 'week' && 'lead-card-amber',
        isSelected && 'border-l-3 border-l-amber-500 bg-white/[0.04]'
      )}
    >
      {/* Header: Urgency pill + confidence + expand indicator */}
      <div className="flex items-start justify-between gap-4 mb-3">
        <div className="flex items-center gap-3">
          <span className={cn('urgency-pill', urgencyConfig.className)}>
            <Clock className="w-3 h-3 mr-1" />
            {urgencyConfig.label}
          </span>
          {data.confidence && (
            <span className={cn('text-xs font-medium', CONFIDENCE_COLORS[data.confidence])}>
              {data.confidence.charAt(0).toUpperCase() + data.confidence.slice(1)} confidence
            </span>
          )}
          {data.signalCount && (
            <span className="text-xs text-olive-muted">
              · {data.signalCount} signals
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          {data.severity >= 7 && (
            <AlertTriangle className="w-5 h-5 text-red-400 animate-pulse" />
          )}
          <ChevronDown
            className={cn(
              "w-4 h-4 text-olive-tertiary transition-transform",
              isExpanded && "rotate-180"
            )}
          />
        </div>
      </div>

      {/* Headline */}
      <h3 className="font-display text-display-lead text-olive-primary mb-2">
        {data.headline}
      </h3>

      {/* Collapsed: Show why it matters */}
      {!isExpanded && (
        <p className="text-sm text-olive-secondary line-clamp-2">
          {data.whyItMatters || data.whatsHappening}
        </p>
      )}

      {/* Expanded content */}
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            {/* What's happening */}
            <div className="mb-4 mt-4">
              <p className="text-[10px] font-medium text-olive-tertiary uppercase tracking-wider mb-1.5">
                What's happening
              </p>
              <p className="text-body-card text-olive-secondary leading-relaxed">
                {data.whatsHappening}
              </p>
            </div>

            {/* Why it matters */}
            <div className="mb-4">
              <p className="text-[10px] font-medium text-olive-tertiary uppercase tracking-wider mb-1.5">
                Why it matters
              </p>
              <p className="text-body-card text-olive-secondary leading-relaxed">
                {data.whyItMatters}
              </p>
            </div>

            {/* What to do */}
            <div className="pt-3 border-t border-white/[0.06]">
              <p className="text-[10px] font-medium text-olive-tertiary uppercase tracking-wider mb-1.5">
                What to do
              </p>
              <p className="text-sm text-olive-secondary mb-3">
                {data.whatToDo}
              </p>

              {/* Action items */}
              {data.actions && data.actions.length > 0 && (
                <div className="space-y-2">
                  {data.actions.map((action) => (
                    <div
                      key={action.id}
                      onClick={(e) => e.stopPropagation()}
                      className="flex items-start gap-3 py-2 px-2 rounded-lg hover:bg-white/[0.02] transition-colors"
                    >
                      <div className="w-4 h-4 rounded border border-olive-tertiary/50 flex-shrink-0 mt-0.5 flex items-center justify-center hover:border-olive-secondary cursor-pointer" />
                      <div className="flex-1 min-w-0">
                        <span className="text-sm text-olive-secondary">{action.text}</span>
                        <span className="text-xs text-olive-muted ml-2">
                          ({action.estimateMinutes} min)
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Source indicators with data sources */}
            {sourceIndicatorsWithSources.length > 0 && (
              <div className="mt-4 pt-3 border-t border-white/[0.04]">
                <p className="text-[10px] text-olive-muted mb-1.5">Based on:</p>
                <div className="flex flex-wrap gap-1.5">
                  {sourceIndicatorsWithSources.slice(0, 3).map((ind) => (
                    <Link
                      key={ind.id}
                      to={`/indicator/${ind.id}`}
                      onClick={(e) => e.stopPropagation()}
                      className="text-[10px] px-2 py-0.5 rounded-md bg-white/[0.04] text-olive-data hover:bg-white/[0.08] hover:text-olive-secondary transition-colors"
                    >
                      {ind.name}
                      {ind.dataSource && (
                        <span className="text-olive-muted"> · {cleanDataSource(ind.dataSource)}</span>
                      )}
                    </Link>
                  ))}
                  {sourceIndicatorsWithSources.length > 3 && (
                    <span className="text-[10px] text-olive-muted px-1">
                      +{sourceIndicatorsWithSources.length - 3} more
                    </span>
                  )}
                </div>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
};

// Default/placeholder lead card when no synthesis data
export const LeadCardPlaceholder: React.FC = () => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.2 }}
      className="lead-card p-5"
    >
      <div className="flex items-center gap-3 mb-3">
        <div className="w-20 h-5 skeleton" />
      </div>
      <div className="w-3/4 h-6 skeleton mb-2" />
      <div className="w-full h-4 skeleton mb-1" />
      <div className="w-2/3 h-4 skeleton" />
    </motion.div>
  );
};
