import { config } from "../config";

// OpenCorporates — company lookups

interface OCCompany {
  name: string;
  jurisdiction_code: string;
  registered_address_in_full: string | null;
  company_number: string;
}

export async function searchCompanies(
  query: string
): Promise<
  {
    name: string;
    country: string;
    address: string | null;
  }[]
> {
  try {
    const { baseUrl, key } = config.datasources.opencorporates;
    const params = new URLSearchParams({ q: query, per_page: "10" });
    if (key) params.set("api_token", key);

    const res = await fetch(
      `${baseUrl}/companies/search?${params.toString()}`,
      { signal: AbortSignal.timeout(10000) }
    );

    if (!res.ok) return [];

    const data = await res.json();
    const companies: OCCompany[] =
      data.results?.companies?.map(
        (c: { company: OCCompany }) => c.company
      ) ?? [];

    return companies.map((c) => ({
      name: c.name,
      country: c.jurisdiction_code?.toUpperCase()?.slice(0, 2) ?? "Unknown",
      address: c.registered_address_in_full,
    }));
  } catch (err) {
    console.error("[OpenCorporates] Search failed:", err);
    return [];
  }
}
