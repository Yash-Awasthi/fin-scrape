const BASE_URL = "https://newsglobe.saurabhn.com";
const CAMPAIGN = "launch";

const TITLE = "NewsGlobe — Real-time trending news from 150 countries on an interactive 3D globe";

interface Platform {
  name: string;
  utm_source: string;
  utm_medium: string;
  /** Returns the platform-specific share URL */
  shareUrl: (link: string) => string;
}

const PLATFORMS: Platform[] = [
  {
    name: "Twitter",
    utm_source: "twitter",
    utm_medium: "social",
    shareUrl: (link) =>
      `https://x.com/intent/tweet?text=${encodeURIComponent(TITLE)}&url=${encodeURIComponent(link)}`,
  },
  {
    name: "LinkedIn",
    utm_source: "linkedin",
    utm_medium: "social",
    shareUrl: (link) =>
      `https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(link)}`,
  },
  {
    name: "Reddit",
    utm_source: "reddit",
    utm_medium: "social",
    shareUrl: (link) =>
      `https://www.reddit.com/submit?url=${encodeURIComponent(link)}&title=${encodeURIComponent(TITLE)}`,
  },
];

function buildUtmUrl(source: string, medium: string): string {
  const params = new URLSearchParams({
    utm_source: source,
    utm_medium: medium,
    utm_campaign: CAMPAIGN,
  });
  return `${BASE_URL}?${params.toString()}`;
}

export interface ShareLink {
  name: string;
  utmUrl: string;
  shareUrl: string;
}

export function getShareLinks(): ShareLink[] {
  return PLATFORMS.map((p) => {
    const utmUrl = buildUtmUrl(p.utm_source, p.utm_medium);
    return {
      name: p.name,
      utmUrl,
      shareUrl: p.shareUrl(utmUrl),
    };
  });
}
