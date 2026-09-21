// The dashboard is ONE page. Panels tile the 12-column grid band by band in
// this exact order — deterministic, no variants, no freeform dragging.
//
// Every band sums to 12, and every panel the app registers appears exactly once:
// a slot naming a panel that does not exist renders nothing, and a panel missing
// from this list is built, wired and then hidden by `applyVariant`. Both failure
// modes are silent, so `layout.test.ts` asserts the two sets match.

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
  // band 3 — chart + research (both re-aim on worldfin:select-symbol)
  { id: "candles", w: 8, h: 6 },
  { id: "agents", w: 4, h: 6 },
  // band 4 — state of the world
  { id: "stats", w: 4, h: 4 },
  { id: "sectors", w: 4, h: 4 },
  { id: "suggestions", w: 4, h: 4 },
  // band 5 — the news room (raw feeds)
  { id: "lobby", w: 12, h: 8 },
  // band 6 — broadcast + curated world news
  { id: "worldnews", w: 4, h: 6 },
  { id: "livetv", w: 8, h: 6 },
  // band 7 — proof: corroboration, realized accuracy, ingest health
  { id: "correlations", w: 4, h: 4 },
  { id: "accuracy", w: 4, h: 4 },
  { id: "sources", w: 4, h: 4 },
  // band 8 — forward-looking + what already fired
  { id: "prediction", w: 6, h: 5 },
  { id: "alerts", w: 6, h: 5 },
  // band 9 — personal
  { id: "sentiment", w: 4, h: 5 },
  { id: "portfolio", w: 4, h: 5 },
  { id: "markets", w: 4, h: 5 },
  // band 10 — date strip
  { id: "calendar", w: 12, h: 2 },
];

export function pagePanelIds(): Set<string> {
  return new Set(PAGE_LAYOUT.map((p) => p.id));
}
