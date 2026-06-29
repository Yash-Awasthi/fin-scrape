import { expect, test } from "@playwright/test";

// EventOut fixture matching server/schemas.py + src/api.ts. Only the fields the UI
// reads need to be realistic; the rest are filled with sane defaults.
function ev(id: number, subject: string, tickers: string[], verdict = "INVEST") {
  return {
    id,
    subject,
    event_type: "geopolitical",
    verdict,
    impact_direction: "positive",
    signal_score: 42,
    confidence: 0.8,
    reasoning: `Why ${subject} matters.`,
    magnitude: "high",
    novelty: "high",
    actionability: "high",
    sector_impact: "tech",
    tickers,
    sources: ["reuters", "ap"],
    articles: ["https://example.com/a"],
    affected_entities: [{ name: "Apple", ticker: "AAPL", role: "supplier", impact: "up" }],
    second_order_effects: [],
    key_metrics: {},
    lat: 37.77,
    lon: -122.41,
    timestamp: "2026-06-28T10:00:00Z",
    created_at: "2026-06-28T10:00:00Z",
  };
}

const INIT_EVENTS = [
  ev(1, "Chip export controls tightened", ["AAPL", "MSFT"]),
  ev(2, "Energy supply shock in Europe", ["XOM"], "CAUTIOUS"),
];
const NEW_EVENT = ev(3, "Breaking: central bank surprise hike", ["JPM"], "OBSERVE");

const STATS = {
  total_events: 2,
  by_verdict: { INVEST: 1, CAUTIOUS: 1 },
  last_update: "2026-06-28T10:00:00Z",
};

// Fulfill every REST call the dashboard makes on load. Shapes mirror src/api.ts.
async function mockBackend(page: import("@playwright/test").Page) {
  await page.route("**/api/**", async (route) => {
    const path = new URL(route.request().url()).pathname;
    const json = (() => {
      if (path.endsWith("/api/events")) return { events: INIT_EVENTS };
      if (path.endsWith("/api/stats")) return STATS;
      if (path.endsWith("/api/dates")) return { dates: [] };
      if (path.endsWith("/api/correlations")) return { correlations: [] };
      if (path.endsWith("/api/health"))
        return { status: "ok", db: true, llm: false, sources: [] };
      if (path.endsWith("/api/markets")) return { tickers: [] };
      if (path.endsWith("/api/crypto")) return { coins: [] };
      if (path.endsWith("/api/feeds")) return { feeds: [] };
      if (path.endsWith("/api/accuracy"))
        return { total: 0, scored: 0, hits: 0, hit_rate: 0, by_verdict: {}, equity_curve: [] };
      return {};
    })();
    await route.fulfill({ json });
  });

  // Mock the WebSocket entirely (no real server): push `init`, then a `new_events`
  // frame after the initial REST load has surely settled, to exercise live update.
  await page.routeWebSocket("**/api/ws", (ws) => {
    ws.send(JSON.stringify({ type: "init", events: INIT_EVENTS, stats: STATS }));
    setTimeout(() => {
      ws.send(
        JSON.stringify({
          type: "new_events",
          events: [NEW_EVENT],
          stats: { ...STATS, total_events: 3 },
        }),
      );
    }, 1200);
  });
}

test.beforeEach(async ({ page }) => {
  await mockBackend(page);
  await page.goto("/app/");
});

test("dashboard shell + globe panel render", async ({ page }) => {
  // Shell mounted with the expected panels.
  await expect(page.locator(".panel-head", { hasText: "Signal Feed" })).toBeVisible();
  await expect(page.locator(".panel-head", { hasText: "Globe" })).toBeVisible();
  // globe.gl lazy-loads three.js and mounts a WebGL canvas (SwiftShader in headless).
  await expect(page.locator("section.panel canvas").first()).toBeVisible({ timeout: 20_000 });
});

test("event → ticker flow: feed row opens modal with tickers", async ({ page }) => {
  const feed = page.locator("table.feed");
  await expect(feed).toBeVisible();
  // Row carries its tickers in the table.
  const row = feed.locator("tr", { hasText: "Chip export controls" });
  await expect(row).toContainText("AAPL");
  await row.click();
  // Modal opens and shows the same tickers + affected entity.
  const modal = page.locator(".modal-overlay:not(.hidden)");
  await expect(modal).toBeVisible();
  await expect(modal).toContainText("AAPL");
  await expect(modal).toContainText("Apple");
});

test("WS update: new_events frame appends a row live", async ({ page }) => {
  const rows = page.locator("table.feed tbody tr");
  await expect(rows).toHaveCount(2); // INIT_EVENTS
  // The mocked socket pushes a third event ~1.2s in.
  await expect(rows).toHaveCount(3);
  await expect(page.locator("table.feed")).toContainText("central bank surprise hike");
});
