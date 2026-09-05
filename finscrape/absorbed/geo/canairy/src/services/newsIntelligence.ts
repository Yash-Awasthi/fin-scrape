/**
 * @fileoverview News Intelligence Service for Brown Man Bunker
 * Adapted from Hummingbird's NewsIntelligenceEngine
 * Focuses on risk indicators and threat analysis
 */

import { RateLimiter } from './rateLimiter';
import { newsCache } from './newsCache';

interface NewsArticle {
  title: string;
  description: string;
  url: string;
  source: {
    id: string;
    name: string;
  };
  publishedAt: string;
  content: string;
  relevance_score?: number;
  source_credibility?: {
    score: number;
    bias: string;
    specialty?: string;
  };
  indicator_relevance?: string[];
}

interface SourceCredibility {
  score: number;
  bias: string;
  specialty: string;
}

interface IndicatorNewsMapping {
  indicators: string[];
  keywords: string[];
  exclusions: string[];
  sources: string[];
  context: string;
}

export class NewsIntelligenceService {
  private newsApiKey: string | undefined;
  private alphaVantageKey: string | undefined;

  // Rate limiters for each API
  private newsApiLimiter: RateLimiter;
  private alphaVantageLimiter: RateLimiter;
  
  private sourceCredibility: Record<string, SourceCredibility> = {
    'wsj': { score: 95, bias: 'center-right', specialty: 'business' },
    'reuters': { score: 92, bias: 'center', specialty: 'global_news' },
    'bloomberg': { score: 90, bias: 'center', specialty: 'finance' },
    'ft': { score: 88, bias: 'center-right', specialty: 'business' },
    'cnbc': { score: 75, bias: 'center', specialty: 'markets' },
    'yahoo-finance': { score: 70, bias: 'center', specialty: 'retail_finance' },
    'marketwatch': { score: 72, bias: 'center', specialty: 'markets' },
    'bbc-news': { score: 85, bias: 'center-left', specialty: 'global_news' },
    'cnn': { score: 65, bias: 'left', specialty: 'general_news' },
    'fox-news': { score: 60, bias: 'right', specialty: 'general_news' }
  };

  private indicatorNewsMapping: Record<string, IndicatorNewsMapping> = {
    econ_01_treasury_tail: {
      indicators: ['econ_01_treasury_tail'],
      keywords: ['treasury auction', 'bond market', 'yield curve', 'federal reserve', 'interest rates', 'banking stress', 'liquidity crisis'],
      exclusions: ['personal finance', 'mortgage rates'],
      sources: ['wsj', 'reuters', 'bloomberg', 'ft'],
      context: 'Federal Reserve and banking system stress indicators'
    },
    taiwan_pla_activity: {
      indicators: ['taiwan_pla_activity'],
      keywords: ['taiwan strait', 'china military', 'pla exercises', 'semiconductor', 'tsmc', 'china taiwan', 'south china sea'],
      exclusions: ['tourism', 'culture'],
      sources: ['reuters', 'bbc-news', 'wsj', 'ft'],
      context: 'Taiwan conflict risk and semiconductor supply chain'
    },
    oil_01_russian_brics: {
      indicators: ['oil_01_russian_brics'],
      keywords: ['russian oil', 'brics oil', 'sanctions evasion', 'oil trade', 'crude exports'],
      exclusions: ['oil prices general'],
      sources: ['reuters', 'bloomberg', 'wsj'],
      context: 'Oil trade de-dollarization and sanctions'
    },
    oil_02_mbridge_settlements: {
      indicators: ['oil_02_mbridge_settlements'],
      keywords: ['mbridge', 'central bank digital currency', 'cbdc', 'dedollarization', 'yuan oil', 'petrodollar'],
      exclusions: ['bitcoin', 'crypto'],
      sources: ['reuters', 'ft', 'wsj', 'bloomberg'],
      context: 'Dollar dominance and alternative payment systems'
    },
    market_01_intraday_swing: {
      indicators: ['market_01_intraday_swing'],
      keywords: ['market volatility', 'treasury yield', 'bond market crash', 'market stress', 'intraday swing'],
      exclusions: ['individual stocks'],
      sources: ['bloomberg', 'wsj', 'marketwatch', 'cnbc'],
      context: 'Market stress and volatility indicators'
    },
    ice_detention_surge: {
      indicators: ['ice_detention_surge'],
      keywords: ['ice detention', 'immigration enforcement', 'border security', 'deportation', 'immigrant detention'],
      exclusions: ['ice hockey'],
      sources: ['reuters', 'bbc-news', 'wsj'],
      context: 'Immigration enforcement and domestic control measures'
    },
    nato_high_readiness: {
      indicators: ['nato_high_readiness'],
      keywords: ['nato readiness', 'nato forces', 'article 5', 'nato activation', 'european security'],
      exclusions: ['nato summit'],
      sources: ['reuters', 'bbc-news', 'wsj'],
      context: 'NATO defense posture and European theater'
    },
    global_conflict_intensity: {
      indicators: ['global_conflict_intensity'],
      keywords: ['military conflict', 'war', 'armed conflict', 'geopolitical tension', 'international crisis'],
      exclusions: ['sports conflict', 'corporate conflict'],
      sources: ['reuters', 'bbc-news', 'wsj'],
      context: 'Global military and political stability'
    }
  };

  constructor() {
    this.newsApiKey = import.meta.env.VITE_NEWS_API_KEY;
    this.alphaVantageKey = import.meta.env.VITE_ALPHA_VANTAGE_API_KEY;

    // Initialize rate limiters based on API limits
    this.newsApiLimiter = new RateLimiter(100, 24 * 60 * 60 * 1000); // 100 requests per day
    this.alphaVantageLimiter = new RateLimiter(5, 60 * 1000); // 5 requests per minute

    if (!this.newsApiKey) {
      console.warn('⚠️ NEWS_API_KEY not found - using demo data');
    }

    // Clean up cache periodically
    setInterval(() => newsCache.cleanup(), 60 * 1000); // Every minute
  }

  async getNewsForIndicator(indicatorId: string, limit: number = 5): Promise<NewsArticle[]> {
    // Check cache first
    const cacheKey = `news:${indicatorId}:${limit}`;
    const cachedNews = newsCache.get<NewsArticle[]>(cacheKey);
    if (cachedNews) {
      console.log(`📰 Returning cached news for ${indicatorId}`);
      return cachedNews;
    }

    const mapping = this.indicatorNewsMapping[indicatorId];
    if (!mapping) {
      console.warn(`No news mapping found for indicator: ${indicatorId}`);
      return this.getMockNewsForIndicator(indicatorId, limit);
    }

    if (!this.newsApiKey) {
      return this.getMockNewsForIndicator(indicatorId, limit);
    }

    // Check rate limit
    if (!await this.newsApiLimiter.checkLimit('newsapi')) {
      console.warn('⚠️ News API rate limit exceeded, using cached or mock data');
      return this.getMockNewsForIndicator(indicatorId, limit);
    }

    try {
      const articles: NewsArticle[] = [];
      
      // Search for each keyword set
      for (const keyword of mapping.keywords.slice(0, 3)) { // Limit to prevent API overuse
        const query = this.buildSearchQuery(keyword, mapping.exclusions);
        const sources = mapping.sources.join(',');
        
        const url = `https://newsapi.org/v2/everything?` +
          `q=${encodeURIComponent(query)}&` +
          `sources=${sources}&` +
          `sortBy=publishedAt&` +
          `pageSize=${Math.ceil(limit / 2)}&` +
          `language=en&` +
          `from=${new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString()}`;

        const response = await fetch(url, {
          headers: {
            'X-API-Key': this.newsApiKey
          }
        });

        if (response.ok) {
          const data = await response.json();
          const enhancedArticles = data.articles.map((article: any) => ({
            ...article,
            relevance_score: this.calculateRelevanceScore(article, keyword),
            source_credibility: this.sourceCredibility[article.source.id] || { score: 60, bias: 'unknown' },
            indicator_relevance: [indicatorId]
          }));
          
          articles.push(...enhancedArticles);
        }
      }

      // Sort by relevance and credibility, remove duplicates
      const uniqueArticles = this.removeDuplicateArticles(articles);
      const sortedArticles = uniqueArticles
        .sort((a, b) => (b.relevance_score! * b.source_credibility!.score) - (a.relevance_score! * a.source_credibility!.score))
        .slice(0, limit);
      
      // Cache the results
      newsCache.set(cacheKey, sortedArticles);
      
      return sortedArticles;

    } catch (error) {
      console.error(`Error fetching news for ${indicatorId}:`, error);
      
      // If it's a 429 (rate limit) error, update our rate limiter
      if (error instanceof Error && error.message.includes('429')) {
        console.warn('📛 News API returned 429 - rate limit hit');
      }
      
      return this.getMockNewsForIndicator(indicatorId, limit);
    }
  }

  async getGlobalNewsFeed(limit: number = 10): Promise<NewsArticle[]> {
    // Get news for all indicators and combine
    const allNews: NewsArticle[] = [];
    
    for (const indicatorId of Object.keys(this.indicatorNewsMapping)) {
      const indicatorNews = await this.getNewsForIndicator(indicatorId, 2);
      allNews.push(...indicatorNews);
    }

    // Sort by publication date and relevance
    return allNews
      .sort((a, b) => new Date(b.publishedAt).getTime() - new Date(a.publishedAt).getTime())
      .slice(0, limit);
  }

  async getNewsForIndicators(indicatorIds: string[], limit: number = 20): Promise<Record<string, NewsArticle[]>> {
    const result: Record<string, NewsArticle[]> = {};
    
    for (const indicatorId of indicatorIds) {
      result[indicatorId] = await this.getNewsForIndicator(indicatorId, Math.ceil(limit / indicatorIds.length));
    }
    
    return result;
  }

  private buildSearchQuery(keyword: string, exclusions: string[]): string {
    let query = keyword;
    
    // Add exclusions with NOT operator
    if (exclusions.length > 0) {
      const excludeTerms = exclusions.map(term => `-"${term}"`).join(' ');
      query += ` ${excludeTerms}`;
    }
    
    return query;
  }

  private calculateRelevanceScore(article: any, keyword: string): number {
    let score = 0;
    const title = (article.title || '').toLowerCase();
    const description = (article.description || '').toLowerCase();
    const keywordLower = keyword.toLowerCase();
    
    // Title matches are more important
    if (title.includes(keywordLower)) score += 10;
    if (description.includes(keywordLower)) score += 5;
    
    // Recency boost (within 24 hours)
    const publishedAt = new Date(article.publishedAt).getTime();
    const now = Date.now();
    const hoursAgo = (now - publishedAt) / (1000 * 60 * 60);
    
    if (hoursAgo < 24) score += 5;
    else if (hoursAgo < 72) score += 2;
    
    return Math.max(score, 1); // Minimum score of 1
  }

  private removeDuplicateArticles(articles: NewsArticle[]): NewsArticle[] {
    const seen = new Set<string>();
    return articles.filter(article => {
      const key = article.title + article.source.name;
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    });
  }

  private getMockNewsForIndicator(indicatorId: string, limit: number): NewsArticle[] {
    const now = Date.now();
    const mockNews: Record<string, NewsArticle[]> = {
      econ_01_treasury_tail: [
        {
          title: "Federal Reserve Signals Cautious Approach to Rate Policy",
          description: "Treasury auction shows mixed demand as investors weigh inflation concerns against growth outlook. The 10-year auction tail widened to 3.5 basis points.",
          url: "https://news.google.com/search?q=treasury+auction+demand+federal+reserve",
          source: { id: "wsj", name: "Wall Street Journal" },
          publishedAt: new Date(now - 2 * 60 * 60 * 1000).toISOString(),
          content: "Demo content",
          relevance_score: 9,
          source_credibility: this.sourceCredibility.wsj,
          indicator_relevance: ["econ_01_treasury_tail"]
        },
        {
          title: "Bond Markets Flash Warning Signs as Auction Demand Weakens",
          description: "Weak demand at Treasury auctions raises concerns about investor appetite for U.S. debt.",
          url: "https://news.google.com/search?q=bond+market+treasury+yields",
          source: { id: "bloomberg", name: "Bloomberg" },
          publishedAt: new Date(now - 8 * 60 * 60 * 1000).toISOString(),
          content: "Demo content",
          relevance_score: 8,
          source_credibility: this.sourceCredibility.bloomberg,
          indicator_relevance: ["econ_01_treasury_tail"]
        }
      ],
      taiwan_pla_activity: [
        {
          title: "China Conducts Military Exercises Near Taiwan Strait",
          description: "PLA Air Force sends 28 aircraft into Taiwan's ADIZ, marking largest incursion this month. Semiconductor supply chain concerns rise.",
          url: "https://news.google.com/search?q=china+taiwan+military+PLA",
          source: { id: "reuters", name: "Reuters" },
          publishedAt: new Date(now - 4 * 60 * 60 * 1000).toISOString(),
          content: "Demo content",
          relevance_score: 10,
          source_credibility: this.sourceCredibility.reuters,
          indicator_relevance: ["taiwan_pla_activity"]
        },
        {
          title: "TSMC Contingency Plans Amid Rising Cross-Strait Tensions",
          description: "World's largest chipmaker reviews supply chain resilience as military activity increases in the region.",
          url: "https://news.google.com/search?q=TSMC+taiwan+semiconductor+supply+chain",
          source: { id: "ft", name: "Financial Times" },
          publishedAt: new Date(now - 12 * 60 * 60 * 1000).toISOString(),
          content: "Demo content",
          relevance_score: 9,
          source_credibility: this.sourceCredibility.ft,
          indicator_relevance: ["taiwan_pla_activity"]
        }
      ],
      market_01_intraday_swing: [
        {
          title: "Market Volatility Spikes on Economic Uncertainty",
          description: "10-year Treasury yields swing 15 basis points intraday as investors brace for Fed announcement.",
          url: "https://news.google.com/search?q=treasury+yield+volatility+market",
          source: { id: "bloomberg", name: "Bloomberg" },
          publishedAt: new Date(now - 1 * 60 * 60 * 1000).toISOString(),
          content: "Demo content",
          relevance_score: 8,
          source_credibility: this.sourceCredibility.bloomberg,
          indicator_relevance: ["market_01_intraday_swing"]
        },
        {
          title: "Wild Swings in Bond Market Raise Systemic Risk Concerns",
          description: "Treasury market liquidity deteriorates amid elevated volatility, regulators monitoring closely.",
          url: "https://news.google.com/search?q=bond+market+liquidity+volatility",
          source: { id: "wsj", name: "Wall Street Journal" },
          publishedAt: new Date(now - 6 * 60 * 60 * 1000).toISOString(),
          content: "Demo content",
          relevance_score: 9,
          source_credibility: this.sourceCredibility.wsj,
          indicator_relevance: ["market_01_intraday_swing"]
        }
      ],
      oil_01_russian_brics: [
        {
          title: "Russia Expands Oil Trade with BRICS Nations, Bypassing Dollar",
          description: "Indian refiners increasingly pay for Russian crude in non-dollar currencies as sanctions reshape global oil trade.",
          url: "https://news.google.com/search?q=russia+oil+BRICS+sanctions",
          source: { id: "reuters", name: "Reuters" },
          publishedAt: new Date(now - 5 * 60 * 60 * 1000).toISOString(),
          content: "Demo content",
          relevance_score: 9,
          source_credibility: this.sourceCredibility.reuters,
          indicator_relevance: ["oil_01_russian_brics"]
        },
        {
          title: "De-Dollarization Accelerates in Energy Markets",
          description: "BRICS nations settle growing share of oil trades in local currencies, challenging petrodollar system.",
          url: "https://news.google.com/search?q=dedollarization+oil+BRICS+currency",
          source: { id: "ft", name: "Financial Times" },
          publishedAt: new Date(now - 18 * 60 * 60 * 1000).toISOString(),
          content: "Demo content",
          relevance_score: 8,
          source_credibility: this.sourceCredibility.ft,
          indicator_relevance: ["oil_01_russian_brics"]
        }
      ],
      oil_02_mbridge_settlements: [
        {
          title: "mBridge CBDC Platform Processes Record Gulf Oil Settlement",
          description: "Central bank digital currency pilot sees surge in cross-border oil trade settlements, bypassing SWIFT.",
          url: "https://news.google.com/search?q=mBridge+CBDC+oil+settlement",
          source: { id: "bloomberg", name: "Bloomberg" },
          publishedAt: new Date(now - 10 * 60 * 60 * 1000).toISOString(),
          content: "Demo content",
          relevance_score: 9,
          source_credibility: this.sourceCredibility.bloomberg,
          indicator_relevance: ["oil_02_mbridge_settlements"]
        }
      ],
      ice_detention_surge: [
        {
          title: "ICE Detention Facilities Near Capacity Amid Enforcement Surge",
          description: "Immigration detention population reaches 45,000 as enhanced interior enforcement continues.",
          url: "https://news.google.com/search?q=ICE+detention+immigration+enforcement",
          source: { id: "reuters", name: "Reuters" },
          publishedAt: new Date(now - 3 * 60 * 60 * 1000).toISOString(),
          content: "Demo content",
          relevance_score: 8,
          source_credibility: this.sourceCredibility.reuters,
          indicator_relevance: ["ice_detention_surge"]
        }
      ],
      nato_high_readiness: [
        {
          title: "NATO Activates High-Readiness Forces Amid Eastern European Tensions",
          description: "Alliance places 300,000 troops on heightened alert status, largest activation since Cold War.",
          url: "https://news.google.com/search?q=NATO+troops+readiness+Europe",
          source: { id: "bbc-news", name: "BBC News" },
          publishedAt: new Date(now - 7 * 60 * 60 * 1000).toISOString(),
          content: "Demo content",
          relevance_score: 10,
          source_credibility: this.sourceCredibility['bbc-news'],
          indicator_relevance: ["nato_high_readiness"]
        }
      ],
      global_conflict_intensity: [
        {
          title: "Global Armed Conflicts Reach Highest Level Since World War II",
          description: "ACLED data shows 56 active conflicts worldwide, with escalation across multiple regions.",
          url: "https://news.google.com/search?q=global+conflicts+armed+wars",
          source: { id: "reuters", name: "Reuters" },
          publishedAt: new Date(now - 14 * 60 * 60 * 1000).toISOString(),
          content: "Demo content",
          relevance_score: 9,
          source_credibility: this.sourceCredibility.reuters,
          indicator_relevance: ["global_conflict_intensity"]
        }
      ],
      info_02_deepfake_shocks: [
        {
          title: "AI-Generated Video Causes Brief Market Panic",
          description: "Deepfake video of Federal Reserve official briefly crashes bond futures before detection.",
          url: "https://news.google.com/search?q=deepfake+AI+misinformation+market",
          source: { id: "wsj", name: "Wall Street Journal" },
          publishedAt: new Date(now - 20 * 60 * 60 * 1000).toISOString(),
          content: "Demo content",
          relevance_score: 10,
          source_credibility: this.sourceCredibility.wsj,
          indicator_relevance: ["info_02_deepfake_shocks"]
        }
      ],
      national_guard_metros: [
        {
          title: "National Guard Deployed to Major Cities Amid Civil Unrest",
          description: "Six metropolitan areas receive National Guard support for critical infrastructure protection.",
          url: "https://news.google.com/search?q=national+guard+deployment+cities",
          source: { id: "bbc-news", name: "BBC News" },
          publishedAt: new Date(now - 16 * 60 * 60 * 1000).toISOString(),
          content: "Demo content",
          relevance_score: 9,
          source_credibility: this.sourceCredibility['bbc-news'],
          indicator_relevance: ["national_guard_metros"]
        }
      ],
      econ_02_grocery_cpi: [
        {
          title: "Food Prices Rise Faster Than Headline Inflation",
          description: "Grocery costs up 8.2% year-over-year, outpacing overall CPI as supply chain pressures persist.",
          url: "https://www.bloomberg.com",
          source: { id: "bloomberg", name: "Bloomberg" },
          publishedAt: new Date(now - 9 * 60 * 60 * 1000).toISOString(),
          content: "Demo content",
          relevance_score: 8,
          source_credibility: this.sourceCredibility.bloomberg,
          indicator_relevance: ["econ_02_grocery_cpi"]
        }
      ],
      job_01_strike_days: [
        {
          title: "Labor Strikes Hit Record Levels Across Multiple Industries",
          description: "Major strikes at automakers, healthcare systems signal rising worker discontent and supply chain risks.",
          url: "https://www.reuters.com",
          source: { id: "reuters", name: "Reuters" },
          publishedAt: new Date(now - 11 * 60 * 60 * 1000).toISOString(),
          content: "Demo content",
          relevance_score: 8,
          source_credibility: this.sourceCredibility.reuters,
          indicator_relevance: ["job_01_strike_days"]
        }
      ]
    };

    // If no specific mock data, generate generic news
    const defaultNews: NewsArticle[] = [
      {
        title: `Risk Monitoring: ${indicatorId.replace(/_/g, ' ').toUpperCase()}`,
        description: "Monitoring this indicator for changes that may affect household preparedness.",
        url: "#",
        source: { id: "wsj", name: "Wall Street Journal" },
        publishedAt: new Date(now - 24 * 60 * 60 * 1000).toISOString(),
        content: "Demo content",
        relevance_score: 5,
        source_credibility: this.sourceCredibility.wsj,
        indicator_relevance: [indicatorId]
      }
    ];

    return (mockNews[indicatorId] || defaultNews).slice(0, limit);
  }

  getSourceCredibilityInfo(): Record<string, SourceCredibility> {
    return this.sourceCredibility;
  }

  getIndicatorMapping(): Record<string, IndicatorNewsMapping> {
    return this.indicatorNewsMapping;
  }

  // Get API status and rate limit info
  getApiStatus() {
    return {
      newsApi: {
        enabled: !!this.newsApiKey,
        remaining: this.newsApiLimiter.getRemainingRequests('newsapi'),
        resetTime: this.newsApiLimiter.getResetTime('newsapi'),
      },
      alphaVantage: {
        enabled: !!this.alphaVantageKey,
        remaining: this.alphaVantageLimiter.getRemainingRequests('alphavantage'),
        resetTime: this.alphaVantageLimiter.getResetTime('alphavantage'),
      },
      cache: newsCache.getStats()
    };
  }
}

export const newsIntelligence = new NewsIntelligenceService();