/**
 * HowItWorks - Educational footer explaining the system
 *
 * Collapsible section for curious users who want to understand
 * how Canairy decides what to recommend.
 */

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown, HelpCircle, Activity, Shield, Gauge } from 'lucide-react';
import { cn } from '../../utils/cn';

export const HowItWorks: React.FC = () => {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="border-t border-olive-700/30 pt-6">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between gap-3 text-left group"
      >
        <div className="flex items-center gap-2">
          <HelpCircle className="w-4 h-4 text-olive-500" />
          <span className="text-sm font-medium text-olive-300 group-hover:text-olive-200 transition-colors">
            How this works
          </span>
        </div>
        <ChevronDown
          className={cn(
            'w-4 h-4 text-olive-500 transition-transform',
            expanded && 'rotate-180'
          )}
        />
      </button>

      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="pt-4 space-y-6">
              {/* How Canairy decides */}
              <section>
                <div className="flex items-center gap-2 mb-2">
                  <Activity className="w-4 h-4 text-olive-400" />
                  <h4 className="text-sm font-medium text-olive-200">
                    How Canairy monitors conditions
                  </h4>
                </div>
                <p className="text-xs text-olive-400 leading-relaxed">
                  Canairy tracks 50+ real-world indicators across the economy, supply chains,
                  energy, security, and more. Each indicator has thresholds based on historical
                  data — when one crosses from "normal" to "elevated" or "alert," it shows up
                  in your recommendations. No guesswork: just data.
                </p>
              </section>

              {/* What phases mean */}
              <section>
                <div className="flex items-center gap-2 mb-2">
                  <Gauge className="w-4 h-4 text-olive-400" />
                  <h4 className="text-sm font-medium text-olive-200">
                    What the phases mean
                  </h4>
                </div>
                <div className="bg-olive-900/40 rounded-lg overflow-hidden">
                  <table className="w-full text-xs">
                    <thead>
                      <tr className="border-b border-olive-700/30">
                        <th className="text-left py-2 px-3 text-olive-400 font-medium">Phase</th>
                        <th className="text-left py-2 px-3 text-olive-400 font-medium">Focus</th>
                        <th className="text-left py-2 px-3 text-olive-400 font-medium">You're ready for...</th>
                      </tr>
                    </thead>
                    <tbody className="text-olive-300">
                      <tr className="border-b border-olive-700/20">
                        <td className="py-2 px-3">1</td>
                        <td className="py-2 px-3">The Basics</td>
                        <td className="py-2 px-3">A long weekend without power or stores</td>
                      </tr>
                      <tr className="border-b border-olive-700/20">
                        <td className="py-2 px-3">2-3</td>
                        <td className="py-2 px-3">Financial + Connected</td>
                        <td className="py-2 px-3">Economic disruption, communication outages</td>
                      </tr>
                      <tr className="border-b border-olive-700/20">
                        <td className="py-2 px-3">4-6</td>
                        <td className="py-2 px-3">Storage & Shelter</td>
                        <td className="py-2 px-3">Extended shelter-in-place scenarios</td>
                      </tr>
                      <tr className="border-b border-olive-700/20">
                        <td className="py-2 px-3">7</td>
                        <td className="py-2 px-3">Energy Independence</td>
                        <td className="py-2 px-3">Grid failures lasting days or weeks</td>
                      </tr>
                      <tr>
                        <td className="py-2 px-3">8-9</td>
                        <td className="py-2 px-3">Water & Beyond</td>
                        <td className="py-2 px-3">Long-term infrastructure disruption</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </section>

              {/* How phases are triggered */}
              <section>
                <div className="flex items-center gap-2 mb-2">
                  <Shield className="w-4 h-4 text-olive-400" />
                  <h4 className="text-sm font-medium text-olive-200">
                    How phases change
                  </h4>
                </div>
                <p className="text-xs text-olive-400 leading-relaxed">
                  Your phase is determined by how many indicators are elevated. One red indicator
                  bumps you to Phase 3. Two or more red indicators ("elevated conditions") means
                  you'll see time-sensitive actions at the top of your list. Your phase also
                  reflects your completed tasks — finish The Basics, and you're ready for Phase 1
                  conditions even if you haven't done them yet.
                </p>
                <div className="mt-3 grid grid-cols-3 gap-2">
                  <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-lg p-2 text-center">
                    <div className="text-emerald-400 text-xs font-medium">Normal</div>
                    <div className="text-[10px] text-olive-400 mt-0.5">0 red indicators</div>
                  </div>
                  <div className="bg-amber-500/10 border border-amber-500/20 rounded-lg p-2 text-center">
                    <div className="text-amber-400 text-xs font-medium">Elevated</div>
                    <div className="text-[10px] text-olive-400 mt-0.5">1 red indicator</div>
                  </div>
                  <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-2 text-center">
                    <div className="text-red-400 text-xs font-medium">Critical</div>
                    <div className="text-[10px] text-olive-400 mt-0.5">2+ red indicators</div>
                  </div>
                </div>
              </section>

              {/* Footer note */}
              <p className="text-[10px] text-olive-500 italic">
                Canairy doesn't tell you what to think — it just surfaces data so you can decide
                what matters for your family. All data sources are public and transparent.
              </p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default HowItWorks;
