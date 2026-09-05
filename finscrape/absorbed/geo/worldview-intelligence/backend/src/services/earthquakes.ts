import axios from 'axios';
import { Earthquake } from '../types';
import { cacheGet, cacheSet } from '../utils/cache';

const USGS_ALL_DAY = 'https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson';
const USGS_SIGNIFICANT = 'https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/significant_month.geojson';
const CACHE_KEY_ALL = 'earthquakes:all_day';
const CACHE_KEY_SIG = 'earthquakes:significant';
const CACHE_TTL = 60;

interface USGSFeature {
  id: string;
  properties: {
    mag: number;
    place: string;
    time: number;
    tsunami: number;
    status: string;
    felt: number | null;
    sig: number;
  };
  geometry: {
    coordinates: [number, number, number];
  };
}

interface USGSResponse {
  features: USGSFeature[];
}

function mapFeatureToEarthquake(feature: USGSFeature): Earthquake {
  const [lng, lat, depth] = feature.geometry.coordinates;
  return {
    id: feature.id,
    magnitude: feature.properties.mag ?? 0,
    depth,
    position: { lat, lng },
    place: feature.properties.place || 'Unknown',
    time: feature.properties.time,
    tsunami: feature.properties.tsunami === 1,
    status: feature.properties.status || 'automatic',
    felt: feature.properties.felt,
    significance: feature.properties.sig ?? 0,
  };
}

function seededRandom(seed: number): number {
  const x = Math.sin(seed) * 10000;
  return x - Math.floor(x);
}

function generateMockEarthquakes(): Earthquake[] {
  const now = Date.now();
  const zones: { lat: number; lng: number; range: number; place: string; maxMag: number }[] = [
    { lat: 36.0, lng: 140.0, range: 3, place: 'Japan', maxMag: 6.5 },
    { lat: -33.0, lng: -71.0, range: 5, place: 'Chile', maxMag: 7.0 },
    { lat: 38.0, lng: 22.0, range: 3, place: 'Greece', maxMag: 5.5 },
    { lat: 28.0, lng: 85.0, range: 3, place: 'Nepal', maxMag: 5.8 },
    { lat: 0.5, lng: 127.5, range: 4, place: 'Indonesia', maxMag: 6.0 },
    { lat: 19.0, lng: -155.0, range: 1, place: 'Hawaii', maxMag: 4.0 },
    { lat: 35.5, lng: -118.0, range: 3, place: 'California', maxMag: 5.0 },
    { lat: 39.0, lng: 44.0, range: 3, place: 'Turkey', maxMag: 5.5 },
    { lat: -5.0, lng: 152.0, range: 3, place: 'Papua New Guinea', maxMag: 6.2 },
    { lat: 61.0, lng: -150.0, range: 3, place: 'Alaska', maxMag: 5.5 },
    { lat: -22.0, lng: -68.0, range: 3, place: 'Argentina-Chile border', maxMag: 5.2 },
    { lat: 16.0, lng: -98.0, range: 2, place: 'Mexico', maxMag: 5.8 },
    { lat: -36.0, lng: 175.0, range: 2, place: 'New Zealand', maxMag: 5.0 },
    { lat: 42.0, lng: 44.5, range: 2, place: 'Georgia', maxMag: 4.5 },
  ];

  const quakes: Earthquake[] = [];
  let id = 0;

  for (const zone of zones) {
    const count = 3 + Math.floor(seededRandom(id * 31 + Math.floor(now / 300000)) * 5);
    for (let i = 0; i < count; i++) {
      const seed = id * 17 + Math.floor(now / 60000);
      const mag = 1.0 + seededRandom(seed) * zone.maxMag;
      const depth = 5 + seededRandom(seed + 1) * 300;
      const ageHours = seededRandom(seed + 2) * 24;

      quakes.push({
        id: `mock-eq-${id}`,
        magnitude: Math.round(mag * 10) / 10,
        depth: Math.round(depth * 10) / 10,
        position: {
          lat: zone.lat + (seededRandom(seed + 3) - 0.5) * 2 * zone.range,
          lng: zone.lng + (seededRandom(seed + 4) - 0.5) * 2 * zone.range,
        },
        place: `${Math.round(seededRandom(seed + 5) * 100)}km ${['N', 'S', 'E', 'W', 'NE', 'SW'][Math.floor(seededRandom(seed + 6) * 6)]} of ${zone.place}`,
        time: now - ageHours * 3600000,
        tsunami: mag > 6.5 && depth < 70,
        status: 'reviewed',
        felt: mag > 3 ? Math.floor(seededRandom(seed + 7) * 500) : null,
        significance: Math.floor(mag * 100),
      });
      id++;
    }
  }

  return quakes;
}

export async function fetchEarthquakes(): Promise<Earthquake[]> {
  try {
    const cached = await cacheGet(CACHE_KEY_ALL);
    if (cached) return JSON.parse(cached) as Earthquake[];

    const { data } = await axios.get<USGSResponse>(USGS_ALL_DAY, { timeout: 10000 });
    if (!data?.features || data.features.length === 0) throw new Error('No USGS data');

    const earthquakes = data.features.map(mapFeatureToEarthquake);
    await cacheSet(CACHE_KEY_ALL, JSON.stringify(earthquakes), CACHE_TTL);
    return earthquakes;
  } catch {
    console.log('[EarthquakeService] USGS unavailable — using mock data');
    const mock = generateMockEarthquakes();
    await cacheSet(CACHE_KEY_ALL, JSON.stringify(mock), CACHE_TTL);
    return mock;
  }
}

export async function fetchSignificantEarthquakes(): Promise<Earthquake[]> {
  try {
    const cached = await cacheGet(CACHE_KEY_SIG);
    if (cached) return JSON.parse(cached) as Earthquake[];

    const { data } = await axios.get<USGSResponse>(USGS_SIGNIFICANT, { timeout: 10000 });
    if (!data?.features) throw new Error('No USGS data');

    const earthquakes = data.features.map(mapFeatureToEarthquake);
    await cacheSet(CACHE_KEY_SIG, JSON.stringify(earthquakes), CACHE_TTL);
    return earthquakes;
  } catch {
    console.log('[EarthquakeService] USGS significant feed unavailable — using filtered mock');
    const all = generateMockEarthquakes();
    const sig = all.filter((e) => e.magnitude >= 5.0);
    await cacheSet(CACHE_KEY_SIG, JSON.stringify(sig), CACHE_TTL);
    return sig;
  }
}
