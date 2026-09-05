import React from 'react';
import { motion } from 'framer-motion';
import {
  DollarSign,
  Briefcase,
  Scale,
  ShieldAlert,
  Fuel,
  Brain,
  Globe,
  Landmark,
  Eye,
  AlertCircle,
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '../core/Card';
import { useStore } from '../../store';
import { Domain, DOMAIN_META } from '../../types';

const DOMAIN_ICONS: Record<string, React.ComponentType<any>> = {
  DollarSign,
  Briefcase,
  Scale,
  ShieldAlert,
  Fuel,
  Brain,
  Globe,
  Landmark,
  Eye,
};

function getScoreColor(score: number): string {
  if (score < 0.3) return '#10B981';
  if (score < 0.6) return '#F59E0B';
  return '#EF4444';
}

export const DomainBreakdown: React.FC = () => {
  const { hopiScore, indicators } = useStore();

  if (!hopiScore) return null;

  const domains = Object.entries(hopiScore.domains) as [Domain, typeof hopiScore.domains[Domain]][];

  // Sort by score descending (worst first)
  const sorted = [...domains].sort((a, b) => b[1].score - a[1].score);

  return (
    <Card className="mb-8">
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <ShieldAlert className="w-5 h-5 text-white/30" />
            <span>Domain Threat Breakdown</span>
          </div>
          <div className="flex items-center gap-2 text-sm text-white/30">
            <span>HOPI:</span>
            <span
              className="font-mono font-bold"
              style={{ color: getScoreColor(hopiScore.score) }}
            >
              {(hopiScore.score * 100).toFixed(0)}
            </span>
          </div>
        </CardTitle>
      </CardHeader>

      <CardContent>
        <div className="space-y-3">
          {sorted.map(([domainKey, domainData], index) => {
            const meta = DOMAIN_META[domainKey];
            if (!meta) return null;

            const Icon = DOMAIN_ICONS[meta.icon] || AlertCircle;
            const color = getScoreColor(domainData.score);
            const domainIndicators = indicators.filter(
              (i) => i.domain === domainKey
            );
            const redCount = domainIndicators.filter(
              (i) => i.status.level === 'red'
            ).length;
            const amberCount = domainIndicators.filter(
              (i) => i.status.level === 'amber'
            ).length;

            return (
              <motion.div
                key={domainKey}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.05 }}
                className="flex items-center gap-4 p-3 rounded-lg hover:bg-white/5 transition-colors"
              >
                {/* Icon */}
                <div
                  className="w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0"
                  style={{ backgroundColor: `${color}15` }}
                >
                  <Icon className="w-4 h-4" style={{ color }} />
                </div>

                {/* Label + bar */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between mb-1">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-white/60 truncate">
                        {meta.label}
                      </span>
                      {meta.weight > 1 && (
                        <span className="text-2xs text-white/20">
                          {meta.weight}x
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-2">
                      {redCount > 0 && (
                        <span className="text-xs text-red-400 font-medium">
                          {redCount} RED
                        </span>
                      )}
                      {amberCount > 0 && (
                        <span className="text-xs text-amber-400 font-medium">
                          {amberCount} AMB
                        </span>
                      )}
                      <span
                        className="text-sm font-mono font-bold"
                        style={{ color }}
                      >
                        {(domainData.score * 100).toFixed(0)}
                      </span>
                    </div>
                  </div>

                  {/* Progress bar */}
                  <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
                    <motion.div
                      className="h-full rounded-full"
                      style={{ backgroundColor: color }}
                      initial={{ width: 0 }}
                      animate={{
                        width: `${Math.min(domainData.score * 100, 100)}%`,
                      }}
                      transition={{ duration: 0.8, delay: index * 0.05 }}
                    />
                  </div>
                </div>
              </motion.div>
            );
          })}
        </div>

        {/* Legend */}
        <div className="mt-6 pt-4 border-t border-white/[0.04] flex flex-wrap items-center gap-4 text-xs text-white/20">
          <div className="flex items-center gap-1">
            <div className="w-2 h-2 rounded-full bg-green-500" />
            <span>0–29 Normal</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-2 h-2 rounded-full bg-amber-500" />
            <span>30–59 Elevated</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-2 h-2 rounded-full bg-red-500" />
            <span>60+ Critical</span>
          </div>
          <span className="text-white/15">|</span>
          <span>Weighted: Global Conflict 1.5x, Security & Domestic 1.25x, Cult 0.75x</span>
        </div>
      </CardContent>
    </Card>
  );
};
