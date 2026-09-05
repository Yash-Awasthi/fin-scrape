import axios from 'axios';
import { WeatherData } from '../types';
import { cacheGet, cacheSet } from '../utils/cache';

const OPEN_METEO_API = 'https://api.open-meteo.com/v1/forecast';
const CACHE_KEY = 'weather:all';
const CACHE_TTL = 300;

interface CityWeatherConfig {
  name: string;
  lat: number;
  lng: number;
}

const WORLD_CITIES: CityWeatherConfig[] = [
  { name: 'New York', lat: 40.71, lng: -74.01 },
  { name: 'London', lat: 51.51, lng: -0.13 },
  { name: 'Paris', lat: 48.86, lng: 2.35 },
  { name: 'Tokyo', lat: 35.68, lng: 139.69 },
  { name: 'Dubai', lat: 25.20, lng: 55.27 },
  { name: 'Singapore', lat: 1.35, lng: 103.82 },
  { name: 'Sydney', lat: -33.87, lng: 151.21 },
  { name: 'Moscow', lat: 55.76, lng: 37.62 },
  { name: 'Beijing', lat: 39.90, lng: 116.40 },
  { name: 'Mumbai', lat: 19.08, lng: 72.88 },
  { name: 'Cairo', lat: 30.04, lng: 31.24 },
  { name: 'São Paulo', lat: -23.55, lng: -46.63 },
  { name: 'Los Angeles', lat: 34.05, lng: -118.24 },
  { name: 'Berlin', lat: 52.52, lng: 13.41 },
  { name: 'Istanbul', lat: 41.01, lng: 28.98 },
  { name: 'Seoul', lat: 37.57, lng: 126.98 },
  { name: 'Mexico City', lat: 19.43, lng: -99.13 },
  { name: 'Johannesburg', lat: -26.20, lng: 28.05 },
  { name: 'Bangkok', lat: 13.76, lng: 100.50 },
  { name: 'Lagos', lat: 6.52, lng: 3.38 },
  { name: 'Buenos Aires', lat: -34.60, lng: -58.38 },
  { name: 'Nairobi', lat: -1.29, lng: 36.82 },
  { name: 'Jakarta', lat: -6.21, lng: 106.85 },
  { name: 'Toronto', lat: 43.65, lng: -79.38 },
  { name: 'Riyadh', lat: 24.71, lng: 46.68 },
];

interface OpenMeteoResponse {
  current?: {
    temperature_2m?: number;
    wind_speed_10m?: number;
    wind_direction_10m?: number;
    relative_humidity_2m?: number;
    weather_code?: number;
  };
}

const WMO_CODES: Record<number, string> = {
  0: 'Clear sky', 1: 'Mainly clear', 2: 'Partly cloudy', 3: 'Overcast',
  45: 'Foggy', 48: 'Rime fog', 51: 'Light drizzle', 53: 'Moderate drizzle',
  55: 'Dense drizzle', 56: 'Freezing drizzle', 57: 'Dense freezing drizzle',
  61: 'Slight rain', 63: 'Moderate rain', 65: 'Heavy rain',
  66: 'Light freezing rain', 67: 'Heavy freezing rain',
  71: 'Slight snow', 73: 'Moderate snow', 75: 'Heavy snow',
  77: 'Snow grains', 80: 'Light showers', 81: 'Moderate showers', 82: 'Violent showers',
  85: 'Light snow showers', 86: 'Heavy snow showers',
  95: 'Thunderstorm', 96: 'Thunderstorm with hail', 99: 'Heavy thunderstorm with hail',
};

function visibilityFromCode(code: number): number {
  if (code >= 45 && code <= 48) return 500;
  if (code >= 95) return 3000;
  if (code >= 61 && code <= 67) return 5000;
  if (code >= 71 && code <= 77) return 2000;
  if (code >= 80 && code <= 86) return 4000;
  return 10000;
}

async function fetchCityWeather(city: CityWeatherConfig): Promise<WeatherData | null> {
  try {
    const { data } = await axios.get<OpenMeteoResponse>(OPEN_METEO_API, {
      params: {
        latitude: city.lat,
        longitude: city.lng,
        current: 'temperature_2m,wind_speed_10m,wind_direction_10m,relative_humidity_2m,weather_code',
      },
      timeout: 8000,
    });

    const current = data?.current;
    if (!current) return null;

    const weatherCode = current.weather_code ?? 0;

    return {
      position: { lat: city.lat, lng: city.lng },
      temperature: current.temperature_2m ?? 0,
      windSpeed: current.wind_speed_10m ?? 0,
      windDirection: current.wind_direction_10m ?? 0,
      condition: WMO_CODES[weatherCode] || 'Unknown',
      humidity: current.relative_humidity_2m ?? 0,
      visibility: visibilityFromCode(weatherCode),
      timestamp: Date.now() / 1000,
    };
  } catch {
    return null;
  }
}

function generateMockWeather(): WeatherData[] {
  const now = Date.now() / 1000;
  const hour = new Date().getUTCHours();

  const mockTemps: Record<string, { base: number; condition: string }> = {
    'New York': { base: 12, condition: 'Partly cloudy' },
    'London': { base: 10, condition: 'Overcast' },
    'Paris': { base: 13, condition: 'Mainly clear' },
    'Tokyo': { base: 18, condition: 'Clear sky' },
    'Dubai': { base: 35, condition: 'Clear sky' },
    'Singapore': { base: 30, condition: 'Moderate showers' },
    'Sydney': { base: 22, condition: 'Partly cloudy' },
    'Moscow': { base: 3, condition: 'Slight snow' },
    'Beijing': { base: 15, condition: 'Foggy' },
    'Mumbai': { base: 32, condition: 'Moderate rain' },
    'Cairo': { base: 28, condition: 'Clear sky' },
    'São Paulo': { base: 24, condition: 'Light showers' },
    'Los Angeles': { base: 20, condition: 'Mainly clear' },
    'Berlin': { base: 8, condition: 'Overcast' },
    'Istanbul': { base: 16, condition: 'Partly cloudy' },
    'Seoul': { base: 14, condition: 'Clear sky' },
    'Mexico City': { base: 19, condition: 'Partly cloudy' },
    'Johannesburg': { base: 21, condition: 'Thunderstorm' },
    'Bangkok': { base: 33, condition: 'Moderate rain' },
    'Lagos': { base: 29, condition: 'Mainly clear' },
    'Buenos Aires': { base: 17, condition: 'Partly cloudy' },
    'Nairobi': { base: 20, condition: 'Light showers' },
    'Jakarta': { base: 31, condition: 'Moderate showers' },
    'Toronto': { base: 7, condition: 'Overcast' },
    'Riyadh': { base: 38, condition: 'Clear sky' },
  };

  return WORLD_CITIES.map((city) => {
    const m = mockTemps[city.name] || { base: 20, condition: 'Clear sky' };
    const nightAdj = (hour >= 20 || hour <= 5) ? -5 : 0;
    return {
      position: { lat: city.lat, lng: city.lng },
      temperature: m.base + nightAdj + Math.round((Math.random() - 0.5) * 4),
      windSpeed: 5 + Math.random() * 25,
      windDirection: Math.random() * 360,
      condition: m.condition,
      humidity: 40 + Math.round(Math.random() * 40),
      visibility: m.condition.includes('Fog') ? 500 : m.condition.includes('rain') || m.condition.includes('shower') ? 5000 : 10000,
      timestamp: now,
    };
  });
}

export async function fetchWeatherData(): Promise<WeatherData[]> {
  try {
    const cached = await cacheGet(CACHE_KEY);
    if (cached) return JSON.parse(cached) as WeatherData[];

    const batchSize = 5;
    const results: WeatherData[] = [];

    for (let i = 0; i < WORLD_CITIES.length; i += batchSize) {
      const batch = WORLD_CITIES.slice(i, i + batchSize);
      const batchResults = await Promise.all(batch.map(fetchCityWeather));
      for (const r of batchResults) {
        if (r) results.push(r);
      }
    }

    if (results.length > 0) {
      await cacheSet(CACHE_KEY, JSON.stringify(results), CACHE_TTL);
      return results;
    }
    throw new Error('No weather results');
  } catch {
    console.log('[WeatherService] Open-Meteo unavailable — using mock data');
    const mock = generateMockWeather();
    await cacheSet(CACHE_KEY, JSON.stringify(mock), CACHE_TTL);
    return mock;
  }
}
