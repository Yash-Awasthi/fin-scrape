import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Shield, Activity, Database, Wifi } from 'lucide-react';
import { CanaryLogo } from '../branding/CanaryLogo';

interface DashboardLoaderProps {
  message?: string;
}

export const DashboardLoader: React.FC<DashboardLoaderProps> = ({
  message = 'Loading threat data...'
}) => {
  const [progress, setProgress] = useState(0);
  const [currentStep, setCurrentStep] = useState(0);

  const steps = [
    { icon: Database, label: 'Connecting to data sources' },
    { icon: Activity, label: 'Fetching indicator status' },
    { icon: Shield, label: 'Calculating threat levels' },
    { icon: Wifi, label: 'Syncing real-time feeds' },
  ];

  useEffect(() => {
    // Simulate progress
    const progressInterval = setInterval(() => {
      setProgress(prev => {
        if (prev >= 95) return prev; // Cap at 95% until actual load
        return prev + Math.random() * 15;
      });
    }, 200);

    const stepInterval = setInterval(() => {
      setCurrentStep(prev => (prev + 1) % steps.length);
    }, 800);

    return () => {
      clearInterval(progressInterval);
      clearInterval(stepInterval);
    };
  }, []);

  const CurrentIcon = steps[currentStep].icon;

  return (
    <div className="min-h-screen bg-[#0A0A0A] flex items-center justify-center p-6">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="w-full max-w-md"
      >
        {/* Logo */}
        <div className="flex justify-center mb-8">
          <CanaryLogo size="lg" showText={true} />
        </div>

        {/* Loading Card */}
        <div className="bg-[#111111] rounded-2xl border border-[#1A1A1A] p-8">
          {/* Animated Icon */}
          <div className="flex justify-center mb-6">
            <motion.div
              key={currentStep}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="w-16 h-16 rounded-2xl bg-[#1A1A1A] flex items-center justify-center"
            >
              <CurrentIcon className="w-8 h-8 text-indigo-400" />
            </motion.div>
          </div>

          {/* Current Step Label */}
          <motion.p
            key={`label-${currentStep}`}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-center text-gray-300 text-sm mb-6"
          >
            {steps[currentStep].label}
          </motion.p>

          {/* Progress Bar */}
          <div className="relative h-2 bg-[#1A1A1A] rounded-full overflow-hidden mb-4">
            <motion.div
              className="absolute left-0 top-0 h-full bg-gradient-to-r from-indigo-500 to-indigo-400 rounded-full"
              initial={{ width: 0 }}
              animate={{ width: `${Math.min(progress, 95)}%` }}
              transition={{ duration: 0.3 }}
            />
            {/* Shimmer effect */}
            <motion.div
              className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent"
              animate={{ x: ['-100%', '100%'] }}
              transition={{ duration: 1.5, repeat: Infinity, ease: 'linear' }}
            />
          </div>

          {/* Message */}
          <p className="text-center text-gray-500 text-xs">
            {message}
          </p>

          {/* Step Indicators */}
          <div className="flex justify-center gap-2 mt-6">
            {steps.map((_, i) => (
              <motion.div
                key={i}
                className={`w-2 h-2 rounded-full ${
                  i === currentStep ? 'bg-indigo-400' : 'bg-[#2A2A2A]'
                }`}
                animate={i === currentStep ? { scale: [1, 1.2, 1] } : {}}
                transition={{ duration: 0.5 }}
              />
            ))}
          </div>
        </div>

        {/* Warning text */}
        <p className="text-center text-gray-600 text-xs mt-6">
          Do not refresh — connecting to live data sources
        </p>
      </motion.div>
    </div>
  );
};
