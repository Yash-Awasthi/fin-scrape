import { NextRequest, NextResponse } from "next/server";
import { COUNTRY_BY_CODE, COUNTRIES, FeedEntry } from "@/lib/countryFeeds";
import { Category } from "@/lib/types";

// --- Topic feeds (US-centric, used when a specific category is selected) ---
const TOPIC_FEEDS: Record<string, string> = {
  general: "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en",
  business: "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx6TVdZU0FtVnVHZ0pWVXlnQVAB?hl=en-US&gl=US&ceid=US:en",
  technology: "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGRqTVhZU0FtVnVHZ0pWVXlnQVAB?hl=en-US&gl=US&ceid=US:en",
  science: "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRFp0Y1RjU0FtVnVHZ0pWVXlnQVAB?hl=en-US&gl=US&ceid=US:en",
  sports: "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRFp1ZEdvU0FtVnVHZ0pWVXlnQVAB?hl=en-US&gl=US&ceid=US:en",
  entertainment: "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNREpxYW5RU0FtVnVHZ0pWVXlnQVAB?hl=en-US&gl=US&ceid=US:en",
  health: "https://news.google.com/rss/topics/CAAqIQgKIhtDQkFTRGdvSUwyMHZNR3QwTlRFU0FtVnVLQUFQAQ?hl=en-US&gl=US&ceid=US:en",
};

// --- Region feeds for global coverage ---
interface RegionFeed {
  gl: string;
  ceid: string;
  hl: string;
  lat: number;
  lng: number;
  name: string;
}

const REGION_FEEDS: RegionFeed[] = [
  { gl: "US", ceid: "US:en", hl: "en-US", lat: 39.8, lng: -98.5, name: "United States" },
  { gl: "GB", ceid: "GB:en", hl: "en-GB", lat: 54.0, lng: -2.0, name: "United Kingdom" },
  { gl: "IN", ceid: "IN:en", hl: "en-IN", lat: 20.6, lng: 78.9, name: "India" },
  { gl: "AU", ceid: "AU:en", hl: "en-AU", lat: -25.3, lng: 133.8, name: "Australia" },
  { gl: "CA", ceid: "CA:en", hl: "en-CA", lat: 56.1, lng: -106.3, name: "Canada" },
  { gl: "DE", ceid: "DE:en", hl: "en", lat: 51.2, lng: 10.4, name: "Germany" },
  { gl: "FR", ceid: "FR:en", hl: "en", lat: 46.2, lng: 2.2, name: "France" },
  { gl: "JP", ceid: "JP:en", hl: "en", lat: 36.2, lng: 138.3, name: "Japan" },
  { gl: "BR", ceid: "BR:pt-419", hl: "pt-BR", lat: -14.2, lng: -51.9, name: "Brazil" },
  { gl: "MX", ceid: "MX:es-419", hl: "es-MX", lat: 23.6, lng: -102.6, name: "Mexico" },
  { gl: "ZA", ceid: "ZA:en", hl: "en-ZA", lat: -30.6, lng: 22.9, name: "South Africa" },
  { gl: "NG", ceid: "NG:en", hl: "en-NG", lat: 9.1, lng: 8.7, name: "Nigeria" },
  { gl: "KE", ceid: "KE:en", hl: "en-KE", lat: -0.02, lng: 37.9, name: "Kenya" },
  { gl: "EG", ceid: "EG:en", hl: "en", lat: 26.8, lng: 30.8, name: "Egypt" },
  { gl: "IL", ceid: "IL:en", hl: "en-IL", lat: 31.0, lng: 34.9, name: "Israel" },
  { gl: "AE", ceid: "AE:en", hl: "en", lat: 23.4, lng: 53.8, name: "UAE" },
  { gl: "SA", ceid: "SA:en", hl: "en", lat: 23.9, lng: 45.1, name: "Saudi Arabia" },
  { gl: "KR", ceid: "KR:en", hl: "en", lat: 35.9, lng: 127.8, name: "South Korea" },
  { gl: "SG", ceid: "SG:en", hl: "en-SG", lat: 1.35, lng: 103.8, name: "Singapore" },
  { gl: "ID", ceid: "ID:en", hl: "en-ID", lat: -0.8, lng: 113.9, name: "Indonesia" },
  { gl: "RU", ceid: "RU:en", hl: "en", lat: 61.5, lng: 105.3, name: "Russia" },
  { gl: "IT", ceid: "IT:en", hl: "en", lat: 41.9, lng: 12.6, name: "Italy" },
  { gl: "ES", ceid: "ES:en", hl: "en", lat: 40.5, lng: -3.7, name: "Spain" },
  { gl: "PL", ceid: "PL:en", hl: "en", lat: 51.9, lng: 19.1, name: "Poland" },
  { gl: "UA", ceid: "UA:en", hl: "en", lat: 48.4, lng: 31.2, name: "Ukraine" },
  { gl: "AR", ceid: "AR:es-419", hl: "es-AR", lat: -38.4, lng: -63.6, name: "Argentina" },
  { gl: "CO", ceid: "CO:es-419", hl: "es-CO", lat: 4.6, lng: -74.3, name: "Colombia" },
  { gl: "PH", ceid: "PH:en", hl: "en-PH", lat: 12.9, lng: 121.8, name: "Philippines" },
  { gl: "TW", ceid: "TW:en", hl: "en-TW", lat: 23.7, lng: 121.0, name: "Taiwan" },
  { gl: "TH", ceid: "TH:en", hl: "en", lat: 15.9, lng: 100.5, name: "Thailand" },
  { gl: "AT", ceid: "AT:de", hl: "de", lat: 47.5, lng: 14.6, name: "Austria" },
  { gl: "CH", ceid: "CH:de", hl: "de", lat: 46.8, lng: 8.2, name: "Switzerland" },
  { gl: "BE", ceid: "BE:fr", hl: "fr", lat: 50.9, lng: 4.4, name: "Belgium" },
  { gl: "NL", ceid: "NL:nl", hl: "nl", lat: 52.1, lng: 5.3, name: "Netherlands" },
  { gl: "IE", ceid: "IE:en", hl: "en", lat: 53.1, lng: -7.7, name: "Ireland" },
  { gl: "PT", ceid: "PT:pt-150", hl: "pt-PT", lat: 39.4, lng: -8.2, name: "Portugal" },
  { gl: "SE", ceid: "SE:sv", hl: "sv", lat: 60.1, lng: 18.6, name: "Sweden" },
  { gl: "NO", ceid: "NO:no", hl: "no", lat: 60.5, lng: 8.5, name: "Norway" },
  { gl: "CZ", ceid: "CZ:cs", hl: "cs", lat: 49.8, lng: 15.5, name: "Czechia" },
  { gl: "SK", ceid: "SK:sk", hl: "sk", lat: 48.7, lng: 19.7, name: "Slovakia" },
  { gl: "HU", ceid: "HU:hu", hl: "hu", lat: 47.2, lng: 19.5, name: "Hungary" },
  { gl: "RO", ceid: "RO:ro", hl: "ro", lat: 45.9, lng: 24.9, name: "Romania" },
  { gl: "BG", ceid: "BG:bg", hl: "bg", lat: 42.7, lng: 25.5, name: "Bulgaria" },
  { gl: "RS", ceid: "RS:sr", hl: "sr", lat: 44.0, lng: 21.0, name: "Serbia" },
  { gl: "SI", ceid: "SI:sl", hl: "sl", lat: 46.2, lng: 15.0, name: "Slovenia" },
  { gl: "LV", ceid: "LV:lv", hl: "lv", lat: 56.9, lng: 24.6, name: "Latvia" },
  { gl: "LT", ceid: "LT:lt", hl: "lt", lat: 55.2, lng: 23.9, name: "Lithuania" },
  { gl: "GR", ceid: "GR:el", hl: "el", lat: 39.1, lng: 21.8, name: "Greece" },
  { gl: "LB", ceid: "LB:ar", hl: "ar", lat: 33.9, lng: 35.9, name: "Lebanon" },
  { gl: "MA", ceid: "MA:fr", hl: "fr", lat: 31.8, lng: -7.1, name: "Morocco" },
  { gl: "TR", ceid: "TR:tr", hl: "tr", lat: 39.0, lng: 35.2, name: "Turkey" },
  { gl: "GH", ceid: "GH:en", hl: "en", lat: 7.9, lng: -1.0, name: "Ghana" },
  { gl: "ET", ceid: "ET:en", hl: "en", lat: 9.1, lng: 40.5, name: "Ethiopia" },
  { gl: "TZ", ceid: "TZ:en", hl: "en", lat: -6.4, lng: 34.9, name: "Tanzania" },
  { gl: "UG", ceid: "UG:en", hl: "en", lat: 1.4, lng: 32.3, name: "Uganda" },
  { gl: "ZW", ceid: "ZW:en", hl: "en", lat: -19.0, lng: 29.2, name: "Zimbabwe" },
  { gl: "BW", ceid: "BW:en", hl: "en", lat: -22.3, lng: 24.7, name: "Botswana" },
  { gl: "NA", ceid: "NA:en", hl: "en", lat: -23.0, lng: 18.5, name: "Namibia" },
  { gl: "SN", ceid: "SN:fr", hl: "fr", lat: 14.5, lng: -14.5, name: "Senegal" },
  { gl: "PK", ceid: "PK:en", hl: "en", lat: 30.4, lng: 69.3, name: "Pakistan" },
  { gl: "BD", ceid: "BD:bn", hl: "bn", lat: 23.7, lng: 90.4, name: "Bangladesh" },
  { gl: "MY", ceid: "MY:en", hl: "en", lat: 4.2, lng: 101.9, name: "Malaysia" },
  { gl: "VN", ceid: "VN:vi", hl: "vi", lat: 14.1, lng: 108.3, name: "Vietnam" },
  { gl: "HK", ceid: "HK:zh-Hant", hl: "zh-HK", lat: 22.3, lng: 114.2, name: "Hong Kong" },
  { gl: "NZ", ceid: "NZ:en", hl: "en", lat: -40.9, lng: 174.9, name: "New Zealand" },
  { gl: "CL", ceid: "CL:es-419", hl: "es-419", lat: -35.7, lng: -71.5, name: "Chile" },
  { gl: "PE", ceid: "PE:es-419", hl: "es-419", lat: -9.2, lng: -75.0, name: "Peru" },
  { gl: "VE", ceid: "VE:es-419", hl: "es-419", lat: 6.4, lng: -66.6, name: "Venezuela" },
  { gl: "CU", ceid: "CU:es-419", hl: "es-419", lat: 21.5, lng: -77.8, name: "Cuba" },
];

// --- Fallback feed countries ---
interface FallbackFeedEntry {
  feeds: (string | FeedEntry)[];
  lat: number;
  lng: number;
  name: string;
}

const FALLBACK_FEED_ENTRIES: FallbackFeedEntry[] = COUNTRIES
  .filter((c) => c.fallbackFeeds && c.fallbackFeeds.length > 0)
  .map((c) => ({ feeds: c.fallbackFeeds!, lat: c.lat, lng: c.lng, name: c.name }));

// --- Unified feed items ---
type GlobalFeedItem =
  | { type: "region"; data: RegionFeed }
  | { type: "fallback"; data: FallbackFeedEntry };

const ALL_GLOBAL_FEEDS: GlobalFeedItem[] = [
  ...REGION_FEEDS.map((r): GlobalFeedItem => ({ type: "region", data: r })),
  ...FALLBACK_FEED_ENTRIES.map((f): GlobalFeedItem => ({ type: "fallback", data: f })),
];

const FEEDS_PER_BATCH = 15;
const CACHE_TTL_SECONDS = 1800; // 30 minutes

export function getTotalBatches(): number {
  return Math.ceil(ALL_GLOBAL_FEEDS.length / FEEDS_PER_BATCH);
}

// --- Raw feed response type ---
// The worker returns raw XML strings + metadata, frontend does all parsing
interface RawFeedResponse {
  xml: string;
  meta: {
    lat: number;
    lng: number;
    name: string;
    feedName?: string;  // For fallback feeds: publication name
    category?: string;
  };
}

/** Fetch a single RSS URL, return raw XML + metadata */
async function fetchRawFeed(
  url: string,
  meta: RawFeedResponse["meta"],
  timeoutMs = 5000
): Promise<RawFeedResponse | null> {
  try {
    const res = await fetch(url, { signal: AbortSignal.timeout(timeoutMs) });
    if (!res.ok) return null;
    const xml = await res.text();
    return { xml, meta };
  } catch {
    return null;
  }
}

function normalizeFeedEntries(feeds: (string | FeedEntry)[]): FeedEntry[] {
  return feeds.map((f) => (typeof f === "string" ? { url: f } : f));
}

/** Reorder feeds so user's country appears first */
function reorderFeeds(loc: string | null): GlobalFeedItem[] {
  if (!loc) return ALL_GLOBAL_FEEDS;
  const upperLoc = loc.toUpperCase();
  const countryData = COUNTRY_BY_CODE.get(upperLoc);
  if (!countryData) return ALL_GLOBAL_FEEDS;

  const userFeeds: GlobalFeedItem[] = [];
  const rest: GlobalFeedItem[] = [];
  for (const f of ALL_GLOBAL_FEEDS) {
    const isUserRegion = f.type === "region" && f.data.gl === upperLoc;
    const isUserFallback = f.type === "fallback" && f.data.name === countryData.name;
    if (isUserRegion || isUserFallback) {
      userFeeds.push(f);
    } else {
      rest.push(f);
    }
  }
  if (userFeeds.length === 0) return ALL_GLOBAL_FEEDS;
  return [...userFeeds, ...rest];
}

function reorderRegions(loc: string | null): RegionFeed[] {
  if (!loc) return REGION_FEEDS;
  const upperLoc = loc.toUpperCase();
  const idx = REGION_FEEDS.findIndex((r) => r.gl === upperLoc);
  if (idx <= 0) return REGION_FEEDS;
  const reordered = [...REGION_FEEDS];
  const [moved] = reordered.splice(idx, 1);
  reordered.unshift(moved);
  return reordered;
}

// --- Cached raw response (caches array of RawFeedResponse) ---
async function cachedRawResponse(
  cacheKey: string,
  fetchData: () => Promise<RawFeedResponse[]>
): Promise<Response> {
  const cacheUrl = new URL(`https://newsglobe-cache.internal/${cacheKey}`);
  const cacheReq = new Request(cacheUrl.toString());

  // @ts-expect-error - caches.default is available in Workers runtime
  const cfCache = typeof caches !== "undefined" && caches.default;
  if (cfCache) {
    const cached = await cfCache.match(cacheReq);
    if (cached) return cached;
  }

  const feeds = await fetchData();
  const response = NextResponse.json(feeds);
  response.headers.set("Cache-Control", `s-maxage=${CACHE_TTL_SECONDS}`);

  // Don't cache empty results — likely a transient fetch failure
  if (cfCache && feeds.length > 0) {
    cfCache.put(cacheReq, response.clone());
  }
  return response;
}

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const topic = (searchParams.get("topic") || "general") as Category;
  const query = searchParams.get("q") || "";
  const country = searchParams.get("country") || "";
  const batch = searchParams.get("batch");
  const loc = searchParams.get("loc") || "";

  // Country-specific feed
  if (country) {
    const countryData = COUNTRY_BY_CODE.get(country.toUpperCase());
    if (!countryData) {
      return NextResponse.json(
        { error: `Country "${country}" not supported` },
        { status: 400 }
      );
    }

    return cachedRawResponse(`country:${country.toUpperCase()}`, async () => {
      const promises: Promise<RawFeedResponse | null>[] = [];
      const meta = { lat: countryData.lat, lng: countryData.lng, name: countryData.name };

      // Google News feed
      if (countryData.gl && countryData.ceid && countryData.hl) {
        const feedUrl = `https://news.google.com/rss?hl=${countryData.hl}&gl=${countryData.gl}&ceid=${countryData.ceid}`;
        promises.push(fetchRawFeed(feedUrl, { ...meta, category: "general" }));
      }

      // Fallback RSS feeds (sample up to 20 for country view)
      if (countryData.fallbackFeeds && countryData.fallbackFeeds.length > 0) {
        const entries = normalizeFeedEntries(countryData.fallbackFeeds);
        const maxFeeds = countryData.gl ? 15 : 30;
        const sampled = entries.length <= maxFeeds
          ? entries
          : entries.sort(() => Math.random() - 0.5).slice(0, maxFeeds);
        for (const entry of sampled) {
          promises.push(fetchRawFeed(entry.url, { ...meta, feedName: entry.name }));
        }
      }

      const results = await Promise.all(promises);
      return results.filter((r): r is RawFeedResponse => r !== null);
    });
  }

  // Search / topic / global batched feeds
  const batchSuffix = batch !== null ? `:b${batch}` : "";
  const locSuffix = loc ? `:loc${loc}` : "";
  return cachedRawResponse(`${topic}:${query}${batchSuffix}${locSuffix}`, async () => {
    if (query) {
      // Search mode
      const searchRegions = reorderRegions(loc).slice(0, 8);
      const results = await Promise.all(
        searchRegions.map((region) => {
          const feedUrl = `https://news.google.com/rss/search?q=${encodeURIComponent(query)}&hl=${region.hl}&gl=${region.gl}&ceid=${region.ceid}`;
          return fetchRawFeed(feedUrl, {
            lat: region.lat, lng: region.lng, name: region.name, category: "general",
          });
        })
      );
      return results.filter((r): r is RawFeedResponse => r !== null);

    } else if (topic !== "general") {
      // Topic feed — single fetch, allow longer timeout
      const feedUrl = TOPIC_FEEDS[topic] || TOPIC_FEEDS.general;
      const result = await fetchRawFeed(feedUrl, {
        lat: 39.8, lng: -98.5, name: "United States", category: topic,
      }, 10000);
      return result ? [result] : [];

    } else {
      // Global batched view
      const totalBatches = getTotalBatches();
      const batchIndex = batch !== null ? parseInt(batch, 10) : null;
      const orderedFeeds = reorderFeeds(loc);

      let feeds: GlobalFeedItem[];
      if (batchIndex !== null && batchIndex >= 0 && batchIndex < totalBatches) {
        const start = batchIndex * FEEDS_PER_BATCH;
        feeds = orderedFeeds.slice(start, start + FEEDS_PER_BATCH);
      } else {
        feeds = orderedFeeds;
      }

      const promises: Promise<RawFeedResponse | null>[] = [];
      for (const feed of feeds) {
        if (feed.type === "region") {
          const r = feed.data;
          const feedUrl = `https://news.google.com/rss?hl=${r.hl}&gl=${r.gl}&ceid=${r.ceid}`;
          promises.push(fetchRawFeed(feedUrl, {
            lat: r.lat, lng: r.lng, name: r.name, category: "general",
          }));
        } else {
          // Fallback: sample 1 feed per country in global view to stay under 50 subrequest limit
          const entries = normalizeFeedEntries(feed.data.feeds);
          const sampled = entries.length <= 1
            ? entries
            : [entries[Math.floor(Math.random() * entries.length)]];
          for (const entry of sampled) {
            promises.push(fetchRawFeed(entry.url, {
              lat: feed.data.lat, lng: feed.data.lng, name: feed.data.name,
              feedName: entry.name,
            }));
          }
        }
      }

      const results = await Promise.all(promises);
      return results.filter((r): r is RawFeedResponse => r !== null);
    }
  });
}
