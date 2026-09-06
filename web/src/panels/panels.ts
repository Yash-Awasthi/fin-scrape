// Product panels fed by the API. Each exposes update()/load() that fills its body.

import {
  type Accuracy,
  api,
  type Correlation,
  type DashboardStats,
  type DateCount,
  type FeedInfo,
  type MarketTicker,
  type Portfolio,
  type RssItem,
  type Sentiment,
  type Suggestion,
} from "../api";
import { CHANNELS, countries, embedUrl } from "../data/channels";
import { escapeHtml } from "../util";
import { type Candle, type Prediction, type Quote } from "../api";
import { getJSON } from "../api";
import { verdictColor } from "../api";
import { Panel } from "./panel";

export class CorrelationPanel extends Panel {
  constructor() {
    super({ id: "correlations", title: "Correlations", w: 4, h: 3 });
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
    super({ id: "markets", title: "Most-mentioned tickers", w: 4, h: 3 });
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

export class StatsPanel extends Panel {
  constructor() {
    super({ id: "stats", title: "Stats", w: 4, h: 3 });
  }
  update(stats: DashboardStats): void {
    const verdicts = Object.entries(stats.by_verdict);
    const max = Math.max(1, ...verdicts.map(([, n]) => n));
    const bars = verdicts
      .map(([verdict, n]) => {
        const color = verdictColor(verdict);
        return (
          `<div class="stat-row"><span class="stat-label">${escapeHtml(verdict)}</span>` +
          `<span class="stat-bar"><i style="width:${Math.round((n / max) * 100)}%;background:${color}"></i></span>` +
          `<span class="stat-n">${n}</span></div>`
        );
      })
      .join("");
    const updated = stats.last_update ? new Date(stats.last_update).toLocaleTimeString() : "—";
    this.setContent(
      `<div class="stat-total">${stats.total_events}<span class="muted"> events · updated ${escapeHtml(updated)}</span></div>` +
        (bars || '<p class="empty">No verdicts yet.</p>'),
    );
  }
}

export class SuggestionsPanel extends Panel {
  constructor() {
    super({ id: "suggestions", title: "Suggestions", w: 4, h: 3 });
  }
  async load(): Promise<void> {
    try {
      this.render(await api.suggestions(10));
    } catch {
      this.setContent('<p class="empty">Suggestions unavailable.</p>');
    }
  }
  private render(sugs: Suggestion[]): void {
    if (!sugs.length) return this.setContent('<p class="empty">No suggestions yet — ingest more events.</p>');
    const rows = sugs
      .map((s) => {
        const color = s.latest_verdict ? verdictColor(s.latest_verdict) : "#8a8f98";
        return (
          `<div class="sug-row">` +
          `<span class="sug-dot" style="background:${color}"></span>` +
          `<b>${escapeHtml(s.ticker)}</b>` +
          `<span class="muted">${s.mentions} events · avg ${s.avg_score >= 0 ? "+" : ""}${s.avg_score}` +
          ` · trust ${Math.round(s.trust * 100)}%</span>` +
          `<span class="sug-score">+${s.score.toFixed(1)}</span>` +
          (s.latest_subject ? `<div class="muted sug-sub">${escapeHtml(s.latest_subject.slice(0, 80))}</div>` : "") +
          `</div>`
        );
      })
      .join("");
    this.setContent(`<div class="sug-list">${rows}</div>`);
  }
}

export class NewsLobbyPanel extends Panel {
  private feeds: FeedInfo[] = [];
  private activeFeed = "";
  constructor() {
    super({ id: "lobby", title: "News Lobby", w: 12, h: 4 });
  }
  async load(): Promise<void> {
    try {
      if (!this.feeds.length) {
        this.feeds = await api.feeds();
        this.activeFeed = this.feeds[0]?.key ?? "";
      }
      await this.renderFeed();
    } catch {
      this.setContent('<p class="empty">Lobby unavailable.</p>');
    }
  }
  private async renderFeed(): Promise<void> {
    const tabs = this.feeds
      .map(
        (f) =>
          `<button class="lobby-tab${f.key === this.activeFeed ? " active" : ""}" data-feed="${f.key}">` +
          `${escapeHtml(f.name)}</button>`,
      )
      .join("");
    const body = document.createElement("div");
    body.className = "lobby";
    body.innerHTML = `<div class="lobby-tabs">${tabs}</div><div class="lobby-body"><p class="muted">Loading…</p></div>`;
    body.addEventListener("click", (e) => {
      const feed = (e.target as HTMLElement).closest<HTMLElement>(".lobby-tab")?.dataset.feed;
      if (feed && feed !== this.activeFeed) {
        this.activeFeed = feed;
        void this.load();
      }
    });
    const list = body.querySelector<HTMLElement>(".lobby-body")!;
    this.setContent(body);
    try {
      const res = await api.rss(this.activeFeed, 30);
      list.innerHTML = this.renderItems(res.items);
    } catch {
      list.innerHTML = '<p class="empty">Feed unavailable.</p>';
    }
  }
  private renderItems(items: RssItem[]): string {
    if (!items.length) return '<p class="empty">No items.</p>';
    return (
      '<ul class="news lobby-list">' +
      items
        .map(
          (i) =>
            `<li><a href="${escapeHtml(i.link)}" target="_blank" rel="noopener">${escapeHtml(i.title)}</a>` +
            `<span class="muted lobby-time">${escapeHtml(i.published)}</span></li>`,
        )
        .join("") +
      "</ul>"
    );
  }
}

export class MarketsLivePanel extends Panel {
  private symbols = [
    // US
    "AAPL", "MSFT", "NVDA", "JPM", "XOM",
    // India
    "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS",
    // China
    "600519.SS", "601398.SS", "300750.SZ",
    // Europe
    "SHEL.L", "SAP.DE", "MC.PA", "ASML.AS",
    // Asia-Pacific
    "7203.T", "0700.HK", "005930.KS", "BHP.AX",
  ];

  constructor() {
    super({ id: "markets-live", title: "Markets Live", w: 8, h: 5 });
  }

  async load(): Promise<void> {
    await this.refresh();
  }

  async refresh(): Promise<void> {
    try {
      this.render(await api.quotes(this.symbols));
    } catch {
      // keep last known prices on the screen
    }
  }

  private render(quotes: Quote[]): void {
    const groups: Record<string, Quote[]> = { Americas: [], Asia: [], Europe: [] };
    for (const q of quotes) {
      groups[regionOf(q.symbol)].push(q);
    }
    const cards = Object.entries(groups)
      .filter(([, qs]) => qs.length)
      .map(
        ([region, qs]) =>
          `<div class="ml-region"><h4>${region}</h4><div class="ml-cards">` +
          qs.map((q) => quoteCard(q)).join("") +
          `</div></div>`,
      )
      .join("");
    this.setContent(
      cards ||
        '<p class="empty">No quotes yet — the quotes API needs a moment.</p>',
    );
  }
}

function quoteCard(q: Quote): string {
  const up = (q.change_pct ?? 0) > 0;
  const down = (q.change_pct ?? 0) < 0;
  const cls = up ? "up" : down ? "down" : "flat";
  const arrow = up ? "▲" : down ? "▼" : "·";
  const price = q.price == null ? "—" : q.price >= 1000 ? q.price.toFixed(0) : q.price.toFixed(2);
  const change = q.change_pct == null ? "—" : `${q.change_pct >= 0 ? "+" : ""}${q.change_pct.toFixed(2)}%`;
  return (
    `<div class="ml-card ml-click" data-sym="${escapeHtml(q.symbol)}"><div class="ml-sym">${escapeHtml(q.symbol)}</div>` +
    `<div class="ml-price">${price}</div>` +
    `<div class="ml-change ${cls}">${arrow} ${change}</div>` +
    `<div class="ml-src">${escapeHtml(q.source)}</div></div>`
  );
}

function regionOf(symbol: string): string {
  const suffix = symbol.includes(".") ? symbol.split(".").pop()! : "";
  if (["NS", "BO", "SS", "SZ", "HK", "T", "KS", "KQ", "TW", "SI", "AX", "JK", "BK"].includes(suffix)) return "Asia";
  if (["L", "DE", "PA", "AS", "BR", "MC", "MI", "SW", "SR", "IS"].includes(suffix)) return "Europe";
  return "Americas";
}

const WATCHLIST_KEY = "worldfin.watchlist";

export class WatchlistPanel extends Panel {
  private symbols: string[];

  constructor() {
    super({ id: "watchlist", title: "Watchlist", w: 4, h: 5 });
    try {
      this.symbols = JSON.parse(localStorage.getItem(WATCHLIST_KEY) ?? "[]");
    } catch {
      this.symbols = [];
    }
    if (!this.symbols.length) this.symbols = ["NVDA", "RELIANCE.NS", "600519.SS"];
  }

  private persist(): void {
    try {
      localStorage.setItem(WATCHLIST_KEY, JSON.stringify(this.symbols));
    } catch {
      /* ignore */
    }
  }

  async load(): Promise<void> {
    await this.refresh();
  }

  async refresh(): Promise<void> {
    if (!this.symbols.length) {
      this.setContent('<p class="empty">Add symbols: AAPL, RELIANCE.NS, 600519.SS …</p>');
      return;
    }
    try {
      const quotes = await api.quotes(this.symbols);
      this.render(quotes);
    } catch {
      // keep last known prices
    }
  }

  private render(quotes: Quote[]): void {
    const rows = quotes
      .map((q) => {
        const up = (q.change_pct ?? 0) > 0;
        const down = (q.change_pct ?? 0) < 0;
        const cls = up ? "up" : down ? "down" : "flat";
        const change = q.change_pct == null ? "—" : `${q.change_pct >= 0 ? "+" : ""}${q.change_pct.toFixed(2)}%`;
        const price = q.price == null ? "—" : q.price >= 1000 ? q.price.toFixed(0) : q.price.toFixed(2);
        return (
          `<tr><td>${escapeHtml(q.symbol)}</td><td>${price}</td>` +
          `<td class="${cls}">${change}</td>` +
          `<td><button class="wl-remove" data-sym="${escapeHtml(q.symbol)}" title="remove">×</button></td></tr>`
        );
      })
      .join("");
    const wrap = document.createElement("div");
    wrap.className = "watchlist";
    wrap.innerHTML =
      `<form class="wl-form"><input class="wl-input" placeholder="add symbol…" maxlength="16" />` +
      `<button type="submit">+</button></form>` +
      `<table class="feed"><thead><tr><th>Symbol</th><th>Price</th><th>Chg</th><th></th></tr></thead>` +
      `<tbody>${rows}</tbody></table>`;
    wrap.querySelector("form")!.addEventListener("submit", (e) => {
      e.preventDefault();
      const input = wrap.querySelector<HTMLInputElement>(".wl-input")!;
      const symbol = input.value.toUpperCase().trim();
      if (symbol && !this.symbols.includes(symbol)) this.symbols.push(symbol);
      input.value = "";
      this.persist();
      void this.refresh();
    });
    wrap.addEventListener("click", (e) => {
      const sym = (e.target as HTMLElement).closest<HTMLElement>(".wl-remove")?.dataset.sym;
      if (sym) {
        this.symbols = this.symbols.filter((s) => s !== sym);
        this.persist();
        void this.refresh();
      }
    });
    this.setContent(wrap);
  }
}

export class CandlesPanel extends Panel {
  private symbol = "AAPL";
  private period = "1mo";

  constructor() {
    super({ id: "candles", title: "Chart", w: 8, h: 6 });
    // any panel can point the chart at a symbol
    window.addEventListener("worldfin:select-symbol", (e) => {
      const sym = (e as CustomEvent<string>).detail?.toUpperCase();
      if (sym) {
        this.symbol = sym;
        void this.load();
      }
    });
  }

  async load(): Promise<void> {
    this.renderShell();
    await this.refresh();
  }

  private renderShell(): void {
    const wrap = document.createElement("div");
    wrap.className = "candles";
    wrap.innerHTML =
      `<form class="candles-form">` +
      `<input class="candles-symbol" value="${escapeHtml(this.symbol)}" maxlength="16" />` +
      `<select class="candles-period">` +
      ["1d", "5d", "1mo", "3mo", "6mo", "1y"]
        .map((p) => `<option${p === this.period ? " selected" : ""}>${p}</option>`)
        .join("") +
      `</select><button type="submit">Load</button></form>` +
      `<div class="candles-body"><p class="muted">Loading…</p></div>`;
    wrap.querySelector("form")!.addEventListener("submit", (e) => {
      e.preventDefault();
      const input = wrap.querySelector<HTMLInputElement>(".candles-symbol")!;
      this.symbol = input.value.toUpperCase().trim() || this.symbol;
      this.period = (wrap.querySelector<HTMLSelectElement>(".candles-period")!).value;
      void this.refresh();
    });
    this.setContent(wrap);
  }

  private async refresh(): Promise<void> {
    const body = this.el.querySelector<HTMLElement>(".candles-body");
    const title = this.el.querySelector<HTMLElement>(".panel-head");
    if (title) title.textContent = `Chart — ${this.symbol} (${this.period})`;
    if (!body) return;
    body.innerHTML = '<p class="muted">Loading…</p>';
    try {
      const data = await api.candles(this.symbol, this.period);
      body.innerHTML = this.renderCandles(data.candles);
    } catch {
      body.innerHTML = '<p class="empty">No candle data for this symbol/period.</p>';
    }
  }

  private renderCandles(candles: Candle[]): string {
    if (candles.length < 2) return '<p class="empty">Not enough data.</p>';
    const w = 860;
    const h = 320;
    const volH = 56; // bottom band for volume
    const pad = 8;
    const highs = candles.map((c) => c.h);
    const lows = candles.map((c) => c.l);
    const max = Math.max(...highs);
    const min = Math.min(...lows);
    const span = max - min || 1;
    const priceH = h - volH - pad * 2;
    const step = (w - pad * 2) / candles.length;
    const bw = Math.max(2, step * 0.62);
    const y = (v: number): number => pad + (1 - (v - min) / span) * priceH;

    // SMA20 overlay
    const sma: Array<{ x: number; v: number }> = [];
    for (let i = 19; i < candles.length; i++) {
      const avg = candles.slice(i - 19, i + 1).reduce((s, c) => s + c.c, 0) / 20;
      sma.push({ x: pad + i * step + step / 2, v: avg });
    }
    const smaPath = sma.map((s, i) => `${i === 0 ? "M" : "L"}${s.x.toFixed(1)},${y(s.v).toFixed(1)}`).join(" ");

    const maxVol = Math.max(...candles.map((c) => c.v), 1);
    const volY = h - pad;

    const bars = candles
      .map((c, i) => {
        const x = pad + i * step + step / 2;
        const up = c.c >= c.o;
        const color = up ? "#16c784" : "#ea3943";
        const yH = y(c.h);
        const yL = y(c.l);
        const yO = y(c.o);
        const yC = y(c.c);
        const top = Math.min(yO, yC);
        const bodyH = Math.max(1.5, Math.abs(yC - yO));
        const vh = Math.max(1, (c.v / maxVol) * (volH - 6));
        return (
          `<line x1="${x.toFixed(1)}" y1="${yH.toFixed(1)}" x2="${x.toFixed(1)}" y2="${yL.toFixed(1)}" stroke="${color}" stroke-width="1"/>` +
          `<rect x="${(x - bw / 2).toFixed(1)}" y="${top.toFixed(1)}" width="${bw.toFixed(1)}" height="${bodyH.toFixed(1)}" fill="${color}"/>` +
          `<rect x="${(x - bw / 2).toFixed(1)}" y="${(volY - vh).toFixed(1)}" width="${bw.toFixed(1)}" height="${vh.toFixed(1)}" fill="${color}" opacity="0.35"/>`
        );
      })
      .join("");

    const smaLine = sma.length > 1 ? `<path d="${smaPath}" fill="none" stroke="#f5a623" stroke-width="1.4"/>` : "";

    const last = candles[candles.length - 1];
    const first = candles[0];
    const chg = (((last.c - first.c) / first.c) * 100).toFixed(2);
    const cls = last.c >= first.c ? "up" : "down";
    return (
      `<div class="candles-head"><b>${escapeHtml(String(last.c))}</b>` +
      `<span class="${cls}"> ${Number(chg) >= 0 ? "+" : ""}${chg}% over period</span>` +
      `<span class="muted"> · SMA20 <span style="color:#f5a623">─</span> · volume ▄</span></div>` +
      `<svg viewBox="0 0 ${w} ${h}" preserveAspectRatio="none" class="candles-svg">${bars}${smaLine}</svg>` +
      `<div class="muted candles-foot">${candles.length} candles</div>`
    );
  }
}

export class AgentPanel extends Panel {
  private ticker = "NVDA";

  constructor() {
    super({ id: "agents", title: "Agent Analysis — multi-agent research (view-only)", w: 4, h: 6 });
  }

  async load(): Promise<void> {
    const wrap = document.createElement("div");
    wrap.className = "agents";
    wrap.innerHTML =
      `<form class="agents-form"><input class="agents-ticker" value="${escapeHtml(this.ticker)}" maxlength="16" />` +
      `<button type="submit">Run council</button></form>` +
      `<div class="agents-body"><p class="muted">Enter a ticker and run the analyst council — commentary only, nothing is executed.</p></div>`;
    const body = wrap.querySelector<HTMLElement>(".agents-body")!;
    wrap.querySelector("form")!.addEventListener("submit", (e) => {
      e.preventDefault();
      const input = wrap.querySelector<HTMLInputElement>(".agents-ticker")!;
      this.ticker = input.value.toUpperCase().trim() || this.ticker;
      void this.run(body);
    });
    this.setContent(wrap);
  }

  private async run(body: HTMLElement): Promise<void> {
    body.innerHTML = '<p class="muted">Council deliberating… analysts debate with live market facts. Local models can take 1–3 minutes.</p>';
    try {
      const a = await api.agentAnalyze(this.ticker);
      body.innerHTML =
        `<div class="agents-signal">Signal: <b>${escapeHtml(String(a.signal))}</b>` +
        ` <span class="muted">· ${a.duration_seconds}s${a.errors.length ? ` · ${a.errors.length} errors` : ""}</span></div>` +
        `<pre class="agents-decision">${escapeHtml(a.decision.slice(0, 4000))}</pre>`;
    } catch {
      body.innerHTML = '<p class="empty">Analysis failed — is the AI provider running?</p>';
    }
  }
}

export class PredictionPanel extends Panel {
  constructor() {
    super({ id: "prediction", title: "Prediction — calibrated event impact", w: 6, h: 5 });
  }
  async load(): Promise<void> {
    try {
      const rel = await api.reliability();
      const events = (await api.events({ limit: 30 })).filter((e) => e.verdict !== "OBSERVE").slice(0, 5);
      const predictions = await Promise.allSettled(events.map((e) => api.predict(e.id)));

      const relTable = rel.reliability;
      const brier = rel.brier.brier == null ? "—" : rel.brier.brier.toFixed(3);
      const n = relTable.sample_size;

      const verds = Object.entries(relTable.by_verdict)
        .map(([v, s]) => {
          const rate = s.hit_rate == null ? "—" : `${Math.round(s.hit_rate * 100)}%`;
          return `<div class="pred-row"><span>${escapeHtml(v)}</span><span class="muted">w ${s.weight}</span><b>${rate}</b></div>`;
        })
        .join("");

      const cards = predictions
        .filter((p) => p.status === "fulfilled")
        .map((p) => {
          const pr = (p as PromiseFulfilledResult<Prediction>).value;
          const pct = Math.round(pr.p_verdict_correct * 100);
          return (
            `<div class="pred-card">` +
            `<div class="pred-top"><b>${escapeHtml(pr.event.ticker || pr.event.subject.slice(0, 30))}</b>` +
            `<span class="pred-p">${pct}%</span></div>` +
            `<div class="pred-bar"><i style="width:${pct}%;background:${pct >= 55 ? "#16c784" : pct <= 45 ? "#ea3943" : "#f5a623"}"></i></div>` +
            `<div class="muted pred-note">P(verdict correct) · ${pr.data_tier} · emp.share ${Math.round(pr.empirical_share * 100)}%</div>` +
            `</div>`
          );
        })
        .join("");

      this.setContent(
        `<div class="pred-summary">` +
          `<span>Global base rate: <b>${relTable.global_hit_rate == null ? "—" : Math.round(relTable.global_hit_rate * 100)}%</b></span>` +
          `<span class="muted"> · ${n} outcomes · Brier ${brier} · recency-decayed</span></div>` +
        `<div class="pred-grid">${cards || '<p class="empty">No directional signals yet.</p>'}</div>` +
        `<div class="pred-table">${verds}</div>`,
      );
    } catch {
      this.setContent('<p class="empty">Prediction engine unavailable.</p>');
    }
  }
}

export class AlertsPanel extends Panel {
  constructor() {
    super({ id: "alerts", title: "Alerts — fired by the pipeline", w: 6, h: 5 });
  }
  async load(): Promise<void> {
    try {
      const { alerts } = await getJSON<{ alerts: AlertRow[] }>("/api/alerts?limit=40");
      if (!alerts.length) return this.setContent('<p class="empty">No alerts fired yet.</p>');
      const rows = alerts
        .map(
          (a) =>
            `<div class="alert-row"><span class="alert-type">${escapeHtml(a.action_type)}</span>` +
            `<span class="alert-subject">${escapeHtml(a.subject.slice(0, 70))}</span>` +
            `<span class="muted">${escapeHtml((a.tickers || []).slice(0, 3).join(", "))} · ${escapeHtml((a.fired_at || "").slice(5, 16))}</span></div>`,
        )
        .join("");
      this.setContent(`<div class="alert-list">${rows}</div>`);
    } catch {
      this.setContent('<p class="empty">Alerts unavailable.</p>');
    }
  }
}

interface AlertRow {
  id: number;
  action_type: string;
  subject: string;
  tickers: string[];
  fired_at: string;
}

export class CalendarPanel extends Panel {
  constructor(private readonly onPick: (day: string) => void) {
    super({ id: "calendar", title: "Dates", w: 4, h: 2 });
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
    super({ id: "worldnews", title: "World News", w: 4, h: 2 });
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
    super({ id: "accuracy", title: "Accuracy", w: 5, h: 3 });
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
    super({ id: "sentiment", title: "Social Sentiment", w: 4, h: 3 });
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
    super({ id: "portfolio", title: "Portfolio", w: 4, h: 3 });
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
  private country = "All";

  constructor() {
    super({ id: "livetv", title: "Live TV — world news channels", w: 8, h: 6 });
  }
  render(): void {
    // Two channels visible side by side; scroll for more. Country filter narrows.
    const wrap = document.createElement("div");
    wrap.className = "tv";
    wrap.innerHTML =
      `<div class="tv-controls"><select class="tv-filter">` +
      `<option value="All">All countries</option>` +
      countries().map((c) => `<option${c === this.country ? " selected" : ""}>${escapeHtml(c)}</option>`).join("") +
      `</select><span class="muted tv-count"></span></div>` +
      `<div class="tv-scroll"></div>`;

    const scroll = wrap.querySelector<HTMLElement>(".tv-scroll")!;
    const count = wrap.querySelector<HTMLElement>(".tv-count")!;
    const fill = (): void => {
      const list = this.country === "All" ? CHANNELS : CHANNELS.filter((c) => c.country === this.country);
      count.textContent = `${list.length} channel${list.length === 1 ? "" : "s"}`;
      scroll.innerHTML = list
        .map(
          (c) =>
            `<div class="tv-card"><div class="tv-name">${escapeHtml(c.name)} · ${escapeHtml(c.country)}</div>` +
            `<iframe class="tv-frame" loading="lazy" allowfullscreen src="${embedUrl(c.channelId)}"></iframe></div>`,
        )
        .join("");
    };
    wrap.querySelector(".tv-filter")!.addEventListener("change", (e) => {
      this.country = (e.target as HTMLSelectElement).value;
      fill();
    });
    fill();
    this.setContent(wrap);
  }
}
