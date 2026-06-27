// SignalFeedPanel: live table of events; row click selects (→ modal). Proves the data pipe.

import { type EventOut, verdictColor } from "../api";
import { Panel } from "./panel";

export class SignalFeedPanel extends Panel {
  constructor(private readonly onSelect: (e: EventOut) => void) {
    super({ id: "feed", title: "Signal Feed", col: 1, row: 1, w: 5, h: 4 });
  }

  update(events: EventOut[]): void {
    if (!events.length) {
      this.setContent('<p class="empty">No signals yet.</p>');
      return;
    }
    const table = document.createElement("table");
    table.className = "feed";
    table.innerHTML =
      "<thead><tr><th>Verdict</th><th>Score</th><th>Subject</th><th>Tickers</th><th>Conf</th></tr></thead>";
    const tbody = document.createElement("tbody");

    for (const e of events.slice(0, 100)) {
      const tr = document.createElement("tr");
      tr.tabIndex = 0;
      tr.innerHTML =
        `<td><span class="dot" style="background:${verdictColor(e.verdict)}"></span>${e.verdict}</td>` +
        `<td>${e.signal_score >= 0 ? "+" : ""}${e.signal_score}</td>` +
        `<td class="subj">${escapeHtml(e.subject)}</td>` +
        `<td>${escapeHtml(e.tickers.join(", "))}</td>` +
        `<td>${Math.round(e.confidence * 100)}%</td>`;
      tr.addEventListener("click", () => this.onSelect(e));
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
