import { useEffect, useRef } from 'react';
import { useMap } from 'react-leaflet';
import L from 'leaflet';
import type { MapLine } from '../../lib/schemas';
import { computeArcPositions, interpolateArcPosition } from './map-helpers';

// ────────────────────────────────────────────
//  Types
// ────────────────────────────────────────────

interface Props {
  lines: MapLine[];
  currentDate: string;
  isPlaying: boolean;
}

// ────────────────────────────────────────────
//  Constants
// ────────────────────────────────────────────

const MAX_SIMULTANEOUS = 8;
const ANIMATION_DURATION_MS = 2000;
const ANIMATION_STEP_MS = 30;

// ────────────────────────────────────────────
//  CSS class for category
// ────────────────────────────────────────────

function projectileClass(cat: string): string {
  return cat === 'strike'
    ? 'arc-projectile arc-projectile-strike'
    : 'arc-projectile arc-projectile-retaliation';
}

// ────────────────────────────────────────────
//  Component (renders nothing — uses map imperatively)
// ────────────────────────────────────────────

export default function MapArcAnimator({ lines, currentDate, isPlaying }: Props) {
  const map = useMap();
  const markersRef = useRef<L.Marker[]>([]);
  const intervalsRef = useRef<ReturnType<typeof setInterval>[]>([]);

  useEffect(() => {
    // Clean up previous animations
    function cleanup() {
      for (const interval of intervalsRef.current) {
        clearInterval(interval);
      }
      intervalsRef.current = [];
      for (const marker of markersRef.current) {
        marker.remove();
      }
      markersRef.current = [];
    }

    cleanup();

    if (!isPlaying) return cleanup;

    // Find strike/retaliation lines matching current date
    const activeLines = lines
      .filter(
        l =>
          (l.cat === 'strike' || l.cat === 'retaliation') &&
          l.date === currentDate,
      )
      .slice(0, MAX_SIMULTANEOUS);

    if (activeLines.length === 0) return cleanup;

    for (const line of activeLines) {
      // Coordinates: line.from/to are [lon, lat], need [lat, lon] for Leaflet
      const from: [number, number] = [line.from[1], line.from[0]];
      const to: [number, number] = [line.to[1], line.to[0]];
      const path = computeArcPositions(from, to);

      const icon = L.divIcon({
        className: projectileClass(line.cat),
        iconSize: [6, 6],
        iconAnchor: [3, 3],
      });

      const marker = L.marker(path[0], { icon, interactive: false });
      marker.addTo(map);
      markersRef.current.push(marker);

      let startTime = Date.now();

      const interval = setInterval(() => {
        const elapsed = Date.now() - startTime;
        let t = elapsed / ANIMATION_DURATION_MS;

        if (t >= 1) {
          // Restart the animation loop
          t = 0;
          startTime = Date.now();
        }

        const pos = interpolateArcPosition(path, t);
        marker.setLatLng(pos);
      }, ANIMATION_STEP_MS);

      intervalsRef.current.push(interval);
    }

    return cleanup;
  }, [map, lines, currentDate, isPlaying]);

  // This component renders nothing — it drives Leaflet markers imperatively
  return null;
}
