/**
 * WelcomeBanner
 *
 * First-visit experience that explains the dashboard.
 * Shows once for new users, dismissable with "Got it" button.
 * Persisted in localStorage.
 */

import React, { useState, useCallback } from 'react';
import { Sparkles } from 'lucide-react';

const STORAGE_KEY = 'canairy_welcome_dismissed';

function loadDismissed(): boolean {
  try {
    return localStorage.getItem(STORAGE_KEY) === 'true';
  } catch {
    return false;
  }
}

function saveDismissed() {
  try {
    localStorage.setItem(STORAGE_KEY, 'true');
  } catch {
    // Ignore storage errors
  }
}

export const WelcomeBanner: React.FC = () => {
  const [dismissed, setDismissed] = useState(loadDismissed);

  const handleDismiss = useCallback(() => {
    setDismissed(true);
    saveDismissed();
  }, []);

  if (dismissed) {
    return null;
  }

  return (
    <div className="glass-card overflow-hidden border border-olive-600/30">
      <div className="px-5 py-4 flex items-start gap-4">
        {/* Icon */}
        <div className="w-10 h-10 rounded-xl bg-olive-600/20 flex items-center justify-center flex-shrink-0">
          <Sparkles className="w-5 h-5 text-olive-400" />
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <h3 className="font-display font-semibold text-olive-100 mb-1">
            Welcome to Canairy
          </h3>
          <p className="text-sm text-olive-300 leading-relaxed">
            This dashboard updates based on real-world conditions. Your action plan tells you
            what to focus on each week. Start with The Basics — most of it takes an afternoon.
          </p>
        </div>

        {/* Dismiss button */}
        <button
          onClick={handleDismiss}
          className="flex-shrink-0 px-3 py-1.5 text-sm font-medium text-olive-100 bg-olive-700/50 hover:bg-olive-600/50 rounded-lg transition-colors"
        >
          Got it
        </button>
      </div>
    </div>
  );
};

export default WelcomeBanner;
