import axios from 'axios';
import { ConflictEvent } from '../types';
import { cacheGet, cacheSet } from '../utils/cache';

const GDELT_API = 'https://api.gdeltproject.org/api/v2/doc/doc?query=conflict&mode=artlist&format=json';
const CACHE_KEY = 'conflicts:all';
const CACHE_TTL = 300;

interface ConflictZone {
  country: string;
  region: string;
  center: { lat: number; lng: number };
  radius: number;
  eventTypes: ConflictEvent['eventType'][];
  severity: ConflictEvent['severity'];
  baseIntensity: number;
  description: string;
}

const CONFLICT_ZONES: ConflictZone[] = [
  {
    country: 'Ukraine', region: 'Donetsk Oblast', center: { lat: 48.0, lng: 37.8 },
    radius: 0.8, eventTypes: ['battle', 'explosion'], severity: 'red', baseIntensity: 8,
    description: 'Active frontline combat in eastern Ukraine',
  },
  {
    country: 'Ukraine', region: 'Zaporizhzhia Oblast', center: { lat: 47.2, lng: 35.5 },
    radius: 0.6, eventTypes: ['battle', 'explosion', 'strategic_development'], severity: 'red', baseIntensity: 7,
    description: 'Military operations near Zaporizhzhia',
  },
  {
    country: 'Ukraine', region: 'Kherson Oblast', center: { lat: 46.6, lng: 32.6 },
    radius: 0.5, eventTypes: ['battle', 'explosion'], severity: 'red', baseIntensity: 6,
    description: 'Cross-river artillery exchanges in Kherson',
  },
  {
    country: 'Ukraine', region: 'Kharkiv Oblast', center: { lat: 49.5, lng: 36.5 },
    radius: 0.7, eventTypes: ['explosion', 'battle'], severity: 'orange', baseIntensity: 6,
    description: 'Sporadic shelling and drone attacks near Kharkiv',
  },
  {
    country: 'Ukraine', region: 'Luhansk Oblast', center: { lat: 48.9, lng: 38.5 },
    radius: 0.6, eventTypes: ['battle', 'explosion'], severity: 'red', baseIntensity: 7,
    description: 'Ongoing hostilities in Luhansk region',
  },
  {
    country: 'Palestine', region: 'Gaza Strip', center: { lat: 31.4, lng: 34.4 },
    radius: 0.2, eventTypes: ['battle', 'explosion', 'violence_against_civilians'], severity: 'red', baseIntensity: 9,
    description: 'Intense military operations in Gaza',
  },
  {
    country: 'Syria', region: 'Idlib', center: { lat: 35.9, lng: 36.6 },
    radius: 0.5, eventTypes: ['battle', 'explosion', 'strategic_development'], severity: 'orange', baseIntensity: 5,
    description: 'Intermittent clashes in northwest Syria',
  },
  {
    country: 'Syria', region: 'Deir ez-Zor', center: { lat: 35.3, lng: 40.1 },
    radius: 0.4, eventTypes: ['battle', 'strategic_development'], severity: 'orange', baseIntensity: 4,
    description: 'ISIS remnant operations in eastern Syria',
  },
  {
    country: 'Sudan', region: 'Khartoum', center: { lat: 15.6, lng: 32.5 },
    radius: 0.3, eventTypes: ['battle', 'violence_against_civilians', 'protest'], severity: 'red', baseIntensity: 7,
    description: 'RSF–SAF clashes in Khartoum metropolitan area',
  },
  {
    country: 'Sudan', region: 'Darfur', center: { lat: 13.5, lng: 25.0 },
    radius: 1.0, eventTypes: ['battle', 'violence_against_civilians'], severity: 'red', baseIntensity: 6,
    description: 'Widespread violence across Darfur region',
  },
  {
    country: 'Yemen', region: 'Red Sea / Bab el-Mandeb', center: { lat: 13.0, lng: 43.5 },
    radius: 1.5, eventTypes: ['explosion', 'strategic_development'], severity: 'orange', baseIntensity: 5,
    description: 'Houthi attacks on commercial shipping in Red Sea',
  },
  {
    country: 'Myanmar', region: 'Sagaing', center: { lat: 22.0, lng: 95.5 },
    radius: 0.8, eventTypes: ['battle', 'violence_against_civilians'], severity: 'orange', baseIntensity: 5,
    description: 'Resistance forces clashing with military junta',
  },
  {
    country: 'Myanmar', region: 'Shan State', center: { lat: 21.0, lng: 97.5 },
    radius: 0.7, eventTypes: ['battle', 'strategic_development'], severity: 'orange', baseIntensity: 4,
    description: 'Ethnic armed organization offensives in Shan State',
  },
  {
    country: 'Ethiopia', region: 'Amhara', center: { lat: 11.5, lng: 38.5 },
    radius: 0.6, eventTypes: ['battle', 'protest', 'violence_against_civilians'], severity: 'orange', baseIntensity: 5,
    description: 'Fano militia insurgency in Amhara region',
  },
  {
    country: 'Ethiopia', region: 'Oromia', center: { lat: 8.5, lng: 39.0 },
    radius: 0.5, eventTypes: ['battle', 'violence_against_civilians'], severity: 'yellow', baseIntensity: 3,
    description: 'OLA activity in Oromia region',
  },
  {
    country: 'DR Congo', region: 'North Kivu', center: { lat: -1.0, lng: 29.0 },
    radius: 0.6, eventTypes: ['battle', 'violence_against_civilians'], severity: 'orange', baseIntensity: 6,
    description: 'M23 and ADF operations in eastern Congo',
  },
  {
    country: 'Somalia', region: 'Mogadishu', center: { lat: 2.05, lng: 45.3 },
    radius: 0.4, eventTypes: ['explosion', 'battle'], severity: 'orange', baseIntensity: 5,
    description: 'Al-Shabaab attacks and counter-operations',
  },
];

function seededRandom(seed: number): number {
  const x = Math.sin(seed) * 10000;
  return x - Math.floor(x);
}

function generateConflictEvents(): ConflictEvent[] {
  const events: ConflictEvent[] = [];
  const now = Date.now();
  let id = 0;

  for (const zone of CONFLICT_ZONES) {
    const eventCount = Math.max(2, Math.round(zone.baseIntensity * 1.5));

    for (let i = 0; i < eventCount; i++) {
      const seed = id * 31 + Math.floor(now / 300000);
      const eventType = zone.eventTypes[Math.floor(seededRandom(seed) * zone.eventTypes.length)];
      const offsetLat = (seededRandom(seed + 1) - 0.5) * 2 * zone.radius;
      const offsetLng = (seededRandom(seed + 2) - 0.5) * 2 * zone.radius;

      const fatalities = eventType === 'battle' || eventType === 'explosion'
        ? Math.floor(seededRandom(seed + 3) * zone.baseIntensity * 3)
        : eventType === 'violence_against_civilians'
          ? Math.floor(seededRandom(seed + 3) * zone.baseIntensity)
          : 0;

      const ageHours = seededRandom(seed + 4) * 24;

      events.push({
        id: `conflict-${id}`,
        eventType,
        position: {
          lat: zone.center.lat + offsetLat,
          lng: zone.center.lng + offsetLng,
        },
        country: zone.country,
        region: zone.region,
        description: `${zone.description} — ${eventType.replace(/_/g, ' ')} reported`,
        fatalities,
        severity: zone.severity,
        source: 'simulated',
        timestamp: (now - ageHours * 3600000) / 1000,
      });

      id++;
    }
  }

  return events;
}

interface GDELTArticle {
  title?: string;
  url?: string;
  seendate?: string;
}

async function fetchGDELTConflicts(): Promise<ConflictEvent[]> {
  try {
    const cached = await cacheGet('conflicts:gdelt');
    if (cached) return JSON.parse(cached) as ConflictEvent[];

    const { data } = await axios.get(GDELT_API, { timeout: 10000 });
    if (!data?.articles) return [];

    const events: ConflictEvent[] = (data.articles as GDELTArticle[])
      .slice(0, 20)
      .map((article: GDELTArticle, i: number) => ({
        id: `gdelt-${i}`,
        eventType: 'strategic_development' as const,
        position: { lat: 0, lng: 0 },
        country: 'Unknown',
        region: 'Unknown',
        description: article.title || 'GDELT conflict report',
        fatalities: 0,
        severity: 'yellow' as const,
        source: article.url || 'GDELT',
        timestamp: article.seendate ? new Date(article.seendate).getTime() / 1000 : Date.now() / 1000,
      }));

    if (events.length > 0) {
      await cacheSet('conflicts:gdelt', JSON.stringify(events), CACHE_TTL);
    }
    return events;
  } catch {
    return [];
  }
}

export async function fetchConflicts(): Promise<ConflictEvent[]> {
  try {
    const cached = await cacheGet(CACHE_KEY);
    if (cached) return JSON.parse(cached) as ConflictEvent[];

    const [simulated, gdelt] = await Promise.all([
      Promise.resolve(generateConflictEvents()),
      fetchGDELTConflicts(),
    ]);

    const allEvents = [...simulated, ...gdelt];
    await cacheSet(CACHE_KEY, JSON.stringify(allEvents), CACHE_TTL);
    return allEvents;
  } catch (err) {
    console.error('[ConflictService] Failed to fetch conflicts:', err instanceof Error ? err.message : err);
    return [];
  }
}
