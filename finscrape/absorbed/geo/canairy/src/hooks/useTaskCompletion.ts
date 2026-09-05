/**
 * Task Completion Persistence Hooks
 *
 * Manages localStorage persistence for completed actions and phase tasks.
 */

import { useState, useCallback, useEffect } from 'react';

const COMPLETED_ACTIONS_KEY = 'canairy-completed-actions';
const COMPLETED_PHASE_TASKS_KEY = 'canairy-phase-tasks';
const ACTION_COMPLETION_TIMESTAMPS_KEY = 'canairy-action-timestamps';

// ============================================================================
// ACTION COMPLETION HOOK
// ============================================================================

export function useActionCompletion() {
  const [completedIds, setCompletedIds] = useState<Set<string>>(() => {
    try {
      const stored = localStorage.getItem(COMPLETED_ACTIONS_KEY);
      return stored ? new Set(JSON.parse(stored)) : new Set();
    } catch {
      return new Set();
    }
  });

  const [timestamps, setTimestamps] = useState<Record<string, string>>(() => {
    try {
      const stored = localStorage.getItem(ACTION_COMPLETION_TIMESTAMPS_KEY);
      return stored ? JSON.parse(stored) : {};
    } catch {
      return {};
    }
  });

  const toggle = useCallback((id: string) => {
    setCompletedIds(prev => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      localStorage.setItem(COMPLETED_ACTIONS_KEY, JSON.stringify([...next]));
      return next;
    });

    setTimestamps(prev => {
      const next = { ...prev };
      if (completedIds.has(id)) {
        delete next[id];
      } else {
        next[id] = new Date().toISOString();
      }
      localStorage.setItem(ACTION_COMPLETION_TIMESTAMPS_KEY, JSON.stringify(next));
      return next;
    });
  }, [completedIds]);

  const isCompleted = useCallback((id: string) => completedIds.has(id), [completedIds]);

  const getCompletedAt = useCallback((id: string) => timestamps[id] || null, [timestamps]);

  const clearAll = useCallback(() => {
    setCompletedIds(new Set());
    setTimestamps({});
    localStorage.removeItem(COMPLETED_ACTIONS_KEY);
    localStorage.removeItem(ACTION_COMPLETION_TIMESTAMPS_KEY);
  }, []);

  return {
    completedIds,
    toggle,
    isCompleted,
    getCompletedAt,
    clearAll,
    completedCount: completedIds.size,
  };
}

// ============================================================================
// PHASE TASK COMPLETION HOOK
// ============================================================================

export function usePhaseTaskCompletion() {
  const [completedIds, setCompletedIds] = useState<Set<string>>(() => {
    try {
      const stored = localStorage.getItem(COMPLETED_PHASE_TASKS_KEY);
      return stored ? new Set(JSON.parse(stored)) : new Set();
    } catch {
      return new Set();
    }
  });

  const toggle = useCallback((id: string) => {
    setCompletedIds(prev => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      localStorage.setItem(COMPLETED_PHASE_TASKS_KEY, JSON.stringify([...next]));
      return next;
    });
  }, []);

  const isCompleted = useCallback((id: string) => completedIds.has(id), [completedIds]);

  const markComplete = useCallback((id: string) => {
    setCompletedIds(prev => {
      const next = new Set(prev);
      next.add(id);
      localStorage.setItem(COMPLETED_PHASE_TASKS_KEY, JSON.stringify([...next]));
      return next;
    });
  }, []);

  const markIncomplete = useCallback((id: string) => {
    setCompletedIds(prev => {
      const next = new Set(prev);
      next.delete(id);
      localStorage.setItem(COMPLETED_PHASE_TASKS_KEY, JSON.stringify([...next]));
      return next;
    });
  }, []);

  const clearAll = useCallback(() => {
    setCompletedIds(new Set());
    localStorage.removeItem(COMPLETED_PHASE_TASKS_KEY);
  }, []);

  return {
    completedIds,
    toggle,
    isCompleted,
    markComplete,
    markIncomplete,
    clearAll,
    completedCount: completedIds.size,
  };
}

// ============================================================================
// COMBINED HOOK
// ============================================================================

export function useAllTaskCompletion() {
  const actions = useActionCompletion();
  const phaseTasks = usePhaseTaskCompletion();

  // Merge both sets for unified "is anything completed" checks
  const allCompletedIds = new Set([
    ...actions.completedIds,
    ...phaseTasks.completedIds,
  ]);

  return {
    actions,
    phaseTasks,
    allCompletedIds,
    totalCompleted: actions.completedCount + phaseTasks.completedCount,
  };
}
