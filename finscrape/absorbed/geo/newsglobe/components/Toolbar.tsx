"use client";

import { useNewsStore } from "@/lib/newsStore";
import { Category, CATEGORY_COLORS, CATEGORY_LABELS } from "@/lib/types";

const categories: (Category | "all")[] = [
  "all",
  "technology",
  "business",
  "science",
  "sports",
  "entertainment",
  "health",
];

export default function Toolbar() {
  const { activeCategory, setActiveCategory, fetchNews, selectedCountry } = useNewsStore();

  if (selectedCountry) return null;

  const handleClick = (cat: Category | "all") => {
    setActiveCategory(cat);
    fetchNews();
  };

  return (
    <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 flex items-center gap-2 bg-black/60 backdrop-blur-md border border-white/10 rounded-full px-4 py-2 max-w-[calc(100vw-2rem)] overflow-x-auto scrollbar-none">
      {categories.map((cat) => {
        const isActive = activeCategory === cat;
        const color = cat === "all" ? "#ffffff" : CATEGORY_COLORS[cat];
        return (
          <button
            key={cat}
            onClick={() => handleClick(cat)}
            className={`text-xs px-3 py-1.5 rounded-full transition-all font-medium whitespace-nowrap shrink-0 active:scale-95 ${
              isActive
                ? "text-white"
                : "text-gray-500 hover:text-gray-300 active:text-gray-200"
            }`}
            style={
              isActive
                ? { backgroundColor: color + "30", color }
                : undefined
            }
          >
            {cat === "all" ? "All" : CATEGORY_LABELS[cat]}
          </button>
        );
      })}
    </div>
  );
}
