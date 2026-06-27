// PanelLayoutManager: a CSS-grid host that mounts panels at their saved positions.

import { Panel } from "./panel";

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

  /** Show only the panels whose id is in `ids`; hide the rest (variant switch). */
  applyVariant(ids: string[]): void {
    const want = new Set(ids);
    for (const [id, panel] of this.panels) {
      panel.el.style.display = want.has(id) ? "" : "none";
    }
  }

  mount(parent: HTMLElement): void {
    parent.append(this.el);
  }
}
