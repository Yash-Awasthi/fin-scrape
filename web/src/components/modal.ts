// SignalModal: event detail + automatic AI expansion when reasoning is missing.

import { api, type EventOut, verdictColor } from "../api";

export class SignalModal {
  readonly el: HTMLElement;
  private box: HTMLElement;

  constructor() {
    this.el = document.createElement("div");
    this.el.className = "modal-overlay hidden";
    this.el.addEventListener("click", (e) => {
      if (e.target === this.el) this.hide();
    });

    this.box = document.createElement("div");
    this.box.className = "modal";
    this.el.append(this.box);
  }

  hide(): void {
    this.el.classList.add("hidden");
  }

  show(ev: EventOut): void {
    this.box.replaceChildren();

    const close = document.createElement("button");
    close.className = "modal-close";
    close.textContent = "✕";
    close.addEventListener("click", () => this.hide());

    const badge = document.createElement("span");
    badge.className = "verdict-badge";
    badge.style.background = verdictColor(ev.verdict);
    badge.textContent = `${ev.verdict} ${ev.signal_score >= 0 ? "+" : ""}${ev.signal_score}`;

    const h = document.createElement("h2");
    h.textContent = ev.subject;

    const meta = document.createElement("div");
    meta.className = "modal-meta";
    meta.textContent = `${ev.event_type} · ${Math.round(ev.confidence * 100)}% · ${ev.tickers.join(", ") || "no tickers"} · ${ev.sources.join(", ")}`;

    const reasoning = document.createElement("p");
    reasoning.className = "modal-reasoning";
    reasoning.textContent = ev.reasoning || "";

    const entities = document.createElement("ul");
    entities.className = "modal-entities";
    for (const ent of ev.affected_entities ?? []) {
      const li = document.createElement("li");
      li.textContent = `${ent.name}${ent.ticker ? ` (${ent.ticker})` : ""} — ${ent.role ?? "?"} / ${ent.impact ?? "?"}`;
      entities.append(li);
    }

    const aiOut = document.createElement("div");
    aiOut.className = "ai-out";
    const aiBtn = document.createElement("button");
    aiBtn.className = "ai-btn";
    aiBtn.textContent = "↻ Re-run AI analysis";

    const runAnalysis = async (): Promise<void> => {
      aiBtn.disabled = true;
      aiOut.textContent = "AI is analyzing… (local model, a few seconds)";
      try {
        const a = await api.analyze(ev.id);
        const impacts = a.ticker_impacts
          .map((t) => `${t.ticker}: ${t.direction} ${t.estimated_pct} — ${t.reason}`)
          .join("\n");
        aiOut.textContent =
          [a.summary, impacts, a.verdict_reason].filter(Boolean).join("\n\n") ||
          "No analysis returned.";
      } catch (err) {
        aiOut.textContent =
          err instanceof Error && err.message.includes("503")
            ? "AI backend unavailable — start Ollama, then: main.py devtools on"
            : "AI analysis unavailable.";
      } finally {
        aiBtn.disabled = false;
      }
    };
    aiBtn.addEventListener("click", () => void runAnalysis());

    this.box.append(close, badge, h, meta, reasoning, entities, aiBtn, aiOut);
    this.el.classList.remove("hidden");

    // Reasoning must never sit blank: events created without the LLM are
    // analyzed automatically the moment they're opened.
    if (!ev.reasoning) void runAnalysis();
  }
}
