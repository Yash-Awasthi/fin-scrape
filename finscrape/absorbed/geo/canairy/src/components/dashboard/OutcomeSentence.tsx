import React, { useMemo } from 'react';
import { motion } from 'framer-motion';
import { useStore, selectTightenUpActive } from '../../store';
import { cn } from '../../utils/cn';
import { getOutcomePhrase, getAction } from '../../data/indicatorTranslations';

export const OutcomeSentence: React.FC = () => {
  const { indicators } = useStore();
  const isHighPhase = useStore(selectTightenUpActive);

  const redIndicators = indicators.filter(i => i.status.level === 'red');
  const amberIndicators = indicators.filter(i => i.status.level === 'amber');

  // Generate family-friendly outcome sentence using translation map
  // Must pass the "kitchen table test" - readable to your partner over coffee
  const outcomeSentence = useMemo(() => {
    // High phase active (2+ reds) - urgent but clear
    if (isHighPhase) {
      const phrases = redIndicators.slice(0, 2).map(i => getOutcomePhrase(i.id, 'red'));
      const experiencePart = phrases.join(' and ');
      return `Multiple signals suggest ${experiencePart}. Check your action plan now.`;
    }

    // Red indicators present - specific impacts
    if (redIndicators.length > 0) {
      const topRed = redIndicators[0];
      const phrase = getOutcomePhrase(topRed.id, 'red');
      const action = getAction(topRed.id, 'red');
      return `Expect ${phrase} this week. ${action}.`;
    }

    // Multiple amber indicators - combined impact
    if (amberIndicators.length >= 3) {
      const phrases = amberIndicators.slice(0, 2).map(i => getOutcomePhrase(i.id, 'amber'));
      const action = getAction(amberIndicators[0].id, 'amber');
      return `Expect ${phrases.join(' and ')} this week. ${action}.`;
    }

    // Some amber indicators - gentle nudge
    if (amberIndicators.length > 0) {
      const topAmber = amberIndicators[0];
      const phrase = getOutcomePhrase(topAmber.id, 'amber');
      const action = getAction(topAmber.id, 'amber');
      return `Conditions suggest ${phrase}. ${action}.`;
    }

    // All clear - reassuring, actionable
    return `No unusual signals this week. A good time to review your supplies and keep building readiness.`;
  }, [indicators, isHighPhase, redIndicators, amberIndicators]);

  return (
    <motion.p
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ delay: 0.1 }}
      className={cn(
        'text-body-outcome text-olive-secondary leading-relaxed',
        'max-w-2xl'
      )}
    >
      {outcomeSentence}
    </motion.p>
  );
};
