/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_NEWS_API_KEY: string
  readonly VITE_ALPHA_VANTAGE_API_KEY: string
  readonly VITE_OPENAI_API_KEY: string
  readonly VITE_API_BASE_URL: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}