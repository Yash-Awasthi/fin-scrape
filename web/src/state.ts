// Tiny reactive store — no framework. Panels subscribe; the app mutates.

import type { Correlation, DashboardStats, EventOut } from "./api";
import type { WSStatus } from "./ws";

export interface AppState {
  events: EventOut[];
  stats: DashboardStats | null;
  correlations: Correlation[];
  connection: WSStatus;
  selected: EventOut | null;
}

type Listener = (state: AppState) => void;

const MAX_EVENTS = 500;

export class Store {
  private state: AppState = {
    events: [],
    stats: null,
    correlations: [],
    connection: "connecting",
    selected: null,
  };
  private listeners = new Set<Listener>();

  get(): AppState {
    return this.state;
  }

  subscribe(fn: Listener): () => void {
    this.listeners.add(fn);
    fn(this.state);
    return () => this.listeners.delete(fn);
  }

  private set(patch: Partial<AppState>): void {
    this.state = { ...this.state, ...patch };
    for (const fn of this.listeners) fn(this.state);
  }

  setConnection(connection: WSStatus): void {
    this.set({ connection });
  }

  setStats(stats: DashboardStats): void {
    this.set({ stats });
  }

  setCorrelations(correlations: Correlation[]): void {
    this.set({ correlations });
  }

  setEvents(events: EventOut[]): void {
    this.set({ events: events.slice(0, MAX_EVENTS) });
  }

  /** Merge newly-arrived events, newest-first, deduped by id, capped. */
  addEvents(incoming: EventOut[]): void {
    if (!incoming.length) return;
    const seen = new Set(incoming.map((e) => e.id));
    const merged = [...incoming, ...this.state.events.filter((e) => !seen.has(e.id))];
    this.set({ events: merged.slice(0, MAX_EVENTS) });
  }

  select(selected: EventOut | null): void {
    this.set({ selected });
  }
}
