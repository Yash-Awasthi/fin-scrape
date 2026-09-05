import axios from 'axios';
import { Aircraft } from '../types';
import { cacheGet, cacheSet } from '../utils/cache';

const OPENSKY_API = 'https://opensky-network.org/api/states/all';
const CACHE_KEY = 'aircraft:all';
const CACHE_TTL = 10;

// ---------------------------------------------------------------------------
// Callsign classification patterns
// ---------------------------------------------------------------------------

const MILITARY_CALLSIGN_PATTERNS = [
  /^RCH/i, /^DUKE/i, /^EVAC/i, /^CASA/i, /^CNV/i, /^TOPCAT/i,
  /^NATO/i, /^RRR/i, /^ASCOT/i, /^IAM/i, /^GAF/i, /^FAF/i,
  /^SPAR/i, /^SAM/i, /^EXEC/i, /^KNIFE/i, /^FORGE/i,
  /^DARKSTAR/i, /^GHOST/i, /^VIPER/i, /^HAWK/i, /^COBRA/i,
];

const CARGO_CALLSIGN_PATTERNS = [
  /^FDX/i, /^UPS/i, /^GTI/i, /^CLX/i, /^BOX/i,
  /^ABW/i, /^GEC/i, /^CAO/i, /^SQC/i, /^KAL\d{4}F/i,
];

// ---------------------------------------------------------------------------
// Airline database
// ---------------------------------------------------------------------------

const AIRLINE_DB: Record<string, { airline: string; country: string }> = {
  'UAE': { airline: 'Emirates', country: 'UAE' },
  'ETD': { airline: 'Etihad Airways', country: 'UAE' },
  'FDB': { airline: 'flydubai', country: 'UAE' },
  'QTR': { airline: 'Qatar Airways', country: 'Qatar' },
  'SVA': { airline: 'Saudia', country: 'Saudi Arabia' },
  'GFA': { airline: 'Gulf Air', country: 'Bahrain' },
  'BAW': { airline: 'British Airways', country: 'UK' },
  'DLH': { airline: 'Lufthansa', country: 'Germany' },
  'AFR': { airline: 'Air France', country: 'France' },
  'KLM': { airline: 'KLM', country: 'Netherlands' },
  'SIA': { airline: 'Singapore Airlines', country: 'Singapore' },
  'CPA': { airline: 'Cathay Pacific', country: 'Hong Kong' },
  'QFA': { airline: 'Qantas', country: 'Australia' },
  'ANA': { airline: 'All Nippon Airways', country: 'Japan' },
  'JAL': { airline: 'Japan Airlines', country: 'Japan' },
  'AAL': { airline: 'American Airlines', country: 'USA' },
  'DAL': { airline: 'Delta Air Lines', country: 'USA' },
  'UAL': { airline: 'United Airlines', country: 'USA' },
  'SWA': { airline: 'Southwest Airlines', country: 'USA' },
  'THY': { airline: 'Turkish Airlines', country: 'Turkey' },
  'EZY': { airline: 'easyJet', country: 'UK' },
  'RYR': { airline: 'Ryanair', country: 'Ireland' },
  'EK':  { airline: 'Emirates', country: 'UAE' },
  'FDX': { airline: 'FedEx', country: 'USA' },
  'UPS': { airline: 'UPS Airlines', country: 'USA' },
  'GTI': { airline: 'Atlas Air', country: 'USA' },
  'CLX': { airline: 'Cargolux', country: 'Luxembourg' },
  'AIC': { airline: 'Air India', country: 'India' },
  'CCA': { airline: 'Air China', country: 'China' },
  'CSN': { airline: 'China Southern', country: 'China' },
  'CES': { airline: 'China Eastern', country: 'China' },
  'KAL': { airline: 'Korean Air', country: 'South Korea' },
  'OMA': { airline: 'Oman Air', country: 'Oman' },
  'RJA': { airline: 'Royal Jordanian', country: 'Jordan' },
  'MSR': { airline: 'EgyptAir', country: 'Egypt' },
  'RAM': { airline: 'Royal Air Maroc', country: 'Morocco' },
  'ETH': { airline: 'Ethiopian Airlines', country: 'Ethiopia' },
  'SAA': { airline: 'South African Airways', country: 'South Africa' },
  'PAL': { airline: 'Philippine Airlines', country: 'Philippines' },
  'MAS': { airline: 'Malaysia Airlines', country: 'Malaysia' },
  'THA': { airline: 'Thai Airways', country: 'Thailand' },
  'VIR': { airline: 'Virgin Atlantic', country: 'UK' },
  'SWR': { airline: 'Swiss International', country: 'Switzerland' },
  'AUA': { airline: 'Austrian Airlines', country: 'Austria' },
  'TAP': { airline: 'TAP Portugal', country: 'Portugal' },
  'IBE': { airline: 'Iberia', country: 'Spain' },
  'SAS': { airline: 'Scandinavian Airlines', country: 'Sweden' },
  'FIN': { airline: 'Finnair', country: 'Finland' },
  'LOT': { airline: 'LOT Polish', country: 'Poland' },
};

// ---------------------------------------------------------------------------
// Aircraft type database (deterministic hash assignment)
// ---------------------------------------------------------------------------

const AIRCRAFT_TYPES = [
  'B777-300ER', 'B787-9', 'B737-800', 'B737 MAX 8', 'A380-800',
  'A350-900', 'A330-300', 'A320neo', 'A321neo', 'B747-8F',
  'B767-300F', 'B757-200', 'E190', 'CRJ-900', 'ATR 72-600',
];

function hashCallsign(callsign: string): number {
  let h = 0;
  for (let i = 0; i < callsign.length; i++) {
    h = ((h << 5) - h + callsign.charCodeAt(i)) | 0;
  }
  return Math.abs(h);
}

function getAircraftType(callsign: string): string {
  return AIRCRAFT_TYPES[hashCallsign(callsign) % AIRCRAFT_TYPES.length];
}

// ---------------------------------------------------------------------------
// Popular routes map
// ---------------------------------------------------------------------------

const ROUTE_DB: Record<string, { hub: string; destinations: string[] }> = {
  'UAE': { hub: 'DXB', destinations: ['LHR', 'JFK', 'SIN', 'BKK', 'SYD', 'CDG', 'FCO', 'NRT', 'ICN', 'BOM'] },
  'ETD': { hub: 'AUH', destinations: ['LHR', 'JFK', 'SIN', 'BKK', 'CDG'] },
  'FDB': { hub: 'DXB', destinations: ['CMB', 'KHI', 'DAC', 'CAI', 'IST'] },
  'BAW': { hub: 'LHR', destinations: ['JFK', 'DXB', 'SIN', 'HKG', 'NRT', 'LAX'] },
  'DLH': { hub: 'FRA', destinations: ['JFK', 'DXB', 'NRT', 'SIN', 'ORD'] },
  'THY': { hub: 'IST', destinations: ['DXB', 'LHR', 'JFK', 'CDG', 'FRA'] },
  'QTR': { hub: 'DOH', destinations: ['LHR', 'JFK', 'SIN', 'DXB', 'BKK'] },
  'SIA': { hub: 'SIN', destinations: ['LHR', 'SYD', 'NRT', 'HKG', 'DXB'] },
  'AAL': { hub: 'DFW', destinations: ['LHR', 'NRT', 'CDG', 'MIA', 'LAX'] },
  'DAL': { hub: 'ATL', destinations: ['LHR', 'CDG', 'NRT', 'AMS', 'JFK'] },
  'UAL': { hub: 'ORD', destinations: ['LHR', 'NRT', 'FRA', 'SIN', 'SYD'] },
  'AFR': { hub: 'CDG', destinations: ['JFK', 'NRT', 'DXB', 'SIN', 'LAX'] },
  'KLM': { hub: 'AMS', destinations: ['JFK', 'NRT', 'SIN', 'DXB', 'SFO'] },
  'CPA': { hub: 'HKG', destinations: ['LHR', 'JFK', 'SYD', 'NRT', 'SIN'] },
  'QFA': { hub: 'SYD', destinations: ['LHR', 'SIN', 'LAX', 'NRT', 'DXB'] },
  'ANA': { hub: 'NRT', destinations: ['LAX', 'JFK', 'LHR', 'SIN', 'SYD'] },
  'JAL': { hub: 'NRT', destinations: ['LAX', 'JFK', 'LHR', 'SIN', 'CDG'] },
  'EK':  { hub: 'DXB', destinations: ['LHR', 'JFK', 'SIN', 'BKK', 'SYD'] },
  'SWR': { hub: 'ZRH', destinations: ['JFK', 'BKK', 'SIN', 'SFO', 'DXB'] },
  'VIR': { hub: 'LHR', destinations: ['JFK', 'LAX', 'DXB', 'BOM', 'HKG'] },
  'AIC': { hub: 'DEL', destinations: ['LHR', 'JFK', 'SIN', 'DXB', 'BOM'] },
  'CCA': { hub: 'PEK', destinations: ['JFK', 'LAX', 'LHR', 'CDG', 'SIN'] },
  'CSN': { hub: 'CAN', destinations: ['SYD', 'LAX', 'NRT', 'SIN', 'LHR'] },
  'CES': { hub: 'PVG', destinations: ['LAX', 'JFK', 'LHR', 'SYD', 'SIN'] },
  'KAL': { hub: 'ICN', destinations: ['LAX', 'JFK', 'LHR', 'NRT', 'SIN'] },
  'OMA': { hub: 'MCT', destinations: ['DXB', 'LHR', 'BKK', 'SIN', 'KUL'] },
  'RJA': { hub: 'AMM', destinations: ['LHR', 'CDG', 'DXB', 'BKK', 'KUL'] },
  'MSR': { hub: 'CAI', destinations: ['LHR', 'CDG', 'JFK', 'DXB', 'IST'] },
  'ETH': { hub: 'ADD', destinations: ['DXB', 'LHR', 'JFK', 'NRT', 'PEK'] },
  'SVA': { hub: 'JED', destinations: ['LHR', 'JFK', 'CAI', 'IST', 'KUL'] },
  'GFA': { hub: 'BAH', destinations: ['DXB', 'LHR', 'BKK', 'MNL', 'IST'] },
  'THA': { hub: 'BKK', destinations: ['LHR', 'NRT', 'SYD', 'FRA', 'SIN'] },
  'MAS': { hub: 'KUL', destinations: ['LHR', 'NRT', 'SYD', 'DXB', 'SIN'] },
  'PAL': { hub: 'MNL', destinations: ['LAX', 'JFK', 'NRT', 'SIN', 'SYD'] },
  'RYR': { hub: 'DUB', destinations: ['STN', 'BCN', 'FCO', 'BER', 'AGP'] },
  'EZY': { hub: 'LGW', destinations: ['CDG', 'AMS', 'BCN', 'FCO', 'BER'] },
  'FDX': { hub: 'MEM', destinations: ['CDG', 'NRT', 'DXB', 'SIN', 'PVG'] },
  'UPS': { hub: 'SDF', destinations: ['CGN', 'PEK', 'NRT', 'HKG', 'DXB'] },
  'GTI': { hub: 'MIA', destinations: ['BOG', 'GRU', 'SCL', 'LIM', 'EZE'] },
  'CLX': { hub: 'LUX', destinations: ['DXB', 'HKG', 'NRT', 'ORD', 'PVG'] },
};

// ---------------------------------------------------------------------------
// Airport coordinates for hub aircraft generation
// ---------------------------------------------------------------------------

interface AirportInfo {
  lat: number;
  lng: number;
  count: number;
  airlines: string[];
}

const AIRPORT_HUBS: Record<string, AirportInfo> = {
  DXB: { lat: 25.25, lng: 55.36, count: 50, airlines: ['UAE', 'ETD', 'FDB', 'QTR', 'BAW', 'DLH', 'SIA', 'AIC', 'THY', 'AFR'] },
  LHR: { lat: 51.47, lng: -0.46, count: 40, airlines: ['BAW', 'VIR', 'AAL', 'UAL', 'DLH', 'AFR', 'UAE', 'SIA', 'QFA', 'CPA'] },
  JFK: { lat: 40.64, lng: -73.78, count: 40, airlines: ['AAL', 'DAL', 'UAL', 'BAW', 'DLH', 'AFR', 'UAE', 'SIA', 'JAL', 'ANA'] },
  SIN: { lat: 1.35, lng: 103.99, count: 30, airlines: ['SIA', 'QFA', 'CPA', 'MAS', 'THA', 'UAE', 'BAW', 'JAL', 'ANA', 'QTR'] },
  IST: { lat: 41.26, lng: 28.74, count: 30, airlines: ['THY', 'BAW', 'DLH', 'AFR', 'UAE', 'QTR', 'MSR', 'RJA', 'SVA', 'AUA'] },
  CDG: { lat: 49.01, lng: 2.55, count: 30, airlines: ['AFR', 'BAW', 'DLH', 'KLM', 'UAE', 'AAL', 'DAL', 'JAL', 'ANA', 'SIA'] },
  FRA: { lat: 50.03, lng: 8.57, count: 25, airlines: ['DLH', 'SWR', 'AUA', 'UAE', 'SIA', 'AAL', 'UAL', 'ANA', 'THY', 'AFR'] },
  NRT: { lat: 35.77, lng: 140.39, count: 25, airlines: ['ANA', 'JAL', 'SIA', 'CPA', 'BAW', 'DLH', 'AAL', 'UAL', 'DAL', 'KAL'] },
  DOH: { lat: 25.26, lng: 51.56, count: 25, airlines: ['QTR', 'UAE', 'BAW', 'DLH', 'THY', 'SIA', 'AIC', 'OMA', 'GFA', 'MSR'] },
  AUH: { lat: 24.44, lng: 54.65, count: 20, airlines: ['ETD', 'UAE', 'BAW', 'DLH', 'SIA', 'AIC', 'THY', 'QTR', 'KLM', 'AFR'] },
  BKK: { lat: 13.69, lng: 100.75, count: 20, airlines: ['THA', 'SIA', 'CPA', 'UAE', 'QTR', 'BAW', 'JAL', 'ANA', 'ETH', 'MAS'] },
  SYD: { lat: -33.95, lng: 151.18, count: 20, airlines: ['QFA', 'SIA', 'CPA', 'UAE', 'BAW', 'AAL', 'ANA', 'JAL', 'MAS', 'THA'] },
  LAX: { lat: 33.94, lng: -118.41, count: 25, airlines: ['AAL', 'DAL', 'UAL', 'SWA', 'BAW', 'QFA', 'SIA', 'ANA', 'JAL', 'KAL'] },
  ORD: { lat: 41.97, lng: -87.91, count: 25, airlines: ['AAL', 'UAL', 'DAL', 'SWA', 'DLH', 'BAW', 'JAL', 'ANA', 'KLM', 'AFR'] },
  ATL: { lat: 33.64, lng: -84.43, count: 25, airlines: ['DAL', 'AAL', 'UAL', 'SWA', 'BAW', 'AFR', 'KLM', 'DLH', 'UAE', 'JAL'] },
  HKG: { lat: 22.31, lng: 113.91, count: 20, airlines: ['CPA', 'SIA', 'BAW', 'UAE', 'QFA', 'ANA', 'JAL', 'KAL', 'THA', 'MAS'] },
  BOM: { lat: 19.09, lng: 72.87, count: 15, airlines: ['AIC', 'UAE', 'BAW', 'SIA', 'QTR', 'ETD', 'DLH', 'THY', 'ETH', 'AFR'] },
  DEL: { lat: 28.56, lng: 77.10, count: 15, airlines: ['AIC', 'UAE', 'BAW', 'SIA', 'QTR', 'ETD', 'DLH', 'THY', 'JAL', 'AFR'] },
  ICN: { lat: 37.46, lng: 126.44, count: 15, airlines: ['KAL', 'ANA', 'JAL', 'SIA', 'CPA', 'UAE', 'DLH', 'AAL', 'UAL', 'DAL'] },
};

// Map airport codes to coordinates for destination display
const AIRPORT_COORDS: Record<string, { lat: number; lng: number }> = {
  DXB: { lat: 25.25, lng: 55.36 }, LHR: { lat: 51.47, lng: -0.46 },
  JFK: { lat: 40.64, lng: -73.78 }, SIN: { lat: 1.35, lng: 103.99 },
  IST: { lat: 41.26, lng: 28.74 }, CDG: { lat: 49.01, lng: 2.55 },
  FRA: { lat: 50.03, lng: 8.57 }, NRT: { lat: 35.77, lng: 140.39 },
  DOH: { lat: 25.26, lng: 51.56 }, AUH: { lat: 24.44, lng: 54.65 },
  BKK: { lat: 13.69, lng: 100.75 }, SYD: { lat: -33.95, lng: 151.18 },
  LAX: { lat: 33.94, lng: -118.41 }, ORD: { lat: 41.97, lng: -87.91 },
  ATL: { lat: 33.64, lng: -84.43 }, HKG: { lat: 22.31, lng: 113.91 },
  BOM: { lat: 19.09, lng: 72.87 }, DEL: { lat: 28.56, lng: 77.10 },
  ICN: { lat: 37.46, lng: 126.44 }, SFO: { lat: 37.62, lng: -122.38 },
  AMS: { lat: 52.31, lng: 4.76 }, FCO: { lat: 41.80, lng: 12.25 },
  MIA: { lat: 25.80, lng: -80.29 }, DFW: { lat: 32.90, lng: -97.04 },
  PEK: { lat: 40.08, lng: 116.58 }, PVG: { lat: 31.14, lng: 121.81 },
  CAN: { lat: 23.39, lng: 113.30 }, KUL: { lat: 2.75, lng: 101.71 },
  MNL: { lat: 14.51, lng: 121.02 }, ZRH: { lat: 47.46, lng: 8.55 },
  MCT: { lat: 23.59, lng: 58.28 }, AMM: { lat: 31.72, lng: 35.99 },
  CAI: { lat: 30.12, lng: 31.41 }, ADD: { lat: 8.98, lng: 38.80 },
  JED: { lat: 21.68, lng: 39.16 }, BAH: { lat: 26.27, lng: 50.63 },
  DUB: { lat: 53.43, lng: -6.27 }, LGW: { lat: 51.15, lng: -0.19 },
  MEM: { lat: 35.04, lng: -89.98 }, SDF: { lat: 38.17, lng: -85.74 },
  LUX: { lat: 49.63, lng: 6.22 }, STN: { lat: 51.89, lng: 0.26 },
  BCN: { lat: 41.30, lng: 2.08 }, BER: { lat: 52.37, lng: 13.52 },
  AGP: { lat: 36.68, lng: -4.50 }, CGN: { lat: 50.87, lng: 7.14 },
  GRU: { lat: -23.43, lng: -46.47 }, BOG: { lat: 4.70, lng: -74.15 },
  SCL: { lat: -33.39, lng: -70.79 }, LIM: { lat: -12.02, lng: -77.11 },
  EZE: { lat: -34.82, lng: -58.54 }, CMB: { lat: 7.18, lng: 79.88 },
  KHI: { lat: 24.91, lng: 67.16 }, DAC: { lat: 23.84, lng: 90.40 },
};

// ---------------------------------------------------------------------------
// Utility
// ---------------------------------------------------------------------------

function seededRandom(seed: number): number {
  const x = Math.sin(seed) * 10000;
  return x - Math.floor(x);
}

export function classifyAircraft(callsign: string): Aircraft['category'] {
  const trimmed = callsign.trim();
  if (!trimmed) return 'unknown';
  if (MILITARY_CALLSIGN_PATTERNS.some((p) => p.test(trimmed))) return 'military';
  if (CARGO_CALLSIGN_PATTERNS.some((p) => p.test(trimmed))) return 'cargo';
  if (/^N\d{1,5}[A-Z]{0,2}$/i.test(trimmed)) return 'private';
  return 'commercial';
}

function mapStateToAircraft(state: unknown[]): Aircraft | null {
  const lat = state[6] as number | null;
  const lng = state[5] as number | null;
  if (lat == null || lng == null) return null;

  const callsign = ((state[1] as string) || '').trim();
  return {
    icao24: state[0] as string,
    callsign,
    originCountry: state[2] as string,
    position: { lat, lng, alt: (state[7] as number) ?? (state[13] as number) ?? undefined },
    velocity: (state[9] as number) ?? 0,
    heading: (state[10] as number) ?? 0,
    verticalRate: (state[11] as number) ?? 0,
    onGround: (state[8] as boolean) ?? false,
    squawk: (state[14] as string) ?? null,
    category: classifyAircraft(callsign),
    timestamp: (state[3] as number) ?? Date.now() / 1000,
  };
}

// ---------------------------------------------------------------------------
// Airline / route lookup helpers
// ---------------------------------------------------------------------------

function lookupAirline(callsign: string): { airline: string; country: string; prefix: string } | null {
  const upper = callsign.toUpperCase();
  for (const len of [3, 2]) {
    const prefix = upper.substring(0, len);
    if (AIRLINE_DB[prefix]) {
      return { ...AIRLINE_DB[prefix], prefix };
    }
  }
  return null;
}

function extractFlightNumber(callsign: string): string {
  return callsign.trim().toUpperCase();
}

function lookupRoute(callsign: string): { origin: string; destination: string } | null {
  const upper = callsign.trim().toUpperCase();

  for (const len of [3, 2]) {
    const prefix = upper.substring(0, len);
    const routeEntry = ROUTE_DB[prefix];
    if (!routeEntry) continue;

    const numPart = upper.substring(len).replace(/\D/g, '');
    const num = parseInt(numPart, 10);
    if (isNaN(num)) {
      return { origin: routeEntry.hub, destination: routeEntry.destinations[0] };
    }
    const idx = num % routeEntry.destinations.length;
    return { origin: routeEntry.hub, destination: routeEntry.destinations[idx] };
  }
  return null;
}

function generateFlightTimes(timestamp: number, callsign: string): { departureTime: string; arrivalTime: string } {
  const h = hashCallsign(callsign);
  const hoursAgo = (h % 8) + 1;
  const flightDuration = ((h >> 4) % 10) + 3; // 3-12 hours
  const dep = new Date((timestamp * 1000) - hoursAgo * 3600_000);
  const arr = new Date(dep.getTime() + flightDuration * 3600_000);
  return {
    departureTime: dep.toISOString(),
    arrivalTime: arr.toISOString(),
  };
}

// ---------------------------------------------------------------------------
// enrichAircraft — adds airline, route, and flight details to an Aircraft
// ---------------------------------------------------------------------------

function enrichAircraft(ac: Aircraft): Aircraft {
  const info = lookupAirline(ac.callsign);
  const routeInfo = lookupRoute(ac.callsign);
  const times = generateFlightTimes(ac.timestamp, ac.callsign);

  return {
    ...ac,
    airline: info?.airline,
    flightNumber: extractFlightNumber(ac.callsign),
    aircraftType: getAircraftType(ac.callsign),
    originAirport: routeInfo?.origin,
    destinationAirport: routeInfo?.destination,
    route: routeInfo ? `${routeInfo.origin} → ${routeInfo.destination}` : undefined,
    departureTime: times.departureTime,
    arrivalTime: times.arrivalTime,
  };
}

// ---------------------------------------------------------------------------
// Hub aircraft generation — dense traffic around major airports
// ---------------------------------------------------------------------------

function generateHubAircraft(): Aircraft[] {
  const aircraft: Aircraft[] = [];
  const now = Date.now();
  const timeFactor = Math.floor(now / 10000);
  let globalId = 0;

  for (const [hubCode, hub] of Object.entries(AIRPORT_HUBS)) {
    for (let i = 0; i < hub.count; i++) {
      const seed = timeFactor * 5 + globalId * 11 + i * 3;
      const airlinePrefix = hub.airlines[Math.floor(seededRandom(seed) * hub.airlines.length)];
      const flightNum = Math.floor(seededRandom(seed + 1) * 900 + 100);
      const callsign = `${airlinePrefix}${flightNum}`;

      // Position: spread within ~3 degrees of the hub
      const angle = seededRandom(seed + 2) * Math.PI * 2;
      const dist = seededRandom(seed + 3) * 3.0;
      const lat = hub.lat + Math.sin(angle) * dist;
      const lng = hub.lng + Math.cos(angle) * dist;

      // Altitude: close aircraft are lower (approaching/departing), farther are at cruise
      const altFactor = dist / 3.0;
      const alt = 1000 + altFactor * 11000 + seededRandom(seed + 4) * 1500;

      // Heading: inbound aircraft point toward hub, outbound point away
      const isInbound = seededRandom(seed + 5) > 0.5;
      const bearingToHub = Math.atan2(hub.lat - lat, hub.lng - lng) * (180 / Math.PI);
      const heading = isInbound
        ? ((bearingToHub % 360) + 360) % 360
        : ((bearingToHub + 180) % 360 + 360) % 360;

      const routeEntry = ROUTE_DB[airlinePrefix];
      let originAirport: string;
      let destinationAirport: string;

      if (isInbound) {
        destinationAirport = hubCode;
        originAirport = routeEntry
          ? routeEntry.destinations[flightNum % routeEntry.destinations.length]
          : hubCode;
      } else {
        originAirport = hubCode;
        destinationAirport = routeEntry
          ? routeEntry.destinations[flightNum % routeEntry.destinations.length]
          : hubCode;
      }

      const airlineInfo = AIRLINE_DB[airlinePrefix];
      const times = generateFlightTimes(now / 1000, callsign);
      const category = classifyAircraft(callsign);

      aircraft.push({
        icao24: `hub${globalId.toString(16).padStart(4, '0')}`,
        callsign,
        originCountry: airlineInfo?.country ?? 'Unknown',
        position: { lat, lng, alt },
        velocity: 180 + seededRandom(seed + 6) * 100,
        heading: heading + (seededRandom(seed + 7) - 0.5) * 15,
        verticalRate: isInbound ? -(seededRandom(seed + 8) * 6) : seededRandom(seed + 8) * 6,
        onGround: dist < 0.15 && seededRandom(seed + 9) > 0.6,
        squawk: null,
        category,
        timestamp: now / 1000,
        airline: airlineInfo?.airline,
        flightNumber: callsign,
        aircraftType: getAircraftType(callsign),
        originAirport,
        destinationAirport,
        route: `${originAirport} → ${destinationAirport}`,
        departureTime: times.departureTime,
        arrivalTime: times.arrivalTime,
      });

      globalId++;
    }
  }

  return aircraft;
}

// ---------------------------------------------------------------------------
// Scattered background fill (~80 aircraft worldwide)
// ---------------------------------------------------------------------------

function generateScatteredAircraft(): Aircraft[] {
  const regions = [
    { lat: 47.0, lng: 8.0, range: 10, count: 12, countries: ['France', 'Germany', 'Italy', 'Spain', 'Netherlands'] },
    { lat: 39.0, lng: -98.0, range: 15, count: 15, countries: ['United States'] },
    { lat: 35.0, lng: 136.0, range: 8, count: 8, countries: ['Japan', 'South Korea', 'China'] },
    { lat: 1.0, lng: 103.0, range: 12, count: 6, countries: ['Singapore', 'Malaysia', 'Indonesia', 'Thailand'] },
    { lat: 25.0, lng: 55.0, range: 10, count: 6, countries: ['UAE', 'Saudi Arabia', 'Qatar'] },
    { lat: -25.0, lng: 135.0, range: 10, count: 6, countries: ['Australia'] },
    { lat: 20.0, lng: 78.0, range: 8, count: 8, countries: ['India'] },
    { lat: -10.0, lng: -50.0, range: 12, count: 6, countries: ['Brazil', 'Argentina'] },
    { lat: 55.0, lng: -3.0, range: 5, count: 8, countries: ['United Kingdom', 'Ireland'] },
    { lat: 35.0, lng: 33.0, range: 8, count: 5, countries: ['Turkey', 'Greece', 'Egypt'] },
  ];

  const airlinePrefixes = ['AAL', 'DAL', 'UAL', 'SWA', 'BAW', 'DLH', 'AFR', 'KLM', 'RYR', 'EZY', 'THY', 'QFA', 'ANA', 'JAL', 'CPA', 'SIA', 'UAE', 'QTR'];
  const now = Date.now();
  const timeFactor = Math.floor(now / 10000);
  const aircraft: Aircraft[] = [];
  let id = 2000;

  for (const region of regions) {
    for (let i = 0; i < region.count; i++) {
      const seed = timeFactor * 3 + id * 7;
      const lat = region.lat + (seededRandom(seed) - 0.5) * 2 * region.range;
      const lng = region.lng + (seededRandom(seed + 1) - 0.5) * 2 * region.range;
      const alt = 8000 + seededRandom(seed + 2) * 5000;
      const prefix = airlinePrefixes[Math.floor(seededRandom(seed + 3) * airlinePrefixes.length)];
      const flightNum = Math.floor(seededRandom(seed + 4) * 9000 + 1000);
      const callsign = `${prefix}${flightNum}`;
      const country = region.countries[Math.floor(seededRandom(seed + 5) * region.countries.length)];

      const ac: Aircraft = {
        icao24: `sc${id.toString(16).padStart(4, '0')}`,
        callsign,
        originCountry: country,
        position: { lat, lng, alt },
        velocity: 180 + seededRandom(seed + 6) * 100,
        heading: seededRandom(seed + 7) * 360,
        verticalRate: (seededRandom(seed + 8) - 0.5) * 3,
        onGround: false,
        squawk: null,
        category: seededRandom(seed + 9) > 0.95 ? 'military' : 'commercial',
        timestamp: now / 1000,
      };

      aircraft.push(enrichAircraft(ac));
      id++;
    }
  }

  return aircraft;
}

// ---------------------------------------------------------------------------
// Public API — OpenSky with enrichment + mock fallback
// ---------------------------------------------------------------------------

export async function fetchAircraft(): Promise<Aircraft[]> {
  try {
    const cached = await cacheGet(CACHE_KEY);
    if (cached) return JSON.parse(cached) as Aircraft[];

    const { data } = await axios.get(OPENSKY_API, { timeout: 15000 });
    if (!data?.states || data.states.length === 0) throw new Error('No data from OpenSky');

    const aircraft: Aircraft[] = [];
    for (const state of data.states) {
      const mapped = mapStateToAircraft(state);
      if (mapped) aircraft.push(enrichAircraft(mapped));
    }

    await cacheSet(CACHE_KEY, JSON.stringify(aircraft), CACHE_TTL);
    return aircraft;
  } catch {
    console.log('[AircraftService] OpenSky unavailable — using mock data');
    const mock = [...generateHubAircraft(), ...generateScatteredAircraft()];
    await cacheSet(CACHE_KEY, JSON.stringify(mock), CACHE_TTL);
    return mock;
  }
}

export async function fetchAircraftByBounds(
  lamin: number, lomin: number, lamax: number, lomax: number
): Promise<Aircraft[]> {
  const cacheKey = `aircraft:bounds:${lamin}:${lomin}:${lamax}:${lomax}`;
  try {
    const cached = await cacheGet(cacheKey);
    if (cached) return JSON.parse(cached) as Aircraft[];

    const { data } = await axios.get(OPENSKY_API, {
      params: { lamin, lomin, lamax, lomax },
      timeout: 15000,
    });
    if (!data?.states) throw new Error('No data');

    const aircraft: Aircraft[] = [];
    for (const state of data.states) {
      const mapped = mapStateToAircraft(state);
      if (mapped) aircraft.push(enrichAircraft(mapped));
    }

    await cacheSet(cacheKey, JSON.stringify(aircraft), CACHE_TTL);
    return aircraft;
  } catch {
    const all = await fetchAircraft();
    return all.filter((a) =>
      a.position.lat >= lamin && a.position.lat <= lamax &&
      a.position.lng >= lomin && a.position.lng <= lomax
    );
  }
}
