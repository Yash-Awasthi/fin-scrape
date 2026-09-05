import { WebSocketServer, WebSocket } from 'ws';
import { IncomingMessage } from 'http';
import { fetchAircraft } from '../services/aircraft';
import { fetchSatellites } from '../services/satellites';
import { fetchShips } from '../services/ships';
import { fetchEarthquakes } from '../services/earthquakes';
import { fetchConflicts } from '../services/conflicts';
import { fetchMissileLaunches } from '../services/missiles';
import { fetchNewsEvents } from '../services/news';
import { fetchTrafficData } from '../services/traffic';
import { fetchWeatherData } from '../services/weather';
import { detectAnomalies } from '../services/intelligence';
import { LayerData, WSMessage } from '../types/index';

type LayerName = keyof LayerData;

interface ClientMeta {
  subscriptions: Set<LayerName>;
  isAlive: boolean;
}

const ALL_LAYERS: LayerName[] = [
  'aircraft', 'satellites', 'ships', 'earthquakes',
  'conflicts', 'missiles', 'news', 'traffic', 'weather',
];

export class WSServer {
  private wss: WebSocketServer;
  private clients = new Map<WebSocket, ClientMeta>();
  private previousData: Partial<LayerData> = {};
  private intervals: NodeJS.Timeout[] = [];
  private heartbeatInterval: NodeJS.Timeout | null = null;

  constructor(port: number) {
    this.wss = new WebSocketServer({ port });

    this.wss.on('connection', (ws: WebSocket, _req: IncomingMessage) => {
      const meta: ClientMeta = {
        subscriptions: new Set(ALL_LAYERS),
        isAlive: true,
      };
      this.clients.set(ws, meta);
      console.log(`[WS] Client connected (total: ${this.clients.size})`);

      ws.on('message', (raw) => {
        try {
          const msg = JSON.parse(raw.toString());
          this.handleClientMessage(ws, meta, msg);
        } catch {
          ws.send(JSON.stringify({ error: 'Invalid message format' }));
        }
      });

      ws.on('pong', () => {
        meta.isAlive = true;
      });

      ws.on('close', () => {
        this.clients.delete(ws);
        console.log(`[WS] Client disconnected (total: ${this.clients.size})`);
      });

      ws.on('error', (err) => {
        console.error('[WS] Client error:', err.message);
        this.clients.delete(ws);
      });
    });

    this.startHeartbeat();
    this.startDataLoops();
    console.log(`[WS] WebSocket server started on port ${port}`);
  }

  private handleClientMessage(
    ws: WebSocket,
    meta: ClientMeta,
    msg: { type: string; layers?: string[] },
  ): void {
    if (msg.type === 'subscribe' && Array.isArray(msg.layers)) {
      meta.subscriptions.clear();
      for (const layer of msg.layers) {
        if (ALL_LAYERS.includes(layer as LayerName)) {
          meta.subscriptions.add(layer as LayerName);
        }
      }
      ws.send(
        JSON.stringify({
          type: 'subscribed',
          layers: Array.from(meta.subscriptions),
        }),
      );
    } else if (msg.type === 'unsubscribe' && Array.isArray(msg.layers)) {
      for (const layer of msg.layers) {
        meta.subscriptions.delete(layer as LayerName);
      }
      ws.send(
        JSON.stringify({
          type: 'subscribed',
          layers: Array.from(meta.subscriptions),
        }),
      );
    }
  }

  private broadcast(layer: LayerName, data: unknown): void {
    const message: WSMessage = {
      type: 'layer_update',
      layer,
      data,
      timestamp: Date.now(),
    };
    const payload = JSON.stringify(message);

    for (const [ws, meta] of this.clients) {
      if (ws.readyState === WebSocket.OPEN && meta.subscriptions.has(layer)) {
        ws.send(payload);
      }
    }
  }

  private broadcastAnomaly(alert: unknown): void {
    const message: WSMessage = {
      type: 'anomaly',
      data: alert,
      timestamp: Date.now(),
    };
    const payload = JSON.stringify(message);

    for (const [ws] of this.clients) {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(payload);
      }
    }
  }

  private startHeartbeat(): void {
    this.heartbeatInterval = setInterval(() => {
      for (const [ws, meta] of this.clients) {
        if (!meta.isAlive) {
          ws.terminate();
          this.clients.delete(ws);
          continue;
        }
        meta.isAlive = false;
        ws.ping();
      }
    }, 30_000);
  }

  private startDataLoops(): void {
    this.scheduleLayer('aircraft', fetchAircraft, 10_000);
    this.scheduleLayer('satellites', fetchSatellites, 30_000);
    this.scheduleLayer('ships', fetchShips, 30_000);
    this.scheduleLayer('earthquakes', fetchEarthquakes, 60_000);
    this.scheduleLayer('conflicts', fetchConflicts, 120_000);
    this.scheduleLayer('missiles', fetchMissileLaunches, 60_000);
    this.scheduleLayer('news', fetchNewsEvents, 300_000);
    this.scheduleLayer('traffic', fetchTrafficData, 60_000);
    this.scheduleLayer('weather', fetchWeatherData, 300_000);
  }

  private scheduleLayer(
    layer: LayerName,
    fetcher: () => Promise<unknown[]>,
    intervalMs: number,
  ): void {
    const run = async () => {
      try {
        const data = await fetcher();
        this.broadcast(layer, data);

        const currentSnapshot: Partial<LayerData> = {
          ...this.previousData,
          [layer]: data,
        };

        const anomalies = detectAnomalies(currentSnapshot, this.previousData);
        for (const alert of anomalies) {
          console.log(`[WS] Anomaly detected: ${alert.title}`);
          this.broadcastAnomaly(alert);
        }

        this.previousData = currentSnapshot;
      } catch (err) {
        console.error(`[WS] Failed to fetch ${layer}:`, err);
      }
    };

    run();
    const id = setInterval(run, intervalMs);
    this.intervals.push(id);
  }

  shutdown(): void {
    for (const id of this.intervals) clearInterval(id);
    if (this.heartbeatInterval) clearInterval(this.heartbeatInterval);
    for (const [ws] of this.clients) ws.terminate();
    this.clients.clear();
    this.wss.close();
    console.log('[WS] Server shut down');
  }
}

export function createWSServer(port: number): WSServer {
  return new WSServer(port);
}
