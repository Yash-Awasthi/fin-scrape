// The dashboard is ONE page. Panels tile the 12-column grid band by band in
// this exact order — deterministic, no variants, no freeform dragging.

export interface PanelSlot {
  id: string;
  w: number;
  h: number;
}

export const PAGE_LAYOUT: PanelSlot[] = [
  // band 1 — live markets + watchlist
  { id: "markets-live", w: 8, h: 6 },
  { id: "watchlist", w: 4, h: 6 },
  // band 2 — intelligence: signals + globe
  { id: "feed", w: 4, h: 8 },
  { id: "globe", w: 8, h: 8 },
  // band 3 — state of the world
  { id: "stats", w: 4, h: 4 },
  { id: "suggestions", w: 4, h: 4 },
  { id: "dates", w: 4, h: 4 },
  // band 4 — the news room (raw feeds)
  { id: "lobby", w: 12, h: 8 },
  // band 5 — broadcast + curated world news
  { id: "worldnews", w: 4, h: 6 },
  { id: "livetv", w: 8, h: 6 },
  // band 6 — proof + signals
  { id: "correlations", w: 6, h: 4 },
  { id: "accuracy", w: 6, h: 4 },
  // band 7 — personal
  { id: "sentiment", w: 4, h: 5 },
  { id: "portfolio", w: 4, h: 5 },
  { id: "calendar", w: 4, h: 5 },
];

export function pagePanelIds(): Set<string> {
  return new Set(PAGE_LAYOUT.map((p) => p.id));
}
