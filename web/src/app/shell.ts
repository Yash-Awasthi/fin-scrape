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

  // ⌘K / Ctrl+K palette: chart any symbol, run agent analysis on it.
  private installPalette(): void {
    const overlay = document.createElement("div");
    overlay.className = "palette hidden";
    const input = document.createElement("input");
    input.placeholder = "chart AAPL · analyze NVDA · goto 600519.SS …";
    const results = document.createElement("div");
    results.className = "palette-results";
    overlay.append(input, results);

    const run = (raw: string): void => {
      const cmd = raw.trim();
      if (!cmd) return;
      overlay.classList.add("hidden");
      input.value = "";
      const [verb, ...rest] = cmd.split(/\s+/);
      const arg = rest.join(" ").toUpperCase();
      const lower = verb.toLowerCase();
      if (lower === "chart" && arg) {
        window.dispatchEvent(new CustomEvent("worldfin:select-symbol", { detail: arg }));
        document.querySelector<HTMLElement>('.panel[data-id="candles"]')?.scrollIntoView({ behavior: "smooth" });
      } else if (lower === "analyze" && arg) {
        window.dispatchEvent(new CustomEvent("worldfin:analyze-symbol", { detail: arg }));
        document.querySelector<HTMLElement>('.panel[data-id="agents"]')?.scrollIntoView({ behavior: "smooth" });
      } else if (lower === "goto" && arg) {
        // jump to first event mentioning the term
        window.dispatchEvent(new CustomEvent("worldfin:search-events", { detail: rest.join(" ").toLowerCase() }));
      } else {
        window.dispatchEvent(new CustomEvent("worldfin:search-events", { detail: cmd.toLowerCase() }));
      }
    };

    // live suggestions from the events store
    const suggest = (): void => {
      const q = input.value.toLowerCase().trim();
      const events = (window as unknown as { __wfEvents?: Array<{ subject: string; tickers: string[] }> }).__wfEvents ?? [];
      const hits = events
        .filter((e) => !q || e.subject.toLowerCase().includes(q))
        .slice(0, 6)
        .map((e) => `<div class="palette-item">▸ ${e.subject.slice(0, 70)}</div>`)
        .join("");
      results.innerHTML = hits;
    };
    input.addEventListener("input", suggest);
    input.addEventListener("keydown", (e) => {
      if (e.key === "Enter") run(input.value);
    });

    this.root.append(overlay);
    window.addEventListener("keydown", (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        overlay.classList.toggle("hidden");
        if (!overlay.classList.contains("hidden")) {
          input.focus();
          input.select();
          suggest();
        }
      } else if (e.key === "Escape") {
        overlay.classList.add("hidden");
      }
    });
  }

  mount(parent: HTMLElement): void {
    parent.append(this.root);
  }
}
