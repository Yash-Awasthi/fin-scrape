import { beforeEach, describe, expect, it } from "vitest";
import { loadConfig, type PanelConfig, saveConfig } from "./panel";

const base: PanelConfig = { id: "t", title: "T", col: 1, row: 1, w: 4, h: 3 };

describe("panel config persistence", () => {
  beforeEach(() => localStorage.clear());

  it("returns fallback when nothing saved", () => {
    expect(loadConfig("t", base)).toEqual(base);
  });

  it("round-trips saved size/position and keeps id", () => {
    saveConfig({ ...base, w: 6, h: 5, col: 3 });
    const loaded = loadConfig("t", base);
    expect(loaded).toMatchObject({ id: "t", w: 6, h: 5, col: 3 });
  });

  it("falls back on corrupt storage", () => {
    localStorage.setItem("worldfin.panel.t", "{not json");
    expect(loadConfig("t", base)).toEqual(base);
  });
});
