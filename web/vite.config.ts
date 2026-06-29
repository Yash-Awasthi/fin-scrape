import { defineConfig } from "vite";

// Dev server proxies /api + /ws to the FastAPI backend so the SPA talks same-origin.
export default defineConfig({
  // The globe.gl (+three.js) vendor chunk is ~1.8MB and is lazy-loaded on its own
  // (src/main.ts dynamic import), so it never blocks first paint — raise the warning
  // limit above it to keep the build output clean.
  build: { chunkSizeWarningLimit: 2000 },
  server: {
    port: 8080,
    proxy: {
      "/api": { target: "http://localhost:8000", changeOrigin: true, ws: true },
    },
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./vitest.setup.ts"],
    // Playwright owns e2e/ — keep vitest from picking up its specs.
    exclude: ["node_modules/**", "e2e/**"],
  },
});
