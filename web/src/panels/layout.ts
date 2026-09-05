// PanelLayoutManager: a deterministic CSS-grid host.
// Variant switch shows exactly the requested panels, in that order, each
// spanning its declared w/h — no freeform dragging, no persisted overrides.

import { Panel } from "./panel";
import type { PanelSlot } from "../app/variants";

export class PanelLayoutManager {
  readonly el: HTMLElement;
  private panels = new Map<string, Panel>();

  constructor(columns = 12) {
    this.el = document.createElement("div");
    this.el.className = "panel-grid";
    this.el.style.setProperty("--cols", String(columns));
  }

  add(panel: Panel): Panel {
    this.panels.set(panel.cfg.id, panel);
    this.el.append(panel.el);
    return panel;
  }

  get(id: string): Panel | undefined {
    return this.panels.get(id);
  }

  /** Show only the listed panels — in order, spanning the exact w/h the variant
   *  prescribes. Deterministic: same variant, same layout, every time. */
  applyVariant(slots: PanelSlot[]): void {
    const want = new Set(slots.map((s) => s.id));
    let order = 0;
    for (const slot of slots) {
      const panel = this.panels.get(slot.id);
      if (!panel) continue;
      panel.el.style.display = "";
      panel.el.style.order = String(order++);
      panel.el.style.gridColumn = `span ${Math.min(slot.w, 12)}`;
      panel.el.style.gridRow = `span ${slot.h}`;
    }
    for (const [id, panel] of this.panels) {
      if (!want.has(id)) panel.el.style.display = "none";
    }
  }

  mount(parent: HTMLElement): void {
    parent.append(this.el);
  }
}
