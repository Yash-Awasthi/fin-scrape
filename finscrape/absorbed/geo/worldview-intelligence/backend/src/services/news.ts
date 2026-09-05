import Parser from 'rss-parser';
import { NewsEvent } from '../types';
import { cacheGet, cacheSet } from '../utils/cache';

const parser = new Parser({ timeout: 10000 });

const RSS_FEEDS = [
  { url: 'https://feeds.bbci.co.uk/news/world/rss.xml', source: 'BBC World' },
  { url: 'https://feeds.bbci.co.uk/news/rss.xml', source: 'BBC News' },
  { url: 'https://rss.nytimes.com/services/xml/rss/nyt/World.xml', source: 'NY Times World' },
  { url: 'https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml', source: 'NY Times' },
  { url: 'https://www.aljazeera.com/xml/rss/all.xml', source: 'Al Jazeera' },
  { url: 'https://feeds.skynews.com/feeds/rss/world.xml', source: 'Sky News' },
  { url: 'https://www.theguardian.com/world/rss', source: 'The Guardian' },
];

const CACHE_KEY = 'news:events';
const CACHE_TTL = 300;

const LOCATION_COORDS: Record<string, { lat: number; lng: number }> = {
  'ukraine': { lat: 48.38, lng: 31.17 }, 'kyiv': { lat: 50.45, lng: 30.52 },
  'russia': { lat: 55.75, lng: 37.62 }, 'moscow': { lat: 55.76, lng: 37.62 },
  'gaza': { lat: 31.35, lng: 34.31 }, 'israel': { lat: 31.77, lng: 35.23 },
  'jerusalem': { lat: 31.77, lng: 35.23 }, 'tel aviv': { lat: 32.08, lng: 34.78 },
  'syria': { lat: 34.80, lng: 38.99 }, 'damascus': { lat: 33.51, lng: 36.29 },
  'iran': { lat: 35.69, lng: 51.39 }, 'tehran': { lat: 35.69, lng: 51.39 },
  'china': { lat: 39.90, lng: 116.40 }, 'beijing': { lat: 39.90, lng: 116.40 },
  'taiwan': { lat: 25.03, lng: 121.57 }, 'taipei': { lat: 25.03, lng: 121.57 },
  'north korea': { lat: 39.02, lng: 125.75 }, 'pyongyang': { lat: 39.02, lng: 125.75 },
  'south korea': { lat: 37.57, lng: 126.98 }, 'seoul': { lat: 37.57, lng: 126.98 },
  'japan': { lat: 35.68, lng: 139.69 }, 'tokyo': { lat: 35.68, lng: 139.69 },
  'india': { lat: 28.61, lng: 77.21 }, 'new delhi': { lat: 28.61, lng: 77.21 },
  'pakistan': { lat: 33.69, lng: 73.04 }, 'islamabad': { lat: 33.69, lng: 73.04 },
  'afghanistan': { lat: 34.53, lng: 69.17 }, 'kabul': { lat: 34.53, lng: 69.17 },
  'iraq': { lat: 33.31, lng: 44.37 }, 'baghdad': { lat: 33.31, lng: 44.37 },
  'yemen': { lat: 15.37, lng: 44.21 }, 'saudi arabia': { lat: 24.71, lng: 46.68 },
  'sudan': { lat: 15.59, lng: 32.53 }, 'khartoum': { lat: 15.59, lng: 32.53 },
  'ethiopia': { lat: 9.02, lng: 38.75 }, 'somalia': { lat: 2.05, lng: 45.34 },
  'myanmar': { lat: 19.76, lng: 96.07 }, 'congo': { lat: -4.32, lng: 15.31 },
  'nigeria': { lat: 9.06, lng: 7.49 }, 'libya': { lat: 32.90, lng: 13.18 },
  'lebanon': { lat: 33.89, lng: 35.50 }, 'beirut': { lat: 33.89, lng: 35.50 },
  'turkey': { lat: 39.93, lng: 32.87 }, 'ankara': { lat: 39.93, lng: 32.87 },
  'united states': { lat: 38.91, lng: -77.04 }, 'washington': { lat: 38.91, lng: -77.04 },
  'new york': { lat: 40.71, lng: -74.01 }, 'london': { lat: 51.51, lng: -0.13 },
  'paris': { lat: 48.86, lng: 2.35 }, 'berlin': { lat: 52.52, lng: 13.41 },
  'brussels': { lat: 50.85, lng: 4.35 }, 'nato': { lat: 50.88, lng: 4.43 },
  'european union': { lat: 50.85, lng: 4.35 }, 'eu': { lat: 46.23, lng: 6.14 },
  'united nations': { lat: 40.75, lng: -73.97 }, 'mexico': { lat: 19.43, lng: -99.13 },
  'brazil': { lat: -15.79, lng: -47.88 }, 'argentina': { lat: -34.60, lng: -58.38 },
  'colombia': { lat: 4.71, lng: -74.07 }, 'venezuela': { lat: 10.49, lng: -66.88 },
  'egypt': { lat: 30.04, lng: 31.24 }, 'cairo': { lat: 30.04, lng: 31.24 },
  'south africa': { lat: -33.92, lng: 18.42 }, 'kenya': { lat: -1.29, lng: 36.82 },
  'australia': { lat: -33.87, lng: 151.21 }, 'singapore': { lat: 1.35, lng: 103.82 },
  'indonesia': { lat: -6.21, lng: 106.85 }, 'philippines': { lat: 14.60, lng: 120.98 },
  'red sea': { lat: 20.0, lng: 38.0 }, 'black sea': { lat: 43.0, lng: 35.0 },
  'mediterranean': { lat: 35.0, lng: 18.0 }, 'crimea': { lat: 45.3, lng: 34.1 },
  'donbas': { lat: 48.0, lng: 37.8 }, 'kherson': { lat: 46.6, lng: 32.6 },
  'odesa': { lat: 46.48, lng: 30.73 }, 'zaporizhzhia': { lat: 47.84, lng: 35.14 },
  'rafah': { lat: 31.28, lng: 34.25 }, 'khan younis': { lat: 31.35, lng: 34.30 },
  'west bank': { lat: 32.0, lng: 35.2 }, 'houthi': { lat: 15.37, lng: 44.21 },
};

const CATEGORY_KEYWORDS: Record<NewsEvent['category'], string[]> = {
  conflict: ['war', 'attack', 'military', 'bomb', 'strike', 'troops', 'killed', 'missile', 'battle', 'invasion', 'airstrike', 'artillery', 'ceasefire', 'hostage', 'combat', 'drone', 'shelling', 'offensive'],
  disaster: ['earthquake', 'flood', 'hurricane', 'tornado', 'wildfire', 'tsunami', 'volcano', 'drought', 'landslide', 'cyclone', 'storm', 'disaster', 'emergency', 'rescue'],
  politics: ['election', 'president', 'minister', 'parliament', 'vote', 'summit', 'treaty', 'sanction', 'diplomat', 'government', 'policy', 'legislation', 'law', 'inauguration'],
  economic: ['economy', 'market', 'trade', 'inflation', 'gdp', 'stock', 'bank', 'currency', 'tariff', 'debt', 'recession', 'oil price', 'investment', 'fed', 'interest rate'],
  protest: ['protest', 'demonstration', 'rally', 'march', 'unrest', 'riot', 'strike', 'uprising', 'dissent', 'activist', 'crackdown'],
  technology: ['ai', 'tech', 'cyber', 'space', 'satellite', 'launch', 'robot', 'quantum', 'software', 'hack', 'data breach', 'innovation', 'spacex', 'nasa'],
};

function categorizeArticle(title: string, content: string): NewsEvent['category'] {
  const text = `${title} ${content}`.toLowerCase();
  let best: NewsEvent['category'] = 'politics';
  let bestScore = 0;
  for (const [cat, keywords] of Object.entries(CATEGORY_KEYWORDS) as [NewsEvent['category'], string[]][]) {
    const score = keywords.reduce((s, kw) => s + (text.includes(kw) ? 1 : 0), 0);
    if (score > bestScore) { bestScore = score; best = cat; }
  }
  return best;
}

function geocodeFromTitle(title: string): { lat: number; lng: number } | null {
  const lower = title.toLowerCase();
  for (const [location, coords] of Object.entries(LOCATION_COORDS)) {
    if (lower.includes(location)) return coords;
  }
  return null;
}

function simpleSentiment(title: string): number {
  const lower = title.toLowerCase();
  const negatives = ['kill', 'dead', 'attack', 'war', 'crisis', 'threat', 'bomb', 'explosion', 'disaster', 'collapse', 'fear', 'terror', 'violence', 'strike', 'missile'];
  const positives = ['peace', 'deal', 'agreement', 'rescue', 'recover', 'growth', 'success', 'aid', 'relief', 'hope', 'ceasefire', 'talks'];
  let score = 0;
  for (const w of negatives) if (lower.includes(w)) score -= 0.15;
  for (const w of positives) if (lower.includes(w)) score += 0.15;
  return Math.max(-1, Math.min(1, score));
}

function generateMockNews(): NewsEvent[] {
  const now = Date.now() / 1000;
  const mockArticles: Omit<NewsEvent, 'id'>[] = [
    { title: 'Heavy shelling reported along Donetsk frontline as Ukraine pushes counteroffensive', description: 'Ukrainian forces launched a series of attacks along the eastern front, targeting Russian positions near Avdiivka.', category: 'conflict', position: { lat: 48.14, lng: 37.74 }, source: 'Mock Intel', url: '', timestamp: now - 1800, sentiment: -0.45 },
    { title: 'Gaza humanitarian crisis deepens as aid deliveries remain blocked', description: 'UN agencies warn of catastrophic food shortages as crossing points remain closed for the third consecutive week.', category: 'conflict', position: { lat: 31.35, lng: 34.31 }, source: 'Mock Intel', url: '', timestamp: now - 3600, sentiment: -0.6 },
    { title: 'Houthi forces claim missile strike on cargo vessel in Red Sea', description: 'A commercial cargo ship was reportedly struck by an anti-ship missile near the Bab el-Mandeb strait.', category: 'conflict', position: { lat: 12.8, lng: 43.3 }, source: 'Mock Intel', url: '', timestamp: now - 5400, sentiment: -0.45 },
    { title: 'NATO summit discusses expanded air defense shield for Eastern Europe', description: 'Alliance leaders met in Brussels to coordinate enhanced defense posture along the eastern flank.', category: 'politics', position: { lat: 50.88, lng: 4.43 }, source: 'Mock Intel', url: '', timestamp: now - 7200, sentiment: 0.15 },
    { title: 'Magnitude 5.8 earthquake strikes central Turkey, no casualties reported', description: 'The quake was felt across several provinces but initial reports indicate minimal structural damage.', category: 'disaster', position: { lat: 39.93, lng: 32.87 }, source: 'Mock Intel', url: '', timestamp: now - 9000, sentiment: -0.15 },
    { title: 'China conducts military exercises near Taiwan strait amid tensions', description: 'PLA Navy and Air Force units conducted joint exercises in waters east of Taiwan.', category: 'conflict', position: { lat: 24.5, lng: 120.0 }, source: 'Mock Intel', url: '', timestamp: now - 10800, sentiment: -0.3 },
    { title: 'US Federal Reserve signals potential rate cut amid slowing inflation', description: 'Federal Reserve Chair indicated the central bank is monitoring data closely for signs of sustained disinflation.', category: 'economic', position: { lat: 38.89, lng: -77.04 }, source: 'Mock Intel', url: '', timestamp: now - 12600, sentiment: 0.15 },
    { title: 'Mass protests erupt in Tbilisi over proposed foreign agents law', description: 'Tens of thousands took to the streets of the Georgian capital in opposition to the controversial legislation.', category: 'protest', position: { lat: 41.72, lng: 44.79 }, source: 'Mock Intel', url: '', timestamp: now - 14400, sentiment: -0.3 },
    { title: 'Sudan civil war forces two million to flee Khartoum region', description: 'Fighting between RSF and SAF has displaced millions as infrastructure collapses.', category: 'conflict', position: { lat: 15.59, lng: 32.53 }, source: 'Mock Intel', url: '', timestamp: now - 16200, sentiment: -0.6 },
    { title: 'SpaceX successfully launches 60 Starlink satellites from Cape Canaveral', description: 'The latest batch brings the constellation total to over 6,000 operational satellites.', category: 'technology', position: { lat: 28.57, lng: -80.65 }, source: 'Mock Intel', url: '', timestamp: now - 18000, sentiment: 0.3 },
    { title: 'EU imposes new sanctions on Russian oil exports and financial institutions', description: 'The 14th package targets shadow fleet tankers and three major Russian banks.', category: 'politics', position: { lat: 50.85, lng: 4.35 }, source: 'Mock Intel', url: '', timestamp: now - 21600, sentiment: -0.15 },
    { title: 'Major flooding displaces thousands in Bangladesh monsoon season', description: 'Rivers broke their banks across the Sylhet division, inundating villages and farmland.', category: 'disaster', position: { lat: 24.90, lng: 91.87 }, source: 'Mock Intel', url: '', timestamp: now - 25200, sentiment: -0.45 },
    { title: 'North Korea test-fires ballistic missile into Sea of Japan', description: 'South Korean and Japanese militaries confirmed the launch of a medium-range ballistic missile.', category: 'conflict', position: { lat: 39.02, lng: 125.75 }, source: 'Mock Intel', url: '', timestamp: now - 28800, sentiment: -0.45 },
    { title: 'Oil prices surge after OPEC announces deeper production cuts', description: 'Brent crude rose above $90/barrel following the cartel decision to extend supply restrictions.', category: 'economic', position: { lat: 24.71, lng: 46.68 }, source: 'Mock Intel', url: '', timestamp: now - 32400, sentiment: -0.15 },
    { title: 'India-Pakistan border tensions escalate after ceasefire violation', description: 'Both nations exchanged artillery fire along the Line of Control in Kashmir.', category: 'conflict', position: { lat: 34.08, lng: 74.79 }, source: 'Mock Intel', url: '', timestamp: now - 36000, sentiment: -0.3 },
    { title: 'Myanmar resistance forces capture key military outpost in Shan State', description: 'Combined ethnic armed organizations overran a junta base controlling a strategic highway.', category: 'conflict', position: { lat: 21.0, lng: 97.5 }, source: 'Mock Intel', url: '', timestamp: now - 39600, sentiment: -0.3 },
    { title: 'Cyberattack disrupts critical infrastructure in three European countries', description: 'Coordinated attacks targeted energy grids and telecommunications networks in Estonia, Latvia, and Poland.', category: 'technology', position: { lat: 59.44, lng: 24.75 }, source: 'Mock Intel', url: '', timestamp: now - 43200, sentiment: -0.45 },
    { title: 'G7 leaders pledge $50 billion aid package for Ukraine reconstruction', description: 'The commitment comes as Western allies seek to bolster long-term support for Ukrainian recovery.', category: 'politics', position: { lat: 50.45, lng: 30.52 }, source: 'Mock Intel', url: '', timestamp: now - 46800, sentiment: 0.3 },
    { title: 'Severe drought threatens crop yields across East Africa', description: 'Kenya, Ethiopia, and Somalia face potential famine as rainfall remains below average for the fifth consecutive season.', category: 'disaster', position: { lat: 1.0, lng: 38.0 }, source: 'Mock Intel', url: '', timestamp: now - 50400, sentiment: -0.45 },
    { title: 'Venezuelan opposition calls for mass demonstrations after disputed election', description: 'Hundreds of thousands gathered in Caracas demanding recognition of opposition victory.', category: 'protest', position: { lat: 10.49, lng: -66.88 }, source: 'Mock Intel', url: '', timestamp: now - 54000, sentiment: -0.3 },
    { title: 'Japan and Philippines sign landmark defense cooperation agreement', description: 'The pact allows reciprocal access to military bases amid shared concerns over regional security.', category: 'politics', position: { lat: 35.68, lng: 139.69 }, source: 'Mock Intel', url: '', timestamp: now - 57600, sentiment: 0.15 },
    { title: 'Russian long-range drone strike hits energy infrastructure in Odesa', description: 'Power outages reported across the port city after multiple Shahed drones struck transformer stations.', category: 'conflict', position: { lat: 46.48, lng: 30.73 }, source: 'Mock Intel', url: '', timestamp: now - 61200, sentiment: -0.45 },
    { title: 'Israeli military expands operations in West Bank amid settler violence', description: 'IDF raids in Jenin and Tulkarm resulted in multiple arrests and clashes with local residents.', category: 'conflict', position: { lat: 32.46, lng: 35.30 }, source: 'Mock Intel', url: '', timestamp: now - 64800, sentiment: -0.45 },
    { title: 'Climate summit in Dubai reaches historic agreement on fossil fuel transition', description: 'Nearly 200 nations agreed to begin transitioning away from fossil fuels in a landmark COP declaration.', category: 'politics', position: { lat: 25.20, lng: 55.27 }, source: 'Mock Intel', url: '', timestamp: now - 72000, sentiment: 0.3 },
    { title: 'South China Sea tensions rise as coast guard vessels clash near disputed reef', description: 'Philippine and Chinese coast guard ships engaged in a water cannon confrontation near Second Thomas Shoal.', category: 'conflict', position: { lat: 9.75, lng: 115.87 }, source: 'Mock Intel', url: '', timestamp: now - 79200, sentiment: -0.3 },
  ];

  return mockArticles.map((a, i) => ({ ...a, id: `mock-news-${i}` }));
}

export async function fetchNewsEvents(): Promise<NewsEvent[]> {
  try {
    const cached = await cacheGet(CACHE_KEY);
    if (cached) return JSON.parse(cached) as NewsEvent[];

    const feedPromises = RSS_FEEDS.map(async (feed) => {
      try {
        const result = await parser.parseURL(feed.url);
        return result.items.map((item) => ({ item, source: feed.source }));
      } catch {
        return [];
      }
    });

    const feedResults = await Promise.allSettled(feedPromises);
    const allItems = feedResults
      .filter((r): r is PromiseFulfilledResult<{ item: Parser.Item; source: string }[]> => r.status === 'fulfilled')
      .flatMap((r) => r.value);

    let events: NewsEvent[] = allItems.map((entry, i) => {
      const title = entry.item.title || 'Untitled';
      const description = entry.item.contentSnippet || entry.item.content || '';
      const coords = geocodeFromTitle(title);

      return {
        id: `news-${i}-${Date.now()}`,
        title,
        description: description.slice(0, 300),
        category: categorizeArticle(title, description),
        position: coords ? { lat: coords.lat, lng: coords.lng } : null,
        source: entry.source,
        url: entry.item.link || '',
        timestamp: entry.item.isoDate ? new Date(entry.item.isoDate).getTime() / 1000 : Date.now() / 1000,
        sentiment: simpleSentiment(title),
      };
    });

    if (events.length < 5) {
      console.log('[NewsService] Few RSS results — supplementing with mock data');
      events = [...events, ...generateMockNews()];
    }

    await cacheSet(CACHE_KEY, JSON.stringify(events), CACHE_TTL);
    return events;
  } catch (err) {
    console.error('[NewsService] RSS failed — using mock data:', err instanceof Error ? err.message : err);
    const mock = generateMockNews();
    await cacheSet(CACHE_KEY, JSON.stringify(mock), CACHE_TTL);
    return mock;
  }
}
