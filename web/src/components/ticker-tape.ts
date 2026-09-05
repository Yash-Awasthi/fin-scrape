// Ticker tape — the always-on live quote strip under the header.
// Polls /api/quotes every TICK_MS; pauses scrolling on hover.

import { api, type Quote } from "../api";

const TICK_MS = 15_000;

const DEFAULT_SYMBOLS = [
  "^GSPC", "NVDA", "AAPL", "MSFT", "JPM",
  "RELIANCE.NS", "^NSEI",
  "600519.SS", "000001.SS",
  "^FTSE", "^GDAXI", "^N225", "^HSI",
];

export class TickerTape {
  readonly el: HTMLElement;
  private quotes: Quote[] = [];
  private timer: number | null = null;
  private symbols: string[];

  constructor(symbols: string[] = DEFAULT_SYMBOLS) {
    this.symbols = symbols;
    this.el = document.createElement("div");
    this.el.className = "tape";
    this.el.title = "live market tape — 15s refresh (hover to pause)";
    void this.refresh();
    this.timer = window.setInterval(() => void this.refresh(), TICK_MS);
  }

  setSymbols(symbols: string[]): void {
    this.symbols = symbols;
    void this.refresh();
  }

  stop(): void {
    if (this.timer !== null) window.clearInterval(this.timer);
    this.timer = null;
  }

  async refresh(): Promise<void> {
    try {
      this.quotes = await api.quotes(this.symbols);
      this.render();
    } catch {
      // stale tape stays visible; never blank on a network blip
    }
  }

  private render(): void {
    if (!this.quotes.length) return;
    const items = this.quotes.map((q) => {
      const up = (q.change_pct ?? 0) > 0;
      const down = (q.change_pct ?? 0) < 0;
      const cls = up ? "up" : down ? "down" : "flat";
      const arrow = up ? "▲" : down ? "▼" : "·";
      const change = q.change_pct == null ? "—" : `${q.change_pct >= 0 ? "+" : ""}${q.change_pct.toFixed(2)}%`;
      const price = q.price == null ? "—" : q.price >= 1000 ? q.price.toFixed(0) : q.price.toFixed(2);
      return `<span class="tape-item ${cls}"><b>${q.symbol}</b> ${price} ${arrow} ${change}</span>`;
    });
    // doubled content → seamless CSS marquee loop
    this.el.innerHTML = `<div class="tape-track">${items.join("")}${items.join("")}</div>`;
  }
}
