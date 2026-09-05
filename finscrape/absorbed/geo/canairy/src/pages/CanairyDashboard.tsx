import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Home, CheckSquare, BookOpen, Settings, RefreshCw, Bell, Download } from 'lucide-react';
import { Link, useLocation } from 'react-router-dom';
import { useStore } from '../store';
import { CanairyMascot } from '../components/canairy/CanairyMascot';
import { NestEggCard } from '../components/canairy/NestEggCard';
import { FamilyStatus } from '../components/canairy/FamilyStatus';
import { QuickActions } from '../components/canairy/QuickActions';
import { canairyMessages } from '../content/canairy-messages';
import { cn } from '../utils/cn';

export const CanairyDashboard: React.FC = () => {
  const location = useLocation();
  const [sidebarOpen] = useState(true);
  const {
    indicators,
    hopiScore,
    currentPhase,
    loading,
    refreshAll
  } = useStore();

  const sidebarItems = [
    { path: '/', icon: Home, label: 'Home' },
    { path: '/checklist', icon: CheckSquare, label: 'Family Actions' },
    { path: '/playbook', icon: BookOpen, label: 'Resilience Playbook' },
    { path: '/settings', icon: Settings, label: 'Settings' },
  ];

  const getOverallStatus = () => {
    const redCount = indicators.filter(i => i.status.level === 'red').length;
    const amberCount = indicators.filter(i => i.status.level === 'amber').length;
    
    if (redCount >= 2) return 'action';
    if (redCount > 0 || amberCount >= 3) return 'attention';
    return 'allGood';
  };

  const overallStatus = getOverallStatus();
  const statusMessage = canairyMessages.status[overallStatus];

  return (
    <div className="min-h-screen bg-canairy-neutral flex">
      {/* Sidebar */}
      <motion.aside
        initial={{ x: -300 }}
        animate={{ x: sidebarOpen ? 0 : -240 }}
        className="w-64 bg-white sidebar-nest shadow-xl z-20 fixed h-full"
      >
        <div className="p-6">
          {/* Logo */}
          <div className="flex items-center gap-3 mb-8">
            <CanairyMascot size="md" mood={overallStatus === 'allGood' ? 'happy' : 'alert'} />
            <div>
              <h1 className="text-xl font-bold text-canairy-charcoal">Canairy</h1>
              <p className="text-xs text-canairy-charcoal-light">Your family's guide</p>
            </div>
          </div>

          {/* Navigation */}
          <nav className="space-y-2">
            {sidebarItems.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                className={cn(
                  "flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200",
                  location.pathname === item.path
                    ? "bg-canairy-yellow text-canairy-charcoal font-semibold shadow-feather"
                    : "text-canairy-charcoal-light hover:bg-canairy-yellow-light/50"
                )}
              >
                <item.icon className="w-5 h-5" />
                <span>{item.label}</span>
              </Link>
            ))}
          </nav>
        </div>

        {/* Bottom section */}
        <div className="absolute bottom-0 left-0 right-0 p-6">
          <button className="btn-canairy btn-secondary-canairy w-full">
            <Bell className="w-4 h-4" />
            <span>Alert Settings</span>
          </button>
        </div>
      </motion.aside>

      {/* Main content */}
      <main className={cn(
        "flex-1 transition-all duration-300",
        sidebarOpen ? "ml-64" : "ml-6"
      )}>
        {/* Header */}
        <header className="header-sunshine p-6 shadow-lg">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold text-canairy-charcoal">
                {canairyMessages.brand.tagline}
              </h2>
              <p className="text-canairy-charcoal-light mt-1">
                {canairyMessages.brand.subtitle}
              </p>
            </div>
            <div className="flex items-center gap-4">
              <button
                onClick={refreshAll}
                className="btn-canairy btn-primary-canairy"
                disabled={loading}
              >
                <RefreshCw className={cn("w-4 h-4", loading && "animate-spin")} />
                <span>Refresh</span>
              </button>
              <button className="btn-canairy btn-secondary-canairy">
                <Download className="w-4 h-4" />
                <span>Export</span>
              </button>
            </div>
          </div>
        </header>

        {/* Content */}
        <div className="p-6">
          {/* Family Status Overview */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-8"
          >
            <FamilyStatus
              status={overallStatus}
              message={statusMessage}
              hopiScore={hopiScore}
              phase={currentPhase}
            />
          </motion.div>

          {/* Quick Actions */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="mb-8"
          >
            <QuickActions status={overallStatus} />
          </motion.div>

          {/* Indicators Grid */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.2 }}
          >
            <h3 className="text-xl font-bold text-canairy-charcoal mb-4">
              Your Nest Eggs
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              <AnimatePresence>
                {indicators.map((indicator, index) => (
                  <motion.div
                    key={indicator.id}
                    initial={{ opacity: 0, scale: 0.8 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: index * 0.05 }}
                  >
                    <NestEggCard
                      indicator={indicator}
                      onClick={() => window.location.href = `/indicator/${indicator.id}`}
                    />
                  </motion.div>
                ))}
              </AnimatePresence>
            </div>
          </motion.div>
        </div>
      </main>

      {/* Floating Canairy Helper */}
      <motion.div
        initial={{ opacity: 0, scale: 0 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ delay: 1 }}
        className="fixed bottom-6 right-6 z-30"
      >
        <button className="bg-white rounded-full p-4 shadow-nest hover:scale-110 transition-transform duration-200">
          <CanairyMascot size="sm" mood="thinking" />
        </button>
      </motion.div>
    </div>
  );
};