// SignalFeedPanel: analyzed intelligence — verdicts, scores, reasoning preview,
// and the source article link. Compact rows.
// (World News shows raw RSS; this panel shows what the pipeline *concluded*.)

import { type EventOut, verdictColor } from "../api";
import { Panel } from "./panel";

export class SignalFeedPanel extends Panel {
  constructor(private readonly onSelect: (e: EventOut) => void) {
    super({ id: "feed", title: "Signal Feed — analyzed events", w: 4, h: 8 });
  }

  update(events: EventOut[]): void {
    if (!events.length) {
      this.setContent('<p class="empty">No signals yet.</p>');
      return;
    }
    const table = document.createElement("table");
    table.className = "feed";
    table.className = "feed compact";
    table.innerHTML = "<thead><tr><th>Signal</th></tr></thead>";
    const tbody = document.createElement("tbody");

    for (const e of events.slice(0, 60)) {
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
    this.setContent(table);
  }
}

function escapeHtml(s: string): string {
  const d = document.createElement("div");
  d.textContent = s;
  return d.innerHTML;
}
