import { searchCompanies } from "../datasources/opencorporates";
import { searchManufacturers } from "../datasources/wikidata";
import { searchFacilities } from "../datasources/opensupplyhub";
import { searchComtrade } from "../datasources/comtrade";
import { searchEdgarFilings } from "../datasources/edgar";
import { geocode } from "../datasources/nominatim";
import { chatCompletionJson } from "../azure/client";
import { insertCompanies, getNode } from "../db/queries";
import type { SupplyNode } from "@/types";

// Multi-source supplier aggregation per node

interface RawSupplierCandidate {
  name: string;
  country?: string;
  city?: string;
  lat?: number;
  lon?: number;
  source: string;
  status: "confirmed_supplier" | "known_producer";
}

export async function discoverSuppliersForNode(
  nodeId: string,
  company: string,
  _product: string
): Promise<void> {
  const node = await getNode(nodeId);
  if (!node) throw new Error("Node not found");

  console.log(`[Supplier Discovery] Searching for: ${node.label}`);

  // Query all data sources in parallel
  const [
    ocResults,
    wikiResults,
    oshResults,
    comtradeResults,
    edgarResults,
  ] = await Promise.all([
    searchCompanies(`${node.label} manufacturer`).catch(() => []),
    searchManufacturers(node.label).catch(() => []),
    searchFacilities(node.label).catch(() => []),
    searchComtrade(node.label).catch(() => []),
    searchEdgarFilings(company, node.label).catch(() => []),
  ]);

  // Normalize into candidates
  const candidates: RawSupplierCandidate[] = [];

  for (const oc of ocResults) {
    candidates.push({
      name: oc.name,
      country: oc.country,
      source: "opencorporates",
      status: "known_producer",
    });
  }

  for (const wiki of wikiResults) {
    candidates.push({
      name: wiki.name,
      country: wiki.country,
      source: "wikidata",
      status: "known_producer",
    });
  }

  for (const osh of oshResults) {
    candidates.push({
      name: osh.name,
      country: osh.country,
      lat: osh.lat,
      lon: osh.lon,
      source: "opensupplyhub",
      status: "confirmed_supplier",
    });
  }

  for (const ct of comtradeResults) {
    candidates.push({
      name: `${ct.country} (trade flow)`,
      country: ct.country,
      source: "comtrade",
      status: "known_producer",
    });
  }

  for (const edgar of edgarResults) {
    candidates.push({
      name: edgar.entityName,
      source: "edgar",
      status: "confirmed_supplier",
    });
  }

  if (candidates.length === 0) return;

  // Deduplicate via LLM fuzzy matching
  const deduped = await deduplicateCompanies(candidates, node);

  // Geocode companies without lat/lon
  for (const company_data of deduped) {
    if (!company_data.lat && company_data.country) {
      const location = `${company_data.name}, ${company_data.city ?? company_data.country}`;
      const geo = await geocode(location);
      if (geo) {
        company_data.lat = geo.lat;
        company_data.lon = geo.lon;
      }
    }
  }

  // Insert into DB
  await insertCompanies(
    nodeId,
    deduped.map((c) => ({
      name: c.name,
      country: c.country,
      city: c.city,
      lat: c.lat,
      lon: c.lon,
      status: c.status,
      source: c.source,
    }))
  );
}

async function deduplicateCompanies(
  candidates: RawSupplierCandidate[],
  node: SupplyNode
): Promise<RawSupplierCandidate[]> {
  if (candidates.length <= 3) return candidates;

  try {
    const result = await chatCompletionJson<{
      companies: {
        name: string;
        country: string;
        status: "confirmed_supplier" | "known_producer";
        source: string;
      }[];
    }>(
      `You are deduplicating company search results for the supply chain component "${node.label}".
Merge entries that refer to the same company (different spellings, abbreviations, etc.).
Keep the most specific/accurate name for each.
Remove entries that are clearly not manufacturers/suppliers of "${node.label}".

Output JSON:
{
  "companies": [
    { "name": "Company Name", "country": "Country", "status": "confirmed_supplier" | "known_producer", "source": "source_name" }
  ]
}`,
      `Deduplicate these supplier candidates:
${JSON.stringify(candidates, null, 2)}`,
      {}
    );

    return (result.companies ?? []).map((c) => ({
      name: c.name,
      country: c.country,
      source: c.source,
      status: c.status,
    }));
  } catch {
    // Fallback: simple dedup by lowercase name
    const seen = new Set<string>();
    return candidates.filter((c) => {
      const key = c.name.toLowerCase().trim();
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    });
  }
}
