export interface GeoPosition {
  lat: number;
  lng: number;
  alt?: number;
}

export interface Aircraft {
  icao24: string;
  callsign: string;
  originCountry: string;
  position: GeoPosition;
  velocity: number;
  heading: number;
  verticalRate: number;
  onGround: boolean;
  squawk: string | null;
  category: 'commercial' | 'military' | 'private' | 'cargo' | 'unknown';
  timestamp: number;
  airline?: string;
  flightNumber?: string;
  originAirport?: string;
  destinationAirport?: string;
  aircraftType?: string;
  departureTime?: string;
  arrivalTime?: string;
  route?: string;
}

export interface Satellite {
  id: number;
  name: string;
  noradId: number;
  position: GeoPosition;
  velocity: number;
  category: 'communication' | 'weather' | 'navigation' | 'military' | 'scientific' | 'iss' | 'starlink' | 'unknown';
  orbitType: 'LEO' | 'MEO' | 'GEO' | 'HEO';
  inclination: number;
  period: number;
  timestamp: number;
}

export interface Ship {
  mmsi: string;
  name: string;
  position: GeoPosition;
  speed: number;
  heading: number;
  shipType: 'cargo' | 'tanker' | 'passenger' | 'naval' | 'fishing' | 'unknown';
  flag: string;
  destination: string | null;
  timestamp: number;
}

export interface Earthquake {
  id: string;
  magnitude: number;
  depth: number;
  position: GeoPosition;
  place: string;
  time: number;
  tsunami: boolean;
  status: string;
  felt: number | null;
  significance: number;
}

export interface ConflictEvent {
  id: string;
  eventType: 'battle' | 'explosion' | 'protest' | 'riot' | 'violence_against_civilians' | 'strategic_development';
  position: GeoPosition;
  country: string;
  region: string;
  description: string;
  fatalities: number;
  severity: 'red' | 'orange' | 'yellow';
  source: string;
  timestamp: number;
}

export interface MissileLaunch {
  id: string;
  type: 'missile' | 'rocket' | 'space_launch';
  launchSite: GeoPosition;
  trajectory: GeoPosition[];
  predictedImpact: GeoPosition | null;
  country: string;
  description: string;
  timestamp: number;
}

export interface NewsEvent {
  id: string;
  title: string;
  description: string;
  category: 'conflict' | 'disaster' | 'politics' | 'economic' | 'protest' | 'technology';
  position: GeoPosition | null;
  source: string;
  url: string;
  timestamp: number;
  sentiment: number;
}

export interface TrafficData {
  city: string;
  position: GeoPosition;
  congestionLevel: number;
  averageSpeed: number;
  incidents: TrafficIncident[];
  timestamp: number;
}

export interface TrafficIncident {
  position: GeoPosition;
  type: 'accident' | 'construction' | 'closure' | 'congestion';
  severity: number;
  description: string;
}

export interface WeatherData {
  position: GeoPosition;
  temperature: number;
  windSpeed: number;
  windDirection: number;
  condition: string;
  humidity: number;
  visibility: number;
  timestamp: number;
}

export interface LayerData {
  aircraft: Aircraft[];
  satellites: Satellite[];
  ships: Ship[];
  earthquakes: Earthquake[];
  conflicts: ConflictEvent[];
  missiles: MissileLaunch[];
  news: NewsEvent[];
  traffic: TrafficData[];
  weather: WeatherData[];
}

export interface WSMessage {
  type: 'layer_update' | 'alert' | 'anomaly' | 'situation_report';
  layer?: keyof LayerData;
  data: unknown;
  timestamp: number;
}

export interface AnomalyAlert {
  id: string;
  type: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  title: string;
  description: string;
  position: GeoPosition;
  relatedEntities: string[];
  timestamp: number;
}

export interface SituationReport {
  id: string;
  region: string;
  summary: string;
  threats: string[];
  escalationProbability: number;
  recommendations: string[];
  timestamp: number;
}
