// ============================================================
// Global configuration
// ============================================================

export const config = {
  treeDepth: 3,
  personaCount: 5,
  consensusThreshold: 3, // 3/5 must agree to include

  azure: {
    endpoint: process.env.AZURE_OPENAI_ENDPOINT || "",
    apiKey: process.env.AZURE_OPENAI_API_KEY || "",
    deployment: process.env.AZURE_OPENAI_DEPLOYMENT || "gpt-5-mini",
    apiVersion: process.env.AZURE_OPENAI_API_VERSION || "2024-12-01-preview",
  },

  newsapi: {
    key: process.env.NEWSAPI_KEY || "",
    baseUrl: "https://newsapi.org/v2",
  },

  gdelt: {
    baseUrl: "https://api.gdeltproject.org/api/v2",
  },

  datasources: {
    comtrade: {
      baseUrl: "https://comtradeapi.un.org/data/v1",
      key: process.env.COMTRADE_API_KEY || "",
    },
    opencorporates: {
      baseUrl: "https://api.opencorporates.com/v0.4",
      key: process.env.OPENCORPORATES_API_KEY || "",
    },
    openSupplyHub: {
      baseUrl: "https://opensupplyhub.org/api",
      key: process.env.OPEN_SUPPLY_HUB_API_KEY || "",
    },
    nominatim: {
      baseUrl: "https://nominatim.openstreetmap.org",
    },
    wikidata: {
      endpoint: "https://query.wikidata.org/sparql",
    },
    edgar: {
      baseUrl: "https://efts.sec.gov/LATEST",
    },
  },

  auth: {
    githubId: process.env.GITHUB_ID || "",
    githubSecret: process.env.GITHUB_SECRET || "",
    secret: process.env.NEXTAUTH_SECRET || "",
  },
} as const;
