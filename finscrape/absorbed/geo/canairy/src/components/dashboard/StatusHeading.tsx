import React from 'react';
import { motion } from 'framer-motion';
import { useStore, selectTightenUpActive } from '../../store';
import { cn } from '../../utils/cn';

type StatusLevel = 'all_clear' | 'caution' | 'act_now' | 'action_protocol';

interface StatusConfig {
  label: string;
  color: string;
  bgColor: string;
  glowColor: string;
}

const STATUS_CONFIG: Record<StatusLevel, StatusConfig> = {
  all_clear: {
    label: 'All Clear',
    color: 'text-green-400',
    bgColor: 'bg-green-500/10',
    glowColor: 'shadow-[0_0_30px_rgba(16,185,129,0.2)]',
  },
  caution: {
    label: 'Caution',
    color: 'text-amber-400',
    bgColor: 'bg-amber-500/10',
    glowColor: 'shadow-[0_0_30px_rgba(245,158,11,0.2)]',
  },
  act_now: {
    label: 'Phase 5',
    color: 'text-red-400',
    bgColor: 'bg-red-500/10',
    glowColor: 'shadow-[0_0_30px_rgba(239,68,68,0.2)]',
  },
  action_protocol: {
    label: 'Phase 7',
    color: 'text-red-300',
    bgColor: 'bg-red-500/15',
    glowColor: 'shadow-[0_0_40px_rgba(239,68,68,0.3)]',
  },
};

export const StatusHeading: React.FC = () => {
  const { indicators } = useStore();
  const actionProtocolActive = useStore(selectTightenUpActive);

  const redCount = indicators.filter(i => i.status.level === 'red').length;
  const amberCount = indicators.filter(i => i.status.level === 'amber').length;

  // Determine status level
  const getStatusLevel = (): StatusLevel => {
    if (actionProtocolActive) return 'action_protocol';
    if (redCount > 0) return 'act_now';
    if (amberCount >= 3) return 'caution';
    if (amberCount > 0) return 'caution';
    return 'all_clear';
  };

  const statusLevel = getStatusLevel();
  const config = STATUS_CONFIG[statusLevel];

  return (
    <motion.div
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      className="mb-2"
    >
      <h1
        className={cn(
          'font-display text-display-status tracking-tight',
          config.color
        )}
      >
        {config.label}
      </h1>
    </motion.div>
  );
};
