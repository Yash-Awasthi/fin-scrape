import type { APIRoute } from 'astro';
import { loadAllTrackers } from '../../lib/tracker-registry';
import { loadTrackerData } from '../../lib/data';

const DEFAULT_COLOR = '#3498db';
const MAX_POINTS_PER_TRACKER = 20;

interface EventPoint {
  lat: number;
  lon: number;
  color: string;
}

export const GET: APIRoute = async () => {
  const trackers = loadAllTrackers().filter((t) => t.status !== 'draft');

  const result: Record<string, EventPoint[]> = {};

  for (const tracker of trackers) {
    const data = loadTrackerData(tracker.slug);
    const color = tracker.color ?? DEFAULT_COLOR;
    const points = data.mapPoints.slice(0, MAX_POINTS_PER_TRACKER);

    result[tracker.slug] = points.map((pt) => ({
      lat: pt.lat,
      lon: pt.lon,
      color,
    }));
  }

  return new Response(JSON.stringify(result), {
    headers: { 'Content-Type': 'application/json' },
  });
};
