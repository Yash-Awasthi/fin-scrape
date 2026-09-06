// SignalFeedPanel: analyzed intelligence — verdicts, scores, reasoning preview,
// and the source article link. Compact rows with verdict filters.
// (World News shows raw RSS; this panel shows what the pipeline *concluded*.)

import { type EventOut, verdictColor } from "../api";
import { Panel } from "./panel";

export class SignalFeedPanel extends Panel {
  private verdictFilter = "ALL";

  constructor(private readonly onSelect: (e: EventOut) => void) {
    super({ id: "feed", title: "Signal Feed — analyzed events", w: 4, h: 8 });
  }

  update(events: EventOut[]): void {
    if (!events.length) {
      this.setContent('<p class="empty">No signals yet.</p>');
      return;
    }
    const verdicts = ["ALL", ...new Set(events.map((e) => e.verdict))];
    const wrap = document.createElement("div");
    wrap.innerHTML =
      `<div class="feed-filters">` +
      verdicts
        .map(
          (v) =>
            `<button class="ffilter${v === this.verdictFilter ? " active" : ""}" data-v="${v}">${v}</button>`,
        )
        .join("") +
      `</div>`;
    wrap.addEventListener("click", (e) => {
      const v = (e.target as HTMLElement).closest<HTMLElement>(".ffilter")?.dataset.v;
      if (v) {
        this.verdictFilter = v;
        this.update(events);
      }
    });
    wrap.append(this.buildTable(events));
    this.setContent(wrap);
  }

  private buildTable(events: EventOut[]): HTMLTableElement {
    const table = document.createElement("table");
    table.className = "feed compact";
    table.innerHTML = "<thead><tr><th>Signal</th></tr></thead>";
    const tbody = document.createElement("tbody");
    const filtered =
      this.verdictFilter === "ALL"
        ? events
        : events.filter((e) => e.verdict === this.verdictFilter);

    for (const e of filtered.slice(0, 60)) {
      const tr = document.createElement("tr");
      tr.tabIndex = 0;
      const link = e.articles?.[0];
      const subject = link
        ? `<a href="${escapeHtml(link)}" target="_blank" rel="noopener" title="open source article">${escapeHtml(e.subject)}</a>`
        : escapeHtml(e.subject);
      const reasoning = e.reasoning
        ? `<div class="row-reasoning">${escapeHtml(e.reasoning.slice(0, 110))}${e.reasoning.length > 110 ? "…" : ""}</div>`
        : "";
      tr.innerHTML =
        `<td><span class="dot" style="background:${verdictColor(e.verdict)}"></span>` +
        `${e.verdict} <b>${e.signal_score >= 0 ? "+" : ""}${e.signal_score}</b>` +
        `<span class="row-meta">${Math.round(e.confidence * 100)}% · ${escapeHtml(e.tickers.slice(0, 4).join(", ")) || "—"}</span>` +
        `<div class="subj">${subject}</div>${reasoning}</td>`;
      tr.addEventListener("click", (ev) => {
        // links open the source; text selection means the user is copying, not clicking
        if (window.getSelection()?.toString()) return;
        if (!(ev.target as HTMLElement).closest("a")) this.onSelect(e);
      });
      tbody.append(tr);
    }
    table.append(tbody);
    return table;
  }
}

function escapeHtml(s: string): string {
  const d = document.createElement("div");
  d.textContent = s;
  return d.innerHTML;
}
