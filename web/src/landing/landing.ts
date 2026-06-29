import "./landing.css";

// ---- content ----------------------------------------------------------------
const FEATURES: [string, string, string][] = [
  ["🌍", "Live globe", "Every event geolocated, colored by verdict. Click a point for the full reasoning chain."],
  ["🎯", "Event → ticker resolution", "A Strait-of-Hormuz headline becomes XOM, CVX, RTX, ZIM — with per-entity impact."],
  ["🔗", "Second-order effects", "The knock-on chain: war-risk premiums, rerouting, LNG spillover, insurer exposure."],
  ["⚖️", "Multi-agent AI council", "Seven analyst personas deliberate each call and surface consensus and dissent."],
  ["📈", "Accuracy proof", "Historical hit-rate, by-verdict breakdown, and an equity-curve sparkline you can audit."],
  ["🛰️", "Correlation engine", "Flags when 3+ independent source-types corroborate a story — before it's news."],
  ["⚡", "Breaking-news detection", "Wire + gov + intel triangulation fires a banner the moment a story converges."],
  ["💬", "Social sentiment", "Reddit + StockTwits bullish/bearish and volume spikes, per ticker."],
  ["💼", "Portfolio & watchlists", "Track positions and get position-aware signal weighting."],
  ["🔔", "Telegram alerts", "Push INVEST / PULL_OUT signals straight to your phone."],
  ["🪙", "Crypto + markets panels", "Most-mentioned tickers and live crypto movers, side by side."],
  ["⏱️", "Freshness guaranteed", "Only news ≤24h old, with per-source health monitoring."],
];

const TICKS = [
  ["INVEST", "NVDA", "+4", "up"], ["PULL_OUT", "XOM", "−3", "down"],
  ["OBSERVE", "BTC", "+1", "up"], ["CAUTIOUS", "TSM", "−2", "down"],
  ["INVEST", "LLY", "+3", "up"], ["PULL_OUT", "TSLA", "−3", "down"],
  ["INVEST", "CVX", "+2", "up"], ["OBSERVE", "ETH", "+1", "up"],
  ["CAUTIOUS", "GOOGL", "−2", "down"], ["INVEST", "RTX", "+4", "up"],
];

function fill(): void {
  const grid = document.getElementById("features-grid");
  if (grid)
    grid.innerHTML = FEATURES.map(
      ([ic, t, d]) => `<div class="card"><div class="ic">${ic}</div><h3>${t}</h3><p>${d}</p></div>`,
    ).join("");

  const row = (v: string, t: string, c: string, cls: string) =>
    `<span><b>${t}</b> <i style="color:var(--${cls === "up" ? "green" : "red"})">${v} ${c}</i></span>`;
  const track = document.getElementById("ticker");
  if (track) {
    const items = TICKS.map(([v, t, c, cls]) => row(v, t, c, cls)).join("");
    track.innerHTML = items + items; // duplicate for seamless loop
  }

  const mini = document.getElementById("hero-stats");
  if (mini)
    mini.innerHTML =
      `<span><b>37+</b> live events</span><span><b>14</b> world feeds</span><span><b>$0</b> free-tier</span>`;
}

// ---- count-up + reveal ------------------------------------------------------
function animate(): void {
  const io = new IntersectionObserver(
    (entries) => {
      for (const e of entries) {
        if (!e.isIntersecting) continue;
        e.target.classList.add("in");
        const el = e.target as HTMLElement;
        if (el.dataset.to) {
          const to = Number(el.dataset.to);
          let n = 0;
          const step = Math.max(1, Math.round(to / 28));
          const tick = () => {
            n = Math.min(to, n + step);
            el.textContent = String(n);
            if (n < to) requestAnimationFrame(tick);
          };
          tick();
        }
        io.unobserve(e.target);
      }
    },
    { threshold: 0.3 },
  );
  document
    .querySelectorAll(".step,.card,.mode,.pillar,.dg,.sec-head,.frame,.stat")
    .forEach((el) => {
      el.classList.add("reveal");
      io.observe(el);
    });
  document.querySelectorAll<HTMLElement>(".count").forEach((el) => io.observe(el));
}

// ---- hero globe (lazy globe.gl) --------------------------------------------
async function globe(): Promise<void> {
  const host = document.getElementById("globe");
  if (!host || window.innerWidth < 560) return;
  try {
    const { default: Globe } = await import("globe.gl");
    const pts = [
      [26.5, 56.2, "#ef4444"], [24.0, 121.0, "#f59e0b"], [40.7, -74.0, "#16c784"],
      [51.5, -0.1, "#3b82f6"], [35.7, 139.7, "#16c784"], [25.2, 55.3, "#ef4444"],
      [1.35, 103.8, "#16c784"], [-23.5, -46.6, "#f59e0b"], [55.7, 37.6, "#ef4444"],
      [37.6, -122.4, "#16c784"], [19.4, -99.1, "#3b82f6"], [-33.9, 151.2, "#16c784"],
    ].map(([lat, lng, color]) => ({ lat, lng, color }));
    const arcs = [
      [26.5, 56.2, 51.5, -0.1], [24.0, 121.0, 37.6, -122.4], [55.7, 37.6, 51.5, -0.1],
      [25.2, 55.3, 1.35, 103.8], [40.7, -74.0, 51.5, -0.1],
    ].map(([sl, sg, el, eg]) => ({ sl, sg, el, eg }));

    const g = (Globe as any)()(host)
      .backgroundColor("rgba(0,0,0,0)")
      .globeImageUrl("//unpkg.com/three-globe/example/img/earth-night.jpg")
      .atmosphereColor("#16c784")
      .atmosphereAltitude(0.18)
      .pointsData(pts)
      .pointLat("lat").pointLng("lng").pointColor("color")
      .pointAltitude(0.04).pointRadius(0.42)
      .arcsData(arcs)
      .arcStartLat("sl").arcStartLng("sg").arcEndLat("el").arcEndLng("eg")
      .arcColor(() => ["#16c784", "rgba(22,199,132,0)"])
      .arcDashLength(0.5).arcDashGap(1).arcDashAnimateTime(2200).arcStroke(0.5);

    const sz = () => g.width(host.clientWidth).height(host.clientHeight);
    sz();
    window.addEventListener("resize", sz);
    g.controls().autoRotate = true;
    g.controls().autoRotateSpeed = 0.7;
    g.controls().enableZoom = false;
    g.pointOfView({ lat: 20, lng: 30, altitude: 2.4 });
  } catch {
    host.innerHTML = ""; // degrade silently if globe fails
  }
}

fill();
animate();
void globe();
