import React from 'react';
import { motion } from 'framer-motion';
import { Zap, Users, Shield } from 'lucide-react';
import { useStore } from '../../store';
import { GlassCard } from '../ui/GlassCard';
import { cn } from '../../utils/cn';

interface PriorityCard {
  id: string;
  icon: React.ComponentType<any>;
  title: string;
  items: string[];
  accent: string;
}

export const WeeklyPriorities: React.FC = () => {
  const { indicators, currentPhase } = useStore();
  const redCount = indicators.filter(i => i.status.level === 'red').length;
  const amberCount = indicators.filter(i => i.status.level === 'amber').length;
  const phaseNum = currentPhase?.number ?? 0;

  const getPriorities = (): PriorityCard[] => {
    // Power priority — always relevant
    const powerItems = redCount >= 2
      ? ['Test generator or battery backup', 'Charge all devices to 100%', 'Fill gas cans safely']
      : amberCount > 0
        ? ['Charge power banks and backup batteries', 'Check flashlight batteries']
        : ['Keep backup battery at 60%+ charge', 'Test NOAA radio monthly'];

    // Family plan priority
    const familyItems = redCount >= 2
      ? ['Brief family on current threat level', 'Confirm rally points', 'Pack go-bags']
      : amberCount > 0
        ? ['Review emergency contact card', 'Practice family comms plan']
        : ['Update emergency contacts if needed', 'Review meeting location'];

    // Neighbors / community priority
    const neighborItems = phaseNum >= 3 || redCount >= 2
      ? ['Check in with 3 neighbors today', 'Share resource inventory', 'Agree on mutual aid roles']
      : phaseNum >= 2 || amberCount >= 2
        ? ['Exchange numbers with 2 neighbors', 'Identify nearby medical skills']
        : ['Introduce yourself to a new neighbor', 'Note who lives nearby'];

    return [
      {
        id: 'power',
        icon: Zap,
        title: 'Power',
        items: powerItems,
        accent: redCount >= 2 ? 'amber' : 'slate',
      },
      {
        id: 'family',
        icon: Shield,
        title: 'Family Plan',
        items: familyItems,
        accent: redCount >= 2 ? 'red' : amberCount > 0 ? 'amber' : 'slate',
      },
      {
        id: 'neighbors',
        icon: Users,
        title: 'Neighbors',
        items: neighborItems,
        accent: 'slate',
      },
    ];
  };

  const priorities = getPriorities();

  const accentColors: Record<string, { icon: string; dot: string }> = {
    red: { icon: 'text-red-400', dot: 'bg-red-400' },
    amber: { icon: 'text-amber-400', dot: 'bg-amber-400' },
    slate: { icon: 'text-white/40', dot: 'bg-white/20' },
  };

  return (
    <div>
      <h2 className="text-xs font-medium text-white/30 uppercase tracking-wider mb-3">This Week's Priorities</h2>
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        {priorities.map((priority, idx) => {
          const colors = accentColors[priority.accent];
          const Icon = priority.icon;

          return (
            <motion.div
              key={priority.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.15 + idx * 0.05 }}
            >
              <GlassCard padding="sm" className="h-full">
                <div className="flex items-center gap-2.5 mb-3">
                  <Icon className={cn('w-4 h-4', colors.icon)} />
                  <h3 className="text-sm font-display font-semibold text-white">{priority.title}</h3>
                </div>
                <ul className="space-y-2">
                  {priority.items.map((item, i) => (
                    <li key={i} className="flex items-start gap-2">
                      <span className={cn('w-1.5 h-1.5 rounded-full mt-1.5 flex-shrink-0', colors.dot)} />
                      <span className="text-xs text-white/50 leading-relaxed">{item}</span>
                    </li>
                  ))}
                </ul>
              </GlassCard>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
};
