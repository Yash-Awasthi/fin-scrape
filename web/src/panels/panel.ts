// Panel base: a titled grid cell with a debounced body.
// Deterministic layout — position comes from the variant's panel order and the
// panel's declared span; no freeform dragging or persisted overrides.

export interface PanelConfig {
  id: string;
  title: string;
  w: number; // column span (of the 12-col grid)
  h: number; // row span
}

export class Panel {
  readonly el: HTMLElement;
  readonly body: HTMLElement;
  readonly cfg: PanelConfig;
  private pending: number | null = null;

  constructor(defaults: PanelConfig) {
    this.cfg = defaults;

    this.el = document.createElement("section");
    this.el.className = "panel";
    this.el.dataset.id = this.cfg.id;

    const header = document.createElement("header");
    header.className = "panel-head";
    header.textContent = this.cfg.title;

    this.body = document.createElement("div");
    this.body.className = "panel-body";

    this.el.append(header, this.body);
    this.applyGrid();
  }

  applyGrid(): void {
    const { w, h } = this.cfg;
    this.el.style.gridColumn = `span ${Math.min(w, 12)}`;
    this.el.style.gridRow = `span ${h}`;
  }

  /** Debounced so rapid live updates coalesce into one paint. */
  setContent(node: Node | string): void {
    if (this.pending !== null) cancelAnimationFrame(this.pending);
    this.pending = requestAnimationFrame(() => {
      this.body.replaceChildren();
      if (typeof node === "string") this.body.innerHTML = node;
      else this.append(node);
      this.pending = null;
    });
  }

  private append(node: Node): void {
    this.body.append(node);
  }
}
