import { create } from "zustand";
import { NewsArticle, Category } from "./types";
import { COUNTRY_BY_CODE } from "./countryFeeds";
import { geocodeFast } from "./geocode";
import { parseRawFeeds, RawFeedResponse } from "./parseFeeds";

interface SelectedCountry {
  code: string;
  name: string;
}

interface FlyToTarget {
  lat: number;
  lng: number;
  zoom: number;
}

interface NewsState {
  articles: NewsArticle[];
  filteredArticles: NewsArticle[];
  activeCategory: Category | "all";
  searchQuery: string;
  loading: boolean;
  error: string | null;
  hoveredArticle: NewsArticle | null;
  selectedCountry: SelectedCountry | null;
  countryArticles: NewsArticle[];
  countryLoading: boolean;
  pendingFlyTo: FlyToTarget | null;
  flyToVersion: number;
  userCountry: string | null;
  setActiveCategory: (cat: Category | "all") => void;
  setSearchQuery: (q: string) => void;
  setHoveredArticle: (a: NewsArticle | null) => void;
  fetchNews: () => Promise<void>;
  flyToArticle: (a: NewsArticle) => void;
  selectCountry: (code: string, name: string) => Promise<void>;
  clearCountry: () => void;
}

/** Small random offset so dots at the same region coord don't stack */
function jitter(): number {
  return (Math.random() - 0.5) * 2; // ±1 degree (~100km)
}

/** Apply client-side geocoding to refine article coordinates */
function geocodeArticles(articles: NewsArticle[]): NewsArticle[] {
  return articles.map((a) => {
    const coords = geocodeFast(`${a.title} ${a.snippet}`);
    if (coords) {
      return { ...a, lat: coords.lat + jitter() * 0.3, lng: coords.lng + jitter() * 0.3 };
    }
    // Fall back to region coords with jitter to spread dots
    return {
      ...a,
      lat: (a.regionLat ?? a.lat) + jitter(),
      lng: (a.regionLng ?? a.lng) + jitter(),
    };
  });
}

function filterArticles(
  articles: NewsArticle[],
  category: Category | "all",
  query: string
) {
  let filtered = articles;
  if (category !== "all") {
    filtered = filtered.filter((a) => a.category === category);
  }
  if (query) {
    const q = query.toLowerCase();
    filtered = filtered.filter(
      (a) =>
        a.title.toLowerCase().includes(q) ||
        a.snippet.toLowerCase().includes(q)
    );
  }
  return filtered;
}

export const useNewsStore = create<NewsState>((set, get) => ({
  articles: [],
  filteredArticles: [],
  activeCategory: "all",
  searchQuery: "",
  loading: false,
  error: null,
  hoveredArticle: null,
  selectedCountry: null,
  countryArticles: [],
  countryLoading: false,
  pendingFlyTo: null,
  flyToVersion: 0,
  userCountry: null,

  setActiveCategory: (cat) => {
    set({ activeCategory: cat });
    const { articles, searchQuery } = get();
    set({ filteredArticles: filterArticles(articles, cat, searchQuery) });
  },

  setSearchQuery: (q) => {
    set({ searchQuery: q });
    const { articles, activeCategory } = get();
    set({ filteredArticles: filterArticles(articles, activeCategory, q) });
  },

  setHoveredArticle: (a) => set({ hoveredArticle: a }),

  flyToArticle: (a) => set({
    hoveredArticle: a,
    pendingFlyTo: { lat: a.lat, lng: a.lng, zoom: 6 },
    flyToVersion: get().flyToVersion + 1,
  }),

  fetchNews: async () => {
    const { activeCategory, searchQuery } = get();
    set({ loading: true, error: null });
    try {
      // Fetch user's geo location once
      let { userCountry } = get();
      if (userCountry === null) {
        try {
          const geoRes = await fetch("/api/geo");
          if (geoRes.ok) {
            const geo = await geoRes.json();
            userCountry = geo.country || "US";
          } else {
            userCountry = "US";
          }
        } catch {
          userCountry = "US";
        }
        set({ userCountry });
      }

      const params = new URLSearchParams();
      if (activeCategory !== "all") params.set("topic", activeCategory);
      if (searchQuery) params.set("q", searchQuery);
      if (userCountry) params.set("loc", userCountry);

      // For search/topic queries, fetch all at once (no batching)
      if (searchQuery || activeCategory !== "all") {
        // When searching, don't pass topic — Google News search doesn't support it
        if (searchQuery) params.delete("topic");
        const res = await fetch(`/api/news?${params.toString()}`);
        if (!res.ok) throw new Error("Failed to fetch news");
        const rawFeeds: RawFeedResponse[] = await res.json();
        const parsed = parseRawFeeds(rawFeeds, activeCategory);
        const data = geocodeArticles(parsed);
        // Don't filter by category during search — results don't have meaningful categories
        const filtered = searchQuery
          ? filterArticles(data, "all", searchQuery)
          : filterArticles(data, activeCategory, searchQuery);

        let pendingFlyTo: FlyToTarget | null = null;
        if (searchQuery && filtered.length > 0) {
          const avgLat = filtered.reduce((s, a) => s + a.lat, 0) / filtered.length;
          const avgLng = filtered.reduce((s, a) => s + a.lng, 0) / filtered.length;
          pendingFlyTo = { lat: avgLat, lng: avgLng, zoom: 4 };
        }

        set({
          articles: data,
          filteredArticles: filtered,
          loading: false,
          pendingFlyTo,
          flyToVersion: pendingFlyTo ? get().flyToVersion + 1 : get().flyToVersion,
        });
        return;
      }

      // Global view: fetch incrementally in batches (stops when a batch returns empty)
      const MAX_BATCHES = 10;

      for (let b = 0; b < MAX_BATCHES; b++) {
        // Abort if user changed category, started a search, or selected a country mid-fetch
        const currentState = get();
        if (currentState.activeCategory !== activeCategory || currentState.searchQuery || currentState.selectedCountry) break;

        const batchParams = new URLSearchParams(params);
        batchParams.set("batch", String(b));
        const res = await fetch(`/api/news?${batchParams.toString()}`);
        if (!res.ok) continue;
        const batchRawFeeds: RawFeedResponse[] = await res.json();
        if (batchRawFeeds.length === 0) break; // no more batches
        const batchParsed = parseRawFeeds(batchRawFeeds);
        const batchData = geocodeArticles(batchParsed);

        const { articles: existing, activeCategory: cat, searchQuery: q } = get();
        // First batch replaces, subsequent batches merge
        const base = b === 0 ? [] : existing;
        const baseUrls = new Set(base.map((a) => a.url));
        const newArticles = batchData.filter((a) => !baseUrls.has(a.url));
        const merged = [...base, ...newArticles];
        const filtered = filterArticles(merged, cat, q);

        set({
          articles: merged,
          filteredArticles: filtered,
          loading: false,
        });
      }

      set({ loading: false });
    } catch (e) {
      set({ error: (e as Error).message, loading: false });
    }
  },

  selectCountry: async (code, name) => {
    const coords = COUNTRY_BY_CODE.get(code.toUpperCase());
    set({
      selectedCountry: { code, name },
      countryLoading: true,
      countryArticles: [],
      pendingFlyTo: coords ? { lat: coords.lat, lng: coords.lng, zoom: 4 } : null,
      flyToVersion: coords ? get().flyToVersion + 1 : get().flyToVersion,
    });
    try {
      const res = await fetch(`/api/news?country=${encodeURIComponent(code)}`);
      if (!res.ok) throw new Error("Failed to fetch country news");
      const rawFeeds: RawFeedResponse[] = await res.json();
      const parsed = parseRawFeeds(rawFeeds);
      const data = geocodeArticles(parsed);
      set({ countryArticles: data, countryLoading: false });
    } catch {
      set({ countryLoading: false });
    }
  },

  clearCountry: () => {
    set({
      selectedCountry: null,
      countryArticles: [],
      pendingFlyTo: { lat: 30, lng: 20, zoom: 1.8 },
      flyToVersion: get().flyToVersion + 1,
    });
  },
}));
