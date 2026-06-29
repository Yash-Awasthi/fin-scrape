import "./styles.css";

import { api } from "./api";
import { Shell } from "./app/shell";
import { loadVariant, saveVariant, type Variant, VARIANTS } from "./app/variants";
import { BreakingNewsBanner } from "./components/banner";
import { SignalModal } from "./components/modal";
import type { GlobeView } from "./globe/globe";
import { PanelLayoutManager } from "./panels/layout";
import { Panel } from "./panels/panel";
import {
  AccuracyPanel,
  CalendarPanel,
  CorrelationPanel,
  CryptoPanel,
  LiveTVPanel,
  MarketsPanel,
  PortfolioPanel,
  SentimentPanel,
  WorldNewsPanel,
} from "./panels/panels";
import { SignalFeedPanel } from "./panels/signal-feed";
import { Store } from "./state";
import { RealtimeClient, wsUrl, type WSMessage } from "./ws";

const store = new Store();
const modal = new SignalModal();
const banner = new BreakingNewsBanner();

let variant: Variant = loadVariant();

const shell = new Shell(
  () => void loadAll(),
  (v) => setVariant(v),
);
const layout = new PanelLayoutManager();

// Panels
const feedPanel = new SignalFeedPanel((e) => store.select(e));
const globePanel = new Panel({ id: "globe", title: "Globe", col: 6, row: 1, w: 7, h: 4 });
const correlationPanel = new CorrelationPanel();
const marketsPanel = new MarketsPanel();
const cryptoPanel = new CryptoPanel();
const worldNewsPanel = new WorldNewsPanel();
const liveTVPanel = new LiveTVPanel();
const accuracyPanel = new AccuracyPanel();
const calendarPanel = new CalendarPanel((day) => void loadDay(day));
const sentimentPanel = new SentimentPanel();
const portfolioPanel = new PortfolioPanel();

for (const p of [
  feedPanel,
  globePanel,
  correlationPanel,
  marketsPanel,
  cryptoPanel,
  worldNewsPanel,
  liveTVPanel,
  accuracyPanel,
  calendarPanel,
  sentimentPanel,
  portfolioPanel,
]) {
  layout.add(p);
}

const app = document.getElementById("app")!;
shell.mount(app);
shell.bannerSlot.append(banner.el);
layout.mount(shell.content);
app.append(modal.el);

// globe.gl (+three.js) is ~1.8MB — load it as its own lazy chunk so the shell and
// panels paint immediately, then pop the globe in and feed it the current events.
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

let lastSelected: number | null = null;
store.subscribe((s) => {
  shell.setConnection(s.connection);
  feedPanel.update(s.events);
  globe?.setEvents(s.events);
  correlationPanel.update(s.correlations);
  banner.update(s.correlations);
  if (s.selected && s.selected.id !== lastSelected) {
    lastSelected = s.selected.id;
    modal.show(s.selected);
  }
});
requestAnimationFrame(sizeGlobe);

function setVariant(v: Variant): void {
  variant = v;
  saveVariant(v);
  shell.setVariant(v);
  layout.applyVariant(VARIANTS[v].panels);
  requestAnimationFrame(sizeGlobe);
  void loadVariantData();
}

async function loadAll(): Promise<void> {
  try {
    const [events, stats, correlations, dates] = await Promise.all([
      api.events({ limit: 200 }),
      api.stats(),
      api.correlations(),
      api.dates(),
    ]);
    store.setEvents(events);
    store.setStats(stats);
    store.setCorrelations(correlations);
    calendarPanel.update(dates);
  } catch (err) {
    console.error("initial load failed", err);
  }
  await loadVariantData();
}

// Only fetch the data the active variant actually shows.
async function loadVariantData(): Promise<void> {
  const shown = new Set(VARIANTS[variant].panels);
  const jobs: Promise<unknown>[] = [];
  if (shown.has("markets")) jobs.push(marketsPanel.load());
  if (shown.has("crypto")) jobs.push(cryptoPanel.load());
  if (shown.has("worldnews")) jobs.push(worldNewsPanel.load());
  if (shown.has("accuracy")) jobs.push(accuracyPanel.load());
  if (shown.has("sentiment")) jobs.push(sentimentPanel.load());
  if (shown.has("portfolio")) jobs.push(portfolioPanel.load());
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

setVariant(variant);
void loadAll();
rt.connect();
