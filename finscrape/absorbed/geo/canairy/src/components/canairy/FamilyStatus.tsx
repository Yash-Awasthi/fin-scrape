import React from 'react';
import { motion } from 'framer-motion';
import { Shield, TrendingUp, Users, Heart } from 'lucide-react';
import { CanairyMascot } from './CanairyMascot';
import { cn } from '../../utils/cn';

interface FamilyStatusProps {
  status: 'allGood' | 'attention' | 'action';
  message: {
    title: string;
    message: string;
    icon: string;
  };
  hopiScore: any;
  phase: any;
}

export const FamilyStatus: React.FC<FamilyStatusProps> = ({
  status,
  message,
  hopiScore,
  phase,
}) => {
  const getStatusColor = () => {
    switch (status) {
      case 'allGood':
        return 'from-canairy-green/20 to-canairy-green/10 border-canairy-green/30';
      case 'attention':
        return 'from-canairy-amber/20 to-canairy-amber/10 border-canairy-amber/30';
      case 'action':
        return 'from-canairy-red/20 to-canairy-red/10 border-canairy-red/30';
    }
  };

  const getMascotMood = () => {
    switch (status) {
      case 'allGood':
        return 'happy';
      case 'attention':
        return 'thinking';
      case 'action':
        return 'alert';
      default:
        return 'happy';
    }
  };

  return (
    <motion.div
      className={cn(
        "card-canairy bg-gradient-to-br border-2",
        getStatusColor()
      )}
      whileHover={{ scale: 1.02 }}
      transition={{ type: "spring", stiffness: 300 }}
    >
      <div className="flex items-start gap-6">
        {/* Mascot */}
        <motion.div
          animate={{ 
            y: status === 'action' ? [0, -10, 0] : 0,
          }}
          transition={{ 
            duration: 2, 
            repeat: status === 'action' ? Infinity : 0,
            ease: "easeInOut"
          }}
        >
          <CanairyMascot size="lg" mood={getMascotMood() as any} />
        </motion.div>

        {/* Status Content */}
        <div className="flex-1">
          <h2 className="text-2xl font-bold text-canairy-charcoal mb-2">
            {message.title}
          </h2>
          <p className="text-canairy-charcoal-light text-lg mb-6">
            {message.message}
          </p>

          {/* Metrics */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {/* Preparedness Score */}
            <div className="bg-white/50 rounded-xl p-4">
              <div className="flex items-center gap-2 mb-1">
                <Shield className="w-4 h-4 text-canairy-teal" />
                <span className="text-sm text-canairy-charcoal-light">Preparedness</span>
              </div>
              <div className="text-2xl font-bold text-canairy-charcoal">
                {hopiScore ? `${Math.round((1 - hopiScore.score) * 100)}%` : '--'}
              </div>
            </div>

            {/* Current Phase */}
            <div className="bg-white/50 rounded-xl p-4">
              <div className="flex items-center gap-2 mb-1">
                <TrendingUp className="w-4 h-4 text-canairy-yellow-dark" />
                <span className="text-sm text-canairy-charcoal-light">Phase</span>
              </div>
              <div className="text-2xl font-bold text-canairy-charcoal">
                {phase ? phase.number : '0'}
              </div>
            </div>

            {/* Family Members */}
            <div className="bg-white/50 rounded-xl p-4">
              <div className="flex items-center gap-2 mb-1">
                <Users className="w-4 h-4 text-canairy-green" />
                <span className="text-sm text-canairy-charcoal-light">Protected</span>
              </div>
              <div className="text-2xl font-bold text-canairy-charcoal">
                4
              </div>
            </div>

            {/* Confidence */}
            <div className="bg-white/50 rounded-xl p-4">
              <div className="flex items-center gap-2 mb-1">
                <Heart className="w-4 h-4 text-canairy-red" />
                <span className="text-sm text-canairy-charcoal-light">Confidence</span>
              </div>
              <div className="text-2xl font-bold text-canairy-charcoal">
                {hopiScore ? `${Math.round(hopiScore.confidence)}%` : '--'}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Decorative feathers */}
      <div className="absolute -bottom-2 -right-2 opacity-20">
        <svg width="60" height="60" viewBox="0 0 60 60">
          <path
            d="M30,10 Q20,20 25,40 Q30,30 35,40 Q40,20 30,10"
            fill="#FFE066"
            stroke="#F9C74F"
          />
        </svg>
      </div>
    </motion.div>
  );
};