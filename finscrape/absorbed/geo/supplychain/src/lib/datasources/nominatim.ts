// OpenStreetMap Nominatim — geocoding

interface NominatimResult {
  lat: string;
  lon: string;
  display_name: string;
}

export async function geocode(
  query: string
): Promise<{ lat: number; lon: number; displayName: string } | null> {
  try {
    const params = new URLSearchParams({
      q: query,
      format: "json",
      limit: "1",
    });

    const res = await fetch(
      `https://nominatim.openstreetmap.org/search?${params.toString()}`,
      {
        headers: {
          "User-Agent": "SupplyChainIntelligence/1.0",
        },
        signal: AbortSignal.timeout(10000),
      }
    );

    if (!res.ok) return null;

    const results: NominatimResult[] = await res.json();
    if (results.length === 0) return null;

    return {
      lat: parseFloat(results[0].lat),
      lon: parseFloat(results[0].lon),
      displayName: results[0].display_name,
    };
  } catch (err) {
    console.error("[Nominatim] Geocode failed:", err);
    return null;
  }
}

// Rate-limited batch geocoding (1 req/sec for Nominatim)
export async function batchGeocode(
  queries: string[]
): Promise<Map<string, { lat: number; lon: number }>> {
  const results = new Map<string, { lat: number; lon: number }>();

  for (const query of queries) {
    const result = await geocode(query);
    if (result) {
      results.set(query, { lat: result.lat, lon: result.lon });
    }
    // Respect rate limit
    await new Promise((resolve) => setTimeout(resolve, 1100));
  }

  return results;
}
