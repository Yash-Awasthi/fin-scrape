// Panel base: a titled grid cell with a debounced body and persisted size/position.

export interface PanelConfig {
  id: string;
  title: string;
  col: number; // grid column start (1-based)
  row: number; // grid row start (1-based)
  w: number; // column span
  h: number; // row span
}

const LS_PREFIX = "worldfin.panel.";

export function loadConfig(id: string, fallback: PanelConfig): PanelConfig {
  try {
    const raw = localStorage.getItem(LS_PREFIX + id);
    if (raw) return { ...fallback, ...(JSON.parse(raw) as Partial<PanelConfig>), id };
  } catch {
    /* corrupt entry → fall back */
  }
  return fallback;
}

export function saveConfig(cfg: PanelConfig): void {
  try {
    localStorage.setItem(LS_PREFIX + cfg.id, JSON.stringify(cfg));
  } catch {
    /* storage full / disabled → in-memory only */
  }
}

export class Panel {
  readonly el: HTMLElement;
  readonly body: HTMLElement;
  cfg: PanelConfig;
  private pending: number | null = null;

  constructor(defaults: PanelConfig) {
    this.cfg = loadConfig(defaults.id, defaults);

    this.el = document.createElement("section");
    this.el.className = "panel";
    this.el.dataset.id = this.cfg.id;

    const header = document.createElement("header");
    header.className = "panel-head";
    header.textContent = this.cfg.title;

    this.body = document.createElement("div");
    this.body.className = "panel-body";

    const handle = document.createElement("div");
    handle.className = "panel-resize";
    handle.addEventListener("pointerdown", (e) => this.beginResize(e));

    this.el.append(header, this.body, handle);
    this.applyGrid();
  }

  applyGrid(): void {
    const { col, row, w, h } = this.cfg;
    this.el.style.gridColumn = `${col} / span ${w}`;
    this.el.style.gridRow = `${row} / span ${h}`;
  }

  /** Debounced so rapid live updates coalesce into one paint. */
  setContent(node: Node | string): void {
    if (this.pending !== null) cancelAnimationFrame(this.pending);
    this.pending = requestAnimationFrame(() => {
      this.body.replaceChildren();
      if (typeof node === "string") this.body.innerHTML = node;
      else this.body.append(node);
      this.pending = null;
    });
  }

  private beginResize(e: PointerEvent): void {
    e.preventDefault();
    const startX = e.clientX;
    const startY = e.clientY;
    const startW = this.cfg.w;
    const startH = this.cfg.h;
    const cell = 80; // px per grid track (approx; snaps on move)

    const move = (ev: PointerEvent) => {
      this.cfg.w = Math.max(1, startW + Math.round((ev.clientX - startX) / cell));
      this.cfg.h = Math.max(1, startH + Math.round((ev.clientY - startY) / cell));
      this.applyGrid();
    };
    const up = () => {
      saveConfig(this.cfg);
      window.removeEventListener("pointermove", move);
      window.removeEventListener("pointerup", up);
    };
    window.addEventListener("pointermove", move);
    window.addEventListener("pointerup", up);
  }
}
