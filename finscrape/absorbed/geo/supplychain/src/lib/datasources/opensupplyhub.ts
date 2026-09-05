// Open Supply Hub — factory/facility database with locations

interface OSHFacility {
  id: string;
  properties: {
    name: string;
    address: string;
    country_name: string;
    country_code: string;
  };
  geometry: {
    coordinates: [number, number]; // [lon, lat]
  };
}

export async function searchFacilities(
  query: string
): Promise<
  {
    name: string;
    country: string;
    countryCode: string;
    address: string;
    lat: number;
    lon: number;
  }[]
> {
  try {
    const params = new URLSearchParams({
      q: query,
      pageSize: "10",
    });

    const res = await fetch(
      `https://opensupplyhub.org/api/facilities/?${params.toString()}`,
      {
        headers: {
          Accept: "application/json",
        },
        signal: AbortSignal.timeout(10000),
      }
    );

    if (!res.ok) return [];

    const data = await res.json();
    const features: OSHFacility[] = data.features ?? [];

    return features.map((f) => ({
      name: f.properties.name,
      country: f.properties.country_name,
      countryCode: f.properties.country_code,
      address: f.properties.address,
      lat: f.geometry.coordinates[1],
      lon: f.geometry.coordinates[0],
    }));
  } catch (err) {
    console.error("[OpenSupplyHub] Search failed:", err);
    return [];
  }
}
