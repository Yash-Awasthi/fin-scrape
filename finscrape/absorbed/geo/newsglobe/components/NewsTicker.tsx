"use client";

import { useState, useCallback } from "react";
import { useNewsStore } from "@/lib/newsStore";

export default function NewsTicker() {
  const { articles, loading } = useNewsStore();
  const [paused, setPaused] = useState(false);

  const handleTouchStart = useCallback(() => setPaused(true), []);
  const handleTouchEnd = useCallback(() => setPaused(false), []);

  if (loading || articles.length === 0) return null;

  const headlines = articles.slice(0, 20);

  return (
    <div
      className="fixed top-0 left-0 right-0 z-50 h-10 md:h-8 bg-black/80 border-b border-white/10 backdrop-blur-sm overflow-hidden"
      onTouchStart={handleTouchStart}
      onTouchEnd={handleTouchEnd}
    >
      <div className="flex items-center h-full">
        <span className="bg-red-600 text-white text-xs md:text-[10px] font-bold px-3 h-full flex items-center gap-1.5 shrink-0 uppercase tracking-wider">
          <span className="inline-block w-3 h-3 rounded-full border border-white/40 relative">
            <span className="absolute inset-0 rounded-full bg-white/20 animate-ping" />
          </span>
          Live
        </span>
        <div className="overflow-hidden whitespace-nowrap flex-1">
          <div
            className="animate-marquee inline-block"
            style={paused ? { animationPlayState: "paused" } : undefined}
          >
            {headlines.map((a, i) => (
              <span key={a.id} className="text-gray-300 text-xs mx-6">
                <span className="text-white/60 mr-2">{a.source}</span>
                {a.title}
                {i < headlines.length - 1 && (
                  <span className="text-red-500 ml-6">●</span>
                )}
              </span>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
