"use client";

import { useState, useCallback } from "react";
import { useNewsStore } from "@/lib/newsStore";

export default function SearchBar() {
  const { setSearchQuery, fetchNews } = useNewsStore();
  const [value, setValue] = useState("");

  const handleSubmit = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault();
      setSearchQuery(value);
      fetchNews();
    },
    [value, setSearchQuery, fetchNews]
  );

  return (
    <form
      onSubmit={handleSubmit}
      className="fixed top-12 left-4 right-4 md:right-auto z-50 flex items-center"
    >
      <div className="relative">
        <input
          type="text"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder="Search news..."
          enterKeyHint="search"
          className="bg-black/60 backdrop-blur-md border border-white/10 rounded-full px-4 py-2 text-sm text-white placeholder-gray-500 w-full md:w-64 focus:outline-none focus:border-white/30 transition-colors"
        />
        <button
          type="submit"
          className="absolute right-1 top-1/2 -translate-y-1/2 text-gray-500 hover:text-white active:text-white transition-colors text-sm min-w-[44px] min-h-[44px] flex items-center justify-center"
        >
          ↵
        </button>
      </div>
    </form>
  );
}
