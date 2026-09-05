import { Ship } from '../types';

interface RouteWaypoint {
  lat: number;
  lng: number;
}

interface ShippingRoute {
  name: string;
  waypoints: RouteWaypoint[];
  shipTypes: Ship['shipType'][];
  flags: string[];
}

const SHIPPING_ROUTES: ShippingRoute[] = [
  {
    name: 'Strait of Malacca',
    waypoints: [
      { lat: 1.27, lng: 103.85 }, { lat: 1.5, lng: 103.5 }, { lat: 2.0, lng: 102.5 },
      { lat: 2.5, lng: 101.5 }, { lat: 3.5, lng: 100.0 }, { lat: 5.0, lng: 98.0 },
      { lat: 6.0, lng: 96.0 },
    ],
    shipTypes: ['cargo', 'tanker', 'cargo', 'tanker', 'cargo'],
    flags: ['SG', 'PA', 'LR', 'MH', 'CN', 'JP', 'HK'],
  },
  {
    name: 'Suez Canal',
    waypoints: [
      { lat: 29.95, lng: 32.58 }, { lat: 30.05, lng: 32.56 }, { lat: 30.3, lng: 32.4 },
      { lat: 30.6, lng: 32.35 }, { lat: 31.0, lng: 32.3 }, { lat: 31.27, lng: 32.31 },
    ],
    shipTypes: ['cargo', 'tanker', 'passenger', 'cargo', 'tanker'],
    flags: ['PA', 'LR', 'MH', 'MT', 'GR', 'CY'],
  },
  {
    name: 'Panama Canal',
    waypoints: [
      { lat: 8.88, lng: -79.55 }, { lat: 9.0, lng: -79.6 }, { lat: 9.1, lng: -79.7 },
      { lat: 9.2, lng: -79.8 }, { lat: 9.28, lng: -79.92 },
    ],
    shipTypes: ['cargo', 'tanker', 'cargo', 'passenger'],
    flags: ['PA', 'LR', 'MH', 'BS', 'US'],
  },
  {
    name: 'English Channel',
    waypoints: [
      { lat: 50.1, lng: -5.7 }, { lat: 50.0, lng: -4.0 }, { lat: 50.2, lng: -2.0 },
      { lat: 50.5, lng: 0.0 }, { lat: 50.8, lng: 1.0 }, { lat: 51.0, lng: 1.5 },
      { lat: 51.3, lng: 2.0 },
    ],
    shipTypes: ['cargo', 'tanker', 'passenger', 'fishing', 'cargo'],
    flags: ['GB', 'FR', 'NL', 'DE', 'BE', 'PA', 'MT'],
  },
  {
    name: 'South China Sea',
    waypoints: [
      { lat: 1.3, lng: 104.0 }, { lat: 5.0, lng: 108.0 }, { lat: 10.0, lng: 112.0 },
      { lat: 15.0, lng: 115.0 }, { lat: 20.0, lng: 117.0 }, { lat: 22.0, lng: 114.5 },
    ],
    shipTypes: ['cargo', 'tanker', 'cargo', 'cargo'],
    flags: ['CN', 'HK', 'SG', 'JP', 'KR', 'PA'],
  },
  {
    name: 'Mediterranean',
    waypoints: [
      { lat: 36.0, lng: -5.3 }, { lat: 36.5, lng: -2.0 }, { lat: 37.0, lng: 2.0 },
      { lat: 37.5, lng: 6.0 }, { lat: 38.0, lng: 10.0 }, { lat: 37.5, lng: 15.0 },
      { lat: 36.0, lng: 20.0 }, { lat: 35.0, lng: 25.0 },
    ],
    shipTypes: ['cargo', 'tanker', 'passenger', 'cargo', 'naval'],
    flags: ['MT', 'GR', 'CY', 'IT', 'TR', 'PA', 'LR'],
  },
  {
    name: 'Persian Gulf',
    waypoints: [
      { lat: 26.5, lng: 56.5 }, { lat: 26.0, lng: 54.0 }, { lat: 26.5, lng: 52.0 },
      { lat: 27.5, lng: 50.5 }, { lat: 28.5, lng: 49.5 }, { lat: 29.5, lng: 48.5 },
    ],
    shipTypes: ['tanker', 'tanker', 'cargo', 'tanker', 'naval'],
    flags: ['PA', 'MH', 'LR', 'SA', 'AE', 'IR', 'KW'],
  },
  {
    name: 'Cape of Good Hope',
    waypoints: [
      { lat: -34.35, lng: 18.5 }, { lat: -35.0, lng: 20.0 }, { lat: -34.5, lng: 22.0 },
      { lat: -33.5, lng: 26.0 }, { lat: -31.0, lng: 30.0 }, { lat: -28.0, lng: 33.0 },
    ],
    shipTypes: ['tanker', 'cargo', 'tanker', 'cargo'],
    flags: ['PA', 'LR', 'MH', 'SG', 'ZA'],
  },
  {
    name: 'US East Coast',
    waypoints: [
      { lat: 25.8, lng: -80.1 }, { lat: 28.0, lng: -79.5 }, { lat: 32.0, lng: -79.0 },
      { lat: 36.8, lng: -75.5 }, { lat: 39.0, lng: -74.0 }, { lat: 40.5, lng: -73.8 },
    ],
    shipTypes: ['cargo', 'tanker', 'passenger', 'cargo'],
    flags: ['US', 'PA', 'LR', 'MH', 'BS'],
  },
  {
    name: 'North Sea',
    waypoints: [
      { lat: 51.9, lng: 4.5 }, { lat: 53.5, lng: 5.0 }, { lat: 55.0, lng: 5.5 },
      { lat: 56.5, lng: 6.0 }, { lat: 58.0, lng: 4.0 }, { lat: 59.5, lng: 2.0 },
    ],
    shipTypes: ['cargo', 'tanker', 'fishing', 'cargo'],
    flags: ['NL', 'NO', 'DK', 'GB', 'DE', 'SE'],
  },
];

const SHIP_NAMES_BY_TYPE: Record<Ship['shipType'], string[]> = {
  cargo: [
    'EVER GIVEN', 'MSC GÜLSÜN', 'HMM ALGECIRAS', 'MAERSK ELBA', 'CMA CGM MARCO POLO',
    'COSCO SHIPPING UNIVERSE', 'ONE COLUMBA', 'YANG MING WITNESS', 'EVERGREEN TRITON',
    'MSC OSCAR', 'MOL TRIUMPH', 'OOCL HONG KONG', 'HAPAG LLOYD BERLIN', 'ZIM TARRAGONA',
    'HYUNDAI DREAM', 'PACIFIC ENDEAVOR', 'ATLANTIC STAR', 'GLOBAL MERCY', 'SEA PIONEER',
    'OCEAN TRADER',
  ],
  tanker: [
    'FRONT ALTA', 'EURONAV CAPTAIN', 'VLCC PIONEER', 'CRUDE CARRIER I', 'STENA BULK',
    'TEEKAY SPIRIT', 'SCORPIO TANKERS', 'HAFNIA ANDES', 'TORM THUNDER', 'NORDIC STAR',
    'ATLANTIC TANKER', 'GULF ENERGY', 'ARABIAN SEA', 'PACIFIC VOYAGER', 'SUEZ MAX',
  ],
  passenger: [
    'SYMPHONY OF THE SEAS', 'MSC GRANDIOSA', 'WONDER OF THE SEAS', 'QUEEN MARY 2',
    'NORWEGIAN BLISS', 'CARNIVAL VISTA', 'CELEBRITY EDGE', 'AIDA NOVA', 'COSTA SMERALDA',
    'PRINCESS ROYAL',
  ],
  naval: [
    'USS EISENHOWER', 'HMS QUEEN ELIZABETH', 'FS CHARLES DE GAULLE', 'INS VIKRAMADITYA',
    'PLAN SHANDONG', 'USS GERALD FORD', 'HMS PRINCE OF WALES', 'JS IZUMO',
  ],
  fishing: [
    'ATLANTIC DAWN', 'NORTHERN EAGLE', 'PACIFIC HARVEST', 'CELTIC EXPLORER',
    'BLUE HORIZON', 'OCEAN BOUNTY', 'NORTH STAR', 'SEA HAWK',
  ],
  unknown: ['VESSEL UNKNOWN'],
};

function seededRandom(seed: number): number {
  const x = Math.sin(seed) * 10000;
  return x - Math.floor(x);
}

function interpolate(waypoints: RouteWaypoint[], t: number): RouteWaypoint {
  const totalSegments = waypoints.length - 1;
  const segFloat = t * totalSegments;
  const segIndex = Math.min(Math.floor(segFloat), totalSegments - 1);
  const segT = segFloat - segIndex;

  const p0 = waypoints[segIndex];
  const p1 = waypoints[segIndex + 1];
  return {
    lat: p0.lat + (p1.lat - p0.lat) * segT,
    lng: p0.lng + (p1.lng - p0.lng) * segT,
  };
}

function calculateHeading(from: RouteWaypoint, to: RouteWaypoint): number {
  const dLng = ((to.lng - from.lng) * Math.PI) / 180;
  const lat1 = (from.lat * Math.PI) / 180;
  const lat2 = (to.lat * Math.PI) / 180;
  const y = Math.sin(dLng) * Math.cos(lat2);
  const x = Math.cos(lat1) * Math.sin(lat2) - Math.sin(lat1) * Math.cos(lat2) * Math.cos(dLng);
  return ((Math.atan2(y, x) * 180) / Math.PI + 360) % 360;
}

function generateMMSI(index: number): string {
  return (200000000 + index * 1337 + 100000).toString().slice(0, 9);
}

let shipCache: Ship[] | null = null;
let lastGenTime = 0;

function generateShips(): Ship[] {
  const now = Date.now();
  const elapsed = (now - lastGenTime) / 1000;

  if (shipCache && elapsed < 5) return shipCache;

  const ships: Ship[] = [];
  let shipIndex = 0;

  for (const route of SHIPPING_ROUTES) {
    const shipsOnRoute = Math.floor(200 / SHIPPING_ROUTES.length) + (shipIndex < 200 % SHIPPING_ROUTES.length ? 1 : 0);

    for (let i = 0; i < shipsOnRoute; i++) {
      const seed = shipIndex * 7919 + 42;
      const shipType = route.shipTypes[shipIndex % route.shipTypes.length];
      const flag = route.flags[shipIndex % route.flags.length];
      const names = SHIP_NAMES_BY_TYPE[shipType];
      const name = names[shipIndex % names.length];

      const baseT = seededRandom(seed);
      const speed = 8 + seededRandom(seed + 1) * 14;
      const timeProgress = (now / 1000 / 3600) * (speed / 1000) * seededRandom(seed + 2);
      const t = (baseT + timeProgress) % 1;
      const tClamped = Math.abs(t > 0.5 ? 1 - t : t) * 2;

      const pos = interpolate(route.waypoints, Math.min(tClamped, 0.999));
      const jitter = 0.02;
      pos.lat += (seededRandom(seed + 3) - 0.5) * jitter;
      pos.lng += (seededRandom(seed + 4) - 0.5) * jitter;

      const nextT = Math.min(tClamped + 0.01, 0.999);
      const nextPos = interpolate(route.waypoints, nextT);
      const heading = calculateHeading(pos, nextPos);

      const destinations = [route.waypoints[route.waypoints.length - 1], route.waypoints[0]];
      const dest = tClamped < 0.5 ? destinations[0] : destinations[1];
      const destName = `${route.name} Terminal (${dest.lat.toFixed(1)}°, ${dest.lng.toFixed(1)}°)`;

      ships.push({
        mmsi: generateMMSI(shipIndex),
        name: `${name} ${(shipIndex + 1).toString().padStart(2, '0')}`,
        position: { lat: pos.lat, lng: pos.lng },
        speed,
        heading: Math.round(heading),
        shipType,
        flag,
        destination: destName,
        timestamp: now / 1000,
      });

      shipIndex++;
    }
  }

  shipCache = ships;
  lastGenTime = now;
  return ships;
}

export async function fetchShips(): Promise<Ship[]> {
  try {
    return generateShips();
  } catch (err) {
    console.error('[ShipService] Failed to generate ship data:', err instanceof Error ? err.message : err);
    return [];
  }
}
