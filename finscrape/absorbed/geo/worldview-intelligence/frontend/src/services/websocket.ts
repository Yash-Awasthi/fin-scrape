import type { WSMessage, LayerData, AnomalyAlert, SituationReport } from '../types';
import { useAppStore } from '../stores/appStore';

const WS_URL = 'ws://localhost:3002';
const MAX_RECONNECT_DELAY = 30_000;
const BASE_RECONNECT_DELAY = 1_000;

let socket: WebSocket | null = null;
let reconnectAttempt = 0;
let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
let intentionalClose = false;

function getReconnectDelay(): number {
  const delay = BASE_RECONNECT_DELAY * Math.pow(2, reconnectAttempt);
  return Math.min(delay, MAX_RECONNECT_DELAY);
}

function handleMessage(event: MessageEvent) {
  try {
    const message: WSMessage = JSON.parse(event.data);
    const store = useAppStore.getState();

    switch (message.type) {
      case 'layer_update':
        if (message.layer) {
          const layer = message.layer;
          store.setLayerData(
            layer,
            message.data as LayerData[keyof LayerData],
          );
        }
        break;

      case 'anomaly':
        store.addAnomaly(message.data as AnomalyAlert);
        break;

      case 'situation_report':
        store.setSituationReport(message.data as SituationReport);
        break;

      case 'alert':
        store.addAnomaly(message.data as AnomalyAlert);
        break;
    }
  } catch {
    console.error('[WS] Failed to parse message');
  }
}

function scheduleReconnect() {
  if (intentionalClose) return;
  const delay = getReconnectDelay();
  reconnectAttempt++;
  console.log(`[WS] Reconnecting in ${delay}ms (attempt ${reconnectAttempt})`);
  reconnectTimer = setTimeout(connectWebSocket, delay);
}

export function connectWebSocket(): void {
  if (socket?.readyState === WebSocket.OPEN) return;

  intentionalClose = false;
  socket = new WebSocket(WS_URL);

  socket.onopen = () => {
    console.log('[WS] Connected');
    reconnectAttempt = 0;
  };

  socket.onmessage = handleMessage;

  socket.onclose = () => {
    console.log('[WS] Disconnected');
    socket = null;
    scheduleReconnect();
  };

  socket.onerror = () => {
    console.error('[WS] Connection error');
    socket?.close();
  };
}

export function disconnectWebSocket(): void {
  intentionalClose = true;
  if (reconnectTimer) {
    clearTimeout(reconnectTimer);
    reconnectTimer = null;
  }
  if (socket) {
    socket.close();
    socket = null;
  }
}

function sendMessage(payload: Record<string, unknown>): void {
  if (socket?.readyState === WebSocket.OPEN) {
    socket.send(JSON.stringify(payload));
  }
}

export function subscribeLayer(layer: keyof LayerData): void {
  sendMessage({ action: 'subscribe', layer });
}

export function unsubscribeLayer(layer: keyof LayerData): void {
  sendMessage({ action: 'unsubscribe', layer });
}
