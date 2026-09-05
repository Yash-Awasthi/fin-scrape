import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Link } from 'react-router-dom';
import { Clock, ChevronDown } from 'lucide-react';
import { cn } from '../../utils/cn';
import { useStore } from '../../store';
import { getDisplayName } from '../../data/indicatorTranslations';
import { ActionItem } from './LeadCard';

export interface SecondaryCardData {
  id: string;
  headline: string;
  whatsHappening: string;
  whyItMatters?: string;
  whatToDo?: string;
  actions?: ActionItem[];
  urgency: 'today' | 'week' | 'knowing';
  indicatorIds: string[];
}

interface SecondaryCardProps {
  data: SecondaryCardData;
  index?: number;
}

const URGENCY_CONFIG = {
  today: {
    label: 'Do this today',
    className: 'urgency-today',
  },
  week: {
    label: 'This week',
    className: 'urgency-week',
  },
  knowing: {
    label: 'Worth knowing',
    className: 'urgency-knowing',
  },
};

export const SecondaryCard: React.FC<SecondaryCardProps> = ({ data, index = 0 }) => {
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

  // Clean up data source display
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
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.25 + index * 0.05 }}
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
      className="secondary-card p-4 cursor-pointer hover:bg-white/[0.02] transition-colors"
    >
      {/* Header: Urgency tag + expand indicator */}
      <div className="flex items-center justify-between gap-2 mb-2">
        <span className={cn('urgency-pill', urgencyConfig.className)}>
          <Clock className="w-3 h-3 mr-1" />
          {urgencyConfig.label}
        </span>
        <ChevronDown
          className={cn(
            "w-4 h-4 text-olive-tertiary transition-transform",
            isExpanded && "rotate-180"
          )}
        />
      </div>

      {/* Headline */}
      <h4 className="font-display text-display-secondary text-olive-primary mb-1.5">
        {data.headline}
      </h4>

      {/* Collapsed: Show why it matters */}
      {!isExpanded && (
        <p className="text-body-small text-olive-secondary leading-relaxed line-clamp-2">
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
            <div className="mb-3 mt-2">
              <p className="text-[10px] font-medium text-olive-tertiary uppercase tracking-wider mb-1">
                What's happening
              </p>
              <p className="text-body-small text-olive-secondary leading-relaxed">
                {data.whatsHappening}
              </p>
            </div>

            {/* Why it matters */}
            {data.whyItMatters && (
              <div className="mb-3">
                <p className="text-[10px] font-medium text-olive-tertiary uppercase tracking-wider mb-1">
                  Why it matters
                </p>
                <p className="text-body-small text-olive-secondary leading-relaxed">
                  {data.whyItMatters}
                </p>
              </div>
            )}

            {/* What to do */}
            {data.whatToDo && (
              <div className="mb-3">
                <p className="text-[10px] font-medium text-olive-tertiary uppercase tracking-wider mb-1">
                  What to do
                </p>
                <p className="text-body-small text-olive-secondary">
                  {data.whatToDo}
                </p>
              </div>
            )}

            {/* Action items */}
            {data.actions && data.actions.length > 0 && (
              <div className="space-y-1.5 mb-3">
                {data.actions.map((action) => (
                  <div
                    key={action.id}
                    onClick={(e) => e.stopPropagation()}
                    className="flex items-start gap-2 py-1.5 px-2 rounded hover:bg-white/[0.02] transition-colors"
                  >
                    <div className="w-3.5 h-3.5 rounded border border-olive-tertiary/50 flex-shrink-0 mt-0.5" />
                    <div className="flex-1 min-w-0">
                      <span className="text-xs text-olive-secondary">{action.text}</span>
                      <span className="text-[10px] text-olive-muted ml-1.5">
                        ({action.estimateMinutes} min)
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Source indicators with data sources */}
            {sourceIndicatorsWithSources.length > 0 && (
              <div className="pt-2 border-t border-white/[0.04]">
                <div className="flex flex-wrap items-center gap-1">
                  <span className="text-[10px] text-olive-muted">Based on:</span>
                  {sourceIndicatorsWithSources.slice(0, 2).map((ind) => (
                    <Link
                      key={ind.id}
                      to={`/indicator/${ind.id}`}
                      onClick={(e) => e.stopPropagation()}
                      className="text-[10px] px-1.5 py-0.5 rounded bg-white/[0.04] text-olive-data hover:bg-white/[0.08] hover:text-olive-secondary transition-colors"
                    >
                      {ind.name}
                      {ind.dataSource && (
                        <span className="text-olive-muted"> · {cleanDataSource(ind.dataSource)}</span>
                      )}
                    </Link>
                  ))}
                  {sourceIndicatorsWithSources.length > 2 && (
                    <span className="text-[10px] text-olive-muted">+{sourceIndicatorsWithSources.length - 2}</span>
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

// Compact row for lower-priority patterns
export interface CompactRowData {
  id: string;
  text: string;
  domain: string;
  href?: string;
}

interface CompactRowProps {
  data: CompactRowData;
  index?: number;
}

export const CompactRow: React.FC<CompactRowProps> = ({ data, index = 0 }) => {
  return (
    <motion.div
      initial={{ opacity: 0, x: -5 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: 0.3 + index * 0.03 }}
      className="flex items-center gap-3 py-2 px-3 rounded-lg hover:bg-white/[0.02] transition-colors"
    >
      <div className="w-1.5 h-1.5 rounded-full bg-olive-tertiary flex-shrink-0" />
      <span className="text-sm text-olive-secondary flex-1">{data.text}</span>
      <span className="text-xs text-olive-muted capitalize">{data.domain.replace('_', ' ')}</span>
    </motion.div>
  );
};

// Grid container for secondary cards
interface SecondaryCardsGridProps {
  cards: SecondaryCardData[];
}

export const SecondaryCardsGrid: React.FC<SecondaryCardsGridProps> = ({ cards }) => {
  if (cards.length === 0) return null;

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
      {cards.map((card, index) => (
        <SecondaryCard key={card.id} data={card} index={index} />
      ))}
    </div>
  );
};
