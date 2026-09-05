import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface LiveClockProps {
  className?: string;
}

export const LiveClock: React.FC<LiveClockProps> = ({ className = '' }) => {
  const [time, setTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => {
      setTime(new Date());
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  const hours = time.getHours().toString().padStart(2, '0');
  const minutes = time.getMinutes().toString().padStart(2, '0');
  const seconds = time.getSeconds().toString().padStart(2, '0');

  return (
    <div className={`font-mono text-sm tracking-wider ${className}`}>
      <span className="text-gray-400">{hours}</span>
      <motion.span
        animate={{ opacity: [1, 0.3, 1] }}
        transition={{ duration: 1, repeat: Infinity }}
        className="text-gray-500"
      >
        :
      </motion.span>
      <span className="text-gray-400">{minutes}</span>
      <motion.span
        animate={{ opacity: [1, 0.3, 1] }}
        transition={{ duration: 1, repeat: Infinity }}
        className="text-gray-500"
      >
        :
      </motion.span>
      <AnimatePresence mode="popLayout">
        <motion.span
          key={seconds}
          initial={{ opacity: 0, y: -8 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 8 }}
          transition={{ duration: 0.15 }}
          className="text-gray-300 inline-block min-w-[1.25rem]"
        >
          {seconds}
        </motion.span>
      </AnimatePresence>
    </div>
  );
};
