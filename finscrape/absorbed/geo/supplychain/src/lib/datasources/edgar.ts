// SEC EDGAR — 10-K filing supplier disclosures

interface EdgarSearchResult {
  hits: {
    hits: {
      _source: {
        file_date: string;
        entity_name: string;
        display_names?: string[];
      };
      _id: string;
    }[];
  };
}

export async function searchEdgarFilings(
  companyName: string,
  componentKeyword: string
): Promise<
  {
    entityName: string;
    filingDate: string;
    filingId: string;
  }[]
> {
  try {
    const query = `"${companyName}" "${componentKeyword}" supplier`;
    const res = await fetch(
      `https://efts.sec.gov/LATEST/search-index?q=${encodeURIComponent(query)}&dateRange=custom&startdt=2020-01-01&forms=10-K&hits.hits.total.value=10`,
      {
        headers: {
          "User-Agent": "SupplyChainIntelligence research@example.com",
          Accept: "application/json",
        },
        signal: AbortSignal.timeout(10000),
      }
    );

    if (!res.ok) return [];

    const data: EdgarSearchResult = await res.json();
    const hits = data.hits?.hits ?? [];

    return hits.map((h) => ({
      entityName: h._source.entity_name,
      filingDate: h._source.file_date,
      filingId: h._id,
    }));
  } catch (err) {
    console.error("[EDGAR] Search failed:", err);
    return [];
  }
}
