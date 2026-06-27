// Variant presets — which panels show for each dashboard mode.

export type Variant = "world" | "finance" | "crypto";

export const VARIANTS: Record<Variant, { label: string; panels: string[] }> = {
  world: {
    label: "World",
    panels: ["feed", "globe", "correlations", "worldnews", "livetv", "calendar", "accuracy"],
  },
  finance: {
    label: "Finance",
    panels: ["feed", "globe", "markets", "correlations", "accuracy", "calendar"],
  },
  crypto: {
    label: "Crypto",
    panels: ["feed", "globe", "crypto", "correlations"],
  },
};

const LS_KEY = "worldfin.variant";

export function loadVariant(): Variant {
  const v = localStorage.getItem(LS_KEY) as Variant | null;
  return v && v in VARIANTS ? v : "world";
}

export function saveVariant(v: Variant): void {
  try {
    localStorage.setItem(LS_KEY, v);
  } catch {
    /* ignore */
  }
}
