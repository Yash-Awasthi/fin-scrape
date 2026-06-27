// Pure event→globe-point mapping (no globe.gl/WebGL import, so it's unit-testable).

import { type EventOut, verdictColor } from "../api";

export interface GlobePoint {
  id: number;
  lat: number;
  lng: number;
  color: string;
  label: string;
  size: number;
  event: EventOut;
}

export function toPoints(events: EventOut[]): GlobePoint[] {
  return events
    .filter((e) => e.lat != null && e.lon != null)
    .map((e) => ({
      id: e.id,
      lat: e.lat as number,
      lng: e.lon as number,
      color: verdictColor(e.verdict),
      label: `${e.verdict} ${e.signal_score >= 0 ? "+" : ""}${e.signal_score} — ${e.subject}`,
      size: 0.15 + Math.min(0.5, Math.abs(e.signal_score) / 10),
      event: e,
    }));
}
