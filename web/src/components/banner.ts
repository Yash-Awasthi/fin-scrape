// BreakingNewsBanner: shows when corroboration (convergence/triangulation) fires.

import type { Correlation } from "../api";
import { escapeHtml } from "../util";

const BREAKING = new Set(["convergence", "triangulation"]);

export class BreakingNewsBanner {
  readonly el: HTMLElement;
  constructor() {
    this.el = document.createElement("div");
    this.el.className = "breaking hidden";
  }
  update(signals: Correlation[]): void {
    const hits = signals.filter((s) => BREAKING.has(s.signal_type));
    if (!hits.length) {
      this.el.classList.add("hidden");
      return;
    }
    const top = hits[0];
    const subject = escapeHtml(String(top.payload?.id ?? "developing story"));
    this.el.innerHTML = `<span class="breaking-tag">BREAKING</span> corroborated across sources — ${subject}`;
    this.el.classList.remove("hidden");
  }
}
