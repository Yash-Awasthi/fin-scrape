// ── Overlay data constants for the 2D IntelMap ──
// Zone data shared between the 2D map and potential 3D globe consumers.
// All coordinates stored as [lon, lat] — consumers must flip to [lat, lon] for Leaflet.

// ────────────────────────────────────────────
//  No-Fly Zones
// ────────────────────────────────────────────

export interface NoFlyZone {
  id: string;
  label: string;
  startDate: string;
  endDate?: string;
  polygon: [number, number][]; // [lon, lat] pairs
  center: [number, number];
  color: string;
}

export const NO_FLY_ZONES: NoFlyZone[] = [
  {
    id: 'nfz-iran',
    label: 'IRAN AIRSPACE CLOSED',
    startDate: '2026-02-28',
    polygon: [
      [44.0, 39.5], [48.5, 38.5], [54.0, 37.5], [60.5, 36.5], [63.0, 34.0],
      [63.5, 27.0], [61.5, 25.3], [57.5, 25.5], [54.0, 26.5], [51.5, 27.8],
      [49.0, 29.5], [48.0, 30.5], [45.5, 33.5], [44.0, 35.5], [44.0, 39.5],
    ],
    center: [54, 33],
    color: '#e74c3c',
  },
  {
    id: 'nfz-iraq',
    label: 'IRAQ AIRSPACE CLOSED',
    startDate: '2026-02-28',
    polygon: [
      [38.8, 37.2], [42.0, 37.3], [44.8, 37.1], [46.0, 35.0],
      [48.0, 30.5], [47.5, 29.5], [44.5, 29.0], [39.0, 32.5], [38.8, 37.2],
    ],
    center: [43.5, 33],
    color: '#e74c3c',
  },
  {
    id: 'nfz-kuwait',
    label: 'KUWAIT CLOSED',
    startDate: '2026-03-01',
    polygon: [
      [46.5, 30.1], [48.5, 30.1], [48.5, 28.5], [46.5, 28.5], [46.5, 30.1],
    ],
    center: [47.5, 29.3],
    color: '#f39c12',
  },
  {
    id: 'nfz-bahrain',
    label: 'BAHRAIN RESTRICTED',
    startDate: '2026-03-01',
    polygon: [
      [50.2, 26.4], [50.8, 26.4], [50.8, 25.8], [50.2, 25.8], [50.2, 26.4],
    ],
    center: [50.5, 26.1],
    color: '#f39c12',
  },
  {
    id: 'nfz-qatar',
    label: 'QATAR RESTRICTED',
    startDate: '2026-03-01',
    polygon: [
      [50.7, 26.2], [51.7, 26.2], [51.7, 24.5], [50.7, 24.5], [50.7, 26.2],
    ],
    center: [51.2, 25.3],
    color: '#f39c12',
  },
  {
    id: 'nfz-uae',
    label: 'UAE RESTRICTED',
    startDate: '2026-03-01',
    polygon: [
      [51.5, 26.1], [56.4, 26.1], [56.4, 22.6], [52.0, 22.6],
      [51.5, 24.0], [51.5, 26.1],
    ],
    center: [54.5, 24.5],
    color: '#f39c12',
  },
];

// ────────────────────────────────────────────
//  GPS Jamming Zones
// ────────────────────────────────────────────

export interface GpsJammingZone {
  id: string;
  label: string;
  center: [number, number]; // [lon, lat]
  radiusKm: number;
  startDate: string;
  endDate?: string;
  severity: 'high' | 'medium' | 'low';
  source?: string;
}

export const GPS_JAMMING_ZONES: GpsJammingZone[] = [
  {
    id: 'jam-tehran',
    label: 'GPS JAMMING TEHRAN',
    center: [51.4, 35.7],
    radiusKm: 80,
    startDate: '2026-02-28',
    severity: 'high',
    source: 'ADSB anomaly reports',
  },
  {
    id: 'jam-isfahan',
    label: 'GPS JAMMING ISFAHAN/NATANZ',
    center: [51.7, 32.8],
    radiusKm: 60,
    startDate: '2026-02-28',
    severity: 'high',
    source: 'ADSB anomaly reports',
  },
  {
    id: 'jam-bushehr',
    label: 'GPS SPOOFING BUSHEHR',
    center: [50.8, 28.9],
    radiusKm: 45,
    startDate: '2026-02-28',
    severity: 'medium',
    source: 'Maritime GPS disruption',
  },
  {
    id: 'jam-hormuz',
    label: 'GPS DISRUPTION HORMUZ',
    center: [56.3, 26.6],
    radiusKm: 70,
    startDate: '2026-03-01',
    severity: 'medium',
    source: 'IRGCN electronic warfare',
  },
  {
    id: 'jam-tabriz',
    label: 'GPS JAMMING TABRIZ AD',
    center: [46.3, 38.1],
    radiusKm: 40,
    startDate: '2026-03-01',
    severity: 'low',
    source: 'Air defense EW activity',
  },
  {
    id: 'jam-bandar',
    label: 'GPS SPOOFING BANDAR ABBAS',
    center: [56.3, 27.2],
    radiusKm: 50,
    startDate: '2026-02-28',
    severity: 'high',
    source: 'IRGCN naval EW',
  },
];

export const GPS_SEVERITY_COLORS: Record<string, string> = {
  high: '#ff2244',
  medium: '#ff6644',
  low: '#ff9944',
};

export const GPS_SEVERITY_ALPHA: Record<string, number> = {
  high: 0.18,
  medium: 0.12,
  low: 0.08,
};

// ────────────────────────────────────────────
//  Internet Blackout Zones
// ────────────────────────────────────────────

export interface InternetBlackout {
  id: string;
  label: string;
  region: string;
  polygon: [number, number][]; // [lon, lat]
  center: [number, number];
  startDate: string;
  endDate?: string;
  severity: 'total' | 'major' | 'partial';
  source?: string;
}

export const INTERNET_BLACKOUTS: InternetBlackout[] = [
  {
    id: 'blackout-tehran',
    label: 'TEHRAN INTERNET BLACKOUT',
    region: 'Tehran Province',
    polygon: [
      [50.5, 36.2], [52.5, 36.2], [52.5, 35.0], [50.5, 35.0], [50.5, 36.2],
    ],
    center: [51.4, 35.7],
    startDate: '2026-02-28',
    severity: 'total',
    source: 'NetBlocks / IODA',
  },
  {
    id: 'blackout-isfahan',
    label: 'ISFAHAN INTERNET DISRUPTION',
    region: 'Isfahan Province',
    polygon: [
      [50.5, 33.5], [52.5, 33.5], [52.5, 32.0], [50.5, 32.0], [50.5, 33.5],
    ],
    center: [51.7, 32.7],
    startDate: '2026-02-28',
    severity: 'major',
    source: 'NetBlocks / Cloudflare Radar',
  },
  {
    id: 'blackout-shiraz',
    label: 'SHIRAZ INTERNET DISRUPTION',
    region: 'Fars Province',
    polygon: [
      [51.5, 30.2], [53.0, 30.2], [53.0, 29.0], [51.5, 29.0], [51.5, 30.2],
    ],
    center: [52.5, 29.6],
    startDate: '2026-03-01',
    severity: 'major',
    source: 'NetBlocks',
  },
  {
    id: 'blackout-mashhad',
    label: 'MASHHAD PARTIAL BLACKOUT',
    region: 'Khorasan Razavi',
    polygon: [
      [58.5, 37.0], [60.0, 37.0], [60.0, 35.8], [58.5, 35.8], [58.5, 37.0],
    ],
    center: [59.6, 36.3],
    startDate: '2026-03-01',
    severity: 'partial',
    source: 'IODA / Kentik',
  },
  {
    id: 'blackout-tabriz',
    label: 'TABRIZ PARTIAL BLACKOUT',
    region: 'East Azerbaijan',
    polygon: [
      [45.5, 38.5], [47.0, 38.5], [47.0, 37.5], [45.5, 37.5], [45.5, 38.5],
    ],
    center: [46.3, 38.1],
    startDate: '2026-03-01',
    severity: 'partial',
    source: 'NetBlocks',
  },
];

export const BLACKOUT_STYLES: Record<string, { color: string; fillAlpha: number; outlineAlpha: number }> = {
  total: { color: '#ff2244', fillAlpha: 0.15, outlineAlpha: 0.6 },
  major: { color: '#ff6644', fillAlpha: 0.10, outlineAlpha: 0.5 },
  partial: { color: '#ff9944', fillAlpha: 0.07, outlineAlpha: 0.4 },
};

// ────────────────────────────────────────────
//  Weather Grid
// ────────────────────────────────────────────

export const WEATHER_GRID = [
  { lat: 35.69, lon: 51.39, label: 'Tehran' },
  { lat: 32.65, lon: 51.68, label: 'Isfahan' },
  { lat: 30.28, lon: 57.07, label: 'Kerman' },
  { lat: 33.51, lon: 51.73, label: 'Natanz' },
  { lat: 33.32, lon: 44.37, label: 'Baghdad' },
  { lat: 29.38, lon: 47.99, label: 'Kuwait City' },
  { lat: 26.07, lon: 50.56, label: 'Bahrain' },
  { lat: 25.29, lon: 51.53, label: 'Doha' },
  { lat: 25.20, lon: 55.27, label: 'Dubai' },
  { lat: 24.47, lon: 54.37, label: 'Abu Dhabi' },
  { lat: 26.50, lon: 56.50, label: 'Hormuz' },
  { lat: 38.07, lon: 46.30, label: 'Tabriz' },
  { lat: 29.62, lon: 52.53, label: 'Shiraz' },
  { lat: 36.30, lon: 59.60, label: 'Mashhad' },
];

export const WIND_ARROWS: Record<string, string> = {
  N: '\u2191', NE: '\u2197', E: '\u2192', SE: '\u2198',
  S: '\u2193', SW: '\u2199', W: '\u2190', NW: '\u2196',
};

export function windDirLabel(deg: number): string {
  const dirs = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'];
  return dirs[Math.round(deg / 45) % 8];
}

// ────────────────────────────────────────────
//  Geometry helpers
// ────────────────────────────────────────────

/**
 * Generate hexagonal polygon vertices as [lat, lon] pairs for Leaflet.
 * Leaflet uses [lat, lon] order, so the output is ready for Leaflet Polygon.
 */
export function hexagonLatLngs(
  centerLon: number,
  centerLat: number,
  radiusKm: number,
): [number, number][] {
  const dLat = radiusKm / 111;
  const dLon = radiusKm / (111 * Math.cos((centerLat * Math.PI) / 180));
  const positions: [number, number][] = [];
  for (let i = 0; i < 6; i++) {
    const angle = (Math.PI / 3) * i - Math.PI / 6;
    const lon = centerLon + dLon * Math.cos(angle);
    const lat = centerLat + dLat * Math.sin(angle);
    positions.push([lat, lon]); // [lat, lon] for Leaflet
  }
  return positions;
}
