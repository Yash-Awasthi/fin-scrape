// Rolling price series for the quote panels.
//
// The quotes API returns a price and a change percentage, no history, so the
// sparklines beside each symbol are built from the 15s poll itself: one point per
// refresh, oldest dropped past MAX.
//
// ponytail: session-only — a reload starts every series empty and sparklines stay
// blank until the second poll. Real history means a candles fetch per symbol
// (`api.candles`), which is one request per row; do that if the blank first
// minute ever matters more than the request budget.

const MAX = 40;
const series = new Map<string, number[]>();

/** Append a price. Repeats of the last value are dropped — a frozen market is not a trend. */
export function record(symbol: string, price: number | null | undefined): void {
  if (price == null || !Number.isFinite(price)) return;
  const points = series.get(symbol) ?? [];
  if (points[points.length - 1] === price) return;
  points.push(price);
  if (points.length > MAX) points.shift();
  series.set(symbol, points);
}

export function history(symbol: string): number[] {
  return series.get(symbol) ?? [];
}

/** Test seam — the map is module state that outlives a single panel. */
export function reset(): void {
  series.clear();
}
