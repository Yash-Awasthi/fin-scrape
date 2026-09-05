import React from 'react';
import { motion } from 'framer-motion';
import { cn } from '../../utils/cn';
import { useStore } from '../../store';

interface CanaryLogoProps {
  size?: 'sm' | 'md' | 'lg';
  showText?: boolean;
  className?: string;
}

export const CanaryLogo: React.FC<CanaryLogoProps> = ({
  size = 'md',
  showText = true,
  className
}) => {
  const { indicators } = useStore();
  
  // Calculate threat level for color
  const getThreatLevel = () => {
    const redCount = indicators.filter(i => i.status.level === 'red').length;
    const criticalReds = indicators.filter(i => i.status.level === 'red' && i.critical).length;
    
    if (criticalReds > 0 || redCount >= 3) return 'critical';
    if (redCount >= 2) return 'high';
    if (redCount > 0) return 'elevated';
    return 'normal';
  };
  
  const threatLevel = getThreatLevel();
  
  // Get canary color based on threat level
  const getCanaryColor = () => {
    switch (threatLevel) {
      case 'critical':
        return '#EF4444'; // Red
      case 'high':
        return '#F59E0B'; // Amber
      case 'elevated':
        return '#F59E0B'; // Amber
      case 'normal':
        return '#10B981'; // Green (healthy canary)
    }
  };
  
  // Size configurations
  const sizeConfig = {
    sm: {
      container: 'w-8 h-8',
      svg: 'w-5 h-5',
      text: 'text-base',
      tagline: 'text-xs'
    },
    md: {
      container: 'w-10 h-10',
      svg: 'w-6 h-6',
      text: 'text-xl',
      tagline: 'text-sm'
    },
    lg: {
      container: 'w-12 h-12',
      svg: 'w-8 h-8',
      text: 'text-2xl',
      tagline: 'text-base'
    }
  };
  
  const config = sizeConfig[size];
  const canaryColor = getCanaryColor();
  const shouldPulse = threatLevel === 'critical';
  
  // Professional canary SVG - geometric, minimal design
  const CanarySVG = () => (
    <motion.svg
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={config.svg}
      animate={shouldPulse ? { 
        scale: [1, 1.1, 1],
        opacity: [1, 0.8, 1]
      } : {}}
      transition={{ duration: 2, repeat: Infinity }}
    >
      {/* Canary body - main shape */}
      <path
        d="M8 12c0-2.5 1.5-4.5 4-5.5 2.5-1 5.5 0 7 2.5 1 1.5 0.5 3.5-1 4.5-1 0.5-2 0.5-3 0-0.5-0.25-1-0.75-1.5-1.25"
        stroke={canaryColor}
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        fill="none"
      />
      
      {/* Wing detail */}
      <path
        d="M12 10c1 0 2-0.5 3-1"
        stroke={canaryColor}
        strokeWidth="1.5"
        strokeLinecap="round"
        fill="none"
        opacity="0.7"
      />
      
      {/* Beak */}
      <path
        d="M7 11l1 1"
        stroke={canaryColor}
        strokeWidth="2"
        strokeLinecap="round"
        fill="none"
      />
      
      {/* Eye */}
      <circle
        cx="9.5"
        cy="10"
        r="1"
        fill={canaryColor}
      />
      
      {/* Tail feathers */}
      <path
        d="M16 14c1.5 0.5 2.5 1.5 3 2.5"
        stroke={canaryColor}
        strokeWidth="1.5"
        strokeLinecap="round"
        fill="none"
        opacity="0.6"
      />
      
      {/* Feet/perch indication */}
      <path
        d="M10 16l0 2M12 16l0 2"
        stroke={canaryColor}
        strokeWidth="1.5"
        strokeLinecap="round"
        fill="none"
        opacity="0.8"
      />
    </motion.svg>
  );
  
  return (
    <div className={cn("flex items-center gap-3", className)}>
      {/* Logo container */}
      <motion.div
        className={cn(
          "rounded-xl flex items-center justify-center transition-colors",
          config.container,
          threatLevel === 'normal' ? "bg-white/[0.06] border border-white/10" :
          threatLevel === 'elevated' ? "bg-amber-500/10 border border-amber-500/30" :
          "bg-red-500/10 border border-red-500/30"
        )}
        whileHover={{ scale: 1.05 }}
        transition={{ duration: 0.2 }}
      >
        <CanarySVG />
      </motion.div>
      
      {/* Text */}
      {showText && (
        <div>
          <h1 className={cn(
            "font-display font-semibold text-white tracking-tight",
            config.text
          )}>
            Canairy
          </h1>
          <p className={cn(
            "font-body text-white/30 leading-tight",
            config.tagline
          )}>
            Resilience Monitoring
          </p>
        </div>
      )}
    </div>
  );
};