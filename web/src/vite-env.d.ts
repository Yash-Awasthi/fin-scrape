/// <reference types="vite/client" />

interface ImportMetaEnv {
  // Base URL of the WorldFin API. Empty = same-origin (dev proxy / nginx).
  // Set at build time for split hosting (e.g. Cloudflare Pages → Render API).
  readonly VITE_API_BASE?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
