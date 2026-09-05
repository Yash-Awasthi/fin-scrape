import { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import { IndicatorData } from '../types';
import {
  generateBriefing,
  getCachedBriefing,
  needsBriefingRefresh,
  BriefingResponse,
} from '../services/synthesis/briefingGenerator';

interface UseBriefingOptions {
  userPhase?: number;
  focusAreas?: string[];
  autoRefresh?: boolean;
  refreshInterval?: number; // in milliseconds
}

interface UseBriefingReturn {
  briefing: BriefingResponse | null;
  isLoading: boolean;
  error: Error | null;
  refresh: () => Promise<void>;
  needsRefresh: boolean;
}

// Create stable hash of indicator states
function getIndicatorHash(indicators: IndicatorData[]): string {
  return indicators
    .map(i => `${i.id}:${i.status.level}`)
    .sort()
    .join('|');
}

export function useBriefing(
  indicators: IndicatorData[],
  options: UseBriefingOptions = {}
): UseBriefingReturn {
  const {
    userPhase = 1,
    focusAreas = [],
    autoRefresh = false, // Disabled by default to prevent unwanted refreshes
    refreshInterval = 15 * 60 * 1000, // 15 minutes
  } = options;

  const [briefing, setBriefing] = useState<BriefingResponse | null>(() => getCachedBriefing());
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  // Track if we've done initial fetch
  const hasFetched = useRef(false);
  const isFetching = useRef(false);

  // Stable hash of indicators to detect real changes
  const indicatorHash = useMemo(() => getIndicatorHash(indicators), [indicators]);

  // Store indicators in ref to avoid dependency issues
  const indicatorsRef = useRef(indicators);
  indicatorsRef.current = indicators;

  // Check if refresh is needed
  const needsRefresh = useMemo(() => {
    if (indicators.length === 0) return false;
    return needsBriefingRefresh(indicators);
  }, [indicatorHash]); // eslint-disable-line react-hooks/exhaustive-deps

  // Generate briefing - stable callback
  const generateNewBriefing = useCallback(async (forceRefresh = false) => {
    const currentIndicators = indicatorsRef.current;
    if (currentIndicators.length === 0) return;
    if (isFetching.current) return; // Prevent concurrent fetches

    isFetching.current = true;
    setIsLoading(true);
    setError(null);

    try {
      const newBriefing = await generateBriefing(currentIndicators, {
        userPhase,
        focusAreas,
        forceRefresh,
      });
      setBriefing(newBriefing);
      hasFetched.current = true;
    } catch (err) {
      console.error('Failed to generate briefing:', err);
      setError(err instanceof Error ? err : new Error('Failed to generate briefing'));
    } finally {
      setIsLoading(false);
      isFetching.current = false;
    }
  }, [userPhase, focusAreas]);

  // Initial load only - runs once when indicators first become available
  useEffect(() => {
    if (hasFetched.current) return;
    if (indicators.length === 0) return;

    // Try cached first
    const cached = getCachedBriefing();
    if (cached) {
      setBriefing(cached);
      hasFetched.current = true;
      return;
    }

    // Generate new if no cache
    generateNewBriefing();
  }, [indicatorHash, generateNewBriefing]); // eslint-disable-line react-hooks/exhaustive-deps

  // Auto-refresh interval (disabled by default)
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      generateNewBriefing();
    }, refreshInterval);

    return () => clearInterval(interval);
  }, [autoRefresh, refreshInterval, generateNewBriefing]);

  // Manual refresh
  const refresh = useCallback(async () => {
    await generateNewBriefing(true);
  }, [generateNewBriefing]);

  return {
    briefing,
    isLoading,
    error,
    refresh,
    needsRefresh,
  };
}

export default useBriefing;
