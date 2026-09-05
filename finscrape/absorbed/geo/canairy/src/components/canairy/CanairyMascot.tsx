import React from 'react';
import { motion } from 'framer-motion';
import { cn } from '../../utils/cn';

interface CanairyMascotProps {
  size?: 'sm' | 'md' | 'lg' | 'xl';
  mood?: 'happy' | 'alert' | 'thinking' | 'sleeping' | 'celebrating';
  animated?: boolean;
  className?: string;
}

export const CanairyMascot: React.FC<CanairyMascotProps> = ({
  size = 'md',
  mood = 'happy',
  animated = true,
  className,
}) => {
  const sizeMap = {
    sm: 40,
    md: 60,
    lg: 80,
    xl: 120,
  };

  const dimensions = sizeMap[size];

  const moodVariants = {
    happy: {
      eyes: 'M15,20 Q17,18 19,20 M31,20 Q33,18 35,20',
      beak: 'M25,28 Q23,30 25,32 Q27,30 25,28',
      eyesOpen: true,
    },
    alert: {
      eyes: 'M15,19 L19,19 M31,19 L35,19',
      beak: 'M25,28 Q24,29 25,30 Q26,29 25,28',
      eyesOpen: true,
    },
    thinking: {
      eyes: 'M15,20 Q17,19 19,20 M33,18 Q33,20 33,22',
      beak: 'M25,28 Q26,29 27,28',
      eyesOpen: true,
    },
    sleeping: {
      eyes: 'M15,20 Q17,20 19,20 M31,20 Q33,20 35,20',
      beak: 'M25,29 Q25,30 25,31',
      eyesOpen: false,
    },
    celebrating: {
      eyes: 'M15,18 Q17,16 19,18 M31,18 Q33,16 35,18',
      beak: 'M25,28 Q22,31 28,31 Q28,28 25,28',
      eyesOpen: true,
    },
  };

  const currentMood = moodVariants[mood];

  const animationVariants = {
    flutter: {
      rotate: [-5, 5, -5],
      y: [0, -5, 0],
      transition: {
        duration: 3,
        repeat: Infinity,
        ease: 'easeInOut' as const,
      },
    },
    hop: {
      y: [0, -10, 0],
      scaleY: [1, 0.9, 1],
      transition: {
        duration: 1,
        repeat: Infinity,
        repeatDelay: 2,
      },
    },
  };

  return (
    <motion.svg
      width={dimensions}
      height={dimensions}
      viewBox="0 0 50 50"
      className={cn('canairy-mascot', className)}
      animate={animated ? (mood === 'happy' ? 'flutter' : 'hop') : undefined}
      variants={animationVariants}
    >
      {/* Shadow */}
      <ellipse
        cx="25"
        cy="45"
        rx="12"
        ry="3"
        fill="#222831"
        opacity="0.1"
      />

      {/* Body */}
      <motion.ellipse
        cx="25"
        cy="30"
        rx="15"
        ry="18"
        fill="#FFE066"
        stroke="#F9C74F"
        strokeWidth="1"
        whileHover={{ scale: 1.05 }}
      />

      {/* Belly */}
      <ellipse
        cx="25"
        cy="33"
        rx="10"
        ry="12"
        fill="#FFF3C4"
        opacity="0.8"
      />

      {/* Wings */}
      <motion.path
        d="M10,25 Q5,28 8,35 Q12,32 15,28"
        fill="#F9C74F"
        stroke="#FFE066"
        strokeWidth="1"
        animate={animated ? { rotate: [-5, -10, -5] } : undefined}
        transition={{ duration: 2, repeat: Infinity }}
      />
      <motion.path
        d="M40,25 Q45,28 42,35 Q38,32 35,28"
        fill="#F9C74F"
        stroke="#FFE066"
        strokeWidth="1"
        animate={animated ? { rotate: [5, 10, 5] } : undefined}
        transition={{ duration: 2, repeat: Infinity }}
      />

      {/* Head */}
      <circle
        cx="25"
        cy="18"
        r="10"
        fill="#FFE066"
        stroke="#F9C74F"
        strokeWidth="1"
      />

      {/* Crest */}
      <path
        d="M25,8 Q23,5 25,7 Q27,5 25,8"
        fill="#FF6B6B"
        stroke="#FF6B6B"
        strokeWidth="1"
      />
      <path
        d="M22,9 Q20,6 22,8 Q24,6 22,9"
        fill="#FF6B6B"
        stroke="#FF6B6B"
        strokeWidth="0.5"
      />
      <path
        d="M28,9 Q26,6 28,8 Q30,6 28,9"
        fill="#FF6B6B"
        stroke="#FF6B6B"
        strokeWidth="0.5"
      />

      {/* Eyes */}
      {currentMood.eyesOpen ? (
        <>
          <circle cx="17" cy="18" r="2" fill="#222831" />
          <circle cx="33" cy="18" r="2" fill="#222831" />
          <circle cx="17.5" cy="17.5" r="0.5" fill="white" />
          <circle cx="33.5" cy="17.5" r="0.5" fill="white" />
        </>
      ) : (
        <path
          d={currentMood.eyes}
          stroke="#222831"
          strokeWidth="2"
          strokeLinecap="round"
          fill="none"
        />
      )}

      {/* Beak */}
      <path
        d={currentMood.beak}
        fill="#FF6B6B"
        stroke="#F9C74F"
        strokeWidth="0.5"
      />

      {/* Feet */}
      <path
        d="M20,42 L20,46 M20,46 L18,48 M20,46 L22,48"
        stroke="#FF6B6B"
        strokeWidth="1.5"
        strokeLinecap="round"
        fill="none"
      />
      <path
        d="M30,42 L30,46 M30,46 L28,48 M30,46 L32,48"
        stroke="#FF6B6B"
        strokeWidth="1.5"
        strokeLinecap="round"
        fill="none"
      />

      {/* Mood-specific extras */}
      {mood === 'alert' && (
        <motion.path
          d="M38,10 L40,8 M40,12 L42,10 M38,14 L40,16"
          stroke="#FFD166"
          strokeWidth="2"
          strokeLinecap="round"
          fill="none"
          animate={{ opacity: [0.5, 1, 0.5] }}
          transition={{ duration: 1, repeat: Infinity }}
        />
      )}

      {mood === 'celebrating' && (
        <>
          <circle cx="10" cy="10" r="1" fill="#5EC6C7" />
          <circle cx="40" cy="8" r="1" fill="#6BCB77" />
          <circle cx="12" cy="40" r="1" fill="#FF6B6B" />
          <circle cx="38" cy="42" r="1" fill="#FFD166" />
        </>
      )}
    </motion.svg>
  );
};

// Preset mascot states for common uses
export const CanairyHappy = (props: Omit<CanairyMascotProps, 'mood'>) => (
  <CanairyMascot mood="happy" {...props} />
);

export const CanairyAlert = (props: Omit<CanairyMascotProps, 'mood'>) => (
  <CanairyMascot mood="alert" {...props} />
);

export const CanairyThinking = (props: Omit<CanairyMascotProps, 'mood'>) => (
  <CanairyMascot mood="thinking" {...props} />
);

export const CanairySleeping = (props: Omit<CanairyMascotProps, 'mood'>) => (
  <CanairyMascot mood="sleeping" {...props} />
);

export const CanairyCelebrating = (props: Omit<CanairyMascotProps, 'mood'>) => (
  <CanairyMascot mood="celebrating" {...props} />
);