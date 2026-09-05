import { LOCATIONS } from "./countries";
import { cityMapping } from "city-timezones";

// --- Build combined location lookup (city-timezones + manual overrides) ---

const CITY_COORDS = new Map<string, { lat: number; lng: number }>();

// First load all 7000+ cities from city-timezones
for (const city of cityMapping) {
  const key = city.city.toLowerCase();
  // Prefer larger cities (higher population) when duplicates exist
  const existing = CITY_COORDS.get(key);
  if (!existing || (city.pop && city.pop > 0)) {
    CITY_COORDS.set(key, { lat: city.lat, lng: city.lng });
  }
  // Also index by "city, country" for disambiguation
  const fullKey = `${city.city}, ${city.country}`.toLowerCase();
  CITY_COORDS.set(fullKey, { lat: city.lat, lng: city.lng });
}

// Then overlay manual LOCATIONS (countries, regions, custom entries take priority)
for (const [key, coords] of Object.entries(LOCATIONS)) {
  CITY_COORDS.set(key, coords);
}

// --- Nominatim geocoding with persistent cache ---

const nominatimCache = new Map<string, { lat: number; lng: number } | null>();
let lastNominatimCall = 0;
const NOMINATIM_MIN_INTERVAL = 1100;

async function nominatimGeocode(
  query: string
): Promise<{ lat: number; lng: number } | null> {
  const cacheKey = query.toLowerCase().trim();
  if (nominatimCache.has(cacheKey)) return nominatimCache.get(cacheKey)!;

  // Rate limit
  const now = Date.now();
  const wait = NOMINATIM_MIN_INTERVAL - (now - lastNominatimCall);
  if (wait > 0) await new Promise((r) => setTimeout(r, wait));
  lastNominatimCall = Date.now();

  try {
    const url = `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(query)}&format=json&limit=1`;
    const res = await fetch(url, {
      headers: { "User-Agent": "NewsGlobe/1.0 (news visualization app)" },
    });
    if (!res.ok) {
      nominatimCache.set(cacheKey, null);
      return null;
    }
    const data = (await res.json()) as { lat: string; lon: string }[];
    if (data.length === 0) {
      nominatimCache.set(cacheKey, null);
      return null;
    }
    const result = {
      lat: parseFloat(data[0].lat),
      lng: parseFloat(data[0].lon),
    };
    nominatimCache.set(cacheKey, result);
    return result;
  } catch {
    nominatimCache.set(cacheKey, null);
    return null;
  }
}

// --- Location keyword extraction ---

const REGIONS = new Set([
  "middle east", "europe", "european", "africa", "african", "asia", "asian",
  "latin america", "eu", "nato",
]);

const DEMONYMS = new Set([
  "american", "canadian", "british", "french", "german", "italian", "spanish",
  "dutch", "swiss", "irish", "greek", "turkish", "ukrainian", "russian",
  "chinese", "japanese", "korean", "indian", "iranian", "syrian", "saudi",
  "israeli", "palestinian", "egyptian", "brazilian", "australian",
]);

const COUNTRIES = new Set([
  "united states", "usa", "u.s.", "america", "canada", "mexico", "brazil",
  "argentina", "colombia", "chile", "peru", "venezuela", "cuba",
  "united kingdom", "uk", "britain", "england", "scotland", "france",
  "germany", "italy", "spain", "portugal", "netherlands", "belgium",
  "switzerland", "austria", "poland", "czech", "sweden", "norway", "denmark",
  "finland", "ireland", "greece", "turkey", "romania", "hungary", "ukraine",
  "russia", "china", "japan", "south korea", "north korea", "india",
  "pakistan", "bangladesh", "indonesia", "thailand", "vietnam", "philippines",
  "malaysia", "singapore", "taiwan", "myanmar", "cambodia", "sri lanka",
  "nepal", "afghanistan", "iraq", "iran", "syria", "saudi arabia", "israel",
  "palestine", "gaza", "lebanon", "jordan", "yemen", "uae", "dubai", "qatar",
  "kuwait", "egypt", "libya", "tunisia", "algeria", "morocco", "nigeria",
  "south africa", "kenya", "ethiopia", "ghana", "tanzania", "uganda", "sudan",
  "congo", "somalia", "senegal", "mozambique", "zimbabwe", "australia",
  "new zealand",
]);

const FALSE_POSITIVES = new Set(["jordan"]);

interface Match {
  key: string;
  specificity: number;
  position: number;
}

function getSpecificity(key: string): number {
  if (REGIONS.has(key)) return 1;
  if (DEMONYMS.has(key)) return 1.5;
  if (COUNTRIES.has(key)) return 2;
  return 3; // cities, states, specific places
}

const locationKeys = Array.from(CITY_COORDS.keys());

function extractCandidates(text: string): Match[] {
  const lower = text.toLowerCase();
  const matches: Match[] = [];

  for (const key of locationKeys) {
    const idx = lower.indexOf(key);
    if (idx === -1) continue;

    const before = lower[idx - 1];
    const after = lower[idx + key.length];
    const wb = (ch: string | undefined) =>
      !ch || /[\s,.\-—:;!?'"()[\]{}\/]/.test(ch);

    if (!wb(before) || !wb(after)) continue;

    if (FALSE_POSITIVES.has(key)) {
      const ctx = lower.slice(Math.max(0, idx - 5), idx).trim();
      if (!/\b(in|of|to|from)\b/.test(ctx)) continue;
    }

    matches.push({ key, specificity: getSpecificity(key), position: idx });
  }

  matches.sort((a, b) => {
    if (b.specificity !== a.specificity) return b.specificity - a.specificity;
    return a.position - b.position;
  });

  return matches;
}

// --- Fast geocode (static table only, no Nominatim, no async) ---

export function geocodeFast(
  text: string
): { lat: number; lng: number } | null {
  const candidates = extractCandidates(text);
  if (candidates.length === 0) return null;
  return staticFallback(candidates[0].key);
}

// --- Main geocode (async, Nominatim-enhanced) ---

export async function geocode(
  text: string
): Promise<{ lat: number; lng: number } | null> {
  const candidates = extractCandidates(text);
  if (candidates.length === 0) return null;

  const best = candidates[0];

  // If best match is already a specific city/state (specificity 3) and is
  // in our static map, use Nominatim to refine it for better precision
  // For country-level matches (specificity 2), also use Nominatim
  // For regions/demonyms (< 2), just use static map (Nominatim won't help)
  if (best.specificity >= 2) {
    // Check if already cached in Nominatim (instant)
    const cached = nominatimCache.get(best.key.toLowerCase().trim());
    if (cached !== undefined) {
      if (cached) {
        return jitter(cached, best.key);
      }
      return staticFallback(best.key);
    }

    // Not cached — try Nominatim (will take ~1.1s due to rate limit)
    const result = await nominatimGeocode(best.key);
    if (result) {
      return jitter(result, best.key);
    }
  }

  return staticFallback(best.key);
}

function staticFallback(
  key: string
): { lat: number; lng: number } | null {
  const loc = CITY_COORDS.get(key);
  if (!loc) return null;
  return jitter(loc, key);
}

// Coastal cities where jitter should push inland only
const COASTAL_BIAS: Record<string, { latDir: number; lngDir: number }> = {
  mumbai: { latDir: 1, lngDir: 1 },     // push NE (inland)
  chennai: { latDir: 1, lngDir: 1 },
  "hong kong": { latDir: 1, lngDir: 1 },
  shanghai: { latDir: 1, lngDir: -1 },
  tokyo: { latDir: 1, lngDir: -1 },
  sydney: { latDir: -1, lngDir: -1 },
  "new york": { latDir: 1, lngDir: 1 },
  miami: { latDir: 1, lngDir: 1 },
  "los angeles": { latDir: 1, lngDir: 1 },
  "san francisco": { latDir: 1, lngDir: 1 },
  london: { latDir: 0, lngDir: 0 },      // inland enough
  dubai: { latDir: 1, lngDir: 1 },
  "tel aviv": { latDir: 1, lngDir: 1 },
  singapore: { latDir: 1, lngDir: 0 },
  istanbul: { latDir: 0, lngDir: 1 },
  lagos: { latDir: 1, lngDir: 1 },
  jakarta: { latDir: -1, lngDir: 1 },
  manila: { latDir: 1, lngDir: 1 },
  lima: { latDir: -1, lngDir: 1 },
  "rio de janeiro": { latDir: -1, lngDir: 1 },
  "cape town": { latDir: -1, lngDir: 1 },
  lisbon: { latDir: 1, lngDir: 1 },
  barcelona: { latDir: 1, lngDir: -1 },
  "gaza": { latDir: 1, lngDir: 1 },
};

function jitter(
  coords: { lat: number; lng: number },
  locationKey?: string
): { lat: number; lng: number } {
  const amount = 0.08; // ~9km, reduced from 0.15
  const bias = locationKey ? COASTAL_BIAS[locationKey.toLowerCase()] : undefined;

  let latOff: number;
  let lngOff: number;

  if (bias) {
    // Bias jitter toward inland direction
    latOff = bias.latDir === 0
      ? (Math.random() - 0.5) * amount
      : Math.abs(Math.random() * amount) * bias.latDir;
    lngOff = bias.lngDir === 0
      ? (Math.random() - 0.5) * amount
      : Math.abs(Math.random() * amount) * bias.lngDir;
  } else {
    latOff = (Math.random() - 0.5) * amount;
    lngOff = (Math.random() - 0.5) * amount;
  }

  return {
    lat: coords.lat + latOff,
    lng: coords.lng + lngOff,
  };
}
