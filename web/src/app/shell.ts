// App shell: header (brand, live clock, connection dot, refresh) + banner slot.

import type { WSStatus } from "../ws";

export class Shell {
  readonly root: HTMLElement;
  readonly content: HTMLElement;
  readonly bannerSlot: HTMLElement;
  private dot: HTMLElement;
  private clock: HTMLElement;

  constructor(onRefresh: () => void) {
    this.root = document.createElement("div");
    this.root.className = "app";

    const header = document.createElement("header");
    header.className = "app-head";

    const brand = document.createElement("div");
    brand.className = "brand";
    brand.textContent = "WorldFin";

    this.clock = document.createElement("time");
    this.clock.className = "clock";

    this.dot = document.createElement("span");
    this.dot.className = "conn-dot";
    this.dot.title = "realtime connection";

    const refresh = document.createElement("button");
    refresh.className = "refresh";
    refresh.textContent = "↻";
    refresh.title = "refresh";
    refresh.addEventListener("click", onRefresh);

    const left = document.createElement("div");
    left.className = "head-left";
    left.append(brand);

    const right = document.createElement("div");
    right.className = "head-right";
    right.append(this.clock, this.dot, refresh);
    header.append(left, right);

    this.bannerSlot = document.createElement("div");
    this.bannerSlot.className = "banner-slot";

    this.content = document.createElement("main");
    this.content.className = "app-main";

    this.root.append(header, this.bannerSlot, this.content);
    this.startClock();
    this.installPalette();
  }

  setConnection(status: WSStatus): void {
    this.dot.dataset.status = status;
  }

  private startClock(): void {
    const tick = () => {
      this.clock.textContent = new Date().toUTCString().slice(17, 25) + " UTC";
    };
    tick();
    setInterval(tick, 1000);
  }

  // ⌘K / Ctrl+K opens a stub command palette (wired to actions in a later phase).
  private installPalette(): void {
    const overlay = document.createElement("div");
    overlay.className = "palette hidden";
    const input = document.createElement("input");
    input.placeholder = "Command palette (coming soon)…";
    overlay.append(input);
    this.root.append(overlay);

    window.addEventListener("keydown", (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        overlay.classList.toggle("hidden");
        if (!overlay.classList.contains("hidden")) input.focus();
      } else if (e.key === "Escape") {
        overlay.classList.add("hidden");
      }
    });
  }

  mount(parent: HTMLElement): void {
    parent.append(this.root);
  }
}
