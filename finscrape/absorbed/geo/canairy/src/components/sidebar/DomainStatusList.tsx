import React from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import {
  DollarSign,
  Briefcase,
  Scale,
  Shield,
  Droplet,
  Cpu,
  Globe,
  Users,
  Truck,
  Zap,
  ChevronRight,
  Waves,
  Radio,
  Home,
  Plane,
  PlaneTakeoff,
  TrendingUp,
} from 'lucide-react';
import { useStore } from '../../store';
import { Domain, DOMAIN_META } from '../../types';
import { cn } from '../../utils/cn';
import { Tooltip } from '../ui/Tooltip';

// Domain descriptions for tooltips
const DOMAIN_DESCRIPTIONS: Record<Domain, string> = {
  economy: 'Treasury markets, inflation, and overall economic stability',
  jobs_labor: 'Employment trends, layoffs, and labor market health',
  rights_governance: 'Civil liberties, rule of law, and democratic institutions',
  security_infrastructure: 'Critical infrastructure protection and cybersecurity',
  oil_axis: 'Oil markets, OPEC dynamics, and energy geopolitics',
  ai_window: 'AI development pace and regulatory landscape',
  global_conflict: 'International tensions, military activity, and war risk',
  domestic_control: 'Immigration enforcement, surveillance, and civil unrest',
  supply_chain: 'Shipping, logistics, and supply disruptions',
  energy: 'Power grid stability and energy supply',
  social_cohesion: 'Social trust, political polarization, and community bonds',
  water_infrastructure: 'Water supply and infrastructure reliability',
  telecommunications: 'Communications networks and internet access',
  housing_mortgage: 'Housing market and mortgage conditions',
  travel_mobility: 'Travel restrictions and freedom of movement',
  aviation: 'Air travel availability and disruptions',
  cult_meta: 'Cultural trends and social sentiment indicators',
};

const DOMAIN_ICONS: Record<Domain, React.ComponentType<{ className?: string }>> = {
  economy: DollarSign,
  jobs_labor: Briefcase,
  rights_governance: Scale,
  security_infrastructure: Shield,
  oil_axis: Droplet,
  ai_window: Cpu,
  global_conflict: Globe,
  domestic_control: Users,
  supply_chain: Truck,
  energy: Zap,
  social_cohesion: Users,
  water_infrastructure: Waves,
  telecommunications: Radio,
  housing_mortgage: Home,
  travel_mobility: Plane,
  aviation: PlaneTakeoff,
  cult_meta: TrendingUp,
};

interface DomainStatus {
  domain: Domain;
  label: string;
  level: 'green' | 'amber' | 'red';
  indicatorCount: number;
  redCount: number;
  amberCount: number;
}

export const DomainStatusList: React.FC = () => {
  const { indicators } = useStore();
  const navigate = useNavigate();

  // Calculate domain statuses
  const domainStatuses: DomainStatus[] = Object.entries(DOMAIN_META).map(([domain, meta]) => {
    const domainIndicators = indicators.filter(i => i.domain === domain);
    const redCount = domainIndicators.filter(i => i.status.level === 'red').length;
    const amberCount = domainIndicators.filter(i => i.status.level === 'amber').length;

    let level: 'green' | 'amber' | 'red' = 'green';
    if (redCount > 0) level = 'red';
    else if (amberCount > 0) level = 'amber';

    return {
      domain: domain as Domain,
      label: meta.label,
      level,
      indicatorCount: domainIndicators.length,
      redCount,
      amberCount,
    };
  });

  // Sort: red first, then amber, then green
  domainStatuses.sort((a, b) => {
    const order = { red: 0, amber: 1, green: 2 };
    return order[a.level] - order[b.level];
  });

  const handleDomainClick = (domain: Domain) => {
    navigate(`/indicators?domain=${encodeURIComponent(domain)}`);
  };

  return (
    <div className="space-y-0.5">
      {domainStatuses.map((status, index) => {
        const Icon = DOMAIN_ICONS[status.domain];
        const description = DOMAIN_DESCRIPTIONS[status.domain];

        return (
          <Tooltip key={status.domain} content={description} side="left">
            <motion.button
              initial={{ opacity: 0, x: 10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.03 }}
              onClick={() => handleDomainClick(status.domain)}
              className={cn(
                'flex items-center justify-between w-full py-2.5 px-2 rounded-lg',
                'hover:bg-white/5 transition-colors cursor-pointer group'
              )}
            >
            <div className="flex items-center gap-2.5">
              <Icon className={cn(
                'w-4 h-4',
                status.level === 'red' && 'text-red-400',
                status.level === 'amber' && 'text-amber-400',
                status.level === 'green' && 'text-olive-tertiary'
              )} />
              <span className={cn(
                'text-sm group-hover:text-white transition-colors',
                status.level === 'red' && 'text-olive-primary',
                status.level === 'amber' && 'text-olive-primary',
                status.level === 'green' && 'text-olive-secondary'
              )}>
                {status.label}
              </span>
            </div>

            <div className="flex items-center gap-1.5">
              {/* Count badges */}
              {status.redCount > 0 && (
                <span className="text-xs font-mono text-red-400 bg-red-500/15 px-1.5 py-0.5 rounded">
                  {status.redCount}
                </span>
              )}
              {status.amberCount > 0 && (
                <span className="text-xs font-mono text-amber-400 bg-amber-500/15 px-1.5 py-0.5 rounded">
                  {status.amberCount}
                </span>
              )}

              {/* Green dot or nothing for green status */}
              {status.amberCount === 0 && status.redCount === 0 && (
                <div className="w-2 h-2 rounded-full bg-green-500/60" />
              )}

              {/* Chevron appears on hover */}
              <ChevronRight
                size={14}
                className="text-olive-muted opacity-0 group-hover:opacity-100 transition-opacity ml-1"
              />
            </div>
            </motion.button>
          </Tooltip>
        );
      })}
    </div>
  );
};
