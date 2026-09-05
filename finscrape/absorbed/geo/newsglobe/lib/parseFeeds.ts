import { NewsArticle, Category } from "./types";

/** Raw feed response from the API (XML string + metadata) */
export interface RawFeedResponse {
  xml: string;
  meta: {
    lat: number;
    lng: number;
    name: string;
    feedName?: string;
    category?: string;
  };
}

/** Parse RSS XML string using browser's native DOMParser */
function parseRssXml(xml: string): {
  title: string;
  items: {
    title: string;
    link: string;
    guid: string;
    pubDate: string;
    content: string;
    thumbnail?: string;
  }[];
} {
  const parser = new DOMParser();
  const doc = parser.parseFromString(xml, "text/xml");

  const feedTitle = doc.querySelector("channel > title")?.textContent || "";
  const itemEls = doc.querySelectorAll("item");

  const items = Array.from(itemEls).map((el) => {
    const title = el.querySelector("title")?.textContent || "";
    const link = el.querySelector("link")?.textContent || "";
    const guid = el.querySelector("guid")?.textContent || link;
    const pubDate = el.querySelector("pubDate")?.textContent || "";
    const content =
      el.querySelector("description")?.textContent ||
      el.querySelector("content\\:encoded, encoded")?.textContent ||
      "";

    // Extract thumbnail from media:content, media:thumbnail, or enclosure
    let thumbnail: string | undefined;
    const mediaContent = el.getElementsByTagNameNS("http://search.yahoo.com/mrss/", "content")[0];
    const mediaThumbnail = el.getElementsByTagNameNS("http://search.yahoo.com/mrss/", "thumbnail")[0];
    const enclosure = el.querySelector("enclosure");

    if (mediaContent?.getAttribute("url")) {
      thumbnail = mediaContent.getAttribute("url")!;
    } else if (mediaThumbnail?.getAttribute("url")) {
      thumbnail = mediaThumbnail.getAttribute("url")!;
    } else if (enclosure?.getAttribute("url")) {
      const encUrl = enclosure.getAttribute("url")!;
      if (/\.(jpg|jpeg|png|webp|gif)/i.test(encUrl)) {
        thumbnail = encUrl;
      }
    }

    return { title, link, guid, pubDate, content, thumbnail };
  });

  return { title: feedTitle, items };
}

function extractSource(title: string): string {
  const match = title.match(/ - ([^-]+)$/);
  return match ? match[1].trim() : "Unknown";
}

function cleanTitle(title: string): string {
  return title.replace(/ - [^-]+$/, "").trim();
}

function stripHtml(html: string): string {
  if (typeof document !== "undefined") {
    const div = document.createElement("div");
    div.innerHTML = html;
    return div.textContent || div.innerText || "";
  }
  return html.replace(/<[^>]*>/g, "");
}

/** Parse an array of raw feed responses into NewsArticle[] */
export function parseRawFeeds(
  rawFeeds: RawFeedResponse[],
  defaultCategory: Category | "all" = "all"
): NewsArticle[] {
  const articles: NewsArticle[] = [];
  const seenUrls = new Set<string>();

  for (const raw of rawFeeds) {
    try {
      const feed = parseRssXml(raw.xml);
      const category = (raw.meta.category || "general") as Category;

      for (const item of feed.items) {
        const url = item.link;
        if (!url || seenUrls.has(url)) continue;
        seenUrls.add(url);

        const title = item.title;
        const titleSource = extractSource(title);
        const source =
          raw.meta.feedName ||
          (titleSource !== "Unknown" ? titleSource : feed.title || "Unknown");

        articles.push({
          id: item.guid || url || Math.random().toString(36),
          title: cleanTitle(title),
          snippet: stripHtml(item.content).slice(0, 200),
          url,
          source,
          publishedAt: item.pubDate
            ? new Date(item.pubDate).toISOString()
            : new Date().toISOString(),
          category: defaultCategory !== "all" ? defaultCategory as Category : category,
          lat: raw.meta.lat,
          lng: raw.meta.lng,
          regionLat: raw.meta.lat,
          regionLng: raw.meta.lng,
          thumbnail: item.thumbnail,
        });
      }
    } catch {
      // Skip feeds that fail to parse
    }
  }

  // Sort by date, newest first
  articles.sort(
    (a, b) =>
      new Date(b.publishedAt).getTime() - new Date(a.publishedAt).getTime()
  );

  return articles;
}
