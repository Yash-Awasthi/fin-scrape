import Redis from 'ioredis';

let redis: Redis | null = null;
const memoryCache = new Map<string, { data: string; expiry: number }>();

export function getRedis(): Redis | null {
  if (redis) return redis;
  try {
    const url = process.env.REDIS_URL || 'redis://localhost:6379';
    redis = new Redis(url, { lazyConnect: true, maxRetriesPerRequest: 1 });
    redis.on('error', () => {
      redis = null;
    });
    redis.connect().catch(() => {
      redis = null;
    });
    return redis;
  } catch {
    return null;
  }
}

export async function cacheGet(key: string): Promise<string | null> {
  const r = getRedis();
  if (r) {
    try {
      return await r.get(key);
    } catch { /* fallback to memory */ }
  }
  const entry = memoryCache.get(key);
  if (entry && entry.expiry > Date.now()) return entry.data;
  if (entry) memoryCache.delete(key);
  return null;
}

export async function cacheSet(key: string, value: string, ttlSeconds: number): Promise<void> {
  const r = getRedis();
  if (r) {
    try {
      await r.setex(key, ttlSeconds, value);
      return;
    } catch { /* fallback */ }
  }
  memoryCache.set(key, { data: value, expiry: Date.now() + ttlSeconds * 1000 });
}
