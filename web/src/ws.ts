// Realtime WS client: reconnect with exponential backoff + jitter, ping keep-alive.
// Messages mirror server/ws.py: init / new_events / ai_updated / pong.
// (SSE fallback is a future seam — the backend exposes only WS today.)

import type { DashboardStats, EventOut } from "./api";

export type WSStatus = "connecting" | "open" | "closed";

export interface WSMessage {
  type: "init" | "new_events" | "ai_updated" | "pong";
  events?: EventOut[];
  stats?: DashboardStats;
}

type MsgHandler = (msg: WSMessage) => void;
type StatusHandler = (status: WSStatus) => void;

// Injectable WebSocket ctor so tests can supply a fake.
type WSFactory = (url: string) => WebSocket;

export class RealtimeClient {
  private ws: WebSocket | null = null;
  private retries = 0;
  private pingTimer: ReturnType<typeof setInterval> | null = null;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private stopped = false;

  constructor(
    private readonly url: string,
    private readonly onMessage: MsgHandler,
    private readonly onStatus: StatusHandler = () => {},
    private readonly factory: WSFactory = (u) => new WebSocket(u),
    private readonly pingMs = 25_000,
  ) {}

  /** Backoff delay for retry n: 0.5s,1s,2s,…capped 15s, ±20% jitter. */
  backoffMs(n: number): number {
    const base = Math.min(15_000, 500 * 2 ** n);
    return Math.round(base * (0.8 + Math.random() * 0.4));
  }

  connect(): void {
    this.stopped = false;
    this.open();
  }

  private open(): void {
    this.onStatus("connecting");
    const ws = this.factory(this.url);
    this.ws = ws;

    ws.onopen = () => {
      this.retries = 0;
      this.onStatus("open");
      this.pingTimer = setInterval(() => this.send({ type: "ping" }), this.pingMs);
    };
    ws.onmessage = (ev: MessageEvent) => {
      try {
        this.onMessage(JSON.parse(ev.data as string) as WSMessage);
      } catch {
        /* ignore malformed frames */
      }
    };
    ws.onclose = () => this.scheduleReconnect();
    ws.onerror = () => ws.close();
  }

  private scheduleReconnect(): void {
    this.clearTimers();
    this.onStatus("closed");
    if (this.stopped) return;
    const delay = this.backoffMs(this.retries++);
    this.reconnectTimer = setTimeout(() => this.open(), delay);
  }

  private send(obj: unknown): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(obj));
    }
  }

  private clearTimers(): void {
    if (this.pingTimer) clearInterval(this.pingTimer);
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
    this.pingTimer = null;
    this.reconnectTimer = null;
  }

  close(): void {
    this.stopped = true;
    this.clearTimers();
    this.ws?.close();
  }
}

export function wsUrl(path = "/api/ws"): string {
  const proto = location.protocol === "https:" ? "wss" : "ws";
  return `${proto}://${location.host}${path}`;
}
