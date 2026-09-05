import axios from 'axios';
import { IndicatorData, HOPIScore, SystemStatus, Phase } from '../types';
import { mockIndicators, mockHOPIScore, mockSystemStatus } from '../mock/mockData';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5555/api/v1';
const USE_MOCK_DATA = import.meta.env.VITE_USE_MOCK_DATA === 'true' || false;

// Disable WebSocket in production (Render free tier doesn't support it)
const IS_PRODUCTION = API_BASE_URL.includes('onrender.com') || API_BASE_URL.includes('https://');

// Derive WebSocket URL from API URL
const getWsUrl = () => {
  const url = new URL(API_BASE_URL);
  const protocol = url.protocol === 'https:' ? 'wss:' : 'ws:';
  return `${protocol}//${url.host}/ws`;
};

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error);
    // If API fails, use mock data
    if (error.response?.status === 404 || error.code === 'ERR_NETWORK') {
      console.log('API unavailable, using mock data');
    }
    return Promise.reject(error);
  }
);

// Response type that indicates if fallback data is being used
export interface ApiResponse<T> {
  data: T;
  isUsingFallback: boolean;
  lastSuccessfulFetch?: Date;
}

export const apiService = {
  // Indicators
  async getIndicators(): Promise<ApiResponse<IndicatorData[]>> {
    if (USE_MOCK_DATA) {
      return { data: mockIndicators, isUsingFallback: true };
    }

    try {
      const { data } = await api.get('/indicators/');
      // Handle both array and {indicators: []} response formats
      const indicators = Array.isArray(data) ? data : data.indicators;
      return {
        data: indicators || mockIndicators,
        isUsingFallback: !indicators || indicators.length === 0,
        lastSuccessfulFetch: new Date()
      };
    } catch (error) {
      console.log('Using mock indicators due to API error');
      return { data: mockIndicators, isUsingFallback: true };
    }
  },

  async getIndicator(id: string): Promise<IndicatorData> {
    const { data } = await api.get(`/indicators/${id}`);
    return data;
  },

  async getIndicatorHistory(id: string, range: string = '7d'): Promise<any> {
    const { data } = await api.get(`/indicators/${id}/history`, {
      params: { range }
    });
    return data;
  },

  // HOPI Score and Phases
  async getHOPIScore(): Promise<ApiResponse<HOPIScore>> {
    if (USE_MOCK_DATA) {
      return { data: mockHOPIScore, isUsingFallback: true };
    }

    try {
      const { data } = await api.get('/hopi');
      return { data, isUsingFallback: false, lastSuccessfulFetch: new Date() };
    } catch (error) {
      console.log('Using mock HOPI score due to API error');
      return { data: mockHOPIScore, isUsingFallback: true };
    }
  },

  async getCurrentPhase(): Promise<Phase> {
    const { data } = await api.get('/phase');
    return data;
  },

  async getPhases(): Promise<Phase[]> {
    const { data } = await api.get('/phases');
    return data.phases;
  },

  // System Status
  async getSystemStatus(): Promise<SystemStatus> {
    if (USE_MOCK_DATA) {
      return mockSystemStatus;
    }
    
    try {
      const { data } = await api.get('/status');
      return data;
    } catch (error) {
      console.log('Using mock system status due to API error');
      return mockSystemStatus;
    }
  },

  // Alerts
  async getAlerts(): Promise<any[]> {
    const { data } = await api.get('/alerts');
    return data.alerts;
  },

  async acknowledgeAlert(id: string): Promise<void> {
    await api.post(`/alerts/${id}/acknowledge`);
  },

  // Emergency Procedures
  async getEmergencyProcedures(phase?: number): Promise<any[]> {
    const { data } = await api.get('/emergency/procedures', {
      params: phase ? { phase } : undefined
    });
    return data.procedures;
  },

  // Manual Refresh
  async refreshIndicator(id: string): Promise<IndicatorData> {
    const { data } = await api.post(`/indicators/${id}/refresh`);
    return data;
  },

  async refreshAll(): Promise<void> {
    await api.post('/indicators/refresh-all');
  },

  // Export
  async exportReport(format: 'pdf' | 'csv' = 'pdf'): Promise<Blob> {
    const { data } = await api.get('/export/report', {
      params: { format },
      responseType: 'blob'
    });
    return data;
  },
};

// WebSocket connection for real-time updates
export class WebSocketService {
  private ws: WebSocket | null = null;
  private reconnectInterval = 5000;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 3; // Reduced from 10
  private listeners: Map<string, Set<(...args: unknown[]) => void>> = new Map();
  private enabled = !USE_MOCK_DATA && !IS_PRODUCTION; // Disable WebSocket in mock mode or production

  connect(url: string = getWsUrl()) {
    if (!this.enabled) {
      // Silently skip WebSocket in production (Render doesn't support it)
      return;
    }
    
    if (this.ws?.readyState === WebSocket.OPEN) return;

    try {
      this.ws = new WebSocket(url);

      this.ws.onopen = () => {
        console.log('WebSocket connected');
        this.reconnectAttempts = 0;
        this.emit('connected', null);
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.emit(data.type, data.payload);
        } catch (error) {
          console.error('WebSocket message parse error:', error);
        }
      };

      this.ws.onerror = (error) => {
        console.warn('WebSocket error:', error);
        this.emit('error', error);
      };

      this.ws.onclose = () => {
        console.log('WebSocket disconnected');
        this.emit('disconnected', null);
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
          this.reconnect();
        }
      };
    } catch (error) {
      console.warn('Failed to create WebSocket connection:', error);
    }
  }

  private reconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached');
      return;
    }

    this.reconnectAttempts++;
    setTimeout(() => {
      console.log(`Reconnecting... (attempt ${this.reconnectAttempts})`);
      this.connect();
    }, this.reconnectInterval);
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  on(event: string, callback: (...args: unknown[]) => void) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event)!.add(callback);
  }

  off(event: string, callback: (...args: unknown[]) => void) {
    const callbacks = this.listeners.get(event);
    if (callbacks) {
      callbacks.delete(callback);
    }
  }

  private emit(event: string, data: any) {
    const callbacks = this.listeners.get(event);
    if (callbacks) {
      callbacks.forEach(callback => callback(data));
    }
  }

  send(type: string, payload: any) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type, payload }));
    }
  }
}

export const wsService = new WebSocketService();