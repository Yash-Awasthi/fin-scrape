import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  AlertCircle,
  TrendingUp,
  TrendingDown,
  Shield,
  Activity,
  Zap,
  ChevronRight,
  Timer,
  Database,
  Wifi
} from 'lucide-react';
import { cn } from '../../utils/cn';
import { useStore } from '../../store';

type ThreatLevel = 'normal' | 'elevated' | 'high' | 'critical';

export const SituationalStatusBar: React.FC = () => {
  const { indicators, hopiScore, currentPhase } = useStore();
  const [, setCurrentTime] = useState(new Date());

  // Update current time every minute
  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 60000);
    return () => clearInterval(timer);
  }, []);
  
  // Calculate threat level
  const getThreatLevel = (): ThreatLevel => {
    const redCount = indicators.filter(i => i.status.level === 'red').length;
    const criticalReds = indicators.filter(i => i.status.level === 'red' && i.critical).length;
    const amberCount = indicators.filter(i => i.status.level === 'amber').length;
    
    if (criticalReds > 0 || redCount >= 3) return 'critical';
    if (redCount >= 2) return 'high';
    if (redCount > 0 || amberCount >= 3) return 'elevated';
    return 'normal';
  };
  
  // Get time to act
  const getTimeToAct = (): string => {
    const criticalCount = indicators.filter(i => i.status.level === 'red' && i.critical).length;
    const redCount = indicators.filter(i => i.status.level === 'red').length;
    
    if (criticalCount > 0) return '24-48 hours';
    if (redCount >= 2) return '2-3 days';
    if (redCount > 0) return '1 week';
    return 'No urgency';
  };
  
  // Get data freshness
  const getDataFreshness = (): { text: string; quality: 'good' | 'stale' | 'poor' } => {
    if (!indicators.length) return { text: 'No data', quality: 'poor' };
    
    const latestUpdate = Math.max(...indicators.map(i => new Date(i.status.lastUpdate).getTime()));
    const minutesAgo = Math.floor((Date.now() - latestUpdate) / 60000);
    
    if (minutesAgo < 5) return { text: `${minutesAgo}m ago`, quality: 'good' };
    if (minutesAgo < 30) return { text: `${minutesAgo}m ago`, quality: 'stale' };
    return { text: '30+ min ago', quality: 'poor' };
  };
  
  // Calculate indicator counts
  const indicatorCounts = {
    red: indicators.filter(i => i.status.level === 'red').length,
    amber: indicators.filter(i => i.status.level === 'amber').length,
    green: indicators.filter(i => i.status.level === 'green').length,
  };
  
  const threatLevel = getThreatLevel();
  const timeToAct = getTimeToAct();
  const dataFreshness = getDataFreshness();
  
  const getThreatLevelConfig = (level: ThreatLevel) => {
    switch (level) {
      case 'critical':
        return {
          label: 'CRITICAL THREAT',
          color: 'text-red-400',
          bgColor: 'bg-red-500/10 border-red-500/30',
          icon: AlertCircle,
          pulse: true
        };
      case 'high':
        return {
          label: 'HIGH THREAT',
          color: 'text-red-400',
          bgColor: 'bg-red-500/10 border-red-500/30',
          icon: AlertCircle,
          pulse: false
        };
      case 'elevated':
        return {
          label: 'ELEVATED THREAT',
          color: 'text-amber-400',
          bgColor: 'bg-amber-500/10 border-amber-500/30',
          icon: Shield,
          pulse: false
        };
      case 'normal':
        return {
          label: 'NORMAL STATUS',
          color: 'text-green-400',
          bgColor: 'bg-green-500/10 border-green-500/30',
          icon: Shield,
          pulse: false
        };
    }
  };
  
  const threatConfig = getThreatLevelConfig(threatLevel);
  const ThreatIcon = threatConfig.icon;
  
  const getHOPITrend = () => {
    // Mock trend - in real app would compare to previous HOPI score
    const trend = Math.random() > 0.5 ? 'up' : 'down';
    return {
      trend,
      icon: trend === 'up' ? TrendingUp : TrendingDown,
      color: trend === 'up' ? 'text-red-400' : 'text-green-400' // Up is bad for HOPI
    };
  };
  
  const hopiTrend = getHOPITrend();
  const HOPITrendIcon = hopiTrend.icon;
  
  return (
    <div className="flex items-center justify-between w-full">
      {/* Left Side - Threat Status */}
      <div className="flex items-center gap-4">
        {/* Threat Level Badge */}
        <motion.div
          className={cn(
            "flex items-center gap-2 px-3 py-2 rounded-lg border text-sm font-medium",
            threatConfig.bgColor,
            threatConfig.color,
            threatConfig.pulse && "animate-pulse"
          )}
          animate={threatConfig.pulse ? { scale: [1, 1.05, 1] } : {}}
          transition={{ duration: 2, repeat: Infinity }}
        >
          <ThreatIcon className="w-4 h-4" />
          <span>{threatConfig.label}</span>
        </motion.div>
        
        {/* Phase Status */}
        <div className="flex items-center gap-2 text-sm">
          <Shield className="w-4 h-4 text-white/30" />
          <span className="text-white font-medium">
            Phase {currentPhase?.number || 0}
          </span>
          <span className="text-white/30">•</span>
          <span className="text-white/30">3 days</span>
          {threatLevel !== 'normal' && (
            <>
              <ChevronRight className="w-3 h-3 text-amber-400" />
              <span className="text-amber-400 text-xs">Phase {(currentPhase?.number || 0) + 1} risk</span>
            </>
          )}
        </div>
        
        {/* HOPI Score */}
        <div className="flex items-center gap-2 text-sm">
          <Activity className="w-4 h-4 text-white/30" />
          <span className="text-white font-mono">
            {hopiScore?.score?.toFixed(1) || 'N/A'}/10
          </span>
          <HOPITrendIcon className={cn("w-3 h-3", hopiTrend.color)} />
        </div>
        
        {/* Time to Act */}
        {timeToAct !== 'No urgency' && (
          <div className="flex items-center gap-2 text-sm">
            <Timer className={cn(
              "w-4 h-4",
              timeToAct.includes('24-48') ? "text-red-400" : 
              timeToAct.includes('2-3') ? "text-amber-400" : "text-blue-400"
            )} />
            <span className={cn(
              "font-medium",
              timeToAct.includes('24-48') ? "text-red-400" : 
              timeToAct.includes('2-3') ? "text-amber-400" : "text-blue-400"
            )}>
              Act in {timeToAct}
            </span>
          </div>
        )}
      </div>
      
      {/* Center - Stats */}
      <div className="flex items-center gap-6">
        {/* Indicator Counts */}
        <div className="flex items-center gap-3 text-sm">
          {indicatorCounts.red > 0 && (
            <div className="flex items-center gap-1">
              <div className="w-2 h-2 bg-red-500 rounded-full" />
              <span className="text-red-400 font-medium">{indicatorCounts.red} RED</span>
            </div>
          )}
          {indicatorCounts.amber > 0 && (
            <div className="flex items-center gap-1">
              <div className="w-2 h-2 bg-amber-500 rounded-full" />
              <span className="text-amber-400 font-medium">{indicatorCounts.amber} AMBER</span>
            </div>
          )}
          <div className="flex items-center gap-1">
            <div className="w-2 h-2 bg-green-500 rounded-full" />
            <span className="text-green-400 font-medium">{indicatorCounts.green} GREEN</span>
          </div>
        </div>
        
        {/* Data Quality */}
        <div className="flex items-center gap-2 text-sm">
          <div className={cn(
            "flex items-center gap-1",
            dataFreshness.quality === 'good' ? "text-green-400" :
            dataFreshness.quality === 'stale' ? "text-amber-400" : "text-red-400"
          )}>
            <Database className="w-4 h-4" />
            <span>Updated {dataFreshness.text}</span>
          </div>
        </div>
      </div>
      
      {/* Right Side - System Status */}
      <div className="flex items-center gap-2 text-sm">
        <div className="flex items-center gap-1 text-green-400">
          <Wifi className="w-4 h-4" />
          <span>Live Data</span>
        </div>
        {threatLevel !== 'normal' && (
          <motion.div
            className="flex items-center gap-1 px-2 py-1 bg-amber-500/10 border border-amber-500/30 rounded text-amber-400 text-xs"
            animate={{ opacity: [1, 0.7, 1] }}
            transition={{ duration: 2, repeat: Infinity }}
          >
            <Zap className="w-3 h-3" />
            <span>Enhanced Monitoring</span>
          </motion.div>
        )}
      </div>
    </div>
  );
};