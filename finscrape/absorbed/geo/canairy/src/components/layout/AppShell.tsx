import React, { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Home,
  Eye,
  ClipboardList,
  Settings,
  RefreshCw,
  Menu,
  X,
  Bell,
} from 'lucide-react';
import { Link, useLocation, Outlet } from 'react-router-dom';
import { useStore } from '../../store';
import { CanaryLogo } from '../branding/CanaryLogo';
import { ErrorBoundary } from '../ErrorBoundary';
import { RightSidebar } from './RightSidebar';
import { CardDetailPanel } from '../dashboard/CardDetailPanel';
import { Tooltip } from '../ui/Tooltip';
import { HelpPanel } from '../common/HelpPanel';
import { generateInsightCardWithEvidence } from '../../services/synthesis/evidenceGenerator';
import { cn } from '../../utils/cn';

// Left nav items - icon only on desktop (simplified to 5 items)
const NAV_ITEMS = [
  { path: '/dashboard', icon: Home, label: 'Home' },
  { path: '/indicators', icon: Eye, label: 'Indicators' },
  { path: '/action-plan', icon: ClipboardList, label: 'Action Plan' },
  { path: '/alerts', icon: Bell, label: 'Alerts' },
  { path: '/settings', icon: Settings, label: 'Settings' },
];

// Bottom tab bar items (mobile) - same 5 items
const BOTTOM_TABS = [
  { path: '/dashboard', icon: Home, label: 'Home' },
  { path: '/action-plan', icon: ClipboardList, label: 'Actions' },
  { path: '/indicators', icon: Eye, label: 'Monitor' },
  { path: '/alerts', icon: Bell, label: 'Alerts' },
  { path: '/settings', icon: Settings, label: 'More' },
];

export const AppShell: React.FC = () => {
  const location = useLocation();
  const { loading, refreshAll, indicators, detailPanelCardId, setDetailPanelCardId, synthesisOutput } = useStore();
  const [showMobileNav, setShowMobileNav] = useState(false);
  const [showMobileSidebar, setShowMobileSidebar] = useState(false);

  const redCount = indicators.filter(i => i.status.level === 'red').length;

  const isActive = (path: string) =>
    path === '/' ? location.pathname === '/' : location.pathname.startsWith(path);

  // Right sidebar only shows on dashboard when panel is closed
  const isDashboard = location.pathname === '/dashboard' || location.pathname === '/';
  const isPanelOpen = detailPanelCardId !== null;
  const showRightSidebar = isDashboard && !isPanelOpen;

  // Generate full evidence card for the detail panel
  const detailCard = useMemo(() => {
    if (!detailPanelCardId || !synthesisOutput?.leadCard || indicators.length === 0) {
      return null;
    }
    // For now, we only support the lead card - check if it matches
    if (synthesisOutput.leadCard.pattern.id === detailPanelCardId) {
      return generateInsightCardWithEvidence(synthesisOutput.leadCard, indicators);
    }
    return null;
  }, [detailPanelCardId, synthesisOutput, indicators]);

  const handleClosePanel = () => setDetailPanelCardId(null);

  return (
    <div className="min-h-screen flex bg-olive-page relative">
      <a href="#main-content" className="skip-to-content">
        Skip to main content
      </a>

      {/* ── Mobile Nav Backdrop ── */}
      <AnimatePresence>
        {showMobileNav && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setShowMobileNav(false)}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 lg:hidden"
          />
        )}
      </AnimatePresence>

      {/* ── Left Nav (56px thin rail on desktop) ── */}
      <aside
        aria-label="Main navigation"
        className={cn(
          'fixed h-full z-50 transition-all duration-300',
          'bg-olive-nav border-r border-olive',
          // Desktop: 56px thin rail (icon-only)
          'lg:w-14 lg:translate-x-0',
          // Mobile: full sidebar with labels
          showMobileNav ? 'w-56 translate-x-0' : 'w-56 -translate-x-full lg:w-14'
        )}
      >
        <div className="flex flex-col h-full items-center">
          {/* Mobile close button */}
          <div className="py-4 flex items-center justify-end w-full lg:hidden px-3">
            <button
              onClick={() => setShowMobileNav(false)}
              aria-label="Close navigation menu"
              className="p-1.5 text-olive-tertiary hover:text-olive-primary rounded-lg hover:bg-white/5"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Spacer for desktop to align nav items */}
          <div className="hidden lg:block h-4" />

          {/* Navigation */}
          <nav aria-label="Primary navigation" className="flex-1 w-full px-2 py-2">
            <div className="flex flex-col items-center gap-1">
              {NAV_ITEMS.map(item => {
                const active = isActive(item.path);
                const showBadge = item.path === '/action-plan' && redCount > 0;

                // Single link element - tooltip shown on desktop via CSS
                return (
                  <Tooltip key={item.path} content={item.label} side="right" wrapperClassName="w-full lg:w-auto">
                    <Link
                      to={item.path}
                      onClick={() => setShowMobileNav(false)}
                      aria-label={item.label}
                      aria-current={active ? 'page' : undefined}
                      className={cn(
                        'flex items-center gap-3 rounded-lg transition-all duration-200 relative group',
                        // Desktop: icon-only centered, 40x40
                        'lg:justify-center lg:w-10 lg:h-10',
                        // Mobile: full width with label
                        'w-full px-3 py-2.5 lg:px-0 lg:py-0',
                        active
                          ? 'text-amber-400 bg-amber-400/10'
                          : 'text-olive-secondary hover:text-olive-primary hover:bg-white/5'
                      )}
                    >
                      {/* Active indicator: 3px left border pill */}
                      {active && (
                        <div className="absolute left-0 top-2 bottom-2 w-[3px] rounded-r-full bg-amber-400 lg:block hidden" />
                      )}
                      <item.icon className="w-5 h-5 flex-shrink-0" aria-hidden="true" />
                      <span className="lg:hidden flex-1">{item.label}</span>
                      {showBadge && (
                        <span className={cn(
                          'flex items-center justify-center text-2xs bg-red-500/20 text-red-400 rounded-md font-medium',
                          'lg:absolute lg:-top-0.5 lg:-right-0.5 lg:w-4 lg:h-4 lg:text-[10px]',
                          'w-5 h-5'
                        )}
                        aria-label={`${redCount} alerts`}
                        >
                          {redCount}
                        </span>
                      )}
                    </Link>
                  </Tooltip>
                );
              })}
            </div>
          </nav>

          {/* Refresh button - pinned to bottom */}
          <div className="w-full p-2 border-t border-olive">
            <Tooltip content="Refresh data" side="right">
              <button
                onClick={refreshAll}
                disabled={loading}
                className={cn(
                  'flex items-center justify-center gap-2 rounded-lg transition-all duration-200',
                  'text-olive-tertiary hover:text-olive-primary hover:bg-white/5',
                  'lg:w-10 lg:h-10 lg:mx-auto',
                  'w-full px-3 py-2.5 lg:px-0 lg:py-0'
                )}
              >
                <RefreshCw className={cn('w-5 h-5', loading && 'animate-spin')} />
                <span className="lg:hidden">Refresh</span>
              </button>
            </Tooltip>
          </div>
        </div>
      </aside>

      {/* ── Main Content Area ── */}
      <div className={cn(
        'flex-1 min-h-screen flex flex-col',
        'lg:ml-14' // Account for 56px left nav
      )}>
        {/* Desktop Header with Logo */}
        <header className="hidden lg:flex items-center justify-between px-8 py-4 border-b border-olive/50">
          <Link to="/dashboard" className="flex items-center gap-2" aria-label="Canairy - Go to Dashboard">
            <span className="text-lg font-display font-bold text-olive-primary" aria-hidden="true">
              Can<span className="text-amber-400">ai</span>ry
            </span>
          </Link>
          <div className="flex items-center gap-3">
            <span className="text-xs text-olive-muted">
              Household Resilience Monitor
            </span>
            <HelpPanel />
          </div>
        </header>

        {/* Mobile Header */}
        <header className="lg:hidden bg-olive-nav/80 backdrop-blur-xl border-b border-olive sticky top-0 z-10">
          <div className="px-4 py-3 flex items-center justify-between">
            <button
              onClick={() => setShowMobileNav(true)}
              aria-label="Open navigation menu"
              className="p-2 text-olive-tertiary hover:text-olive-primary hover:bg-white/5 rounded-xl transition-colors"
            >
              <Menu className="w-5 h-5" />
            </button>

            <Link to="/dashboard">
              <CanaryLogo size="sm" showText={true} />
            </Link>

            {showRightSidebar ? (
              <button
                onClick={() => setShowMobileSidebar(true)}
                aria-label="Open sidebar"
                className="p-2 text-olive-tertiary hover:text-olive-primary hover:bg-white/5 rounded-xl transition-colors"
              >
                <Eye className="w-5 h-5" />
              </button>
            ) : (
              <div className="w-9 h-9" /> // Spacer for layout balance
            )}
          </div>
        </header>

        {/* Content row with main + sidebar */}
        <div className="flex-1 flex">
          {/* Main Feed - centered with max-width */}
          <main
            id="main-content"
            className={cn(
              'flex-1 min-h-screen flex flex-col',
              'pb-16 lg:pb-0', // Bottom padding for mobile tabs
              'transition-all duration-300',
              // Centered main content area - wider
              showRightSidebar && 'lg:max-w-5xl lg:mx-auto lg:w-full lg:px-8',
              isPanelOpen && 'lg:w-[50%] lg:flex-none lg:max-w-none lg:mx-0'
            )}
          >
            {/* Page content */}
            <div className="flex-1">
              <ErrorBoundary>
                <Outlet />
              </ErrorBoundary>
            </div>
          </main>

          {/* Right Sidebar - fixed width on right edge */}
          {showRightSidebar && (
            <aside
              className={cn(
                'hidden lg:flex lg:flex-col',
                'lg:w-80 lg:flex-none',
                'bg-olive-sidebar border-l border-olive',
                'h-[calc(100vh-65px)] sticky top-[65px] overflow-y-auto'
              )}
            >
              <RightSidebar />
            </aside>
          )}

          {/* Card Detail Panel - replaces right sidebar when open */}
          {isDashboard && (
            <CardDetailPanel
              card={detailCard}
              onClose={handleClosePanel}
            />
          )}
        </div>
      </div>

      {/* ── Mobile Sidebar Drawer (Dashboard only) ── */}
      <AnimatePresence>
        {showMobileSidebar && showRightSidebar && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setShowMobileSidebar(false)}
              className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 lg:hidden"
            />
            <motion.aside
              initial={{ x: '100%' }}
              animate={{ x: 0 }}
              exit={{ x: '100%' }}
              transition={{ type: 'spring', damping: 25, stiffness: 300 }}
              className="fixed right-0 top-0 h-full w-[85%] max-w-sm bg-olive-sidebar border-l border-olive z-50 lg:hidden overflow-y-auto"
            >
              <div className="p-4 border-b border-olive flex items-center justify-between">
                <span className="font-display font-semibold text-olive-primary">Status</span>
                <button
                  onClick={() => setShowMobileSidebar(false)}
                  className="p-2 text-olive-tertiary hover:text-olive-primary rounded-lg hover:bg-white/5"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
              <RightSidebar />
            </motion.aside>
          </>
        )}
      </AnimatePresence>

      {/* ── Mobile Bottom Tabs ── */}
      <nav
        aria-label="Mobile navigation"
        className="fixed bottom-0 left-0 right-0 z-30 lg:hidden bg-olive-nav/95 backdrop-blur-xl border-t border-olive"
      >
        <div className="flex items-center justify-around px-2 py-1.5">
          {BOTTOM_TABS.map(tab => {
            const active = isActive(tab.path);
            return (
              <Link
                key={tab.path}
                to={tab.path}
                className={cn(
                  'flex flex-col items-center gap-0.5 px-3 py-1.5 rounded-xl transition-colors min-w-0',
                  active ? 'text-olive-primary' : 'text-olive-muted'
                )}
              >
                <tab.icon className="w-5 h-5" />
                <span className="text-2xs truncate">{tab.label}</span>
              </Link>
            );
          })}
        </div>
      </nav>
    </div>
  );
};
