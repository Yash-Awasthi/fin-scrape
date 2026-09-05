import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  X,
  Clock,
  Shield,
  Globe,
  Microscope,
  Radio,
  BarChart3,
  Search,
  Users,
  ExternalLink,
  ChevronDown,
  ChevronRight,
  CheckCircle2,
  Circle,
  AlertTriangle,
  Info,
} from 'lucide-react';
import { cn } from '../../utils/cn';
import {
  InsightCardWithEvidence,
  CONFIDENCE_DESCRIPTIONS,
  URGENCY_CONFIG,
  EFFORT_CONFIG,
  PRIORITY_CONFIG,
} from '../../types/trust';
import { SourceType, EvidenceSignal } from '../../data/sourceRegistry';

interface CardDetailModalProps {
  card: InsightCardWithEvidence;
  isOpen: boolean;
  onClose: () => void;
}

/**
 * Get icon for source type
 */
function getSourceIcon(type: SourceType) {
  switch (type) {
    case 'government-official':
      return <Shield className="w-3.5 h-3.5" />;
    case 'international-org':
      return <Globe className="w-3.5 h-3.5" />;
    case 'academic-research':
      return <Microscope className="w-3.5 h-3.5" />;
    case 'wire-service':
      return <Radio className="w-3.5 h-3.5" />;
    case 'industry-data':
      return <BarChart3 className="w-3.5 h-3.5" />;
    case 'investigative-journalism':
      return <Search className="w-3.5 h-3.5" />;
    case 'community-reporting':
      return <Users className="w-3.5 h-3.5" />;
    default:
      return <Info className="w-3.5 h-3.5" />;
  }
}

/**
 * Get color for source type badge
 */
function getSourceColor(type: SourceType): string {
  switch (type) {
    case 'government-official':
    case 'international-org':
      return 'bg-blue-500/20 text-blue-400 border-blue-500/30';
    case 'academic-research':
      return 'bg-purple-500/20 text-purple-400 border-purple-500/30';
    case 'wire-service':
      return 'bg-gray-500/20 text-gray-400 border-gray-500/30';
    case 'industry-data':
      return 'bg-teal-500/20 text-teal-400 border-teal-500/30';
    case 'investigative-journalism':
      return 'bg-amber-500/20 text-amber-400 border-amber-500/30';
    case 'community-reporting':
      return 'bg-olive-hover text-olive-tertiary border-olive-hover';
    default:
      return 'bg-olive-hover text-olive-tertiary border-olive-hover';
  }
}

/**
 * Evidence signal card
 */
function EvidenceCard({ signal }: { signal: EvidenceSignal }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="bg-olive-card/50 rounded-lg border border-olive p-4">
      <div className="flex items-start gap-3">
        {/* Source type badge */}
        <div
          className={cn(
            'flex items-center gap-1.5 px-2 py-1 rounded-md border text-xs font-medium',
            getSourceColor(signal.source.type)
          )}
        >
          {getSourceIcon(signal.source.type)}
          <span>{signal.source.abbreviation}</span>
        </div>

        <div className="flex-1 min-w-0">
          {/* Headline */}
          <h4 className="text-sm font-medium text-olive-primary mb-1">
            {signal.headline}
          </h4>

          {/* Meta line */}
          <div className="flex items-center gap-2 text-xs text-olive-tertiary mb-2">
            <span className="capitalize">
              {signal.source.type.replace(/-/g, ' ')}
            </span>
            <span className="text-olive-muted">·</span>
            <span>
              {new Date(signal.date).toLocaleDateString('en-US', {
                month: 'short',
                day: 'numeric',
                year: 'numeric',
              })}
            </span>
          </div>

          {/* Data point if present */}
          {signal.dataPoint && (
            <div className="bg-olive-page/50 rounded px-3 py-2 mb-2">
              <span className="text-xs text-olive-tertiary">Data point: </span>
              <span className="text-sm text-olive-primary font-mono">
                {signal.dataPoint}
              </span>
            </div>
          )}

          {/* Relevance */}
          <p className="text-xs text-olive-secondary leading-relaxed">
            <span className="text-olive-tertiary">Relevance: </span>
            {signal.relevance}
          </p>

          {/* Expandable source details */}
          <button
            onClick={() => setExpanded(!expanded)}
            className="flex items-center gap-1 mt-2 text-xs text-olive-tertiary hover:text-olive-secondary transition-colors"
          >
            {expanded ? (
              <ChevronDown className="w-3 h-3" />
            ) : (
              <ChevronRight className="w-3 h-3" />
            )}
            Why this source?
          </button>

          <AnimatePresence>
            {expanded && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                className="overflow-hidden"
              >
                <div className="mt-2 p-3 bg-olive-page/30 rounded text-xs text-olive-secondary">
                  <p className="mb-2">{signal.source.description}</p>
                  {signal.url && (
                    <a
                      href={signal.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 text-olive-tertiary hover:text-olive-primary transition-colors"
                    >
                      View original source
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  )}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}

/**
 * Collapsible section wrapper
 */
function CollapsibleSection({
  title,
  count,
  defaultOpen = false,
  children,
}: {
  title: string;
  count?: number;
  defaultOpen?: boolean;
  children: React.ReactNode;
}) {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  return (
    <div className="border-t border-olive pt-4">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center justify-between w-full text-left mb-3"
      >
        <h3 className="text-sm font-medium text-olive-primary flex items-center gap-2">
          {isOpen ? (
            <ChevronDown className="w-4 h-4 text-olive-tertiary" />
          ) : (
            <ChevronRight className="w-4 h-4 text-olive-tertiary" />
          )}
          {title}
          {count !== undefined && (
            <span className="text-xs text-olive-tertiary">({count})</span>
          )}
        </h3>
      </button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden"
          >
            {children}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export const CardDetailModal: React.FC<CardDetailModalProps> = ({
  card,
  isOpen,
  onClose,
}) => {
  const urgencyConfig = URGENCY_CONFIG[card.urgency];
  const confidenceConfig = CONFIDENCE_DESCRIPTIONS[card.confidence];

  // Close on escape
  React.useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleEscape);
    return () => window.removeEventListener('keydown', handleEscape);
  }, [onClose]);

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/60 z-50"
          />

          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.98 }}
            transition={{ type: 'spring', damping: 25, stiffness: 300 }}
            className="fixed inset-4 md:inset-auto md:top-1/2 md:left-1/2 md:-translate-x-1/2 md:-translate-y-1/2 md:w-full md:max-w-2xl md:max-h-[85vh] bg-olive-card rounded-xl border border-olive shadow-2xl z-50 flex flex-col overflow-hidden"
          >
            {/* Header - Sticky */}
            <div className="flex-shrink-0 p-5 border-b border-olive bg-olive-card">
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1">
                  {/* Urgency + Confidence */}
                  <div className="flex items-center gap-3 mb-2">
                    <span
                      className={cn(
                        'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium',
                        urgencyConfig.bgColor,
                        urgencyConfig.color
                      )}
                    >
                      <Clock className="w-3 h-3" />
                      {urgencyConfig.label}
                    </span>
                    <span
                      className={cn(
                        'text-xs font-medium',
                        confidenceConfig.color
                      )}
                    >
                      {confidenceConfig.label}
                    </span>
                    <span className="text-xs text-olive-muted">
                      · Based on {card.evidence.length} signals
                    </span>
                  </div>

                  {/* Headline */}
                  <h2 className="font-display text-xl text-olive-primary">
                    {card.headline}
                  </h2>
                </div>

                {/* Close button */}
                <button
                  onClick={onClose}
                  className="p-2 rounded-lg text-olive-tertiary hover:text-olive-primary hover:bg-white/5 transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            {/* Scrollable content */}
            <div className="flex-1 overflow-y-auto p-5 space-y-6">
              {/* Section 1: The Situation */}
              <div>
                <h3 className="text-xs font-medium text-olive-tertiary uppercase tracking-wider mb-3">
                  The Situation
                </h3>
                <div className="prose prose-invert prose-sm max-w-none">
                  <div className="text-sm text-olive-secondary leading-relaxed whitespace-pre-line">
                    {card.situationBrief.narrative}
                  </div>
                  {card.situationBrief.historicalContext && (
                    <p className="text-xs text-olive-tertiary mt-3 italic">
                      {card.situationBrief.historicalContext}
                    </p>
                  )}
                  <p className="text-xs text-olive-muted mt-3">
                    {card.situationBrief.timeHorizon}
                  </p>
                </div>
              </div>

              {/* Section 2: Evidence */}
              <CollapsibleSection
                title="The Evidence"
                count={card.evidence.length}
                defaultOpen={false}
              >
                <div className="space-y-3">
                  {card.evidence.map((signal) => (
                    <EvidenceCard key={signal.id} signal={signal} />
                  ))}
                </div>
              </CollapsibleSection>

              {/* Section 3: Reasoning */}
              <CollapsibleSection
                title="Our Reasoning"
                defaultOpen={false}
              >
                <div className="space-y-4 text-sm">
                  {/* Observation */}
                  <div>
                    <h4 className="text-xs font-medium text-olive-tertiary mb-1">
                      Observation
                    </h4>
                    <p className="text-olive-secondary">
                      {card.reasoningChain.observation}
                    </p>
                  </div>

                  {/* Interpretation */}
                  <div>
                    <h4 className="text-xs font-medium text-olive-tertiary mb-1">
                      Our interpretation
                    </h4>
                    <p className="text-olive-secondary">
                      {card.reasoningChain.interpretation}
                    </p>
                  </div>

                  {/* Implication */}
                  <div>
                    <h4 className="text-xs font-medium text-olive-tertiary mb-1">
                      What this means for your household
                    </h4>
                    <p className="text-olive-secondary">
                      {card.reasoningChain.implication}
                    </p>
                  </div>

                  {/* Recommendation */}
                  <div>
                    <h4 className="text-xs font-medium text-olive-tertiary mb-1">
                      Why we recommend acting now
                    </h4>
                    <p className="text-olive-secondary">
                      {card.reasoningChain.recommendation}
                    </p>
                  </div>

                  {/* Assumptions */}
                  <div className="bg-olive-page/30 rounded-lg p-3">
                    <h4 className="text-xs font-medium text-olive-tertiary mb-2">
                      What we're assuming
                    </h4>
                    <ul className="space-y-1">
                      {card.reasoningChain.assumptions.map((assumption, i) => (
                        <li
                          key={i}
                          className="text-xs text-olive-secondary flex items-start gap-2"
                        >
                          <span className="text-olive-muted mt-1">•</span>
                          {assumption}
                        </li>
                      ))}
                    </ul>
                  </div>

                  {/* Update triggers */}
                  <div className="bg-olive-page/30 rounded-lg p-3">
                    <h4 className="text-xs font-medium text-olive-tertiary mb-2">
                      What would change this recommendation
                    </h4>
                    <ul className="space-y-1">
                      {card.reasoningChain.updateTriggers.map((trigger, i) => (
                        <li
                          key={i}
                          className="text-xs text-olive-secondary flex items-start gap-2"
                        >
                          <span className="text-olive-muted mt-1">→</span>
                          {trigger}
                        </li>
                      ))}
                    </ul>
                  </div>

                  {/* Counterpoints */}
                  {card.reasoningChain.counterpoints.length > 0 && (
                    <div className="bg-amber-500/5 border border-amber-500/20 rounded-lg p-3">
                      <h4 className="text-xs font-medium text-amber-400 mb-2 flex items-center gap-1.5">
                        <AlertTriangle className="w-3 h-3" />
                        What could make us wrong
                      </h4>
                      <ul className="space-y-1">
                        {card.reasoningChain.counterpoints.map((point, i) => (
                          <li
                            key={i}
                            className="text-xs text-olive-secondary flex items-start gap-2"
                          >
                            <span className="text-amber-400/60 mt-1">•</span>
                            {point}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </CollapsibleSection>

              {/* Section 4: Actions */}
              <div className="border-t border-olive pt-4">
                <h3 className="text-xs font-medium text-olive-tertiary uppercase tracking-wider mb-3">
                  Recommended Actions
                </h3>
                <div className="space-y-3">
                  {card.actions.map((action) => {
                    const priorityConfig = PRIORITY_CONFIG[action.priority];
                    const effortConfig = EFFORT_CONFIG[action.effort];

                    return (
                      <div
                        key={action.id}
                        className="bg-olive-page/30 rounded-lg p-4 border border-olive"
                      >
                        <div className="flex items-start gap-3">
                          {/* Checkbox */}
                          <button className="mt-0.5 text-olive-tertiary hover:text-olive-primary transition-colors">
                            {action.completed ? (
                              <CheckCircle2 className="w-5 h-5 text-green-400" />
                            ) : (
                              <Circle className="w-5 h-5" />
                            )}
                          </button>

                          <div className="flex-1">
                            {/* Task + badges */}
                            <div className="flex items-start justify-between gap-2 mb-1">
                              <h4 className="text-sm font-medium text-olive-primary">
                                {action.task}
                              </h4>
                              <div className="flex items-center gap-2 flex-shrink-0">
                                <span
                                  className={cn(
                                    'text-xs px-2 py-0.5 rounded',
                                    priorityConfig.bgColor,
                                    priorityConfig.color
                                  )}
                                >
                                  {priorityConfig.label}
                                </span>
                                <span
                                  className={cn(
                                    'text-xs',
                                    effortConfig.color
                                  )}
                                >
                                  {action.timeEstimate}
                                </span>
                              </div>
                            </div>

                            {/* Why */}
                            <p className="text-xs text-olive-secondary">
                              {action.why}
                            </p>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>

                {/* Add all to action plan */}
                <button className="w-full mt-4 py-2.5 rounded-lg bg-olive-hover hover:bg-white/10 text-sm font-medium text-olive-primary transition-colors">
                  Add to action plan
                </button>
              </div>
            </div>

            {/* Footer */}
            <div className="flex-shrink-0 p-4 border-t border-olive bg-olive-card/50">
              <div className="flex items-center justify-between text-xs text-olive-muted">
                <span>
                  Updated{' '}
                  {new Date(card.generatedAt).toLocaleString('en-US', {
                    month: 'short',
                    day: 'numeric',
                    hour: 'numeric',
                    minute: '2-digit',
                  })}
                </span>
                <a
                  href={`/insight/${card.id}`}
                  className="text-olive-tertiary hover:text-olive-primary transition-colors"
                >
                  Open as full page →
                </a>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
};

export default CardDetailModal;
