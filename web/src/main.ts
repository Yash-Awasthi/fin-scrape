import "./styles.css";

import { api } from "./api";
import { PAGE_LAYOUT, pagePanelIds } from "./app/variants";
import { Shell } from "./app/shell";
import { BreakingNewsBanner } from "./components/banner";
import { SignalModal } from "./components/modal";
import { TickerTape } from "./components/ticker-tape";
import type { GlobeView } from "./globe/globe";
import type { EventOut } from "./api";
import { PanelLayoutManager } from "./panels/layout";
import { Panel } from "./panels/panel";
import {
  AccuracyPanel,
  AgentPanel,
  CalendarPanel,
  CandlesPanel,
  CorrelationPanel,
  LiveTVPanel,
  MarketsLivePanel,
  MarketsPanel,
  NewsLobbyPanel,
  PortfolioPanel,
  SentimentPanel,
  StatsPanel,
  SuggestionsPanel,
  WatchlistPanel,
  WorldNewsPanel,
} from "./panels/panels";
import { SignalFeedPanel } from "./panels/signal-feed";
import { Store } from "./state";
import { RealtimeClient, wsUrl, type WSMessage } from "./ws";

const store = new Store();
const modal = new SignalModal();
const banner = new BreakingNewsBanner();

const shell = new Shell(() => void loadAll());
const layout = new PanelLayoutManager();

// Panels — one page, in the order the layout declares.
const candlesPanel = new CandlesPanel();
const agentPanel = new AgentPanel();
const marketsLivePanel = new MarketsLivePanel();
const watchlistPanel = new WatchlistPanel();
const feedPanel = new SignalFeedPanel((e) => store.select(e));
const globePanel = new Panel({ id: "globe", title: "Globe", w: 8, h: 8 });
const statsPanel = new StatsPanel();
const suggestionsPanel = new SuggestionsPanel();
const datesPanel = new CalendarPanel((day) => void loadDay(day));
const newsLobbyPanel = new NewsLobbyPanel();
const worldNewsPanel = new WorldNewsPanel();
const liveTVPanel = new LiveTVPanel();
const correlationPanel = new CorrelationPanel();
const accuracyPanel = new AccuracyPanel();
const sentimentPanel = new SentimentPanel();
const portfolioPanel = new PortfolioPanel();
const marketsPanel = new MarketsPanel();

for (const p of [
  candlesPanel,
  agentPanel,
  marketsLivePanel,
  watchlistPanel,
  feedPanel,
  globePanel,
  statsPanel,
  suggestionsPanel,
  datesPanel,
  newsLobbyPanel,
  worldNewsPanel,
  liveTVPanel,
  correlationPanel,
  accuracyPanel,
  sentimentPanel,
  portfolioPanel,
  marketsPanel,
]) {
  layout.add(p);
}

const app = document.getElementById("app")!;
shell.mount(app);
shell.bannerSlot.append(banner.el);
layout.mount(shell.content);

// Live market tape (always on) + 15s quote polling.
const tape = new TickerTape();
shell.content.before(tape.el);
app.append(modal.el);
const quotesTimer = window.setInterval(() => {
  void tape.refresh();
  void marketsLivePanel.refresh();
  void watchlistPanel.refresh();
}, 15_000);
window.addEventListener("beforeunload", () => {
  window.clearInterval(quotesTimer);
  tape.stop();
});

// globe.gl (+three.js) is ~1.8MB — lazy chunk so the shell paints immediately.
let globe: GlobeView | null = null;
function sizeGlobe(): void {
  if (!globe) return;
  const r = globePanel.body.getBoundingClientRect();
  if (r.width && r.height) globe.resize(r.width, r.height);
}
window.addEventListener("resize", sizeGlobe);
void import("./globe/globe").then(({ GlobeView }) => {
  globe = new GlobeView(globePanel.body, (e) => store.select(e));
  sizeGlobe();
  globe.setEvents(store.get().events);
});

// The globe re-creates its meshes on setEvents — only feed it when the event
// array actually changed (loads / WS pushes), never on row clicks/selection.
let lastGlobeEvents: EventOut[] | null = null;
let lastSelectedId: number | null = null;
store.subscribe((s) => {
  shell.setConnection(s.connection);
  if (s.events !== lastGlobeEvents) {
    lastGlobeEvents = s.events;
    feedPanel.update(s.events);
    globe?.setEvents(s.events);
  }
  if (s.stats) statsPanel.update(s.stats);
  correlationPanel.update(s.correlations);
  banner.update(s.correlations);
  if (s.selected && s.selected.id !== lastSelectedId) {
    lastSelectedId = s.selected.id;
    modal.show(s.selected);
  }
});
requestAnimationFrame(sizeGlobe);

async function loadAll(): Promise<void> {
  // allSettled: one missing backend endpoint must never blank the whole load.
  const [events, stats, correlations, dates] = await Promise.allSettled([
    api.events({ limit: 200 }),
    api.stats(),
    api.correlations(),
    api.dates(),
  ]);
  if (events.status === "fulfilled") store.setEvents(events.value);
  if (stats.status === "fulfilled") store.setStats(stats.value);
  if (correlations.status === "fulfilled") store.setCorrelations(correlations.value);
  if (dates.status === "fulfilled") datesPanel.update(dates.value);
  await loadPanelsData();
}

// Pull-once panels (each handles its own errors).
async function loadPanelsData(): Promise<void> {
  const shown = pagePanelIds();
  const jobs: Promise<unknown>[] = [];
  if (shown.has("markets-live")) jobs.push(marketsLivePanel.load());
  if (shown.has("candles")) jobs.push(candlesPanel.load());
  if (shown.has("agents")) jobs.push(agentPanel.load());
  if (shown.has("watchlist")) jobs.push(watchlistPanel.load());
  if (shown.has("suggestions")) jobs.push(suggestionsPanel.load());
  if (shown.has("lobby")) jobs.push(newsLobbyPanel.load());
  if (shown.has("worldnews")) jobs.push(worldNewsPanel.load());
  if (shown.has("accuracy")) jobs.push(accuracyPanel.load());
  if (shown.has("sentiment")) jobs.push(sentimentPanel.load());
  if (shown.has("portfolio")) jobs.push(portfolioPanel.load());
  if (shown.has("markets")) jobs.push(marketsPanel.load());
  if (shown.has("livetv")) liveTVPanel.render();
  await Promise.allSettled(jobs);
}

async function loadDay(day: string): Promise<void> {
  try {
    store.setEvents(await api.events({ date: day, limit: 200 }));
    store.setCorrelations(await api.correlations(day));
  } catch (err) {
    console.error("day load failed", err);
  }
}

function onMessage(msg: WSMessage): void {
  if (msg.type === "init" && msg.events) store.setEvents(msg.events);
  else if (msg.type === "new_events" && msg.events) store.addEvents(msg.events);
  if (msg.stats) store.setStats(msg.stats);
}

const rt = new RealtimeClient(wsUrl(), onMessage, (status) => store.setConnection(status));

layout.applyVariant(PAGE_LAYOUT);
void loadAll();
rt.connect();
