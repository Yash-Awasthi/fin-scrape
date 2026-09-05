import React from 'react';
import { motion } from 'framer-motion';
import {
  Shield,
  AlertCircle,
  CheckCircle,
  AlertTriangle,
  ArrowRight,
  Activity
} from 'lucide-react';
import { cn } from '../../utils/cn';
import { useStore } from '../../store';
import { Badge } from '../core/Badge';
import { useNavigate } from 'react-router-dom';

type ThreatStatus = 'ok' | 'watch' | 'act';

export const HeroStatusCard: React.FC = () => {
  const { indicators, hopiScore, currentPhase } = useStore();
  const navigate = useNavigate();

  // Determine overall threat status
  const getThreatStatus = (): { status: ThreatStatus; label: string; message: string } => {
    const redCount = indicators.filter(i => i.status.level === 'red').length;
    const criticalReds = indicators.filter(i => i.status.level === 'red' && i.critical).length;
    const amberCount = indicators.filter(i => i.status.level === 'amber').length;

    if (criticalReds > 0 || redCount >= 2) {
      return {
        status: 'act',
        label: 'ACTION REQUIRED',
        message: criticalReds > 0
          ? 'Critical indicators triggered — take protective action now'
          : 'Multiple red alerts — review your preparedness checklist'
      };
    }

    if (redCount > 0 || amberCount >= 3) {
      return {
        status: 'watch',
        label: 'STAY ALERT',
        message: 'Elevated risk detected — monitor closely this week'
      };
    }

    return {
      status: 'ok',
      label: 'ALL CLEAR',
      message: 'No significant threats — maintain normal preparedness'
    };
  };

  // Get top priority action
  const getTopAction = () => {
    const redIndicators = indicators.filter(i => i.status.level === 'red');
    const criticalReds = redIndicators.filter(i => i.critical);

    if (criticalReds.some(i => i.id === 'econ_01_treasury_tail' || i.id === 'market_01_intraday_swing')) {
      return { text: 'Check bank accounts & withdraw 2 weeks cash', cta: 'View Playbook', path: '/playbook' };
    }

    if (redIndicators.some(i => i.id === 'taiwan_pla_activity')) {
      return { text: 'Stock up on electronics & medications today', cta: 'View Checklist', path: '/checklist' };
    }

    if (redIndicators.some(i => i.domain === 'oil_axis')) {
      return { text: 'Fill gas tanks & review cash reserves', cta: 'View Playbook', path: '/playbook' };
    }

    if (redIndicators.length >= 2) {
      return { text: 'Complete 48-hour tighten-up protocol', cta: 'Start Protocol', path: '/playbook' };
    }

    if (redIndicators.length > 0) {
      return { text: `Monitor ${redIndicators[0].name} closely`, cta: 'View Details', path: `/indicator/${redIndicators[0].id}` };
    }

    return null;
  };

  const { status, label, message } = getThreatStatus();
  const topAction = getTopAction();

  const getStatusConfig = () => {
    switch (status) {
      case 'act':
        return {
          bgGradient: 'from-red-500/20 to-red-500/5',
          borderColor: 'border-red-500/40',
          iconBg: 'bg-red-500/20',
          iconColor: 'text-red-400',
          labelColor: 'text-red-400',
          Icon: AlertCircle,
          pulse: true
        };
      case 'watch':
        return {
          bgGradient: 'from-amber-500/20 to-amber-500/5',
          borderColor: 'border-amber-500/40',
          iconBg: 'bg-amber-500/20',
          iconColor: 'text-amber-400',
          labelColor: 'text-amber-400',
          Icon: AlertTriangle,
          pulse: false
        };
      case 'ok':
        return {
          bgGradient: 'from-green-500/20 to-green-500/5',
          borderColor: 'border-green-500/40',
          iconBg: 'bg-green-500/20',
          iconColor: 'text-green-400',
          labelColor: 'text-green-400',
          Icon: CheckCircle,
          pulse: false
        };
    }
  };

  const config = getStatusConfig();
  const { Icon } = config;

  // HOPI score color
  const getHopiColor = () => {
    const score = hopiScore?.score || 0;
    if (score >= 7) return 'text-red-400';
    if (score >= 4) return 'text-amber-400';
    return 'text-green-400';
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      className="mb-8"
    >
      <div className={cn(
        'rounded-2xl border-2 p-6 bg-gradient-to-br',
        config.bgGradient,
        config.borderColor
      )}>
        <div className="flex flex-col lg:flex-row lg:items-center gap-6">
          {/* Left: Status Icon + Message */}
          <div className="flex items-start gap-4 flex-1">
            <motion.div
              className={cn(
                'w-16 h-16 rounded-2xl flex items-center justify-center flex-shrink-0',
                config.iconBg
              )}
              animate={config.pulse ? { scale: [1, 1.05, 1] } : {}}
              transition={{ duration: 2, repeat: Infinity }}
            >
              <Icon className={cn('w-8 h-8', config.iconColor)} />
            </motion.div>

            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-3 mb-1">
                <span className={cn('text-sm font-bold tracking-wider', config.labelColor)}>
                  {label}
                </span>
                <Badge
                  variant={status === 'act' ? 'red' : status === 'watch' ? 'amber' : 'green'}
                  size="sm"
                >
                  Phase {currentPhase?.number || 0}
                </Badge>
              </div>
              <h2 className="text-xl sm:text-2xl font-semibold text-white mb-1 leading-tight">
                {message}
              </h2>
            </div>
          </div>

          {/* Center: HOPI Score */}
          <div className="flex items-center gap-6 px-6 py-4 bg-[#0A0A0A] rounded-xl lg:flex-shrink-0">
            <div className="text-center">
              <div className="flex items-center gap-1 mb-1">
                <Activity className="w-4 h-4 text-gray-400" />
                <span className="text-xs text-gray-400 uppercase tracking-wider">HOPI Score</span>
              </div>
              <div className={cn('text-4xl font-bold font-mono', getHopiColor())}>
                {hopiScore?.score?.toFixed(1) || '—'}
              </div>
              <div className="text-xs text-gray-500">out of 10</div>
            </div>

            <div className="w-px h-16 bg-[#2A2A2A]" />

            <div className="text-center">
              <div className="flex items-center gap-1 mb-1">
                <Shield className="w-4 h-4 text-gray-400" />
                <span className="text-xs text-gray-400 uppercase tracking-wider">Status</span>
              </div>
              <div className="flex items-center gap-1.5 justify-center">
                {indicators.filter(i => i.status.level === 'red').length > 0 && (
                  <span className="flex items-center gap-1">
                    <span className="w-2.5 h-2.5 bg-red-500 rounded-full" />
                    <span className="text-red-400 font-medium">{indicators.filter(i => i.status.level === 'red').length}</span>
                  </span>
                )}
                {indicators.filter(i => i.status.level === 'amber').length > 0 && (
                  <span className="flex items-center gap-1">
                    <span className="w-2.5 h-2.5 bg-amber-500 rounded-full" />
                    <span className="text-amber-400 font-medium">{indicators.filter(i => i.status.level === 'amber').length}</span>
                  </span>
                )}
                <span className="flex items-center gap-1">
                  <span className="w-2.5 h-2.5 bg-green-500 rounded-full" />
                  <span className="text-green-400 font-medium">{indicators.filter(i => i.status.level === 'green').length}</span>
                </span>
              </div>
              <div className="text-xs text-gray-500 mt-1">
                {indicators.length} indicators
              </div>
            </div>
          </div>

          {/* Right: Top Action CTA */}
          {topAction && status !== 'ok' && (
            <div className="lg:flex-shrink-0">
              <button
                onClick={() => navigate(topAction.path)}
                className={cn(
                  'w-full lg:w-auto px-5 py-4 rounded-xl font-medium transition-all',
                  'flex items-center justify-between lg:justify-center gap-3',
                  status === 'act'
                    ? 'bg-red-500 hover:bg-red-600 text-white'
                    : 'bg-amber-500 hover:bg-amber-600 text-black'
                )}
              >
                <span className="text-left lg:text-center">
                  <span className="block text-xs opacity-75 mb-0.5">Top Priority</span>
                  <span className="block text-sm font-semibold">{topAction.text}</span>
                </span>
                <ArrowRight className="w-5 h-5 flex-shrink-0" />
              </button>
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
};
