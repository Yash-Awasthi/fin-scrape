"""
Cache Manager
Advanced caching system with Redis integration and intelligent cache strategies
"""

import json
import pickle
import hashlib
import time
from typing import Any, Dict, List, Optional, Union, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
import asyncio
import redis
from functools import wraps
from concurrent.futures import ThreadPoolExecutor


class CacheLevel(Enum):
    """Cache levels"""
    L1_MEMORY = "l1_memory"      # In-memory cache (fastest)
    L2_REDIS = "l2_redis"        # Redis cache (distributed)
    L3_DATABASE = "l3_database"  # Database cache (persistent)


class CacheStrategy(Enum):
    """Caching strategies"""
    LRU = "lru"              # Least Recently Used
    LFU = "lfu"              # Least Frequently Used
    TTL = "ttl"              # Time To Live
    WRITE_THROUGH = "write_through"  # Write through to persistent storage
    WRITE_BACK = "write_back"      # Write back to persistent storage
    WRITE_AROUND = "write_around"  # Write around cache


@dataclass
class CacheEntry:
    """Cache entry metadata"""
    key: str
    value: Any
    created_at: datetime
    ttl: Optional[timedelta] = None
    access_count: int = 0
    last_accessed: datetime = field(default_factory=datetime.now)
    size_bytes: int = 0
    compression_enabled: bool = False
    serializer_type: str = "pickle"  # pickle, json, msgpack

    def is_expired(self) -> bool:
        """Check if cache entry has expired"""
        if self.ttl is None:
            return False
        return datetime.now() > self.created_at + self.ttl

    def increment_access(self):
        """Increment access count and update last accessed time"""
        self.access_count += 1
        self.last_accessed = datetime.now()


@dataclass
class CacheStats:
    """Cache performance statistics"""
    total_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    total_operations: int = 0
    failed_operations: int = 0
    average_response_time: float = 0.0
    cache_size_bytes: int = 0
    eviction_count: int = 0
    hit_rate: float = 0.0
    miss_rate: float = 0.0

    def update_hit_rate(self):
        """Update hit and miss rates"""
        if self.total_requests > 0:
            self.hit_rate = self.cache_hits / self.total_requests
            self.miss_rate = self.cache_misses / self.total_requests


class CacheManager:
    """Advanced cache manager with multi-level caching"""

    def __init__(self, redis_url: str = "redis://localhost:6379",
                 max_memory_size: int = 100 * 1024 * 1024,  # 100MB
                 default_ttl: timedelta = timedelta(hours=1),
                 enable_compression: bool = True,
                 max_workers: int = 10):
        self.logger = logging.getLogger(__name__)
        self.redis_url = redis_url
        self.max_memory_size = max_memory_size
        self.default_ttl = default_ttl
        self.enable_compression = enable_compression
        self.max_workers = max_workers

        # Initialize cache stores
        self.l1_cache: Dict[str, CacheEntry] = {}
        self.redis_client: Optional[redis.Redis] = None
        self.thread_pool = ThreadPoolExecutor(max_workers=max_workers)

        # Initialize statistics
        self.stats = CacheStats()
        self.lock = asyncio.Lock()

        # Cache strategies
        self.memory_strategy = CacheStrategy.LRU
        self.redis_strategy = CacheStrategy.TTL

    async def initialize(self):
        """Initialize cache manager and Redis connection"""
        try:
            # Initialize Redis connection
            self.redis_client = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=False,
                max_connections=20
            )

            # Test Redis connection
            await self.redis_client.ping()
            self.logger.info("Cache manager initialized successfully")

        except Exception as e:
            self.logger.error(f"Failed to initialize cache manager: {str(e)}")
            raise

    async def get(self, key: str, level: CacheLevel = CacheLevel.L1_MEMORY) -> Optional[Any]:
        """Get value from cache"""
        start_time = time.time()
        self.stats.total_requests += 1

        try:
            # Try L1 cache first
            if level == CacheLevel.L1_MEMORY and key in self.l1_cache:
                cache_entry = self.l1_cache[key]
                if not cache_entry.is_expired():
                    cache_entry.increment_access()
                    self.stats.cache_hits += 1
                    self.stats.update_hit_rate()
                    self.stats.average_response_time = (
                        (self.stats.average_response_time * (self.stats.total_requests - 1) +
                         (time.time() - start_time)) / self.stats.total_requests
                    )
                    return cache_entry.value
                else:
                    # Remove expired entry
                    del self.l1_cache[key]
                    self.stats.eviction_count += 1

            # Try L2 cache (Redis)
            if level in [CacheLevel.L2_REDIS, CacheLevel.L1_MEMORY] and self.redis_client:
                try:
                    cached_data = await self.redis_client.get(key)
                    if cached_data:
                        cache_entry = self._deserialize_cache_entry(cached_data)
                        if not cache_entry.is_expired():
                            # Promote to L1 cache
                            if level == CacheLevel.L1_MEMORY:
                                self._add_to_l1_cache(key, cache_entry)

                            self.stats.cache_hits += 1
                            self.stats.update_hit_rate()
                            return cache_entry.value
                except Exception as e:
                    self.logger.warning(f"Error accessing Redis cache: {str(e)}")

            # Cache miss
            self.stats.cache_misses += 1
            self.stats.update_hit_rate()
            return None

        except Exception as e:
            self.logger.error(f"Error getting from cache: {str(e)}")
            self.stats.failed_operations += 1
            return None

    async def set(self, key: str, value: Any, ttl: Optional[timedelta] = None,
                  level: CacheLevel = CacheLevel.L1_MEMORY,
                  serializer: str = "pickle") -> bool:
        """Set value in cache"""
        self.stats.total_operations += 1

        try:
            if ttl is None:
                ttl = self.default_ttl

            # Create cache entry
            cache_entry = CacheEntry(
                key=key,
                value=value,
                created_at=datetime.now(),
                ttl=ttl,
                compression_enabled=self.enable_compression,
                serializer_type=serializer
            )

            # Add to L1 cache
            if level == CacheLevel.L1_MEMORY:
                self._add_to_l1_cache(key, cache_entry)

            # Add to L2 cache (Redis)
            if level in [CacheLevel.L2_REDIS, CacheLevel.L1_MEMORY] and self.redis_client:
                try:
                    serialized_data = self._serialize_cache_entry(cache_entry)
                    await self.redis_client.setex(
                        key,
                        int(ttl.total_seconds()),
                        serialized_data
                    )
                except Exception as e:
                    self.logger.warning(f"Error setting Redis cache: {str(e)}")

            return True

        except Exception as e:
            self.logger.error(f"Error setting cache: {str(e)}")
            self.stats.failed_operations += 1
            return False

    async def delete(self, key: str, level: CacheLevel = CacheLevel.L1_MEMORY) -> bool:
        """Delete value from cache"""
        self.stats.total_operations += 1

        try:
            # Delete from L1 cache
            if level == CacheLevel.L1_MEMORY and key in self.l1_cache:
                del self.l1_cache[key]

            # Delete from L2 cache (Redis)
            if level in [CacheLevel.L2_REDIS, CacheLevel.L1_MEMORY] and self.redis_client:
                try:
                    await self.redis_client.delete(key)
                except Exception as e:
                    self.logger.warning(f"Error deleting from Redis cache: {str(e)}")

            return True

        except Exception as e:
            self.logger.error(f"Error deleting from cache: {str(e)}")
            self.stats.failed_operations += 1
            return False

    async def exists(self, key: str, level: CacheLevel = CacheLevel.L1_MEMORY) -> bool:
        """Check if key exists in cache"""
        try:
            # Check L1 cache
            if level == CacheLevel.L1_MEMORY and key in self.l1_cache:
                return not self.l1_cache[key].is_expired()

            # Check L2 cache (Redis)
            if level in [CacheLevel.L2_REDIS, CacheLevel.L1_MEMORY] and self.redis_client:
                try:
                    return await self.redis_client.exists(key) > 0
                except Exception as e:
                    self.logger.warning(f"Error checking Redis cache existence: {str(e)}")

            return False

        except Exception as e:
            self.logger.error(f"Error checking cache existence: {str(e)}")
            return False

    async def clear(self, level: CacheLevel = CacheLevel.L1_MEMORY) -> bool:
        """Clear cache level"""
        try:
            if level == CacheLevel.L1_MEMORY:
                self.l1_cache.clear()
            elif level == CacheLevel.L2_REDIS and self.redis_client:
                await self.redis_client.flushdb()
            elif level == CacheLevel.L3_DATABASE:
                # Clear database cache (implementation depends on database)
                pass

            return True

        except Exception as e:
            self.logger.error(f"Error clearing cache: {str(e)}")
            return False

    def _add_to_l1_cache(self, key: str, cache_entry: CacheEntry):
        """Add entry to L1 cache with eviction policy"""
        # Check memory constraints
        self._enforce_memory_limits()

        # Add to cache
        self.l1_cache[key] = cache_entry

        # Update cache size
        self._update_cache_size()

    def _enforce_memory_limits(self):
        """Enforce memory limits using eviction policy"""
        current_size = sum(entry.size_bytes for entry in self.l1_cache.values())

        while current_size > self.max_memory_size and self.l1_cache:
            # Evict based on strategy
            if self.memory_strategy == CacheStrategy.LRU:
                # Remove least recently used
                oldest_key = min(self.l1_cache.keys(),
                               key=lambda k: self.l1_cache[k].last_accessed)
                del self.l1_cache[oldest_key]
            elif self.memory_strategy == CacheStrategy.LFU:
                # Remove least frequently used
                least_used_key = min(self.l1_cache.keys(),
                                   key=lambda k: self.l1_cache[k].access_count)
                del self.l1_cache[least_used_key]

            self.stats.eviction_count += 1
            current_size = sum(entry.size_bytes for entry in self.l1_cache.values())

    def _update_cache_size(self):
        """Update cache size statistics"""
        self.stats.cache_size_bytes = sum(
            entry.size_bytes for entry in self.l1_cache.values()
        )

    def _serialize_cache_entry(self, cache_entry: CacheEntry) -> bytes:
        """Serialize cache entry"""
        try:
            # Create serializable dictionary
            data = {
                'key': cache_entry.key,
                'value': cache_entry.value,
                'created_at': cache_entry.created_at.isoformat(),
                'ttl': cache_entry.ttl.total_seconds() if cache_entry.ttl else None,
                'access_count': cache_entry.access_count,
                'last_accessed': cache_entry.last_accessed.isoformat(),
                'size_bytes': cache_entry.size_bytes,
                'compression_enabled': cache_entry.compression_enabled,
                'serializer_type': cache_entry.serializer_type
            }

            # Serialize based on type
            if cache_entry.serializer_type == "json":
                serialized = json.dumps(data).encode('utf-8')
            elif cache_entry.serializer_type == "pickle":
                serialized = pickle.dumps(data)
            else:
                serialized = pickle.dumps(data)

            # Update size
            cache_entry.size_bytes = len(serialized)

            return serialized

        except Exception as e:
            self.logger.error(f"Error serializing cache entry: {str(e)}")
            raise

    def _deserialize_cache_entry(self, serialized_data: bytes) -> CacheEntry:
        """Deserialize cache entry"""
        try:
            # Try to determine serializer type
            try:
                data = json.loads(serialized_data.decode('utf-8'))
                serializer_type = "json"
            except:
                data = pickle.loads(serialized_data)
                serializer_type = "pickle"

            return CacheEntry(
                key=data['key'],
                value=data['value'],
                created_at=datetime.fromisoformat(data['created_at']),
                ttl=timedelta(seconds=data['ttl']) if data['ttl'] else None,
                access_count=data['access_count'],
                last_accessed=datetime.fromisoformat(data['last_accessed']),
                size_bytes=data['size_bytes'],
                compression_enabled=data['compression_enabled'],
                serializer_type=serializer_type
            )

        except Exception as e:
            self.logger.error(f"Error deserializing cache entry: {str(e)}")
            raise

    def generate_cache_key(self, *args, **kwargs) -> str:
        """Generate consistent cache key from arguments"""
        key_data = {
            'args': args,
            'kwargs': kwargs
        }
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()

    async def get_or_set(self, key: str, value_func: Callable,
                        ttl: Optional[timedelta] = None,
                        level: CacheLevel = CacheLevel.L1_MEMORY) -> Any:
        """Get value from cache or set using provided function"""
        # Try to get from cache
        cached_value = await self.get(key, level)
        if cached_value is not None:
            return cached_value

        # Get value from function
        try:
            if asyncio.iscoroutinefunction(value_func):
                value = await value_func()
            else:
                value = await asyncio.get_event_loop().run_in_executor(
                    self.thread_pool, value_func
                )

            # Set in cache
            await self.set(key, value, ttl, level)
            return value

        except Exception as e:
            self.logger.error(f"Error in get_or_set: {str(e)}")
            raise

    def cache_decorator(self, ttl: Optional[timedelta] = None,
                       level: CacheLevel = CacheLevel.L1_MEMORY,
                       key_func: Optional[Callable] = None):
        """Cache decorator for functions"""
        def decorator(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                # Generate cache key
                if key_func:
                    key = key_func(*args, **kwargs)
                else:
                    key = self.generate_cache_key(func.__name__, *args, **kwargs)

                # Get or set from cache
                return await self.get_or_set(
                    key,
                    lambda: func(*args, **kwargs),
                    ttl,
                    level
                )

            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                # Generate cache key
                if key_func:
                    key = key_func(*args, **kwargs)
                else:
                    key = self.generate_cache_key(func.__name__, *args, **kwargs)

                # Get or set from cache (synchronous version)
                cached_value = asyncio.run(self.get(key, level))
                if cached_value is not None:
                    return cached_value

                # Execute function and cache result
                value = func(*args, **kwargs)
                asyncio.run(self.set(key, value, ttl, level))
                return value

            return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

        return decorator

    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        stats_dict = {
            'total_requests': self.stats.total_requests,
            'cache_hits': self.stats.cache_hits,
            'cache_misses': self.stats.cache_misses,
            'hit_rate': self.stats.hit_rate,
            'miss_rate': self.stats.miss_rate,
            'cache_size_bytes': self.stats.cache_size_bytes,
            'eviction_count': self.stats.eviction_count,
            'average_response_time': self.stats.average_response_time,
            'l1_cache_size': len(self.l1_cache),
            'memory_usage_ratio': self.stats.cache_size_bytes / self.max_memory_size if self.max_memory_size > 0 else 0,
        }

        # Add Redis stats if available
        if self.redis_client:
            try:
                redis_info = await self.redis_client.info()
                stats_dict['redis_memory_used'] = redis_info.get('used_memory', 0)
                stats_dict['redis_keyspace_hits'] = redis_info.get('keyspace_hits', 0)
                stats_dict['redis_keyspace_misses'] = redis_info.get('keyspace_misses', 0)
            except Exception as e:
                self.logger.warning(f"Error getting Redis stats: {str(e)}")

        return stats_dict

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on cache system"""
        health_status = {
            'l1_cache': {
                'status': 'healthy',
                'size': len(self.l1_cache),
                'memory_usage': sum(entry.size_bytes for entry in self.l1_cache.values())
            },
            'l2_cache': {
                'status': 'unknown',
                'connection': 'disconnected'
            }
        }

        # Check Redis connection
        if self.redis_client:
            try:
                await self.redis_client.ping()
                health_status['l2_cache']['status'] = 'healthy'
                health_status['l2_cache']['connection'] = 'connected'
            except Exception as e:
                health_status['l2_cache']['status'] = 'unhealthy'
                health_status['l2_cache']['error'] = str(e)

        # Overall health
        overall_healthy = (
            health_status['l1_cache']['status'] == 'healthy' and
            health_status['l2_cache']['status'] in ['healthy', 'unknown']
        )

        health_status['overall'] = 'healthy' if overall_healthy else 'unhealthy'

        return health_status

    async def cleanup_expired_entries(self):
        """Clean up expired cache entries"""
        try:
            # Clean L1 cache
            expired_keys = [
                key for key, entry in self.l1_cache.items()
                if entry.is_expired()
            ]
            for key in expired_keys:
                del self.l1_cache[key]
                self.stats.eviction_count += 1

            # Clean L2 cache (Redis handles TTL automatically)
            # But we can still scan for any manually set keys that might be expired
            if self.redis_client:
                try:
                    # This would be implemented with Redis SCAN in a real system
                    pass
                except Exception as e:
                    self.logger.warning(f"Error cleaning Redis cache: {str(e)}")

            self.logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")

        except Exception as e:
            self.logger.error(f"Error cleaning up expired entries: {str(e)}")

    async def warm_up_cache(self, key_value_pairs: List[Tuple[str, Any, Optional[timedelta]]]):
        """Warm up cache with predefined key-value pairs"""
        try:
            for key, value, ttl in key_value_pairs:
                await self.set(key, value, ttl)

            self.logger.info(f"Warmed up cache with {len(key_value_pairs)} entries")

        except Exception as e:
            self.logger.error(f"Error warming up cache: {str(e)}")

    async def shutdown(self):
        """Shutdown cache manager"""
        try:
            # Close Redis connection
            if self.redis_client:
                await self.redis_client.close()

            # Shutdown thread pool
            self.thread_pool.shutdown(wait=True)

            self.logger.info("Cache manager shutdown completed")

        except Exception as e:
            self.logger.error(f"Error shutting down cache manager: {str(e)}")


# Global cache instance
_cache_manager: Optional[CacheManager] = None


async def get_cache_manager() -> CacheManager:
    """Get global cache manager instance"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
        await _cache_manager.initialize()
    return _cache_manager


# Convenience decorators
def cached(ttl: Optional[timedelta] = None,
           level: CacheLevel = CacheLevel.L1_MEMORY,
           key_func: Optional[Callable] = None):
    """Convenience cache decorator"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            cache_manager = await get_cache_manager()
            return await cache_manager.get_or_set(
                cache_manager.generate_cache_key(func.__name__, *args, **kwargs),
                lambda: func(*args, **kwargs),
                ttl,
                level
            )

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            cache_manager = asyncio.run(get_cache_manager())
            key = cache_manager.generate_cache_key(func.__name__, *args, **kwargs)
            cached_value = asyncio.run(cache_manager.get(key, level))
            if cached_value is not None:
                return cached_value

            value = func(*args, **kwargs)
            asyncio.run(cache_manager.set(key, value, ttl, level))
            return value

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator