import { config } from "../config";
import type { NewsArticle } from "@/types";

// News fetching per company/node (NewsAPI + GDELT)

export async function fetchNewsForCompany(
  companyName: string
): Promise<NewsArticle[]> {
  const results: NewsArticle[] = [];

  // Try NewsAPI
  const newsApiResults = await fetchFromNewsAPI(companyName);
  results.push(...newsApiResults);

  // Try GDELT
  const gdeltResults = await fetchFromGDELT(companyName);
  results.push(...gdeltResults);

  // Deduplicate by URL
  const seen = new Set<string>();
  return results.filter((article) => {
    if (seen.has(article.url)) return false;
    seen.add(article.url);
    return true;
  });
}

async function fetchFromNewsAPI(query: string): Promise<NewsArticle[]> {
  try {
    if (!config.newsapi.key) return [];

    const params = new URLSearchParams({
      q: query,
      sortBy: "relevancy",
      pageSize: "5",
      apiKey: config.newsapi.key,
    });

    const res = await fetch(
      `${config.newsapi.baseUrl}/everything?${params.toString()}`,
      { signal: AbortSignal.timeout(10000) }
    );

    if (!res.ok) return [];

    const data = await res.json();
    return (data.articles ?? []).map(
      (a: {
        title: string;
        source: { name: string };
        url: string;
        publishedAt: string;
        description: string;
      }) => ({
        title: a.title,
        source: a.source?.name ?? "Unknown",
        url: a.url,
        publishedAt: a.publishedAt,
        summary: a.description ?? "",
      })
    );
  } catch (err) {
    console.error("[NewsAPI] Fetch failed:", err);
    return [];
  }
}

async function fetchFromGDELT(query: string): Promise<NewsArticle[]> {
  try {
    const params = new URLSearchParams({
      query: query,
      mode: "artlist",
      maxrecords: "5",
      format: "json",
    });

    const res = await fetch(
      `${config.gdelt.baseUrl}/doc/doc?${params.toString()}`,
      { signal: AbortSignal.timeout(10000) }
    );

    if (!res.ok) return [];

    const data = await res.json();
    return (data.articles ?? []).map(
      (a: {
        title: string;
        domain: string;
        url: string;
        seendate: string;
      }) => ({
        title: a.title,
        source: a.domain ?? "GDELT",
        url: a.url,
        publishedAt: a.seendate ?? "",
        summary: "",
      })
    );
  } catch (err) {
    console.error("[GDELT] Fetch failed:", err);
    return [];
  }
}

export async function fetchNewsForNode(
  nodeLabel: string,
  relatedCompanies: string[]
): Promise<NewsArticle[]> {
  const allArticles: NewsArticle[] = [];

  // Search for the component/material itself
  const nodeNews = await fetchFromGDELT(`${nodeLabel} supply chain`);
  allArticles.push(...nodeNews);

  // Search for each related company
  for (const company of relatedCompanies.slice(0, 3)) {
    const companyNews = await fetchNewsForCompany(company);
    allArticles.push(...companyNews);
  }

  // Deduplicate
  const seen = new Set<string>();
  return allArticles.filter((article) => {
    if (seen.has(article.url)) return false;
    seen.add(article.url);
    return true;
  });
}
