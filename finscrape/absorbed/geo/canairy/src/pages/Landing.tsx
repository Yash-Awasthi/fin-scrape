import React from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import {
  ArrowRight,
  Shield,
  Activity,
  Bell,
  TrendingUp,
  Zap,
  ShoppingCart,
  Database,
  Clock,
  CheckCircle,
  AlertTriangle,
  Bird,
} from 'lucide-react';

const STORAGE_KEY = 'canairy_seen_landing';

export const Landing: React.FC = () => {
  const navigate = useNavigate();

  const handleEnter = () => {
    localStorage.setItem(STORAGE_KEY, 'true');
    navigate('/dashboard');
  };

  return (
    <div className="min-h-screen bg-[#09090B] flex flex-col items-center p-6 relative overflow-hidden">
      {/* Subtle gradient background */}
      <div className="absolute inset-0 bg-gradient-to-b from-white/[0.02] via-transparent to-transparent pointer-events-none" />

      {/* Ambient glow */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[600px] h-[400px] bg-green-500/5 rounded-full blur-[120px] pointer-events-none" />

      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className="max-w-3xl w-full relative z-10 pt-8 sm:pt-12"
      >
        {/* Header */}
        <div className="text-center mb-8">
          {/* Logo / Icon - Canary bird */}
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ duration: 0.3 }}
            className="mb-5"
          >
            <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-amber-500/10 border border-amber-500/20">
              <Bird className="w-7 h-7 text-amber-400" />
            </div>
          </motion.div>

          {/* Wordmark */}
          <motion.h1
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.1 }}
            className="text-4xl sm:text-5xl font-display font-bold text-white mb-3 tracking-tight"
          >
            Canairy
          </motion.h1>

          {/* Tagline - Family-centric, not doomsday */}
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.15 }}
            className="text-lg sm:text-xl text-white/60 leading-relaxed max-w-lg mx-auto"
          >
            Your family's early warning system.
            <span className="block mt-2 text-white/40">We watch 35+ economic and safety signals so you don't have to — and tell you exactly what to do about them.</span>
          </motion.p>
        </div>

        {/* What We Track - Parent-friendly language */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-white/[0.03] border border-white/[0.06] rounded-2xl p-6 mb-5"
        >
          <h2 className="text-sm font-medium text-white/40 uppercase tracking-wider mb-4">
            What We Watch For You
          </h2>

          <div className="grid sm:grid-cols-3 gap-4">
            <div className="flex items-start gap-3">
              <div className="w-8 h-8 rounded-lg bg-blue-500/10 flex items-center justify-center flex-shrink-0">
                <ShoppingCart className="w-4 h-4 text-blue-400" />
              </div>
              <div>
                <p className="text-white font-medium text-sm">Your Wallet</p>
                <p className="text-white/40 text-xs mt-0.5">Grocery prices, job market, cost of living, your 401k</p>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <div className="w-8 h-8 rounded-lg bg-amber-500/10 flex items-center justify-center flex-shrink-0">
                <TrendingUp className="w-4 h-4 text-amber-400" />
              </div>
              <div>
                <p className="text-white font-medium text-sm">Supply & Shortages</p>
                <p className="text-white/40 text-xs mt-0.5">Things that could affect what's on shelves or at the pump</p>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <div className="w-8 h-8 rounded-lg bg-red-500/10 flex items-center justify-center flex-shrink-0">
                <Zap className="w-4 h-4 text-red-400" />
              </div>
              <div>
                <p className="text-white font-medium text-sm">Keeping Things Running</p>
                <p className="text-white/40 text-xs mt-0.5">Power grid, internet, travel, the stuff daily life depends on</p>
              </div>
            </div>
          </div>
        </motion.div>

        {/* Sample Dashboard Preview */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.25 }}
          className="bg-white/[0.03] border border-white/[0.06] rounded-2xl p-5 mb-5"
        >
          <h2 className="text-sm font-medium text-white/40 uppercase tracking-wider mb-3">
            Here's What Families Are Doing This Week
          </h2>

          <div className="space-y-2">
            <div className="flex items-start gap-3 p-3 rounded-lg bg-white/[0.02] border border-white/[0.04]">
              <CheckCircle className="w-4 h-4 text-emerald-400 mt-0.5 flex-shrink-0" />
              <div>
                <p className="text-white text-sm">Stock 2 weeks of shelf-stable essentials at current prices</p>
                <p className="text-white/30 text-xs mt-0.5">Grocery prices up 4% this quarter</p>
              </div>
            </div>
            <div className="flex items-start gap-3 p-3 rounded-lg bg-white/[0.02] border border-white/[0.04]">
              <CheckCircle className="w-4 h-4 text-emerald-400 mt-0.5 flex-shrink-0" />
              <div>
                <p className="text-white text-sm">Update passwords on banking and email — enable 2FA</p>
                <p className="text-white/30 text-xs mt-0.5">Elevated cyber activity detected</p>
              </div>
            </div>
            <div className="flex items-start gap-3 p-3 rounded-lg bg-amber-500/5 border border-amber-500/10">
              <AlertTriangle className="w-4 h-4 text-amber-400 mt-0.5 flex-shrink-0" />
              <div>
                <p className="text-white text-sm">Check your 401k allocation — history shows staying the course wins</p>
                <p className="text-white/30 text-xs mt-0.5">Market volatility elevated but within normal range</p>
              </div>
            </div>
          </div>
        </motion.div>

        {/* What You'll Find */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="bg-white/[0.03] border border-white/[0.06] rounded-2xl p-6 mb-5"
        >
          <h2 className="text-sm font-medium text-white/40 uppercase tracking-wider mb-4">
            How It Works
          </h2>

          <div className="space-y-3">
            <div className="flex items-center gap-3 text-sm">
              <Activity className="w-4 h-4 text-green-400 flex-shrink-0" />
              <span className="text-white/70">
                <span className="text-white font-medium">35+ live indicators</span> — pulled from official government and financial sources
              </span>
            </div>

            <div className="flex items-center gap-3 text-sm">
              <Bell className="w-4 h-4 text-amber-400 flex-shrink-0" />
              <span className="text-white/70">
                <span className="text-white font-medium">Green / Amber / Red</span> — instantly see what needs attention
              </span>
            </div>

            <div className="flex items-center gap-3 text-sm">
              <Shield className="w-4 h-4 text-blue-400 flex-shrink-0" />
              <span className="text-white/70">
                <span className="text-white font-medium">Weekly action plans</span> — specific steps, not vague warnings
              </span>
            </div>

            <div className="flex items-center gap-3 text-sm">
              <Database className="w-4 h-4 text-purple-400 flex-shrink-0" />
              <span className="text-white/70">
                <span className="text-white font-medium">Transparent sources</span> — every data point links to its origin
              </span>
            </div>

            <div className="flex items-center gap-3 text-sm">
              <Clock className="w-4 h-4 text-cyan-400 flex-shrink-0" />
              <span className="text-white/70">
                <span className="text-white font-medium">2-minute weekly check-in</span> — updates automatically
              </span>
            </div>
          </div>
        </motion.div>

        {/* Founder note - attributed, human */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.35 }}
          className="text-center mb-6 px-4"
        >
          <p className="text-white/40 text-sm italic leading-relaxed">
            "I built this because I was spending hours each week trying to figure out what the news meant for my family.
            I figured other parents might want the same shortcut."
          </p>
          <p className="text-white/25 text-xs mt-2">— The Canairy Team</p>
        </motion.div>

        {/* CTA - Benefit-centric */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="text-center"
        >
          <button
            onClick={handleEnter}
            className="group inline-flex items-center gap-3 px-8 py-4 bg-amber-400 text-[#09090B] rounded-xl font-medium text-lg hover:bg-amber-300 transition-all"
          >
            <span>See this week's action plan</span>
            <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
          </button>

          <p className="mt-4 text-xs text-white/30">
            Free and open source. No account required. No data collection.
          </p>
        </motion.div>
      </motion.div>

      {/* Bottom - Social proof instead of defensive tagline */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5 }}
        className="mt-auto pt-10 pb-6 text-center"
      >
        <p className="text-xs text-white/20">
          Smart families plan ahead.
        </p>
      </motion.div>
    </div>
  );
};

// Helper to check if user has seen landing
export const hasSeenLanding = (): boolean => {
  return localStorage.getItem(STORAGE_KEY) === 'true';
};

export default Landing;
