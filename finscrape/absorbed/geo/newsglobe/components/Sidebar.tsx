"use client";

import { useState } from "react";
import { useNewsStore } from "@/lib/newsStore";
import { CATEGORY_COLORS } from "@/lib/types";

function timeAgo(date: string): string {
  const seconds = Math.floor(
    (Date.now() - new Date(date).getTime()) / 1000
  );
  if (seconds < 60) return "just now";
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

function ArticleList() {
  const {
    filteredArticles,
    loading,
    setHoveredArticle,
    flyToArticle,
    selectedCountry,
    countryArticles,
    countryLoading,
    clearCountry,
  } = useNewsStore();

  const isCountryView = !!selectedCountry;
  const items = isCountryView ? countryArticles : filteredArticles;
  const isLoading = isCountryView ? countryLoading : loading;

  return (
    <>
      <div className="px-4 py-3 border-b border-white/10 flex items-center justify-between shrink-0">
        {isCountryView ? (
          <>
            <div className="flex items-center gap-2">
              <button
                onClick={clearCountry}
                className="text-gray-400 hover:text-white active:text-white text-xs transition-colors active:scale-95"
              >
                ← Back
              </button>
              <span className="text-white text-xs font-semibold uppercase tracking-wider">
                {selectedCountry.name}
              </span>
            </div>
            <span className="text-gray-500 text-[10px]">
              {countryArticles.length} stories
            </span>
          </>
        ) : (
          <>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
              <span className="text-white text-xs font-semibold uppercase tracking-wider">
                Live Feed
              </span>
            </div>
            <span className="text-gray-500 text-[10px]">
              {filteredArticles.length} stories
            </span>
          </>
        )}
      </div>

      <div className="flex-1 overflow-y-auto scrollbar-thin">
        {isLoading && items.length === 0 && (
          <div className="flex items-center justify-center h-32">
            <div className="w-5 h-5 border-2 border-white/20 border-t-white rounded-full animate-spin" />
          </div>
        )}
        {items.map((article) => {
          const color = CATEGORY_COLORS[article.category];
          return (
            <div
              key={article.id}
              className="block px-4 py-3 border-b border-white/5 hover:bg-white/5 active:bg-white/10 transition-colors cursor-pointer active:scale-[0.99]"
              onClick={() => flyToArticle(article)}
              onMouseEnter={() => setHoveredArticle(article)}
              onMouseLeave={() => setHoveredArticle(null)}
            >
              <div className="flex items-start gap-3">
                <div
                  className="w-1 h-full min-h-[40px] rounded-full shrink-0"
                  style={{ backgroundColor: color }}
                />
                <div className="flex-1 min-w-0">
                  <p className="text-white text-xs font-medium leading-tight line-clamp-2">
                    {article.title}
                  </p>
                  <div className="flex items-center gap-2 mt-1.5">
                    <span className="text-gray-500 text-[10px]">
                      {article.source}
                    </span>
                    <span className="text-gray-600 text-[10px]">·</span>
                    <span className="text-gray-500 text-[10px]">
                      {timeAgo(article.publishedAt)}
                    </span>
                    <a
                      href={article.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      onClick={(e) => e.stopPropagation()}
                      className="text-gray-600 hover:text-white text-[10px] transition-colors ml-auto"
                      title="Open article"
                    >
                      ↗
                    </a>
                  </div>
                </div>
                {article.thumbnail && (
                  <img
                    src={article.thumbnail}
                    alt=""
                    className="w-14 h-14 rounded-lg object-cover shrink-0"
                    loading="lazy"
                  />
                )}
              </div>
            </div>
          );
        })}
      </div>
    </>
  );
}

export default function Sidebar() {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <>
      {/* Desktop sidebar */}
      <div className="fixed right-4 top-12 bottom-20 w-80 z-40 flex-col bg-black/50 backdrop-blur-md border border-white/10 rounded-2xl overflow-hidden hidden md:flex">
        <ArticleList />
      </div>

      {/* Mobile toggle button */}
      <button
        onClick={() => setMobileOpen(!mobileOpen)}
        className="fixed bottom-20 right-4 z-50 w-10 h-10 rounded-full bg-black/60 backdrop-blur-md border border-white/10 text-white/60 hover:text-white hover:border-white/30 active:bg-white/10 active:scale-95 transition-colors flex items-center justify-center text-lg md:hidden"
      >
        {mobileOpen ? "×" : "☰"}
      </button>

      {/* Mobile slide-up sheet */}
      {mobileOpen && (
        <div className="fixed inset-0 z-40 md:hidden" onClick={() => setMobileOpen(false)}>
          <div className="absolute inset-0 bg-black/40" />
          <div
            className="absolute bottom-0 left-0 right-0 h-[60vh] bg-black/90 backdrop-blur-md border-t border-white/10 rounded-t-2xl flex flex-col overflow-hidden animate-slide-up"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex justify-center py-2 shrink-0">
              <div className="w-10 h-1 rounded-full bg-white/20" />
            </div>
            <ArticleList />
          </div>
        </div>
      )}
    </>
  );
}
