// Product panels fed by the API. Each exposes update()/load() that fills its body.

import {
  type Accuracy,
  api,
  type Correlation,
  type CryptoCoin,
  type DateCount,
  type MarketTicker,
  type Portfolio,
  type Sentiment,
} from "../api";
import { CHANNELS, embedUrl } from "../data/channels";
import { escapeHtml, fmtPct } from "../util";
import { Panel } from "./panel";

export class CorrelationPanel extends Panel {
  constructor() {
    super({ id: "correlations", title: "Correlations", col: 1, row: 5, w: 4, h: 3 });
  }
  update(signals: Correlation[]): void {
    if (!signals.length) {
      this.setContent('<p class="empty">No correlation signals yet.</p>');
      return;
    }
    const rows = signals
      .map((s) => {
        const id = escapeHtml(String(s.payload?.id ?? ""));
        return `<li><b>${escapeHtml(s.signal_type)}</b> · ${Math.round(s.confidence * 100)}%<br><span class="muted">${id}</span></li>`;
      })
      .join("");
    this.setContent(`<ul class="corr-list">${rows}</ul>`);
  }
}

export class MarketsPanel extends Panel {
  constructor() {
    super({ id: "markets", title: "Most-mentioned tickers", col: 5, row: 5, w: 4, h: 3 });
  }
  async load(): Promise<void> {
    try {
      this.render(await api.markets(25));
    } catch {
      this.setContent('<p class="empty">Markets unavailable.</p>');
    }
  }
  private render(tickers: MarketTicker[]): void {
    if (!tickers.length) return this.setContent('<p class="empty">No tickers yet.</p>');
    const rows = tickers
      .map(
        (t) =>
          `<tr><td>${escapeHtml(t.ticker)}</td><td>${t.mentions}</td><td>${t.avg_score >= 0 ? "+" : ""}${t.avg_score}</td></tr>`,
      )
      .join("");
    this.setContent(
      `<table class="feed"><thead><tr><th>Ticker</th><th>Mentions</th><th>Avg</th></tr></thead><tbody>${rows}</tbody></table>`,
    );
  }
}

export class CryptoPanel extends Panel {
  constructor() {
    super({ id: "crypto", title: "Crypto", col: 9, row: 5, w: 4, h: 3 });
  }
  async load(): Promise<void> {
    try {
      this.render(await api.crypto(20));
    } catch {
      this.setContent('<p class="empty">Crypto unavailable.</p>');
    }
  }
  private render(coins: CryptoCoin[]): void {
    if (!coins.length) return this.setContent('<p class="empty">No crypto data.</p>');
    const rows = coins
      .map((c) => {
        const cls = (c.change_24h ?? 0) >= 0 ? "up" : "down";
        return `<tr><td>${escapeHtml(c.symbol)}</td><td>$${c.price ?? "—"}</td><td class="${cls}">${fmtPct(c.change_24h)}</td></tr>`;
      })
      .join("");
    this.setContent(
      `<table class="feed"><thead><tr><th>Sym</th><th>Price</th><th>24h</th></tr></thead><tbody>${rows}</tbody></table>`,
    );
  }
}

export class CalendarPanel extends Panel {
  constructor(private readonly onPick: (day: string) => void) {
    super({ id: "calendar", title: "Dates", col: 1, row: 8, w: 4, h: 2 });
  }
  update(dates: DateCount[]): void {
    if (!dates.length) return this.setContent('<p class="empty">No dates.</p>');
    const items = dates
      .map(
        (d) =>
          `<button class="day" data-day="${d.day}">${d.day} <span class="muted">(${d.count})</span></button>`,
      )
      .join("");
    const wrap = document.createElement("div");
    wrap.className = "cal";
    wrap.innerHTML = items;
    wrap.addEventListener("click", (e) => {
      const t = e.target as HTMLElement;
      const day = t.closest<HTMLElement>(".day")?.dataset.day;
      if (day) this.onPick(day);
    });
    this.setContent(wrap);
  }
}

export class WorldNewsPanel extends Panel {
  private feedKey = "reuters_world_gnews";
  constructor() {
    super({ id: "worldnews", title: "World News", col: 5, row: 8, w: 4, h: 2 });
  }
  async load(): Promise<void> {
    try {
      const res = await api.rss(this.feedKey, 15);
      const rows = res.items
        .map(
          (i) =>
            `<li><a href="${escapeHtml(i.link)}" target="_blank" rel="noopener">${escapeHtml(i.title)}</a></li>`,
        )
        .join("");
      this.setContent(
        rows ? `<ul class="news">${rows}</ul>` : '<p class="empty">No items.</p>',
      );
    } catch {
      this.setContent('<p class="empty">News unavailable.</p>');
    }
  }
}

export class AccuracyPanel extends Panel {
  constructor() {
    super({ id: "accuracy", title: "Accuracy", col: 1, row: 10, w: 5, h: 3 });
  }
  async load(): Promise<void> {
    try {
      this.render(await api.accuracy());
    } catch {
      this.setContent('<p class="empty">Accuracy unavailable.</p>');
    }
  }
  private render(a: Accuracy): void {
    if (!a.scored) {
      this.setContent('<p class="empty">No scored outcomes yet (run the backtest).</p>');
      return;
    }
    const pct = Math.round(a.hit_rate * 100);
    const byV = Object.entries(a.by_verdict)
      .map(
        ([v, b]) =>
          `<li>${escapeHtml(v)}: <b>${Math.round(b.hit_rate * 100)}%</b> <span class="muted">(${b.hits}/${b.total})</span></li>`,
      )
      .join("");
    const wrap = document.createElement("div");
    wrap.className = "acc";
    wrap.innerHTML =
      `<div class="acc-big">${pct}%<span class="muted"> hit-rate · ${a.hits}/${a.scored}</span></div>` +
      `<ul class="acc-by">${byV}</ul>` +
      sparkline(a.equity_curve);
    this.setContent(wrap);
  }
}

/** Tiny inline-SVG equity curve. */
function sparkline(curve: number[]): string {
  if (curve.length < 2) return "";
  const w = 240;
  const h = 48;
  const min = Math.min(...curve, 0);
  const max = Math.max(...curve, 0);
  const span = max - min || 1;
  const pts = curve
    .map((y, i) => {
      const x = (i / (curve.length - 1)) * w;
      const yy = h - ((y - min) / span) * h;
      return `${x.toFixed(1)},${yy.toFixed(1)}`;
    })
    .join(" ");
  return `<svg class="spark" viewBox="0 0 ${w} ${h}" preserveAspectRatio="none"><polyline points="${pts}" fill="none" stroke="#16c784" stroke-width="2"/></svg>`;
}

export class SentimentPanel extends Panel {
  private ticker = "AAPL";
  constructor() {
    super({ id: "sentiment", title: "Social Sentiment", col: 5, row: 10, w: 4, h: 3 });
  }
  async load(): Promise<void> {
    const wrap = document.createElement("div");
    wrap.className = "senti";
    wrap.innerHTML =
      `<form class="senti-form"><input class="senti-tk" value="${escapeHtml(this.ticker)}" maxlength="10" />` +
      `<button type="submit">Load</button></form><div class="senti-body"><p class="muted">Enter a ticker.</p></div>`;
    const body = wrap.querySelector<HTMLElement>(".senti-body")!;
    const input = wrap.querySelector<HTMLInputElement>(".senti-tk")!;
    wrap.querySelector("form")!.addEventListener("submit", (e) => {
      e.preventDefault();
      this.ticker = input.value.toUpperCase().trim() || this.ticker;
      void this.fetch(body, this.ticker);
    });
    this.setContent(wrap);
    void this.fetch(body, this.ticker);
  }
  private async fetch(body: HTMLElement, ticker: string): Promise<void> {
    body.innerHTML = '<p class="muted">Loading…</p>';
    try {
      this.render(body, await api.sentiment(ticker));
    } catch {
      body.innerHTML = '<p class="empty">Sentiment unavailable.</p>';
    }
  }
  private render(body: HTMLElement, s: Sentiment): void {
    if (!s.total_posts) {
      body.innerHTML = `<p class="empty">No social posts for ${escapeHtml(s.ticker)}.</p>`;
      return;
    }
    const cls = s.sentiment_score >= 0 ? "up" : "down";
    const posts = s.top_posts
      .slice(0, 5)
      .map(
        (p) =>
          `<li><a href="${escapeHtml(p.url)}" target="_blank" rel="noopener">${escapeHtml(p.text.slice(0, 90))}</a> <span class="muted">${escapeHtml(p.platform)}</span></li>`,
      )
      .join("");
    body.innerHTML =
      `<div class="senti-score ${cls}">${s.sentiment_score >= 0 ? "+" : ""}${s.sentiment_score.toFixed(2)}` +
      ` <span class="muted">${Math.round(s.bullish_pct * 100)}% bullish · ${s.total_posts} posts${s.volume_spike ? " · 🔥 spike" : ""}</span></div>` +
      `<div class="muted">bull ${s.bullish_count} · bear ${s.bearish_count} · neut ${s.neutral_count} · ${escapeHtml(s.platforms.join(", ") || "—")}</div>` +
      `<ul class="news">${posts}</ul>`;
  }
}

export class PortfolioPanel extends Panel {
  constructor() {
    super({ id: "portfolio", title: "Portfolio", col: 9, row: 10, w: 4, h: 3 });
  }
  async load(): Promise<void> {
    try {
      this.render(await api.portfolio());
    } catch {
      this.setContent('<p class="empty">Portfolio unavailable.</p>');
    }
  }
  private render(p: Portfolio): void {
    const positions = p.positions.length
      ? p.positions
          .map(
            (pos) =>
              `<tr><td>${escapeHtml(pos.ticker)}</td><td>${pos.shares}</td><td>$${pos.avg_cost}</td></tr>`,
          )
          .join("")
      : '<tr><td colspan="3" class="muted">No positions.</td></tr>';
    const watch = p.watchlists.length
      ? p.watchlists
          .map(
            (w) =>
              `<li><b>${escapeHtml(w.name)}</b>: ${escapeHtml((w.tickers || []).join(", ")) || "—"}</li>`,
          )
          .join("")
      : '<li class="muted">No watchlists.</li>';
    this.setContent(
      `<table class="feed"><thead><tr><th>Ticker</th><th>Shares</th><th>Cost</th></tr></thead><tbody>${positions}</tbody></table>` +
        `<ul class="news">${watch}</ul>`,
    );
  }
}

export class LiveTVPanel extends Panel {
  constructor() {
    super({ id: "livetv", title: "Live TV", col: 9, row: 8, w: 4, h: 2 });
  }
  render(): void {
    const tabs = CHANNELS.map(
      (c, i) => `<button class="tv-tab" data-i="${i}">${escapeHtml(c.name)}</button>`,
    ).join("");
    const wrap = document.createElement("div");
    wrap.className = "tv";
    wrap.innerHTML = `<div class="tv-tabs">${tabs}</div><iframe class="tv-frame" allowfullscreen src="${embedUrl(CHANNELS[0].channelId)}"></iframe>`;
    wrap.addEventListener("click", (e) => {
      const i = (e.target as HTMLElement).closest<HTMLElement>(".tv-tab")?.dataset.i;
      if (i != null) {
        const frame = wrap.querySelector<HTMLIFrameElement>(".tv-frame");
        if (frame) frame.src = embedUrl(CHANNELS[Number(i)].channelId);
      }
    });
    this.setContent(wrap);
  }
}
