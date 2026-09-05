"use client";

import { useEffect } from "react";
import dynamic from "next/dynamic";
import { useNewsStore } from "@/lib/newsStore";
import NewsTicker from "@/components/NewsTicker";
import Toolbar from "@/components/Toolbar";
import SearchBar from "@/components/SearchBar";
import Sidebar from "@/components/Sidebar";
import Watermark from "@/components/Watermark";
import InfoButton from "@/components/InfoButton";

const GlobeScene = dynamic(() => import("@/components/GlobeScene"), {
  ssr: false,
});

export default function Home() {
  const fetchNews = useNewsStore((s) => s.fetchNews);

  useEffect(() => {
    fetchNews();
    const interval = setInterval(fetchNews, 60_000);
    return () => clearInterval(interval);
  }, [fetchNews]);

  return (
    <main className="relative h-screen w-screen bg-black overflow-hidden">
      <Watermark />
      <GlobeScene />
      <NewsTicker />
      <SearchBar />
      <Sidebar />
      <Toolbar />
      <InfoButton />
    </main>
  );
}
