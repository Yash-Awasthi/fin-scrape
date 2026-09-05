import { MissileLaunch, GeoPosition } from '../types';

interface LaunchSite {
  name: string;
  position: GeoPosition;
  country: string;
  types: MissileLaunch['type'][];
}

const LAUNCH_SITES: LaunchSite[] = [
  { name: 'Cape Canaveral', position: { lat: 28.396, lng: -80.605 }, country: 'United States', types: ['space_launch', 'rocket'] },
  { name: 'Kennedy Space Center', position: { lat: 28.573, lng: -80.649 }, country: 'United States', types: ['space_launch'] },
  { name: 'Vandenberg SFB', position: { lat: 34.742, lng: -120.572 }, country: 'United States', types: ['space_launch', 'rocket'] },
  { name: 'Baikonur Cosmodrome', position: { lat: 45.965, lng: 63.305 }, country: 'Russia', types: ['space_launch', 'rocket'] },
  { name: 'Plesetsk', position: { lat: 62.927, lng: 40.577 }, country: 'Russia', types: ['space_launch', 'missile'] },
  { name: 'Jiuquan', position: { lat: 40.958, lng: 100.291 }, country: 'China', types: ['space_launch', 'rocket'] },
  { name: 'Xichang', position: { lat: 28.246, lng: 102.027 }, country: 'China', types: ['space_launch'] },
  { name: 'Wenchang', position: { lat: 19.614, lng: 110.951 }, country: 'China', types: ['space_launch'] },
  { name: 'Satish Dhawan', position: { lat: 13.733, lng: 80.235 }, country: 'India', types: ['space_launch', 'rocket'] },
  { name: 'Tanegashima', position: { lat: 30.4, lng: 131.0 }, country: 'Japan', types: ['space_launch'] },
  { name: 'Guiana Space Centre', position: { lat: 5.236, lng: -52.768 }, country: 'France (ESA)', types: ['space_launch'] },
  { name: 'Semnan', position: { lat: 35.235, lng: 53.921 }, country: 'Iran', types: ['space_launch', 'missile'] },
  { name: 'Sohae', position: { lat: 39.66, lng: 124.705 }, country: 'North Korea', types: ['missile', 'rocket'] },
  { name: 'Tonghae', position: { lat: 40.855, lng: 129.666 }, country: 'North Korea', types: ['missile'] },
  { name: 'Palmachim', position: { lat: 31.897, lng: 34.691 }, country: 'Israel', types: ['space_launch', 'missile'] },
];

function seededRandom(seed: number): number {
  const x = Math.sin(seed) * 10000;
  return x - Math.floor(x);
}

function calculateParabolicTrajectory(
  launch: GeoPosition,
  azimuth: number,
  rangeKm: number,
  maxAltKm: number,
  steps: number,
): GeoPosition[] {
  const trajectory: GeoPosition[] = [];
  const earthRadius = 6371;

  for (let i = 0; i <= steps; i++) {
    const t = i / steps;
    const distKm = rangeKm * t;

    const alt = maxAltKm * 4 * t * (1 - t);

    const angularDist = distKm / earthRadius;
    const azRad = (azimuth * Math.PI) / 180;
    const lat1 = (launch.lat * Math.PI) / 180;
    const lng1 = (launch.lng * Math.PI) / 180;

    const lat2 = Math.asin(
      Math.sin(lat1) * Math.cos(angularDist) +
      Math.cos(lat1) * Math.sin(angularDist) * Math.cos(azRad),
    );
    const lng2 = lng1 + Math.atan2(
      Math.sin(azRad) * Math.sin(angularDist) * Math.cos(lat1),
      Math.cos(angularDist) - Math.sin(lat1) * Math.sin(lat2),
    );

    trajectory.push({
      lat: (lat2 * 180) / Math.PI,
      lng: (lng2 * 180) / Math.PI,
      alt,
    });
  }

  return trajectory;
}

function generateLaunches(): MissileLaunch[] {
  const now = Date.now();
  const launches: MissileLaunch[] = [];
  const hourSeed = Math.floor(now / 3600000);

  for (let i = 0; i < LAUNCH_SITES.length; i++) {
    const site = LAUNCH_SITES[i];
    const seed = hourSeed * 97 + i * 13;
    const shouldLaunch = seededRandom(seed) > 0.4;
    if (!shouldLaunch) continue;

    const type = site.types[Math.floor(seededRandom(seed + 1) * site.types.length)];
    const ageMinutes = seededRandom(seed + 2) * 120;

    let rangeKm: number;
    let maxAltKm: number;
    let azimuth: number;
    let description: string;

    switch (type) {
      case 'space_launch':
        rangeKm = 500 + seededRandom(seed + 3) * 2000;
        maxAltKm = 200 + seededRandom(seed + 4) * 400;
        azimuth = 80 + seededRandom(seed + 5) * 20;
        description = `${site.name}: Orbital launch — ${['Starlink batch', 'communications satellite', 'Earth observation', 'crew mission', 'resupply mission'][Math.floor(seededRandom(seed + 6) * 5)]}`;
        break;
      case 'rocket':
        rangeKm = 200 + seededRandom(seed + 3) * 800;
        maxAltKm = 100 + seededRandom(seed + 4) * 200;
        azimuth = seededRandom(seed + 5) * 360;
        description = `${site.name}: Sounding rocket / test launch`;
        break;
      case 'missile':
        rangeKm = 300 + seededRandom(seed + 3) * 3000;
        maxAltKm = 150 + seededRandom(seed + 4) * 600;
        azimuth = seededRandom(seed + 5) * 360;
        description = `${site.name}: Ballistic missile test detected`;
        break;
      default:
        rangeKm = 500;
        maxAltKm = 200;
        azimuth = 90;
        description = `${site.name}: Unknown launch event`;
    }

    const trajectory = calculateParabolicTrajectory(site.position, azimuth, rangeKm, maxAltKm, 30);
    const predictedImpact = type === 'missile' ? trajectory[trajectory.length - 1] : null;

    launches.push({
      id: `launch-${i}-${hourSeed}`,
      type,
      launchSite: { ...site.position },
      trajectory,
      predictedImpact,
      country: site.country,
      description,
      timestamp: (now - ageMinutes * 60000) / 1000,
    });
  }

  return launches;
}

export async function fetchMissileLaunches(): Promise<MissileLaunch[]> {
  try {
    return generateLaunches();
  } catch (err) {
    console.error('[MissileService] Failed to generate launch data:', err instanceof Error ? err.message : err);
    return [];
  }
}
