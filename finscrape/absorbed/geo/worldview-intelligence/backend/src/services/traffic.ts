import { TrafficData, TrafficIncident } from '../types';

interface CityConfig {
  city: string;
  position: { lat: number; lng: number };
  peakHoursUTC: number[];
  baseCongestion: number;
  baseSpeed: number;
  incidentZones: { lat: number; lng: number }[];
}

const CITIES: CityConfig[] = [
  {
    city: 'New York',
    position: { lat: 40.7128, lng: -74.006 },
    peakHoursUTC: [12, 13, 14, 22, 23, 0],
    baseCongestion: 65,
    baseSpeed: 25,
    incidentZones: [
      { lat: 40.758, lng: -73.985 }, { lat: 40.728, lng: -73.995 },
      { lat: 40.745, lng: -73.978 }, { lat: 40.695, lng: -73.985 },
    ],
  },
  {
    city: 'London',
    position: { lat: 51.5074, lng: -0.1278 },
    peakHoursUTC: [7, 8, 9, 16, 17, 18],
    baseCongestion: 60,
    baseSpeed: 22,
    incidentZones: [
      { lat: 51.515, lng: -0.142 }, { lat: 51.505, lng: -0.089 },
      { lat: 51.520, lng: -0.078 }, { lat: 51.497, lng: -0.135 },
    ],
  },
  {
    city: 'Dubai',
    position: { lat: 25.2048, lng: 55.2708 },
    peakHoursUTC: [4, 5, 6, 13, 14, 15],
    baseCongestion: 55,
    baseSpeed: 35,
    incidentZones: [
      { lat: 25.210, lng: 55.280 }, { lat: 25.190, lng: 55.260 },
      { lat: 25.076, lng: 55.133 },
    ],
  },
  {
    city: 'Tokyo',
    position: { lat: 35.6762, lng: 139.6503 },
    peakHoursUTC: [23, 0, 1, 7, 8, 9],
    baseCongestion: 70,
    baseSpeed: 20,
    incidentZones: [
      { lat: 35.681, lng: 139.767 }, { lat: 35.660, lng: 139.700 },
      { lat: 35.690, lng: 139.692 }, { lat: 35.645, lng: 139.710 },
    ],
  },
  {
    city: 'Paris',
    position: { lat: 48.8566, lng: 2.3522 },
    peakHoursUTC: [7, 8, 9, 17, 18, 19],
    baseCongestion: 62,
    baseSpeed: 24,
    incidentZones: [
      { lat: 48.860, lng: 2.340 }, { lat: 48.850, lng: 2.370 },
      { lat: 48.875, lng: 2.345 },
    ],
  },
  {
    city: 'Singapore',
    position: { lat: 1.3521, lng: 103.8198 },
    peakHoursUTC: [0, 1, 2, 9, 10, 11],
    baseCongestion: 50,
    baseSpeed: 30,
    incidentZones: [
      { lat: 1.290, lng: 103.852 }, { lat: 1.310, lng: 103.830 },
      { lat: 1.350, lng: 103.845 },
    ],
  },
];

const INCIDENT_DESCRIPTIONS: Record<TrafficIncident['type'], string[]> = {
  accident: [
    'Multi-vehicle collision on expressway',
    'Minor fender bender blocking right lane',
    'Overturned truck on highway ramp',
    'Pedestrian incident near intersection',
  ],
  construction: [
    'Road resurfacing — lane closure',
    'Bridge maintenance — reduced lanes',
    'Utility work — partial road closure',
    'Building construction — sidewalk detour',
  ],
  closure: [
    'Road closed for emergency repairs',
    'Event-related road closure',
    'Flooding — road impassable',
    'Police activity — road closure',
  ],
  congestion: [
    'Heavy congestion — expect delays',
    'Bottleneck forming near interchange',
    'Slow traffic due to high volume',
    'Rush hour congestion building',
  ],
};

function seededRandom(seed: number): number {
  const x = Math.sin(seed) * 10000;
  return x - Math.floor(x);
}

function generateTrafficForCity(city: CityConfig): TrafficData {
  const now = new Date();
  const utcHour = now.getUTCHours();
  const minuteSeed = Math.floor(now.getTime() / 60000);

  const isPeak = city.peakHoursUTC.includes(utcHour);
  const peakMultiplier = isPeak ? 1.4 + seededRandom(minuteSeed) * 0.3 : 0.6 + seededRandom(minuteSeed) * 0.3;

  const congestionLevel = Math.min(100, Math.round(city.baseCongestion * peakMultiplier));
  const speedReduction = peakMultiplier > 1 ? peakMultiplier * 0.6 : 1;
  const averageSpeed = Math.max(5, Math.round(city.baseSpeed / speedReduction));

  const incidentTypes: TrafficIncident['type'][] = ['accident', 'construction', 'closure', 'congestion'];
  const incidents: TrafficIncident[] = [];

  for (let i = 0; i < city.incidentZones.length; i++) {
    const seed = minuteSeed * 53 + i * 7 + city.city.charCodeAt(0);
    if (seededRandom(seed) > 0.45) continue;

    const type = incidentTypes[Math.floor(seededRandom(seed + 1) * incidentTypes.length)];
    const descriptions = INCIDENT_DESCRIPTIONS[type];
    const description = descriptions[Math.floor(seededRandom(seed + 2) * descriptions.length)];

    incidents.push({
      position: {
        lat: city.incidentZones[i].lat + (seededRandom(seed + 3) - 0.5) * 0.01,
        lng: city.incidentZones[i].lng + (seededRandom(seed + 4) - 0.5) * 0.01,
      },
      type,
      severity: Math.ceil(seededRandom(seed + 5) * 5),
      description,
    });
  }

  return {
    city: city.city,
    position: { lat: city.position.lat, lng: city.position.lng },
    congestionLevel,
    averageSpeed,
    incidents,
    timestamp: Date.now() / 1000,
  };
}

export async function fetchTrafficData(): Promise<TrafficData[]> {
  try {
    return CITIES.map(generateTrafficForCity);
  } catch (err) {
    console.error('[TrafficService] Failed to generate traffic data:', err instanceof Error ? err.message : err);
    return [];
  }
}
