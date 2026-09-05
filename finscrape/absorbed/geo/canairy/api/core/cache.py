"""
Redis caching implementation with async support
"""

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
import json
import pickle
from typing import Optional, Any, Union
from datetime import timedelta
import hashlib
import logging
from functools import wraps
import asyncio

from api.core.config import settings

logger = logging.getLogger(__name__)

class CacheManager:
    """
    Async Redis cache manager with multiple serialization strategies
    """
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.default_ttl = settings.CACHE_TTL
        self.key_prefix = settings.CACHE_KEY_PREFIX
        
    async def initialize(self):
        """Initialize Redis connection"""
        if not REDIS_AVAILABLE:
            logger.warning("Redis not available, caching disabled")
            self.redis_client = None
            return
            
        try:
            self.redis_client = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=False
            )
            await self.redis_client.ping()
            logger.info("Redis cache initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Redis: {e}")
            self.redis_client = None
            
    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
            
    def _make_key(self, key: str) -> str:
        """Create namespaced cache key"""
        return f"{self.key_prefix}{key}"
    
    def _serialize(self, value: Any) -> bytes:
        """Serialize value for storage"""
        try:
            # Try JSON first (more portable)
            return json.dumps(value).encode('utf-8')
        except (TypeError, ValueError):
            # Fall back to pickle for complex objects
            return pickle.dumps(value)
    
    def _deserialize(self, value: bytes) -> Any:
        """Deserialize value from storage"""
        if value is None:
            return None
        try:
            # Try JSON first
            return json.loads(value.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError):
            # Fall back to pickle
            return pickle.loads(value)
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.redis_client:
            return None
            
        try:
            full_key = self._make_key(key)
            value = await self.redis_client.get(full_key)
            return self._deserialize(value)
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None
    ) -> bool:
        """Set value in cache with optional TTL"""
        if not self.redis_client:
            return False
            
        try:
            full_key = self._make_key(key)
            serialized = self._serialize(value)
            ttl = ttl or self.default_ttl
            
            await self.redis_client.set(
                full_key, 
                serialized,
                ex=ttl
            )
            return True
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if not self.redis_client:
            return False
            
        try:
            full_key = self._make_key(key)
            result = await self.redis_client.delete(full_key)
            return result > 0
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        if not self.redis_client:
            return False
            
        try:
            full_key = self._make_key(key)
            return await self.redis_client.exists(full_key) > 0
        except Exception as e:
            logger.error(f"Cache exists error for key {key}: {e}")
            return False
    
    async def get_many(self, keys: list[str]) -> dict[str, Any]:
        """Get multiple values from cache"""
        if not self.redis_client:
            return {}
            
        try:
            full_keys = [self._make_key(k) for k in keys]
            values = await self.redis_client.mget(full_keys)
            return {
                key: self._deserialize(value) 
                for key, value in zip(keys, values) 
                if value is not None
            }
        except Exception as e:
            logger.error(f"Cache get_many error: {e}")
            return {}
    
    async def set_many(
        self, 
        mapping: dict[str, Any], 
        ttl: Optional[int] = None
    ) -> bool:
        """Set multiple values in cache"""
        if not self.redis_client:
            return False
            
        try:
            ttl = ttl or self.default_ttl
            pipe = self.redis_client.pipeline()
            
            for key, value in mapping.items():
                full_key = self._make_key(key)
                serialized = self._serialize(value)
                pipe.set(full_key, serialized, ex=ttl)
                
            await pipe.execute()
            return True
        except Exception as e:
            logger.error(f"Cache set_many error: {e}")
            return False
    
    async def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern"""
        if not self.redis_client:
            return 0
            
        try:
            full_pattern = self._make_key(pattern)
            keys = []
            async for key in self.redis_client.scan_iter(full_pattern):
                keys.append(key)
                
            if keys:
                return await self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Cache clear_pattern error for {pattern}: {e}")
            return 0
    
    async def increment(
        self, 
        key: str, 
        amount: int = 1,
        ttl: Optional[int] = None
    ) -> Optional[int]:
        """Increment counter in cache"""
        if not self.redis_client:
            return None
            
        try:
            full_key = self._make_key(key)
            value = await self.redis_client.incr(full_key, amount)
            
            if ttl:
                await self.redis_client.expire(full_key, ttl)
                
            return value
        except Exception as e:
            logger.error(f"Cache increment error for key {key}: {e}")
            return None

# Global cache manager instance
cache_manager = CacheManager()

def cache_key_builder(*args, **kwargs) -> str:
    """Build cache key from function arguments"""
    key_parts = [str(arg) for arg in args]
    key_parts.extend([f"{k}:{v}" for k, v in sorted(kwargs.items())])
    key_str = ":".join(key_parts)
    return hashlib.md5(key_str.encode()).hexdigest()

def cached(
    ttl: Optional[int] = None,
    key_prefix: Optional[str] = None,
    key_builder: Optional[callable] = None
):
    """
    Decorator for caching async function results
    
    Args:
        ttl: Time to live in seconds
        key_prefix: Custom key prefix
        key_builder: Custom key builder function
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Build cache key
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                cache_key = cache_key_builder(*args, **kwargs)
                
            if key_prefix:
                cache_key = f"{key_prefix}:{cache_key}"
            else:
                cache_key = f"{func.__module__}.{func.__name__}:{cache_key}"
            
            # Try to get from cache
            cached_value = await cache_manager.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_value
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            await cache_manager.set(cache_key, result, ttl)
            logger.debug(f"Cache miss for {cache_key}, cached with TTL {ttl}")
            
            return result
        return wrapper
    return decorator

def invalidate_cache(pattern: str):
    """
    Decorator to invalidate cache keys matching pattern after function execution
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)
            await cache_manager.clear_pattern(pattern)
            logger.debug(f"Invalidated cache for pattern: {pattern}")
            return result
        return wrapper
    return decorator

class CacheService:
    """
    High-level caching service for specific data types
    """
    
    @staticmethod
    async def get_indicator(indicator_id: str) -> Optional[dict]:
        """Get cached indicator data"""
        return await cache_manager.get(f"indicator:{indicator_id}")
    
    @staticmethod
    async def set_indicator(indicator_id: str, data: dict, ttl: int = 300) -> bool:
        """Cache indicator data"""
        return await cache_manager.set(f"indicator:{indicator_id}", data, ttl)
    
    @staticmethod
    async def get_hopi_score() -> Optional[dict]:
        """Get cached HOPI score"""
        return await cache_manager.get("hopi:score")
    
    @staticmethod
    async def set_hopi_score(score: dict, ttl: int = 60) -> bool:
        """Cache HOPI score"""
        return await cache_manager.set("hopi:score", score, ttl)
    
    @staticmethod
    async def get_news_intelligence() -> Optional[dict]:
        """Get cached news intelligence"""
        return await cache_manager.get("news:intelligence")
    
    @staticmethod
    async def set_news_intelligence(data: dict, ttl: int = 600) -> bool:
        """Cache news intelligence"""
        return await cache_manager.set("news:intelligence", data, ttl)
    
    @staticmethod
    async def invalidate_indicators():
        """Invalidate all indicator caches"""
        return await cache_manager.clear_pattern("indicator:*")
    
    @staticmethod
    async def invalidate_all():
        """Invalidate all caches"""
        patterns = ["indicator:*", "hopi:*", "news:*", "analytics:*"]
        total = 0
        for pattern in patterns:
            total += await cache_manager.clear_pattern(pattern)
        return total