import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  AlertCircle,
  AlertTriangle,
  CheckCircle,
  ChevronDown,
  ChevronUp,
  Clock,
  Eye,
  Shield,
  Loader2,
  RefreshCw,
} from 'lucide-react';
import { cn } from '../../utils/cn';
import { BriefingResponse, TopicBriefing } from '../../services/synthesis/domainKnowledge';

interface BriefingCardProps {
  briefing: BriefingResponse | null;
  isLoading?: boolean;
  onRefresh?: () => void;
  className?: string;
}

// Single topic card component
const TopicCard: React.FC<{ topic: TopicBriefing; index: number }> = ({ topic, index }) => {
  const [expanded, setExpanded] = useState(false); // All cards start collapsed

  const getStatusIcon = () => {
    switch (topic.status) {
      case 'red':
        return <AlertCircle className="w-5 h-5 text-red-400" />;
      case 'amber':
        return <AlertTriangle className="w-5 h-5 text-amber-400" />;
      case 'green':
        return <CheckCircle className="w-5 h-5 text-green-400" />;
    }
  };

  const getStatusBorder = () => {
    switch (topic.status) {
      case 'red':
        return 'border-red-500/30 bg-red-500/5';
      case 'amber':
        return 'border-amber-500/20 bg-amber-500/5';
      case 'green':
        return 'border-green-500/20 bg-green-500/5';
    }
  };

  const getUrgencyBadge = (urgency: 'now' | 'soon' | 'when-ready') => {
    const styles = {
      now: 'bg-red-500/20 text-red-300 border-red-500/30',
      soon: 'bg-amber-500/20 text-amber-300 border-amber-500/30',
      'when-ready': 'bg-white/10 text-white/50 border-white/20',
    };
    const labels = { now: 'Now', soon: 'This Week', 'when-ready': 'When Ready' };
    return (
      <span className={cn('px-2 py-0.5 text-xs font-medium rounded border', styles[urgency])}>
        {labels[urgency]}
      </span>
    );
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.1 }}
      className={cn('glass-card rounded-xl border overflow-hidden', getStatusBorder())}
    >
      {/* Topic Header */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full p-4 flex items-start justify-between gap-3 text-left hover:bg-white/[0.02] transition-colors"
      >
        <div className="flex items-start gap-3 flex-1">
          <div className="mt-0.5">{getStatusIcon()}</div>
          <div className="flex-1">
            <div className="text-xs text-white/40 uppercase tracking-wide mb-1">{topic.topic}</div>
            <h3 className="text-white font-medium leading-snug">{topic.headline}</h3>

            {/* Preview when collapsed */}
            {!expanded && topic.whatsHappening && (
              <p className="text-white/40 text-sm mt-2 line-clamp-2">
                {topic.whatsHappening.split('\n')[0]}
              </p>
            )}

            {/* Show action preview when collapsed */}
            {!expanded && topic.actions && topic.actions.length > 0 && (
              <div className="flex items-center gap-2 mt-2">
                <Shield className="w-3 h-3 text-white/30" />
                <span className="text-xs text-white/40">
                  {topic.actions.length} action{topic.actions.length > 1 ? 's' : ''} recommended
                </span>
                {topic.actions.some(a => a.urgency === 'now') && (
                  <span className="text-xs text-red-400">• Immediate</span>
                )}
              </div>
            )}
          </div>
        </div>
        {expanded ? (
          <ChevronUp className="w-4 h-4 text-white/30 mt-1" />
        ) : (
          <ChevronDown className="w-4 h-4 text-white/30 mt-1" />
        )}
      </button>

      {/* Expanded Content */}
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="px-4 pb-4 space-y-4">
              {/* What's Happening */}
              {topic.whatsHappening && (
                <div>
                  <div className="text-xs text-white/40 uppercase tracking-wide mb-2">What's Happening</div>
                  <div className="space-y-2">
                    {topic.whatsHappening.split('\n\n').map((p, i) => (
                      <p key={i} className="text-white/60 text-sm leading-relaxed">{p}</p>
                    ))}
                  </div>
                </div>
              )}

              {/* Why It Matters */}
              {topic.whyItMatters && (
                <div>
                  <div className="text-xs text-white/40 uppercase tracking-wide mb-2">Why It Matters</div>
                  <p className="text-white/60 text-sm leading-relaxed">{topic.whyItMatters}</p>
                </div>
              )}

              {/* Where It's Heading */}
              {topic.whereItsHeading && (
                <div>
                  <div className="text-xs text-white/40 uppercase tracking-wide mb-2">Where It's Heading</div>
                  <p className="text-white/60 text-sm leading-relaxed">{topic.whereItsHeading}</p>
                </div>
              )}

              {/* What to Watch */}
              {topic.whatToWatch && topic.whatToWatch.length > 0 && (
                <div>
                  <div className="text-xs text-white/40 uppercase tracking-wide mb-2">What to Watch</div>
                  <ul className="space-y-1">
                    {topic.whatToWatch.map((item, i) => (
                      <li key={i} className="flex items-start gap-2 text-sm">
                        <span className="text-amber-400 mt-0.5">•</span>
                        <span className="text-white/60">{item}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Actions */}
              {topic.actions && topic.actions.length > 0 && (
                <div>
                  <div className="text-xs text-white/40 uppercase tracking-wide mb-2">Recommended Actions</div>
                  <div className="space-y-2">
                    {topic.actions.map((action, i) => (
                      <div
                        key={i}
                        className={cn(
                          'p-3 rounded-lg border',
                          action.urgency === 'now'
                            ? 'bg-red-500/10 border-red-500/20'
                            : action.urgency === 'soon'
                            ? 'bg-amber-500/10 border-amber-500/20'
                            : 'bg-white/5 border-white/10'
                        )}
                      >
                        <div className="flex items-start gap-2 mb-1">
                          <span className="font-medium text-white text-sm flex-1">{action.action}</span>
                          {getUrgencyBadge(action.urgency)}
                        </div>
                        {action.reasoning && (
                          <p className="text-xs text-white/40">{action.reasoning}</p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
};

// Compact row for secondary topics (Zone 3: Thread List)
const CompactTopicRow: React.FC<{ topic: TopicBriefing; index: number }> = ({ topic }) => {
  const [expanded, setExpanded] = useState(false);

  const getStatusDot = () => {
    switch (topic.status) {
      case 'red':
        return 'bg-red-400';
      case 'amber':
        return 'bg-amber-400';
      case 'green':
        return 'bg-green-400';
    }
  };

  const hasUrgentAction = topic.actions?.some(a => a.urgency === 'now');

  return (
    <div className="group">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full py-3 flex items-start gap-3 text-left hover:bg-white/[0.02] transition-colors"
      >
        {/* Status dot */}
        <div className={cn('w-2 h-2 rounded-full mt-1.5 flex-shrink-0', getStatusDot())} />

        <div className="flex-1 min-w-0">
          {/* Topic + Headline */}
          <div className="flex items-baseline gap-2">
            <span className="text-xs text-white/30 uppercase tracking-wide">{topic.topic}</span>
            {hasUrgentAction && (
              <span className="text-xs text-red-400">Action needed</span>
            )}
          </div>
          <p className="text-white/80 text-sm font-medium leading-snug mt-0.5 line-clamp-1">
            {topic.headline}
          </p>

          {/* Preview when collapsed */}
          {!expanded && topic.whatsHappening && (
            <p className="text-white/40 text-xs mt-1 line-clamp-1">
              {topic.whatsHappening.split('\n')[0]}
            </p>
          )}
        </div>

        {/* Expand indicator */}
        <div className="text-white/20 group-hover:text-white/40 transition-colors mt-1">
          {expanded ? (
            <ChevronUp className="w-4 h-4" />
          ) : (
            <ChevronDown className="w-4 h-4" />
          )}
        </div>
      </button>

      {/* Expanded content */}
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="pl-5 pb-4 space-y-3">
              {topic.whatsHappening && (
                <p className="text-white/50 text-sm leading-relaxed">{topic.whatsHappening}</p>
              )}

              {topic.whyItMatters && (
                <div>
                  <span className="text-xs text-white/30 uppercase tracking-wide">Why it matters</span>
                  <p className="text-white/50 text-sm mt-1">{topic.whyItMatters}</p>
                </div>
              )}

              {topic.actions && topic.actions.length > 0 && (
                <div className="flex flex-wrap gap-2 pt-1">
                  {topic.actions.map((action, i) => (
                    <span
                      key={i}
                      className={cn(
                        'text-xs',
                        action.urgency === 'now' ? 'text-red-400' :
                        action.urgency === 'soon' ? 'text-amber-400' : 'text-white/40'
                      )}
                    >
                      → {action.action}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export const BriefingCard: React.FC<BriefingCardProps> = ({
  briefing,
  isLoading = false,
  onRefresh,
  className,
}) => {
  const getStatusIcon = () => {
    if (!briefing) return <Loader2 className="w-5 h-5 animate-spin" />;
    switch (briefing.status) {
      case 'red':
        return <AlertCircle className="w-5 h-5 text-red-400" />;
      case 'amber':
        return <AlertTriangle className="w-5 h-5 text-amber-400" />;
      case 'green':
        return <CheckCircle className="w-5 h-5 text-green-400" />;
    }
  };

  if (isLoading && !briefing) {
    return (
      <div className={cn('space-y-6', className)}>
        <div className="py-12 text-center">
          <Loader2 className="w-6 h-6 animate-spin text-white/30 mx-auto mb-3" />
          <span className="text-white/40 text-sm">Analyzing indicators...</span>
        </div>
      </div>
    );
  }

  if (!briefing) {
    return (
      <div className={cn('space-y-6', className)}>
        <p className="text-white/40 text-sm">No briefing available</p>
      </div>
    );
  }

  const hasTopics = briefing.topics && briefing.topics.length > 0;
  const topicCount = briefing.topics?.length || 0;
  const urgentCount = briefing.topics?.filter(t => t.actions?.some(a => a.urgency === 'now')).length || 0;

  return (
    <div className={cn('space-y-8', className)}>
      {/* Zone 1: Status Hero - NO CONTAINER, just text on the page */}
      <div className="space-y-2">
        <div className="flex items-start justify-between">
          <div className="flex items-start gap-3">
            {getStatusIcon()}
            <div>
              {/* Main headline - typography carries the weight */}
              <h1 className="text-xl text-white font-medium leading-tight">
                {briefing.headline}
              </h1>
              {/* Dynamic context line */}
              <p className="text-sm text-white/50 mt-1">
                {topicCount} signals detected
                {urgentCount > 0 && <span className="text-amber-400"> · {urgentCount} need attention</span>}
              </p>
            </div>
          </div>
          {onRefresh && (
            <button
              onClick={onRefresh}
              disabled={isLoading}
              className="p-2 text-white/30 hover:text-white/60 transition-colors disabled:opacity-50"
            >
              <RefreshCw className={cn('w-4 h-4', isLoading && 'animate-spin')} />
            </button>
          )}
        </div>
        <div className="flex items-center gap-2 text-xs text-white/30 ml-8">
          <Clock className="w-3 h-3" />
          <span>Updated {new Date(briefing.generatedAt).toLocaleTimeString()}</span>
        </div>
      </div>

      {/* Zone 2: Spotlight Card - THE ONE elevated element */}
      {hasTopics && briefing.topics[0] && (
        <div className="mt-6">
          <TopicCard topic={briefing.topics[0]} index={0} />
        </div>
      )}

      {/* Zone 3: Thread List - compact rows, NO card wrappers */}
      {briefing.topics.length > 1 && (
        <div className="mt-8">
          {/* Section header with rule */}
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-medium text-white/60">Other signals</h2>
          </div>
          <div className="border-t border-white/[0.06]" />

          {/* Compact thread rows */}
          <div className="divide-y divide-white/[0.04]">
            {briefing.topics.slice(1).map((topic, i) => (
              <CompactTopicRow key={topic.topic} topic={topic} index={i + 1} />
            ))}
          </div>
        </div>
      )}

      {/* Watch List - lightweight, no card */}
      {briefing.whatToWatch.length > 0 && (
        <div className="mt-6 pt-6 border-t border-white/[0.06]">
          <div className="flex items-center gap-2 mb-3">
            <Eye className="w-4 h-4 text-white/30" />
            <span className="text-sm font-medium text-white/50">Watch for</span>
          </div>
          <ul className="space-y-1.5">
            {briefing.whatToWatch.map((item, i) => (
              <li key={i} className="flex items-start gap-2 text-sm">
                <span className="text-amber-400/60 mt-0.5">•</span>
                <span className="text-white/50">{item}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default BriefingCard;
