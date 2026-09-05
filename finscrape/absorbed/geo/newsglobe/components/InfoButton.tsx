"use client";

import { useState } from "react";
import ShareButton from "./ShareButton";

export default function InfoButton() {
  const [open, setOpen] = useState(false);

  return (
    <>
      <div className="fixed bottom-20 left-4 md:bottom-4 md:right-4 md:left-auto z-30 md:z-50 flex items-center gap-2">
        <button
          onClick={() => setOpen(true)}
          className="w-9 h-9 rounded-full bg-black/60 backdrop-blur-md border border-white/10 text-white/60 hover:text-white hover:border-white/30 active:bg-white/10 active:scale-95 transition-colors flex items-center justify-center text-sm font-serif italic"
        >
          i
        </button>
        <a
          href="https://github.com/EXTREMOPHILARUM/newsglobe"
          target="_blank"
          rel="noopener noreferrer"
          className="w-9 h-9 rounded-full bg-black/60 backdrop-blur-md border border-white/10 text-white/60 hover:text-white hover:border-white/30 active:bg-white/10 active:scale-95 transition-colors flex items-center justify-center"
        >
          <svg viewBox="0 0 24 24" className="w-4 h-4 fill-current">
            <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z"/>
          </svg>
        </a>
        <ShareButton />
      </div>

      {open && (
        <div
          className="fixed inset-0 z-[100] flex items-center justify-center p-4"
          onClick={() => setOpen(false)}
        >
          <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" />
          <div
            className="relative bg-zinc-950/95 border border-white/10 rounded-2xl max-w-md w-full p-6 text-white shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              onClick={() => setOpen(false)}
              className="absolute top-4 right-4 text-white/40 hover:text-white transition-colors text-lg"
            >
              &times;
            </button>

            <h2 className="text-lg font-semibold mb-1">NewsGlobe</h2>
            <p className="text-white/40 text-xs mb-4">Real-time news on a 3D globe</p>

            <div className="space-y-3 text-sm text-white/70 leading-relaxed">
              <p>
                I saw{" "}
                <a
                  href="https://pizz.watch/polyglobe"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-white/90 underline underline-offset-2 decoration-white/30 hover:decoration-white/60 transition-colors"
                >
                  Polyglobe
                </a>
                {" "}doing this for Polymarket bets and thought — why not news?
                The spinning globe looked cool so I just went ahead and built it.
              </p>

              <p>
                It grabs headlines from ~150 countries, throws them on a globe,
                and you can click around to see what&apos;s going on anywhere.
                That&apos;s pretty much it.
              </p>

              <div className="pt-2 border-t border-white/5">
                <p className="text-white/40 text-xs">
                  Next.js &middot; MapLibre GL &middot; Three.js &middot; Cloudflare Workers
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
