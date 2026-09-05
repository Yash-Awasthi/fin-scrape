// Wikidata SPARQL — product/material/manufacturer relationships

export async function searchManufacturers(
  productOrMaterial: string
): Promise<
  {
    name: string;
    country: string;
    description: string;
  }[]
> {
  try {
    const sparql = `
SELECT DISTINCT ?company ?companyLabel ?countryLabel ?desc WHERE {
  ?product rdfs:label ?productLabel .
  FILTER(CONTAINS(LCASE(?productLabel), "${productOrMaterial.toLowerCase()}"))
  FILTER(LANG(?productLabel) = "en")

  { ?product wdt:P176 ?company . }
  UNION
  { ?product wdt:P1056 ?company . }
  UNION
  { ?company wdt:P1056 ?product . }

  OPTIONAL { ?company wdt:P17 ?country . }
  OPTIONAL { ?company schema:description ?desc . FILTER(LANG(?desc) = "en") }

  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
LIMIT 15`;

    const res = await fetch(
      `https://query.wikidata.org/sparql?query=${encodeURIComponent(sparql)}`,
      {
        headers: { Accept: "application/sparql-results+json" },
        signal: AbortSignal.timeout(15000),
      }
    );

    if (!res.ok) return [];

    const data = await res.json();
    const bindings = data.results?.bindings ?? [];

    return bindings.map(
      (b: {
        companyLabel?: { value: string };
        countryLabel?: { value: string };
        desc?: { value: string };
      }) => ({
        name: b.companyLabel?.value ?? "Unknown",
        country: b.countryLabel?.value ?? "Unknown",
        description: b.desc?.value ?? "",
      })
    );
  } catch (err) {
    console.error("[Wikidata] Search failed:", err);
    return [];
  }
}
