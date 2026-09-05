"""
Memory Manager
Advanced memory management with optimization strategies and garbage collection
"""

import gc
import psutil
import threading
import time
import tracemalloc
import weakref
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import logging
import pickle
import sys

logger = logging.getLogger(__name__)


class MemoryStrategy(Enum):
    """Memory optimization strategies"""
    AGGRESSIVE = "aggressive"
    MODERATE = "moderate"
    CONSERVATIVE = "conservative"
    CUSTOM = "custom"


@dataclass
class MemoryProfile:
    """Memory usage profile"""
    timestamp: datetime
    rss_memory: int  # Resident Set Size
    vms_memory: int  # Virtual Memory Size
    shared_memory: int
    text_memory: int
    lib_memory: int
    data_memory: int
    dirty_memory: int
    percent_usage: float
    custom_metrics: Dict[str, Any] = field(default_factory=dict)


class MemoryManager:
    """Advanced memory management with optimization strategies"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}

        # Memory settings
        self.strategy = MemoryStrategy(self.config.get('strategy', 'moderate'))
        self.memory_limit_mb = self.config.get('memory_limit_mb', 1024)
        self.gc_threshold_ratio = self.config.get('gc_threshold_ratio', 0.8)
        self.cleanup_interval = self.config.get('cleanup_interval', 300)  # 5 minutes

        # Memory tracking
        self.memory_history: List[MemoryProfile] = []
        self.max_history_size = self.config.get('max_history_size', 1000)
        self.tracking_enabled = self.config.get('enable_tracking', True)

        # Weak references for cleanup
        self.weak_references: Dict[str, weakref.ref] = {}
        self.cleanup_callbacks: Dict[str, Callable] = {}

        # Memory pools
        self.memory_pools: Dict[str, List[Any]] = {}
        self.pool_sizes: Dict[str, int] = {}
        self.pool_limits: Dict[str, int] = {}

        # Object caching
        self.object_cache: Dict[str, Any] = {}
        self.cache_max_size = self.config.get('cache_max_size', 1000)
        self.cache_ttl = self.config.get('cache_ttl', 3600)  # 1 hour

        # Monitoring
        self.monitoring = False
        self.monitor_thread = None
        self.stop_event = threading.Event()

        # Statistics
        self.stats = {
            'gc_collections': 0,
            'memory_cleaned': 0,
            'cache_evictions': 0,
            'pool_hits': 0,
            'pool_misses': 0,
            'peak_memory': 0,
            'avg_memory': 0.0
        }

        # Initialize
        if self.tracking_enabled:
            tracemalloc.start()

        self._apply_memory_strategy()
        self._initialize_memory_pools()

        logger.info(f"Memory Manager initialized with strategy: {self.strategy.value}")

    def _apply_memory_strategy(self):
        """Apply memory management strategy"""
        strategies = {
            MemoryStrategy.AGGRESSIVE: {
                'gc_threshold_ratio': 0.6,
                'cleanup_interval': 120,
                'cache_max_size': 500,
                'memory_limit_mb': 512
            },
            MemoryStrategy.MODERATE: {
                'gc_threshold_ratio': 0.8,
                'cleanup_interval': 300,
                'cache_max_size': 1000,
                'memory_limit_mb': 1024
            },
            MemoryStrategy.CONSERVATIVE: {
                'gc_threshold_ratio': 0.9,
                'cleanup_interval': 600,
                'cache_max_size': 2000,
                'memory_limit_mb': 2048
            }
        }

        if self.strategy in strategies:
            strategy_config = strategies[self.strategy]
            self.config.update(strategy_config)

    def _initialize_memory_pools(self):
        """Initialize memory pools for common objects"""
        self.create_memory_pool('string_pool', 100)
        self.create_memory_pool('list_pool', 50)
        self.create_memory_pool('dict_pool', 50)

    def create_memory_pool(self, pool_name: str, max_size: int):
        """Create a memory pool for specific object types"""
        self.memory_pools[pool_name] = []
        self.pool_sizes[pool_name] = 0
        self.pool_limits[pool_name] = max_size
        logger.debug(f"Created memory pool: {pool_name} with limit {max_size}")

    def get_from_pool(self, pool_name: str, factory: Callable) -> Any:
        """Get object from memory pool or create new one"""
        if pool_name not in self.memory_pools:
            self.create_memory_pool(pool_name, 50)

        pool = self.memory_pools[pool_name]
        if pool:
            obj = pool.pop()
            self.pool_sizes[pool_name] -= 1
            self.stats['pool_hits'] += 1
            return obj
        else:
            self.stats['pool_misses'] += 1
            return factory()

    def return_to_pool(self, pool_name: str, obj: Any):
        """Return object to memory pool"""
        if pool_name in self.memory_pools:
            pool = self.memory_pools[pool_name]
            if len(pool) < self.pool_limits[pool_name]:
                pool.append(obj)
                self.pool_sizes[pool_name] += 1

    def start_monitoring(self):
        """Start memory monitoring"""
        if self.monitoring:
            return

        self.monitoring = True
        self.stop_event.clear()
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()

        logger.info("Memory monitoring started")

    def stop_monitoring(self):
        """Stop memory monitoring"""
        if not self.monitoring:
            return

        self.monitoring = False
        self.stop_event.set()
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)

        logger.info("Memory monitoring stopped")

    def _monitor_loop(self):
        """Memory monitoring loop"""
        while not self.stop_event.is_set():
            try:
                self.collect_memory_profile()
                self._check_memory_thresholds()
                self._perform_cleanup()

                time.sleep(self.cleanup_interval)

            except Exception as e:
                logger.error(f"Error in memory monitoring: {e}")
                time.sleep(60)

    def collect_memory_profile(self) -> MemoryProfile:
        """Collect current memory profile"""
        process = psutil.Process()
        memory_info = process.memory_info()

        profile = MemoryProfile(
            timestamp=datetime.now(),
            rss_memory=memory_info.rss,
            vms_memory=memory_info.vms,
            shared_memory=memory_info.shared if hasattr(memory_info, 'shared') else 0,
            text_memory=memory_info.text if hasattr(memory_info, 'text') else 0,
            lib_memory=memory_info.lib if hasattr(memory_info, 'lib') else 0,
            data_memory=memory_info.data if hasattr(memory_info, 'data') else 0,
            dirty_memory=memory_info.dirty if hasattr(memory_info, 'dirty') else 0,
            percent_usage=process.memory_percent()
        )

        self.memory_history.append(profile)

        # Maintain history size
        if len(self.memory_history) > self.max_history_size:
            self.memory_history = self.memory_history[-self.max_history_size:]

        # Update statistics
        self.stats['peak_memory'] = max(self.stats['peak_memory'], profile.rss_memory)
        self.stats['avg_memory'] = sum(p.rss_memory for p in self.memory_history) / len(self.memory_history)

        return profile

    def _check_memory_thresholds(self):
        """Check if memory usage exceeds thresholds"""
        if not self.memory_history:
            return

        current_profile = self.memory_history[-1]
        memory_limit_bytes = self.memory_limit_mb * 1024 * 1024

        if current_profile.rss_memory > memory_limit_bytes * self.gc_threshold_ratio:
            logger.warning(f"Memory usage high: {current_profile.rss_memory / 1024 / 1024:.1f}MB")
            self.force_garbage_collection()

        if current_profile.rss_memory > memory_limit_bytes:
            logger.critical(f"Memory limit exceeded: {current_profile.rss_memory / 1024 / 1024:.1f}MB")
            self.emergency_cleanup()

    def _perform_cleanup(self):
        """Perform regular cleanup operations"""
        # Clean expired cache entries
        self.cleanup_cache()

        # Clean weak references
        self.cleanup_weak_references()

        # Adjust memory pools
        self.adjust_memory_pools()

    def force_garbage_collection(self) -> Dict[str, Any]:
        """Force garbage collection and return statistics"""
        before = self.get_memory_usage()

        # Force collection
        collected = gc.collect()

        after = self.get_memory_usage()
        memory_saved = before['rss'] - after['rss']

        self.stats['gc_collections'] += 1
        self.stats['memory_cleaned'] += memory_saved

        logger.info(f"Garbage collection: {collected} objects collected, {memory_saved / 1024 / 1024:.1f}MB saved")

        return {
            'objects_collected': collected,
            'memory_before': before,
            'memory_after': after,
            'memory_saved': memory_saved
        }

    def emergency_cleanup(self) -> Dict[str, Any]:
        """Perform emergency memory cleanup"""
        logger.info("Emergency cleanup initiated")

        # Force multiple garbage collection cycles
        total_collected = 0
        for _ in range(3):
            collected = gc.collect()
            total_collected += collected

        # Clear all caches
        self.clear_cache()
        self.clear_memory_pools()

        # Clear old memory profiles
        self.memory_history = self.memory_history[-100:]

        # Collect final stats
        after_cleanup = self.get_memory_usage()

        return {
            'total_collected': total_collected,
            'final_memory_usage': after_cleanup,
            'caches_cleared': True,
            'pools_cleared': True
        }

    def cache_object(self, key: str, obj: Any, ttl: Optional[int] = None):
        """Cache object with TTL"""
        if ttl is None:
            ttl = self.cache_ttl

        # Check cache size limit
        if len(self.object_cache) >= self.cache_max_size:
            self._evict_from_cache()

        self.object_cache[key] = {
            'object': obj,
            'timestamp': datetime.now(),
            'ttl': ttl
        }

    def get_cached_object(self, key: str) -> Optional[Any]:
        """Get cached object if valid"""
        if key not in self.object_cache:
            return None

        cache_entry = self.object_cache[key]
        if self._is_cache_valid(cache_entry):
            return cache_entry['object']
        else:
            del self.object_cache[key]
            return None

    def _is_cache_valid(self, cache_entry: Dict[str, Any]) -> bool:
        """Check if cache entry is still valid"""
        age = (datetime.now() - cache_entry['timestamp']).total_seconds()
        return age < cache_entry['ttl']

    def _evict_from_cache(self):
        """Evict oldest entries from cache"""
        if not self.object_cache:
            return

        # Sort by timestamp and remove oldest
        sorted_items = sorted(self.object_cache.items(), key=lambda x: x[1]['timestamp'])
        items_to_remove = len(self.object_cache) - int(self.cache_max_size * 0.8)

        for key, _ in sorted_items[:items_to_remove]:
            del self.object_cache[key]
            self.stats['cache_evictions'] += 1

    def cleanup_cache(self):
        """Clean up expired cache entries"""
        current_time = datetime.now()
        expired_keys = []

        for key, entry in self.object_cache.items():
            age = (current_time - entry['timestamp']).total_seconds()
            if age > entry['ttl']:
                expired_keys.append(key)

        for key in expired_keys:
            del self.object_cache[key]
            self.stats['cache_evictions'] += len(expired_keys)

    def clear_cache(self):
        """Clear entire object cache"""
        count = len(self.object_cache)
        self.object_cache.clear()
        self.stats['cache_evictions'] += count
        logger.info(f"Cleared {count} cached objects")

    def clear_memory_pools(self):
        """Clear all memory pools"""
        for pool_name in self.memory_pools:
            count = len(self.memory_pools[pool_name])
            self.memory_pools[pool_name].clear()
            self.pool_sizes[pool_name] = 0
            logger.debug(f"Cleared memory pool {pool_name}: {count} objects")

    def adjust_memory_pools(self):
        """Adjust memory pool sizes based on usage"""
        for pool_name, pool in self.memory_pools.items():
            # If pool is too large, shrink it
            if len(pool) > self.pool_limits[pool_name] * 1.5:
                new_size = int(self.pool_limits[pool_name] * 0.8)
                self.memory_pools[pool_name] = pool[:new_size]
                logger.debug(f"Shrunk memory pool {pool_name} to {new_size}")

    def add_weak_reference(self, key: str, obj: Any, callback: Optional[Callable] = None):
        """Add weak reference with optional cleanup callback"""
        def cleanup_callback(ref):
            if key in self.weak_references:
                del self.weak_references[key]
            if callback:
                callback()

        self.weak_references[key] = weakref.ref(obj, cleanup_callback)
        if callback:
            self.cleanup_callbacks[key] = callback

    def cleanup_weak_references(self):
        """Clean up dead weak references"""
        dead_keys = []
        for key, ref in self.weak_references.items():
            if ref() is None:
                dead_keys.append(key)

        for key in dead_keys:
            del self.weak_references[key]
            if key in self.cleanup_callbacks:
                del self.cleanup_callbacks[key]

    def get_memory_usage(self) -> Dict[str, Any]:
        """Get current memory usage statistics"""
        process = psutil.Process()
        memory_info = process.memory_info()

        # Get garbage collector stats
        gc_stats = gc.get_stats()

        return {
            'rss': memory_info.rss,
            'vms': memory_info.vms,
            'percent': process.memory_percent(),
            'available': psutil.virtual_memory().available,
            'total': psutil.virtual_memory().total,
            'gc_stats': gc_stats,
            'cache_size': len(self.object_cache),
            'pool_sizes': {name: len(pool) for name, pool in self.memory_pools.items()}
        }

    def get_memory_summary(self) -> Dict[str, Any]:
        """Get comprehensive memory summary"""
        current_usage = self.get_memory_usage()

        # Calculate memory trends
        if len(self.memory_history) > 1:
            recent_memory = [p.rss_memory for p in self.memory_history[-10:]]
            memory_trend = (recent_memory[-1] - recent_memory[0]) / len(recent_memory)
        else:
            memory_trend = 0

        return {
            'current_usage': current_usage,
            'trend': memory_trend,
            'statistics': self.stats,
            'efficiency': {
                'cache_hit_rate': self.stats['pool_hits'] / (self.stats['pool_hits'] + self.stats['pool_misses']) if (self.stats['pool_hits'] + self.stats['pool_misses']) > 0 else 0,
                'memory_efficiency': 1.0 - (current_usage['rss'] / current_usage['total']) if current_usage['total'] > 0 else 0
            },
            'recommendations': self._get_memory_recommendations()
        }

    def _get_memory_recommendations(self) -> List[str]:
        """Get memory optimization recommendations"""
        recommendations = []

        current_usage = self.get_memory_usage()
        memory_percent = current_usage['percent']

        if memory_percent > 90:
            recommendations.append("High memory usage detected - consider memory optimization strategies")
        elif memory_percent > 75:
            recommendations.append("Memory usage is elevated - monitor closely")

        if len(self.object_cache) > self.cache_max_size * 0.8:
            recommendations.append("Cache is near capacity - consider increasing limit or cleaning up")

        if self.stats['cache_evictions'] > 100:
            recommendations.append("High cache eviction rate - consider increasing cache size")

        return recommendations

    def export_memory_report(self, filepath: str):
        """Export memory usage report to file"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'strategy': self.strategy.value,
            'configuration': self.config,
            'current_usage': self.get_memory_usage(),
            'statistics': self.stats,
            'memory_history': [
                {
                    'timestamp': p.timestamp.isoformat(),
                    'rss_memory': p.rss_memory,
                    'vms_memory': p.vms_memory,
                    'percent_usage': p.percent_usage
                }
                for p in self.memory_history[-100:]  # Last 100 entries
            ],
            'summary': self.get_memory_summary()
        }

        with open(filepath, 'w') as f:
            import json
            json.dump(report, f, indent=2)

        logger.info(f"Memory report exported to {filepath}")

    def optimize_memory(self) -> Dict[str, Any]:
        """Run comprehensive memory optimization"""
        results = {}

        # Garbage collection
        results['garbage_collection'] = self.force_garbage_collection()

        # Cache cleanup
        cache_before = len(self.object_cache)
        self.cleanup_cache()
        results['cache_cleanup'] = {
            'before': cache_before,
            'after': len(self.object_cache),
            'cleaned': cache_before - len(self.object_cache)
        }

        # Pool optimization
        pool_before = sum(len(pool) for pool in self.memory_pools.values())
        self.adjust_memory_pools()
        pool_after = sum(len(pool) for pool in self.memory_pools.values())
        results['pool_optimization'] = {
            'before': pool_before,
            'after': pool_after,
            'optimized': pool_before - pool_after
        }

        # Weak reference cleanup
        weak_before = len(self.weak_references)
        self.cleanup_weak_references()
        results['weak_reference_cleanup'] = {
            'before': weak_before,
            'after': len(self.weak_references),
            'cleaned': weak_before - len(self.weak_references)
        }

        return results

    def __del__(self):
        """Cleanup on destruction"""
        self.stop_monitoring()
        if self.tracking_enabled:
            tracemalloc.stop()


# Global instances
_memory_manager: Optional[MemoryManager] = None


def get_memory_manager(config: Dict[str, Any] = None) -> MemoryManager:
    """Get or create the global memory manager instance"""
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = MemoryManager(config)
    return _memory_manager


def optimize_memory() -> Dict[str, Any]:
    """Optimize memory using the global manager"""
    manager = get_memory_manager()
    return manager.optimize_memory()


def cleanup_memory():
    """Run memory cleanup"""
    manager = get_memory_manager()
    manager.force_garbage_collection()


def get_memory_usage() -> Dict[str, Any]:
    """Get current memory usage"""
    manager = get_memory_manager()
    return manager.get_memory_usage()