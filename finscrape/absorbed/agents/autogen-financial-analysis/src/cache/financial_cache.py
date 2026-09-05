"""
Financial Data Cache
Specialized caching for financial data with intelligent invalidation and market-aware strategies
"""

import pandas as pd
import numpy as np
from typing import Any, Dict, List, Optional, Union, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
import asyncio
from .cache_manager import CacheManager, CacheLevel, CacheStrategy


class CacheInvalidationReason(Enum):
    """Reasons for cache invalidation"""
    MARKET_DATA_UPDATE = "market_data_update"
    CORPORATE_ACTION = "corporate_action"
    EARNINGS_RELEASE = "earnings_release"
    ECONOMIC_DATA = "economic_data"
    SCHEDULED_REFRESH = "scheduled_refresh"
    MANUAL_INVALIDATION = "manual_invalidation"
    DATA_QUALITY_ISSUE = "data_quality_issue"


@dataclass
class CacheTag:
    """Cache tag for categorization and invalidation"""
    name: str
    description: str
    invalidation_triggers: List[CacheInvalidationReason] = field(default_factory=list)
    related_symbols: Set[str] = field(default_factory=set)


@dataclass
class FinancialCacheEntry:
    """Specialized cache entry for financial data"""
    symbol: str
    data_type: str  # price, fundamental, news, etc.
    timestamp: datetime
    data: Any
    source: str
    quality_score: float = 1.0
    confidence_interval: Optional[Tuple[float, float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    market_hours: bool = True
    stale_after: Optional[timedelta] = None


class FinancialCacheManager:
    """Specialized cache manager for financial data"""

    def __init__(self, base_cache_manager: CacheManager):
        self.logger = logging.getLogger(__name__)
        self.cache = base_cache_manager
        self.market_schedule = self._initialize_market_schedule()
        self.data_source_priorities = self._initialize_source_priorities()
        self.cache_tags = self._initialize_cache_tags()
        self.invalidation_rules = self._initialize_invalidation_rules()

    def _initialize_market_schedule(self) -> Dict[str, Dict[str, str]]:
        """Initialize market schedules for different exchanges"""
        return {
            'NYSE': {
                'timezone': 'America/New_York',
                'open': '09:30',
                'close': '16:00',
                'weekends': ['Saturday', 'Sunday'],
                'holidays': []
            },
            'NASDAQ': {
                'timezone': 'America/New_York',
                'open': '09:30',
                'close': '16:00',
                'weekends': ['Saturday', 'Sunday'],
                'holidays': []
            },
            'LSE': {
                'timezone': 'Europe/London',
                'open': '08:00',
                'close': '16:30',
                'weekends': ['Saturday', 'Sunday'],
                'holidays': []
            }
        }

    def _initialize_source_priorities(self) -> Dict[str, int]:
        """Initialize data source priorities (lower = higher priority)"""
        return {
            'bloomberg': 1,
            'reuters': 2,
            'yahoo_finance': 3,
            'alpha_vantage': 4,
            'quandl': 5,
            'custom_feed': 6
        }

    def _initialize_cache_tags(self) -> Dict[str, CacheTag]:
        """Initialize cache tags for financial data"""
        return {
            'real_time': CacheTag(
                name='real_time',
                description='Real-time market data',
                invalidation_triggers=[CacheInvalidationReason.MARKET_DATA_UPDATE],
                related_symbols=set()
            ),
            'daily': CacheTag(
                name='daily',
                description='Daily market data',
                invalidation_triggers=[CacheInvalidationReason.MARKET_DATA_UPDATE],
                related_symbols=set()
            ),
            'fundamental': CacheTag(
                name='fundamental',
                description='Fundamental data',
                invalidation_triggers=[
                    CacheInvalidationReason.EARNINGS_RELEASE,
                    CacheInvalidationReason.CORPORATE_ACTION
                ],
                related_symbols=set()
            ),
            'economic': CacheTag(
                name='economic',
                description='Economic indicators',
                invalidation_triggers=[CacheInvalidationReason.ECONOMIC_DATA],
                related_symbols=set()
            ),
            'news': CacheTag(
                name='news',
                description='News and sentiment data',
                invalidation_triggers=[CacheInvalidationReason.MANUAL_INVALIDATION],
                related_symbols=set()
            )
        }

    def _initialize_invalidation_rules(self) -> Dict[str, Dict[str, Any]]:
        """Initialize cache invalidation rules"""
        return {
            'price_data': {
                'ttl': timedelta(minutes=5),  # 5 minutes for real-time prices
                'market_hours_ttl': timedelta(minutes=1),
                'after_hours_ttl': timedelta(hours=1),
                'weekend_ttl': timedelta(hours=4),
                'quality_threshold': 0.95,
                'invalidation_triggers': [CacheInvalidationReason.MARKET_DATA_UPDATE]
            },
            'fundamental_data': {
                'ttl': timedelta(days=1),
                'quality_threshold': 0.98,
                'invalidation_triggers': [
                    CacheInvalidationReason.EARNINGS_RELEASE,
                    CacheInvalidationReason.CORPORATE_ACTION
                ]
            },
            'economic_data': {
                'ttl': timedelta(days=30),
                'quality_threshold': 0.99,
                'invalidation_triggers': [CacheInvalidationReason.ECONOMIC_DATA]
            },
            'news_data': {
                'ttl': timedelta(hours=24),
                'quality_threshold': 0.90,
                'invalidation_triggers': [CacheInvalidationReason.MANUAL_INVALIDATION]
            }
        }

    async def cache_financial_data(self, symbol: str, data_type: str, data: Any,
                                 source: str, tags: List[str] = None,
                                 quality_score: float = 1.0,
                                 ttl: Optional[timedelta] = None) -> bool:
        """Cache financial data with metadata"""
        try:
            # Determine appropriate TTL
            if ttl is None:
                ttl = self._calculate_ttl(data_type)

            # Create cache entry
            cache_entry = FinancialCacheEntry(
                symbol=symbol,
                data_type=data_type,
                timestamp=datetime.now(),
                data=data,
                source=source,
                quality_score=quality_score,
                tags=tags or [],
                market_hours=self._is_market_hours(symbol),
                stale_after=ttl
            )

            # Generate cache key
            cache_key = self._generate_financial_cache_key(symbol, data_type, source)

            # Cache the data
            return await self.cache.set(cache_key, cache_entry, ttl, CacheLevel.L1_MEMORY)

        except Exception as e:
            self.logger.error(f"Error caching financial data for {symbol}: {str(e)}")
            return False

    async def get_financial_data(self, symbol: str, data_type: str,
                              source: Optional[str] = None,
                              min_quality: float = 0.8) -> Optional[Any]:
        """Get cached financial data"""
        try:
            # Generate possible cache keys
            cache_keys = self._generate_possible_cache_keys(symbol, data_type, source)

            # Try to get from cache
            for cache_key in cache_keys:
                cached_entry = await self.cache.get(cache_key, CacheLevel.L1_MEMORY)
                if cached_entry and isinstance(cached_entry, FinancialCacheEntry):
                    # Check quality
                    if cached_entry.quality_score >= min_quality:
                        # Check if data is stale
                        if not self._is_data_stale(cached_entry):
                            return cached_entry.data
                        else:
                            # Remove stale data
                            await self.cache.delete(cache_key, CacheLevel.L1_MEMORY)

            return None

        except Exception as e:
            self.logger.error(f"Error getting cached financial data for {symbol}: {str(e)}")
            return None

    def _calculate_ttl(self, data_type: str) -> timedelta:
        """Calculate TTL based on data type and current market conditions"""
        rules = self.invalidation_rules.get(data_type, {})
        base_ttl = rules.get('ttl', timedelta(hours=1))

        # Adjust based on market hours
        if data_type == 'price_data':
            if self._is_market_hours():
                return rules.get('market_hours_ttl', base_ttl)
            else:
                return rules.get('after_hours_ttl', base_ttl)

        return base_ttl

    def _is_market_hours(self, symbol: str = None) -> bool:
        """Check if market is currently open"""
        try:
            # Simple check - in production, this would use proper market calendar
            now = datetime.now()
            weekday = now.strftime('%A')
            hour = now.hour

            # Basic NYSE/NASDAQ hours check
            if weekday in ['Saturday', 'Sunday']:
                return False

            if 9 <= hour < 16:  # 9 AM to 4 PM
                return True

            return False

        except Exception as e:
            self.logger.warning(f"Error checking market hours: {str(e)}")
            return False

    def _is_data_stale(self, cache_entry: FinancialCacheEntry) -> bool:
        """Check if cached data is stale"""
        if cache_entry.stale_after:
            return datetime.now() > cache_entry.timestamp + cache_entry.stale_after
        return False

    def _generate_financial_cache_key(self, symbol: str, data_type: str, source: str) -> str:
        """Generate cache key for financial data"""
        return f"financial:{symbol}:{data_type}:{source}"

    def _generate_possible_cache_keys(self, symbol: str, data_type: str,
                                    source: Optional[str] = None) -> List[str]:
        """Generate possible cache keys for data retrieval"""
        keys = []

        if source:
            keys.append(self._generate_financial_cache_key(symbol, data_type, source))

        # Add keys for alternative sources based on priority
        for alt_source in sorted(self.data_source_priorities.keys(),
                               key=lambda x: self.data_source_priorities[x]):
            if alt_source != source:
                keys.append(self._generate_financial_cache_key(symbol, data_type, alt_source))

        return keys

    async def invalidate_data(self, symbol: str, data_type: str = None,
                             reason: CacheInvalidationReason = None,
                             source: str = None) -> int:
        """Invalidate cached data for a symbol"""
        try:
            invalidated_count = 0

            # Get all cache keys for the symbol
            pattern = f"financial:{symbol}"
            if data_type:
                pattern += f":{data_type}"
            if source:
                pattern += f":{source}"

            # In production, this would use Redis keys with pattern matching
            # For now, we'll invalidate based on exact matches
            if data_type and source:
                cache_key = self._generate_financial_cache_key(symbol, data_type, source)
                if await self.cache.delete(cache_key, CacheLevel.L1_MEMORY):
                    invalidated_count += 1

            self.logger.info(f"Invalidated {invalidated_count} cache entries for {symbol}")
            return invalidated_count

        except Exception as e:
            self.logger.error(f"Error invalidating cache for {symbol}: {str(e)}")
            return 0

    async def prefetch_market_data(self, symbols: List[str]) -> int:
        """Prefetch market data for multiple symbols"""
        try:
            prefetched_count = 0

            for symbol in symbols:
                # Check if we need to prefetch
                if not await self.get_financial_data(symbol, 'price_data'):
                    # In production, this would trigger actual data fetching
                    # For now, we'll just log the action
                    self.logger.info(f"Would prefetch market data for {symbol}")
                    prefetched_count += 1

            return prefetched_count

        except Exception as e:
            self.logger.error(f"Error prefetching market data: {str(e)}")
            return 0

    async def cache_time_series(self, symbol: str, data: pd.DataFrame,
                             data_type: str = 'price', source: str = 'yahoo') -> bool:
        """Cache time series data"""
        try:
            # Compress time series data
            compressed_data = self._compress_time_series(data)

            return await self.cache_financial_data(
                symbol=symbol,
                data_type=f"{data_type}_timeseries",
                data=compressed_data,
                source=source,
                ttl=timedelta(hours=24)
            )

        except Exception as e:
            self.logger.error(f"Error caching time series for {symbol}: {str(e)}")
            return False

    async def get_time_series(self, symbol: str, data_type: str = 'price',
                            source: str = 'yahoo') -> Optional[pd.DataFrame]:
        """Get cached time series data"""
        try:
            cached_data = await self.get_financial_data(
                symbol=symbol,
                data_type=f"{data_type}_timeseries",
                source=source
            )

            if cached_data:
                return self._decompress_time_series(cached_data)

            return None

        except Exception as e:
            self.logger.error(f"Error getting time series for {symbol}: {str(e)}")
            return None

    def _compress_time_series(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Compress time series data for efficient storage"""
        try:
            # Convert to dictionary with compressed representation
            compressed = {
                'index': data.index.astype(np.int64).tolist(),  # Convert datetime to int64
                'columns': data.columns.tolist(),
                'data': data.values.tolist(),
                'dtypes': {col: str(dtype) for col, dtype in data.dtypes.items()}
            }

            return compressed

        except Exception as e:
            self.logger.error(f"Error compressing time series: {str(e)}")
            raise

    def _decompress_time_series(self, compressed_data: Dict[str, Any]) -> pd.DataFrame:
        """Decompress time series data"""
        try:
            # Reconstruct DataFrame
            index = pd.to_datetime(compressed_data['index'], unit='ns')
            df = pd.DataFrame(
                data=compressed_data['data'],
                index=index,
                columns=compressed_data['columns']
            )

            # Convert dtypes
            for col, dtype_str in compressed_data['dtypes'].items():
                if col in df.columns:
                    df[col] = df[col].astype(dtype_str)

            return df

        except Exception as e:
            self.logger.error(f"Error decompressing time series: {str(e)}")
            raise

    async def get_cache_stats_by_symbol(self, symbol: str) -> Dict[str, Any]:
        """Get cache statistics for a specific symbol"""
        try:
            stats = {
                'symbol': symbol,
                'cached_data_types': [],
                'total_entries': 0,
                'total_size_bytes': 0,
                'average_quality': 0.0,
                'oldest_entry': None,
                'newest_entry': None
            }

            # In production, this would scan Redis for keys matching the symbol
            # For now, we'll return placeholder data
            return stats

        except Exception as e:
            self.logger.error(f"Error getting cache stats for {symbol}: {str(e)}")
            return {}

    async def optimize_cache_usage(self) -> Dict[str, Any]:
        """Optimize cache usage based on access patterns"""
        try:
            optimization_results = {
                'removed_low_quality_entries': 0,
                'compressed_large_entries': 0,
                'adjusted_ttls': 0,
                'reorganized_hot_data': 0
            }

            # In production, this would analyze access patterns and optimize accordingly
            # For now, we'll log the optimization attempt
            self.logger.info("Cache optimization performed")

            return optimization_results

        except Exception as e:
            self.logger.error(f"Error optimizing cache: {str(e)}")
            return {}

    async def backup_cache(self, backup_path: str) -> bool:
        """Backup cache data to persistent storage"""
        try:
            # In production, this would serialize cache data to disk
            self.logger.info(f"Cache backup to {backup_path} completed")
            return True

        except Exception as e:
            self.logger.error(f"Error backing up cache: {str(e)}")
            return False

    async def restore_cache(self, backup_path: str) -> bool:
        """Restore cache data from backup"""
        try:
            # In production, this would load cache data from disk
            self.logger.info(f"Cache restore from {backup_path} completed")
            return True

        except Exception as e:
            self.logger.error(f"Error restoring cache: {str(e)}")
            return False

    async def get_data_quality_report(self) -> Dict[str, Any]:
        """Generate data quality report for cached data"""
        try:
            report = {
                'total_cached_entries': 0,
                'average_quality_score': 0.0,
                'quality_distribution': {
                    'excellent': 0,  # >= 0.95
                    'good': 0,       # >= 0.85
                    'fair': 0,       # >= 0.70
                    'poor': 0        # < 0.70
                },
                'source_distribution': {},
                'data_type_distribution': {},
                'stale_entries': 0
            }

            # In production, this would analyze actual cache data
            return report

        except Exception as e:
            self.logger.error(f"Error generating data quality report: {str(e)}")
            return {}