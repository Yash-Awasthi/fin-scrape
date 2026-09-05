import { useState, useEffect, useMemo, useRef } from 'react';
import { Cartesian3, Math as CesiumMath } from 'cesium';
import type { Viewer as CesiumViewer } from 'cesium';
import type { MapLine, MapPoint } from '../../../lib/schemas';
import type { FlatEvent } from '../../../lib/timeline-utils';

// ── Types ──

export interface CinematicShot {
  id: string;
  type: 'overview' | 'arc' | 'target' | 'point';
  lon: number;
  lat: number;
  alt: number;
  heading: number;
  pitch: number;
  simTimeMs: number;
  dwellMs: number;
  transitionMs: number;
  label: string;
  eventIds: string[];
  lineId?: string;
  pointId?: string;
}

// ── Geometry helpers ──

function haversineDistanceDeg(
  lon1: number, lat1: number, lon2: number, lat2: number,
): number {
  const dLat = (lat2 - lat1);
  const dLon = (lon2 - lon1);
  return Math.sqrt(dLat * dLat + dLon * dLon);
}

function approximateKmDistance(
  lon1: number, lat1: number, lon2: number, lat2: number,
): number {
  const dLat = (lat2 - lat1) * 111;
  const dLon = (lon2 - lon1) * 111 * Math.cos(((lat1 + lat2) / 2) * Math.PI / 180);
  return Math.sqrt(dLat * dLat + dLon * dLon);
}

function bearingDeg(
  lon1: number, lat1: number, lon2: number, lat2: number,
): number {
  const dLon = lon2 - lon1;
  const dLat = lat2 - lat1;
  const angle = Math.atan2(dLon, dLat) * (180 / Math.PI);
  return (angle + 360) % 360;
}

function transitionMsForDistance(degDist: number): number {
  if (degDist < 0.5) return 800;
  if (degDist < 2) return 1200;
  return 2000;
}

function parseTimeToMs(time: string): number {
  const parts = time.split(':');
  const hours = parseInt(parts[0], 10);
  const mins = parseInt(parts[1], 10);
  return (hours * 3600 + mins * 60) * 1000;
}

// ── Shot computation ──

function computeShotsForDate(
  date: string,
  lines: MapLine[],
  points: MapPoint[],
  events: FlatEvent[],
  playbackSpeed: number,
  cameraPresets: Record<string, { lon: number; lat: number; alt: number; pitch: number; heading: number; label?: string }>,
): CinematicShot[] {
  const shots: CinematicShot[] = [];
  const baseSimTime = new Date(date + 'T00:00:00Z').getTime();

  const baseDwell = 4000 * Math.max(1, Math.log10(playbackSpeed));

  // 1. Collect lines for date, sorted by time ascending
  const dateLines = lines
    .filter(l => l.date === date)
    .sort((a, b) => {
      const tA = a.time ? parseTimeToMs(a.time) : 0;
      const tB = b.time ? parseTimeToMs(b.time) : 0;
      return tA - tB;
    });

  // 2. Collect non-base points for date
  const datePoints = points.filter(p => p.date === date && !p.base);

  // 3. Collect events for date
  const dateEvents = events.filter(ev => ev.resolvedDate === date);

  // 4. Track line target coordinates to avoid duplicate point shots
  const lineTargetCoords: Array<{ lon: number; lat: number }> = [];

  // 5. Build shots from lines
  for (const line of dateLines) {
    const timeOffsetMs = line.time ? parseTimeToMs(line.time) : 0;
    const simTimeMs = baseSimTime + timeOffsetMs;

    const fromLon = line.from[0];
    const fromLat = line.from[1];
    const toLon = line.to[0];
    const toLat = line.to[1];

    lineTargetCoords.push({ lon: toLon, lat: toLat });

    const distKm = approximateKmDistance(fromLon, fromLat, toLon, toLat);
    const degDist = haversineDistanceDeg(fromLon, fromLat, toLon, toLat);

    // Arc overview shot — midpoint
    const midLon = (fromLon + toLon) / 2;
    const midLat = (fromLat + toLat) / 2;
    const arcAlt = Math.min(distKm * 0.4 * 1000, 800000);
    const arcHeading = bearingDeg(midLon, midLat, toLon, toLat);

    shots.push({
      id: `arc-${line.id}`,
      type: 'arc',
      lon: midLon,
      lat: midLat,
      alt: arcAlt,
      heading: arcHeading,
      pitch: -45,
      simTimeMs,
      dwellMs: baseDwell,
      transitionMs: transitionMsForDistance(degDist),
      label: line.label || `Strike: ${line.id}`,
      eventIds: [],
      lineId: line.id,
    });

    // Target shot — at line.to
    shots.push({
      id: `target-${line.id}`,
      type: 'target',
      lon: toLon,
      lat: toLat,
      alt: 80000,
      heading: 0,
      pitch: -70,
      simTimeMs: simTimeMs + 4000 * playbackSpeed,
      dwellMs: baseDwell,
      transitionMs: transitionMsForDistance(degDist * 0.5),
      label: line.label || line.id,
      eventIds: [],
      lineId: line.id,
    });
  }

  // 6. Build shots from points not near any line target
  const orphanPoints = datePoints.filter(p => {
    return !lineTargetCoords.some(
      tc => Math.abs(tc.lon - p.lon) < 0.3 && Math.abs(tc.lat - p.lat) < 0.3,
    );
  });

  if (orphanPoints.length > 0) {
    // Distribute point shots evenly across gaps between line shots
    const lineShotTimes = shots.map(s => s.simTimeMs).sort((a, b) => a - b);
    const dayEndMs = baseSimTime + 86400000;

    for (let i = 0; i < orphanPoints.length; i++) {
      const p = orphanPoints[i];
      let pointSimTime: number;

      if (lineShotTimes.length === 0) {
        // No line shots — distribute across the day
        pointSimTime = baseSimTime + ((i + 1) / (orphanPoints.length + 1)) * 86400000;
      } else {
        // Place between line shots
        const fraction = (i + 1) / (orphanPoints.length + 1);
        const earliest = lineShotTimes[0];
        const latest = lineShotTimes[lineShotTimes.length - 1];
        const range = Math.max(latest - earliest, dayEndMs - earliest);
        pointSimTime = earliest + fraction * range;
      }

      shots.push({
        id: `point-${p.id}`,
        type: 'point',
        lon: p.lon,
        lat: p.lat,
        alt: 100000,
        heading: 0,
        pitch: -90,
        simTimeMs: pointSimTime,
        dwellMs: baseDwell,
        transitionMs: 1200,
        label: p.label,
        eventIds: [],
        pointId: p.id,
      });
    }
  }

  // 7. Sort all shots by simTimeMs
  shots.sort((a, b) => a.simTimeMs - b.simTimeMs);

  // 8. Prepend overview shot
  const presetEntries = Object.values(cameraPresets);
  const firstPreset = presetEntries[0];

  let overviewLon: number;
  let overviewLat: number;
  let overviewAlt: number;
  let overviewPitch: number;
  let overviewHeading: number;

  if (firstPreset) {
    overviewLon = firstPreset.lon;
    overviewLat = firstPreset.lat;
    overviewAlt = firstPreset.alt;
    overviewPitch = firstPreset.pitch;
    overviewHeading = firstPreset.heading;
  } else if (shots.length > 0) {
    // Compute centroid of all shot positions
    const sumLon = shots.reduce((s, sh) => s + sh.lon, 0);
    const sumLat = shots.reduce((s, sh) => s + sh.lat, 0);
    overviewLon = sumLon / shots.length;
    overviewLat = sumLat / shots.length;
    overviewAlt = 2_000_000;
    overviewPitch = -90;
    overviewHeading = 0;
  } else {
    overviewLon = 0;
    overviewLat = 0;
    overviewAlt = 2_000_000;
    overviewPitch = -90;
    overviewHeading = 0;
  }

  shots.unshift({
    id: `overview-${date}`,
    type: 'overview',
    lon: overviewLon,
    lat: overviewLat,
    alt: overviewAlt,
    heading: overviewHeading,
    pitch: overviewPitch,
    simTimeMs: baseSimTime,
    dwellMs: baseDwell * 1.5,
    transitionMs: 2000,
    label: `Overview \u2014 ${date}`,
    eventIds: [],
  });

  // 9. Assign events to closest shots by time
  for (const ev of dateEvents) {
    let closestIdx = 0;
    let closestDist = Infinity;

    for (let i = 0; i < shots.length; i++) {
      const dist = Math.abs(shots[i].simTimeMs - baseSimTime);
      if (dist < closestDist) {
        closestDist = dist;
        closestIdx = i;
      }
    }

    shots[closestIdx].eventIds.push(ev.id);
  }

  return shots;
}

// ── Hook ──

export function useCinematicMode(
  viewer: CesiumViewer | null,
  enabled: boolean,
  simTimeRef: React.MutableRefObject<number>,
  currentDate: string,
  playbackSpeed: number,
  lines: MapLine[],
  points: MapPoint[],
  events: FlatEvent[],
  cameraPresets: Record<string, { lon: number; lat: number; alt: number; pitch: number; heading: number; label?: string }>,
): {
  activeEventId: string | null;
  currentShot: CinematicShot | null;
  totalShots: number;
  currentShotIndex: number;
  shotLabel: string;
} {
  const [currentShotIndex, setCurrentShotIndex] = useState(0);
  const [activeEventId, setActiveEventId] = useState<string | null>(null);
  const currentShotIndexRef = useRef(0);

  // Compute shots for the current date
  const shots = useMemo(() => {
    if (!enabled) return [];
    return computeShotsForDate(
      currentDate, lines, points, events, playbackSpeed, cameraPresets,
    );
  }, [enabled, currentDate, lines, points, events, playbackSpeed, cameraPresets]);

  // Reset shot index when shots change (date change)
  useEffect(() => {
    currentShotIndexRef.current = 0;
    setCurrentShotIndex(0);
    setActiveEventId(null);
  }, [shots]);

  // Camera orchestration RAF loop
  useEffect(() => {
    if (!enabled || !viewer || viewer.isDestroyed() || shots.length === 0) return;

    let rafId = 0;
    let lastFrame = 0;
    let headingDrift = 0;

    const tick = (timestamp: number) => {
      if (!enabled || !viewer || viewer.isDestroyed()) return;

      const dt = lastFrame ? Math.min((timestamp - lastFrame) / 1000, 0.1) : 0;
      lastFrame = timestamp;

      const simNow = simTimeRef.current;

      // Find which shot should be active
      let targetIdx = currentShotIndexRef.current;
      while (targetIdx < shots.length - 1 && simNow >= shots[targetIdx + 1].simTimeMs) {
        targetIdx++;
      }

      if (targetIdx !== currentShotIndexRef.current) {
        // New shot — fly to it
        currentShotIndexRef.current = targetIdx;
        const shot = shots[targetIdx];
        headingDrift = 0;

        viewer.camera.flyTo({
          destination: Cartesian3.fromDegrees(shot.lon, shot.lat, shot.alt),
          orientation: {
            heading: CesiumMath.toRadians(shot.heading),
            pitch: CesiumMath.toRadians(shot.pitch),
            roll: 0,
          },
          duration: shot.transitionMs / 1000,
        });

        // Update state (throttled via RAF — only once per shot change)
        setCurrentShotIndex(targetIdx);
        setActiveEventId(shot.eventIds[0] || null);
      } else if (dt > 0) {
        // Dwell — subtle heading drift for cinematic feel
        headingDrift += 0.3 * dt; // 0.3 degrees per second
        const shot = shots[targetIdx];
        if (shot) {
          try {
            // Only drift when not mid-flight
            const cam = viewer.camera as any;
            if (!cam._currentFlight) {
              const carto = viewer.camera.positionCartographic;
              viewer.camera.setView({
                destination: Cartesian3.fromRadians(carto.longitude, carto.latitude, carto.height),
                orientation: {
                  heading: CesiumMath.toRadians(shot.heading + headingDrift),
                  pitch: viewer.camera.pitch,
                  roll: 0,
                },
              });
            }
          } catch {
            // Ignore errors during camera transitions
          }
        }
      }

      rafId = requestAnimationFrame(tick);
    };

    rafId = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(rafId);
  }, [enabled, viewer, shots, simTimeRef]);

  // Return defaults when disabled
  if (!enabled) {
    return {
      activeEventId: null,
      currentShot: null,
      totalShots: 0,
      currentShotIndex: 0,
      shotLabel: '',
    };
  }

  const currentShot = shots[currentShotIndex] || null;

  return {
    activeEventId,
    currentShot,
    totalShots: shots.length,
    currentShotIndex,
    shotLabel: currentShot?.label || '',
  };
}
