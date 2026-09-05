import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { HelpCircle, X, BookOpen, Palette, Clock, Shield, Users } from 'lucide-react';
import { Link } from 'react-router-dom';
import { cn } from '../../utils/cn';

interface HelpPanelProps {
  className?: string;
}

export const HelpPanel: React.FC<HelpPanelProps> = ({ className }) => {
  const [isOpen, setIsOpen] = useState(false);

  const helpItems = [
    {
      icon: Palette,
      title: 'What do the colors mean?',
      content: (
        <div className="space-y-1.5 text-xs">
          <p><span className="text-emerald-400 font-medium">Green</span> — Within normal range. No action needed.</p>
          <p><span className="text-amber-400 font-medium">Amber</span> — Elevated. Worth watching, maybe prep.</p>
          <p><span className="text-red-400 font-medium">Red</span> — Action recommended. Check your plan.</p>
        </div>
      ),
    },
    {
      icon: Clock,
      title: 'How often should I check?',
      content: (
        <p className="text-xs text-white/50">
          Most families check weekly — like a Sunday habit. We'll surface alerts if something needs attention sooner.
        </p>
      ),
    },
    {
      icon: Shield,
      title: 'Is my data private?',
      content: (
        <p className="text-xs text-white/50">
          Yes. No account needed, no tracking, no data collection. Your preferences stay in your browser.
        </p>
      ),
    },
    {
      icon: Users,
      title: 'Who built this?',
      content: (
        <p className="text-xs text-white/50">
          Canairy was built by parents who wanted a simple way to stay ahead of disruptions — without doomscrolling.
        </p>
      ),
    },
  ];

  return (
    <>
      {/* Help trigger button */}
      <button
        onClick={() => setIsOpen(true)}
        className={cn(
          'p-2 rounded-lg text-olive-tertiary hover:text-olive-primary hover:bg-white/5 transition-colors',
          className
        )}
        aria-label="Help"
        title="Help & FAQ"
      >
        <HelpCircle className="w-5 h-5" />
      </button>

      {/* Slide-out panel */}
      <AnimatePresence>
        {isOpen && (
          <>
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setIsOpen(false)}
              className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50"
            />

            {/* Panel */}
            <motion.div
              initial={{ x: '100%' }}
              animate={{ x: 0 }}
              exit={{ x: '100%' }}
              transition={{ type: 'spring', damping: 25, stiffness: 300 }}
              className="fixed right-0 top-0 h-full w-[90%] max-w-sm bg-olive-card border-l border-olive z-50 overflow-y-auto"
            >
              {/* Header */}
              <div className="sticky top-0 bg-olive-card border-b border-olive px-4 py-3 flex items-center justify-between">
                <h2 className="font-display font-semibold text-olive-primary">Help & FAQ</h2>
                <button
                  onClick={() => setIsOpen(false)}
                  className="p-2 text-olive-tertiary hover:text-olive-primary rounded-lg hover:bg-white/5"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Content */}
              <div className="p-4 space-y-4">
                {/* Quick links */}
                <div className="space-y-2">
                  <p className="text-xs font-medium text-olive-tertiary uppercase tracking-wider">Quick Links</p>
                  <div className="grid grid-cols-2 gap-2">
                    <Link
                      to="/action-plan"
                      onClick={() => setIsOpen(false)}
                      className="flex items-center gap-2 p-3 rounded-lg bg-white/[0.03] border border-white/[0.06] text-sm text-olive-secondary hover:bg-white/[0.06] transition-colors"
                    >
                      <BookOpen className="w-4 h-4 text-olive-tertiary" />
                      Action Plan
                    </Link>
                    <Link
                      to="/indicators"
                      onClick={() => setIsOpen(false)}
                      className="flex items-center gap-2 p-3 rounded-lg bg-white/[0.03] border border-white/[0.06] text-sm text-olive-secondary hover:bg-white/[0.06] transition-colors"
                    >
                      <Palette className="w-4 h-4 text-olive-tertiary" />
                      All Indicators
                    </Link>
                  </div>
                </div>

                {/* FAQ items */}
                <div className="space-y-3">
                  <p className="text-xs font-medium text-olive-tertiary uppercase tracking-wider">Frequently Asked</p>
                  {helpItems.map((item, index) => (
                    <div
                      key={index}
                      className="p-3 rounded-lg bg-white/[0.02] border border-white/[0.04]"
                    >
                      <div className="flex items-center gap-2 mb-2">
                        <item.icon className="w-4 h-4 text-amber-400" />
                        <h3 className="text-sm font-medium text-olive-primary">{item.title}</h3>
                      </div>
                      {item.content}
                    </div>
                  ))}
                </div>

                {/* How it works */}
                <div className="p-3 rounded-lg bg-amber-500/5 border border-amber-500/10">
                  <h3 className="text-sm font-medium text-amber-300 mb-2">How Canairy works</h3>
                  <p className="text-xs text-white/40 leading-relaxed">
                    We monitor 35+ public data sources — government APIs, financial data, infrastructure reports — and translate them into simple recommendations for your family. All data is sourced from official channels and updated automatically.
                  </p>
                  <Link
                    to="/action-plan#how-it-works"
                    onClick={() => setIsOpen(false)}
                    className="inline-block mt-2 text-xs text-amber-400 hover:text-amber-300"
                  >
                    Learn more →
                  </Link>
                </div>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </>
  );
};

export default HelpPanel;
