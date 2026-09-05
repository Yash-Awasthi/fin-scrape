"use client";

import { useState, useRef, useEffect } from "react";
import { getShareLinks } from "@/lib/shareUrls";

const ICONS: Record<string, string> = {
  Twitter: "𝕏",
  LinkedIn: "in",
  Reddit: "r/",
};

export default function ShareButton() {
  const [open, setOpen] = useState(false);
  const [copied, setCopied] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  const links = getShareLinks();

  useEffect(() => {
    if (!open) return;
    const handler = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [open]);

  const handleCopy = async () => {
    const url = links[0]?.utmUrl.replace(/utm_source=\w+/, "utm_source=clipboard");
    await navigator.clipboard.writeText(url);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="relative" ref={menuRef}>
      <button
        onClick={() => setOpen(!open)}
        className="w-9 h-9 rounded-full bg-black/60 backdrop-blur-md border border-white/10 text-white/60 hover:text-white hover:border-white/30 active:bg-white/10 active:scale-95 transition-colors flex items-center justify-center"
      >
        <svg viewBox="0 0 24 24" className="w-4 h-4 fill-current">
          <path d="M18 16.08c-.76 0-1.44.3-1.96.77L8.91 12.7c.05-.23.09-.46.09-.7s-.04-.47-.09-.7l7.05-4.11c.54.5 1.25.81 2.04.81 1.66 0 3-1.34 3-3s-1.34-3-3-3-3 1.34-3 3c0 .24.04.47.09.7L8.04 9.81C7.5 9.31 6.79 9 6 9c-1.66 0-3 1.34-3 3s1.34 3 3 3c.79 0 1.5-.31 2.04-.81l7.12 4.16c-.05.21-.08.43-.08.65 0 1.61 1.31 2.92 2.92 2.92s2.92-1.31 2.92-2.92-1.31-2.92-2.92-2.92z" />
        </svg>
      </button>

      {open && (
        <div className="absolute bottom-12 left-0 md:bottom-12 md:right-0 md:left-auto bg-zinc-950/95 border border-white/10 rounded-xl p-2 min-w-[180px] shadow-2xl backdrop-blur-md">
          <button
            onClick={handleCopy}
            className="w-full flex items-center gap-3 px-3 py-2 text-sm text-white/70 hover:text-white hover:bg-white/5 rounded-lg transition-colors"
          >
            <span className="w-6 text-center text-xs">{copied ? "✓" : "🔗"}</span>
            <span>{copied ? "Copied!" : "Copy link"}</span>
          </button>
          <div className="h-px bg-white/5 my-1" />
          {links.map((link) => (
            <a
              key={link.name}
              href={link.shareUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-3 px-3 py-2 text-sm text-white/70 hover:text-white hover:bg-white/5 rounded-lg transition-colors"
            >
              <span className="w-6 text-center text-xs font-bold">{ICONS[link.name]}</span>
              <span>{link.name}</span>
            </a>
          ))}
        </div>
      )}
    </div>
  );
}
