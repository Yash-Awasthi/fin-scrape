import { describe, expect, it, vi } from "vitest";

import { PAGE_LAYOUT } from "../app/variants";
import { PanelLayoutManager } from "./layout";
import { Panel } from "./panel";

const panel = (id: string) => new Panel({ id, title: id, w: 6, h: 2 });

describe("PAGE_LAYOUT", () => {
  it("lists each panel exactly once", () => {
    const ids = PAGE_LAYOUT.map((s) => s.id);
    expect(ids).toHaveLength(new Set(ids).size);
  });

  it("fills whole 12-column rows", () => {
    // Bands lay out in order; a band that does not sum to 12 leaves a ragged gap.
    let row = 0;
    for (const slot of PAGE_LAYOUT) {
      expect(slot.w).toBeGreaterThan(0);
      expect(slot.w).toBeLessThanOrEqual(12);
      row = (row + slot.w) % 12;
    }
    expect(row).toBe(0);
  });
});

describe("applyVariant", () => {
  it("shows the listed panels and hides the rest", () => {
    const layout = new PanelLayoutManager();
    layout.add(panel("a"));
    layout.add(panel("b"));
    layout.applyVariant([{ id: "a", w: 6, h: 2 }]);
    expect(layout.get("a")!.el.style.display).toBe("");
    expect(layout.get("b")!.el.style.display).toBe("none");
  });

  it("warns about a registered panel the layout forgot", () => {
    const warn = vi.spyOn(console, "warn").mockImplementation(() => {});
    const layout = new PanelLayoutManager();
    layout.add(panel("shown"));
    layout.add(panel("forgotten"));
    layout.applyVariant([{ id: "shown", w: 12, h: 2 }]);
    expect(warn).toHaveBeenCalledWith(expect.stringContaining("forgotten"));
    warn.mockRestore();
  });

  it("warns about a slot naming a panel that does not exist", () => {
    const warn = vi.spyOn(console, "warn").mockImplementation(() => {});
    const layout = new PanelLayoutManager();
    layout.add(panel("real"));
    layout.applyVariant([
      { id: "real", w: 6, h: 2 },
      { id: "ghost", w: 6, h: 2 },
    ]);
    expect(warn).toHaveBeenCalledWith(expect.stringContaining("ghost"));
    warn.mockRestore();
  });
});
