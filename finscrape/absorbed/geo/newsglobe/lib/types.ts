export type Category =
  | "general"
  | "business"
  | "technology"
  | "science"
  | "sports"
  | "entertainment"
  | "health";

export interface NewsArticle {
  id: string;
  title: string;
  snippet: string;
  url: string;
  source: string;
  publishedAt: string;
  category: Category;
  lat: number;
  lng: number;
  regionLat?: number;
  regionLng?: number;
  thumbnail?: string;
}

export const CATEGORY_COLORS: Record<Category, string> = {
  general: "#ffffff",
  business: "#f97316",
  technology: "#3b82f6",
  science: "#a855f7",
  sports: "#22c55e",
  entertainment: "#ec4899",
  health: "#14b8a6",
};

export const CATEGORY_LABELS: Record<Category, string> = {
  general: "General",
  business: "Business",
  technology: "Tech",
  science: "Science",
  sports: "Sports",
  entertainment: "Entertainment",
  health: "Health",
};
