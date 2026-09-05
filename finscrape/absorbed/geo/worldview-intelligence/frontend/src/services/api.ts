import type { LayerData, SituationReport } from '../types';

const BASE_URL = '/api';

async function request<T>(path: string, params?: Record<string, string>): Promise<T> {
  const url = new URL(path, window.location.origin);
  if (params) {
    Object.entries(params).forEach(([k, v]) => url.searchParams.set(k, v));
  }

  const response = await fetch(url.toString());
  if (!response.ok) {
    throw new Error(`API ${response.status}: ${response.statusText}`);
  }
  return response.json();
}

export async function fetchLayerData<K extends keyof LayerData>(
  layer: K,
  params?: Record<string, string>,
): Promise<LayerData[K]> {
  return request<LayerData[K]>(`${BASE_URL}/layers/${layer}`, params);
}

export async function searchEntities(
  query: string,
): Promise<{ results: Array<{ type: keyof LayerData; id: string; label: string; data: unknown }> }> {
  return request(`${BASE_URL}/search`, { q: query });
}

export async function fetchSituationReport(region: string): Promise<SituationReport> {
  return request<SituationReport>(`${BASE_URL}/intelligence/sitrep`, { region });
}

export async function fetchHealth(): Promise<{ status: string; uptime: number }> {
  return request(`${BASE_URL}/health`);
}
