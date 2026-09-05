import axios from 'axios';
import {
  twoline2satrec,
  propagate,
  gstime,
  eciToGeodetic,
  degreesLong,
  degreesLat,
  SatRec,
} from 'satellite.js';
import { Satellite } from '../types';
import { cacheGet, cacheSet } from '../utils/cache';

const CELESTRAK_URL = 'https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=tle';
const TLE_CACHE_KEY = 'satellites:tle_raw';
const SAT_CACHE_KEY = 'satellites:positions';
const TLE_TTL = 3600;
const POS_TTL = 30;

interface TLERecord {
  name: string;
  line1: string;
  line2: string;
}

function categorizeSatellite(name: string): Satellite['category'] {
  const upper = name.toUpperCase();
  if (upper.includes('ISS') || upper.includes('ZARYA')) return 'iss';
  if (upper.includes('STARLINK')) return 'starlink';
  if (upper.includes('GPS') || upper.includes('NAVSTAR') || upper.includes('GLONASS') || upper.includes('GALILEO') || upper.includes('BEIDOU')) return 'navigation';
  if (upper.includes('NOAA') || upper.includes('METEOSAT') || upper.includes('GOES') || upper.includes('HIMAWARI') || upper.includes('METEOR-M')) return 'weather';
  if (upper.includes('USA ') || upper.includes('NROL') || upper.includes('COSMO-SKYMED') || upper.includes('LACROSSE')) return 'military';
  if (upper.includes('TDRS') || upper.includes('INTELSAT') || upper.includes('SES') || upper.includes('IRIDIUM') || upper.includes('GLOBALSTAR') || upper.includes('ORBCOMM')) return 'communication';
  if (upper.includes('HUBBLE') || upper.includes('TERRA') || upper.includes('AQUA') || upper.includes('LANDSAT') || upper.includes('SENTINEL') || upper.includes('JAMES WEBB')) return 'scientific';
  return 'unknown';
}

function classifyOrbit(periodMinutes: number): Satellite['orbitType'] {
  if (periodMinutes < 128) return 'LEO';
  if (periodMinutes < 800) return 'MEO';
  if (periodMinutes > 1400 && periodMinutes < 1500) return 'GEO';
  return 'HEO';
}

function parseTLEData(raw: string): TLERecord[] {
  const lines = raw.trim().split('\n').map((l) => l.trim()).filter(Boolean);
  const records: TLERecord[] = [];
  for (let i = 0; i + 2 < lines.length; i += 3) {
    if (lines[i + 1]?.startsWith('1 ') && lines[i + 2]?.startsWith('2 ')) {
      records.push({ name: lines[i], line1: lines[i + 1], line2: lines[i + 2] });
    }
  }
  return records;
}

export function propagateSatellitePosition(tle: TLERecord): Satellite | null {
  try {
    const satrec: SatRec = twoline2satrec(tle.line1, tle.line2);
    const now = new Date();
    const result = propagate(satrec, now);

    if (typeof result.position === 'boolean' || !result.position) return null;

    const gmst = gstime(now);
    const geo = eciToGeodetic(result.position, gmst);

    const lat = degreesLat(geo.latitude);
    const lng = degreesLong(geo.longitude);
    const alt = geo.height;

    if (isNaN(lat) || isNaN(lng)) return null;

    const vel = typeof result.velocity !== 'boolean' && result.velocity
      ? Math.sqrt(result.velocity.x ** 2 + result.velocity.y ** 2 + result.velocity.z ** 2)
      : 0;

    const noradId = parseInt(tle.line1.substring(2, 7).trim(), 10);
    const inclination = parseFloat(tle.line2.substring(8, 16).trim());
    const meanMotion = parseFloat(tle.line2.substring(52, 63).trim());
    const period = meanMotion > 0 ? 1440 / meanMotion : 0;

    return {
      id: noradId,
      name: tle.name.trim(),
      noradId,
      position: { lat, lng, alt },
      velocity: vel,
      category: categorizeSatellite(tle.name),
      orbitType: classifyOrbit(period),
      inclination,
      period,
      timestamp: Date.now() / 1000,
    };
  } catch {
    return null;
  }
}

async function fetchTLEData(): Promise<TLERecord[]> {
  const cached = await cacheGet(TLE_CACHE_KEY);
  if (cached) return JSON.parse(cached) as TLERecord[];

  const { data } = await axios.get<string>(CELESTRAK_URL, {
    timeout: 30000,
    responseType: 'text',
  });

  const records = parseTLEData(data);
  if (records.length > 0) {
    await cacheSet(TLE_CACHE_KEY, JSON.stringify(records), TLE_TTL);
  }
  return records;
}

function seededRandom(seed: number): number {
  const x = Math.sin(seed) * 10000;
  return x - Math.floor(x);
}

function generateMockSatellites(): Satellite[] {
  const now = Date.now();
  const timeFactor = now / 90000; // orbital period ~90 min for LEO
  const sats: Satellite[] = [];

  // ISS
  const issAngle = (timeFactor * 2 * Math.PI) % (2 * Math.PI);
  sats.push({
    id: 25544, name: 'ISS (ZARYA)', noradId: 25544,
    position: { lat: 51.6 * Math.sin(issAngle), lng: ((issAngle * 180 / Math.PI * 4) % 360) - 180, alt: 420 },
    velocity: 7.66, category: 'iss', orbitType: 'LEO', inclination: 51.6, period: 92, timestamp: now / 1000,
  });

  // Starlink constellation
  for (let i = 0; i < 200; i++) {
    const plane = i % 20;
    const slot = Math.floor(i / 20);
    const angle = (timeFactor * 2 * Math.PI + plane * Math.PI / 10 + slot * Math.PI * 2 / 10) % (2 * Math.PI);
    const incl = 53 + (plane % 3) * 4;
    sats.push({
      id: 70000 + i, name: `STARLINK-${1000 + i}`, noradId: 70000 + i,
      position: {
        lat: incl * Math.sin(angle) * (0.8 + seededRandom(i * 7) * 0.2),
        lng: ((angle * 180 / Math.PI * (3 + seededRandom(i * 11))) % 360) - 180,
        alt: 550 + seededRandom(i * 13) * 10,
      },
      velocity: 7.59, category: 'starlink', orbitType: 'LEO', inclination: incl, period: 95, timestamp: now / 1000,
    });
  }

  // GPS constellation
  const gpsNames = ['NAVSTAR', 'GPS BIIR', 'GPS BIIF', 'GPS III'];
  for (let i = 0; i < 31; i++) {
    const plane = i % 6;
    const angle = (timeFactor * 0.5 * Math.PI + plane * Math.PI / 3 + i * Math.PI * 2 / 31) % (2 * Math.PI);
    sats.push({
      id: 40000 + i, name: `${gpsNames[i % gpsNames.length]}-${i + 1}`, noradId: 40000 + i,
      position: {
        lat: 55 * Math.sin(angle + i * 0.5),
        lng: ((angle * 180 / Math.PI * 2 + i * 30) % 360) - 180,
        alt: 20200,
      },
      velocity: 3.87, category: 'navigation', orbitType: 'MEO', inclination: 55, period: 718, timestamp: now / 1000,
    });
  }

  // Military / reconnaissance
  const milNames = ['USA 314', 'USA 326', 'NROL-82', 'NROL-87', 'LACROSSE 5', 'USA 338', 'KH-11', 'MISTY 2'];
  for (let i = 0; i < milNames.length; i++) {
    const angle = (timeFactor * 2.5 + i * Math.PI / 4) % (2 * Math.PI);
    sats.push({
      id: 50000 + i, name: milNames[i], noradId: 50000 + i,
      position: {
        lat: 97 * Math.sin(angle) * 0.6,
        lng: ((angle * 180 / Math.PI * 3 + i * 45) % 360) - 180,
        alt: 400 + seededRandom(i * 31) * 500,
      },
      velocity: 7.5, category: 'military', orbitType: 'LEO', inclination: 97, period: 94, timestamp: now / 1000,
    });
  }

  // Weather satellites
  const wxNames = ['NOAA 20', 'NOAA 21', 'METEOSAT-12', 'GOES-18', 'HIMAWARI-9', 'METEOR-M 2-3', 'FY-4B'];
  for (let i = 0; i < wxNames.length; i++) {
    const isGeo = wxNames[i].includes('GOES') || wxNames[i].includes('METEOSAT') || wxNames[i].includes('HIMAWARI') || wxNames[i].includes('FY-4');
    const geoLng = [-137.2, 0, 140.7, 105][i % 4];
    sats.push({
      id: 60000 + i, name: wxNames[i], noradId: 60000 + i,
      position: isGeo
        ? { lat: (seededRandom(i * 41) - 0.5) * 2, lng: geoLng, alt: 35786 }
        : { lat: 99 * Math.sin((timeFactor * 2 + i) % (2 * Math.PI)) * 0.5, lng: ((timeFactor * 200 + i * 50) % 360) - 180, alt: 830 },
      velocity: isGeo ? 3.07 : 7.45, category: 'weather', orbitType: isGeo ? 'GEO' : 'LEO',
      inclination: isGeo ? 0.1 : 99, period: isGeo ? 1436 : 101, timestamp: now / 1000,
    });
  }

  // Communication satellites
  const comNames = ['IRIDIUM 180', 'IRIDIUM 181', 'INTELSAT 40e', 'SES-17', 'GLOBALSTAR M098', 'ORBCOMM-FM44', 'TDRS-13'];
  for (let i = 0; i < comNames.length; i++) {
    const isGeo = comNames[i].includes('INTELSAT') || comNames[i].includes('SES') || comNames[i].includes('TDRS');
    sats.push({
      id: 55000 + i, name: comNames[i], noradId: 55000 + i,
      position: isGeo
        ? { lat: (seededRandom(i * 59) - 0.5) * 1, lng: ((i * 72 + 30) % 360) - 180, alt: 35786 }
        : { lat: 86 * Math.sin((timeFactor * 1.8 + i * 0.8) % (2 * Math.PI)) * 0.7, lng: ((timeFactor * 220 + i * 40) % 360) - 180, alt: 780 },
      velocity: isGeo ? 3.07 : 7.46, category: 'communication', orbitType: isGeo ? 'GEO' : 'LEO',
      inclination: isGeo ? 0 : 86, period: isGeo ? 1436 : 100, timestamp: now / 1000,
    });
  }

  // Scientific
  const sciNames = ['HUBBLE', 'TERRA', 'AQUA', 'LANDSAT 9', 'SENTINEL-2A', 'SENTINEL-6A', 'JASON-3'];
  for (let i = 0; i < sciNames.length; i++) {
    const angle = (timeFactor * 2.2 + i * 0.9) % (2 * Math.PI);
    sats.push({
      id: 65000 + i, name: sciNames[i], noradId: 65000 + i,
      position: {
        lat: 98 * Math.sin(angle) * 0.55,
        lng: ((angle * 180 / Math.PI * 3.5 + i * 50) % 360) - 180,
        alt: sciNames[i] === 'HUBBLE' ? 540 : 700 + seededRandom(i * 47) * 200,
      },
      velocity: 7.5, category: 'scientific', orbitType: 'LEO', inclination: 98, period: 98, timestamp: now / 1000,
    });
  }

  return sats;
}

export async function fetchSatellites(): Promise<Satellite[]> {
  try {
    const posCached = await cacheGet(SAT_CACHE_KEY);
    if (posCached) return JSON.parse(posCached) as Satellite[];

    const tleRecords = await fetchTLEData();
    if (tleRecords.length === 0) throw new Error('No TLE data');

    const satellites: Satellite[] = [];
    const sampleSize = Math.min(tleRecords.length, 500);
    const step = Math.max(1, Math.floor(tleRecords.length / sampleSize));

    for (let i = 0; i < tleRecords.length && satellites.length < sampleSize; i += step) {
      const sat = propagateSatellitePosition(tleRecords[i]);
      if (sat) satellites.push(sat);
    }

    if (satellites.length > 0) {
      await cacheSet(SAT_CACHE_KEY, JSON.stringify(satellites), POS_TTL);
      return satellites;
    }
    throw new Error('Propagation returned no results');
  } catch (err) {
    console.log('[SatelliteService] CelesTrak unavailable — using mock data');
    const mock = generateMockSatellites();
    await cacheSet(SAT_CACHE_KEY, JSON.stringify(mock), POS_TTL);
    return mock;
  }
}
