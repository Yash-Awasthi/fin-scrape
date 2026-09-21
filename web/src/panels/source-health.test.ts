import { describe, expect, it, vi } from "vitest";

import * as apiModule from "../api";
import { api, type HealthResponse } from "../api";
import { timeAgo } from "../util";
import { SourceHealthPanel } from "./panels";

// setContent paints on the next animation frame.
const painted = () => new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)));

const health = (sources: HealthResponse["sources"], db = true): HealthResponse => ({
  status: db ? "ok" : "degraded",
  db,
  llm: false,
  sources,
});

describe("timeAgo", () => {
  const now = Date.parse("2026-01-02T12:00:00Z");

  it("renders compact ages", () => {
    expect(timeAgo("2026-01-02T11:59:30Z", now)).toBe("30s");
    expect(timeAgo("2026-01-02T11:40:00Z", now)).toBe("20m");
    expect(timeAgo("2026-01-02T09:00:00Z", now)).toBe("3h");
    expect(timeAgo("2025-12-31T12:00:00Z", now)).toBe("2d");
  });

  it("never throws on missing or unparseable input", () => {
    expect(timeAgo(null, now)).toBe("never");
    expect(timeAgo("not a date", now)).toBe("never");
  });
});

describe("SourceHealthPanel", () => {
  it("surfaces a failing source above healthy ones", async () => {
    vi.spyOn(api, "health").mockResolvedValue(
      health([
        { source: "world_rss", status: "OK", fetched_at: null, record_count: 12 },
        { source: "gdelt", status: "WARN", fetched_at: null, record_count: 0 },
        { source: "usgs_quakes", status: "STALE", fetched_at: null, record_count: 3 },
      ]),
    );
    const panel = new SourceHealthPanel();
    await panel.load();
    await painted();

    const names = [...panel.body.querySelectorAll("b")].map((b) => b.textContent);
    expect(names).toEqual(["gdelt", "usgs_quakes", "world_rss"]); // worst first
    expect(panel.body.querySelector(".src-dot.bad")).not.toBeNull();
    expect(panel.body.textContent).toContain("failing");
  });

  it("reports an unreachable database as its own row", async () => {
    vi.spyOn(api, "health").mockResolvedValue(health([], false));
    const panel = new SourceHealthPanel();
    await panel.load();
    await painted();
    expect(panel.body.textContent).toContain("unreachable");
  });

  it("degrades to a message instead of throwing when the endpoint is down", async () => {
    vi.spyOn(api, "health").mockRejectedValue(new Error("502"));
    const panel = new SourceHealthPanel();
    await panel.load();
    await painted();
    expect(panel.body.textContent).toContain("Health unavailable");
  });
});

describe("AlertsPanel", () => {
  it("names the deployment gap on 404 rather than reporting a failure", async () => {
    const { AlertsPanel } = await import("./panels");
    vi.spyOn(apiModule, "getJSON").mockRejectedValue(new Error("GET /api/alerts → 404"));
    const panel = new AlertsPanel();
    await panel.load();
    await painted();
    expect(panel.body.textContent).toContain("Telegram");
  });

  it("still reports a real failure as a failure", async () => {
    const { AlertsPanel } = await import("./panels");
    vi.spyOn(apiModule, "getJSON").mockRejectedValue(new Error("GET /api/alerts → 500"));
    const panel = new AlertsPanel();
    await panel.load();
    await painted();
    expect(panel.body.textContent).toContain("Alerts unavailable");
  });
});
