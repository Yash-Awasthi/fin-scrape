import { Router, Request, Response } from 'express';
import { fetchAircraft, fetchAircraftByBounds } from '../services/aircraft';
import { fetchSatellites } from '../services/satellites';
import { fetchShips } from '../services/ships';
import { fetchEarthquakes, fetchSignificantEarthquakes } from '../services/earthquakes';
import { fetchConflicts } from '../services/conflicts';
import { fetchMissileLaunches } from '../services/missiles';
import { fetchNewsEvents } from '../services/news';
import { fetchTrafficData } from '../services/traffic';
import { fetchWeatherData } from '../services/weather';
import { generateSituationReport } from '../services/intelligence';
import { LayerData } from '../types/index';

export const router = Router();

function asyncHandler(
  fn: (req: Request, res: Response) => Promise<void>,
) {
  return (req: Request, res: Response) => {
    fn(req, res).catch((err) => {
      console.error(`[API] ${req.path} error:`, err);
      res.status(500).json({ error: 'Internal server error' });
    });
  };
}

router.get(
  '/layers/aircraft',
  asyncHandler(async (req, res) => {
    const { bounds } = req.query;
    if (typeof bounds === 'string') {
      const parts = bounds.split(',').map(Number);
      if (parts.length === 4 && parts.every((n) => !isNaN(n))) {
        const [lamin, lomin, lamax, lomax] = parts;
        const data = await fetchAircraftByBounds(lamin, lomin, lamax, lomax);
        res.json({ layer: 'aircraft', data, timestamp: Date.now() });
        return;
      }
      res.status(400).json({ error: 'bounds must be lamin,lomin,lamax,lomax' });
      return;
    }
    const data = await fetchAircraft();
    res.json({ layer: 'aircraft', data, timestamp: Date.now() });
  }),
);

router.get(
  '/layers/satellites',
  asyncHandler(async (_req, res) => {
    const data = await fetchSatellites();
    res.json({ layer: 'satellites', data, timestamp: Date.now() });
  }),
);

router.get(
  '/layers/ships',
  asyncHandler(async (_req, res) => {
    const data = await fetchShips();
    res.json({ layer: 'ships', data, timestamp: Date.now() });
  }),
);

router.get(
  '/layers/earthquakes',
  asyncHandler(async (_req, res) => {
    const data = await fetchEarthquakes();
    res.json({ layer: 'earthquakes', data, timestamp: Date.now() });
  }),
);

router.get(
  '/layers/conflicts',
  asyncHandler(async (_req, res) => {
    const data = await fetchConflicts();
    res.json({ layer: 'conflicts', data, timestamp: Date.now() });
  }),
);

router.get(
  '/layers/missiles',
  asyncHandler(async (_req, res) => {
    const data = await fetchMissileLaunches();
    res.json({ layer: 'missiles', data, timestamp: Date.now() });
  }),
);

router.get(
  '/layers/news',
  asyncHandler(async (_req, res) => {
    const data = await fetchNewsEvents();
    res.json({ layer: 'news', data, timestamp: Date.now() });
  }),
);

router.get(
  '/layers/traffic',
  asyncHandler(async (_req, res) => {
    const data = await fetchTrafficData();
    res.json({ layer: 'traffic', data, timestamp: Date.now() });
  }),
);

router.get(
  '/layers/weather',
  asyncHandler(async (_req, res) => {
    const data = await fetchWeatherData();
    res.json({ layer: 'weather', data, timestamp: Date.now() });
  }),
);

router.get(
  '/intelligence/report',
  asyncHandler(async (req, res) => {
    const region = (req.query.region as string) || 'global';

    const [conflicts, earthquakes, missiles, news] = await Promise.allSettled([
      fetchConflicts(),
      fetchEarthquakes(),
      fetchMissileLaunches(),
      fetchNewsEvents(),
    ]);

    const data: Partial<LayerData> = {
      conflicts: conflicts.status === 'fulfilled' ? conflicts.value : [],
      earthquakes: earthquakes.status === 'fulfilled' ? earthquakes.value : [],
      missiles: missiles.status === 'fulfilled' ? missiles.value : [],
      news: news.status === 'fulfilled' ? news.value : [],
    };

    const report = generateSituationReport(region, data);
    res.json(report);
  }),
);

router.get(
  '/search',
  asyncHandler(async (req, res) => {
    const q = ((req.query.q as string) || '').toLowerCase().trim();
    if (!q) {
      res.status(400).json({ error: 'Query parameter "q" is required' });
      return;
    }

    const results: Array<{ type: string; item: unknown }> = [];

    const [aircraft, conflicts, news, earthquakes] = await Promise.allSettled([
      fetchAircraft(),
      fetchConflicts(),
      fetchNewsEvents(),
      fetchEarthquakes(),
    ]);

    if (aircraft.status === 'fulfilled') {
      for (const a of aircraft.value) {
        if (
          a.callsign.toLowerCase().includes(q) ||
          a.originCountry.toLowerCase().includes(q)
        ) {
          results.push({ type: 'aircraft', item: a });
        }
      }
    }

    if (conflicts.status === 'fulfilled') {
      for (const c of conflicts.value) {
        if (
          c.description.toLowerCase().includes(q) ||
          c.country.toLowerCase().includes(q) ||
          c.region.toLowerCase().includes(q)
        ) {
          results.push({ type: 'conflict', item: c });
        }
      }
    }

    if (news.status === 'fulfilled') {
      for (const n of news.value) {
        if (
          n.title.toLowerCase().includes(q) ||
          n.description.toLowerCase().includes(q)
        ) {
          results.push({ type: 'news', item: n });
        }
      }
    }

    if (earthquakes.status === 'fulfilled') {
      for (const e of earthquakes.value) {
        if (e.place.toLowerCase().includes(q)) {
          results.push({ type: 'earthquake', item: e });
        }
      }
    }

    res.json({ query: q, count: results.length, results: results.slice(0, 50) });
  }),
);

router.get('/health', (_req, res) => {
  res.json({
    status: 'ok',
    uptime: process.uptime(),
    timestamp: Date.now(),
    memory: process.memoryUsage(),
  });
});
