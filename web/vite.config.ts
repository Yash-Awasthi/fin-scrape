import { defineConfig } from "vite";

// Dev server proxies /api + /ws to the FastAPI backend so the SPA talks same-origin.
export default defineConfig({
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
  },
});
