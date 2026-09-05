"""
Enterprise Data Collector
Multi-source financial data collection with intelligent merging and validation
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Union, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from .data_sources import DataSource, YahooFinanceSource, AlphaVantageSource, CompositeDataSource, DataSourceConfig
from .data_models import FinancialData, MarketData, CollectionResult, DataQuality
from .data_validator import DataValidator
from ..cache import CacheManager
from ..config import ConfigurationManager


@dataclass
class CollectionRequest:
    """Data collection request"""
    symbol: str
    data_types: List[str] = field(default_factory=lambda: ["all"])
    period: str = "5y"
    use_cache: bool = True
    force_refresh: bool = False
    priority: int = 1  # 1-5, where 5 is highest
    timeout: int = 300
    context: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        # Validate data types
        valid_types = ["market", "financial", "analyst", "ownership", "options", "all"]
        for data_type in self.data_types:
            if data_type not in valid_types:
                raise ValueError(f"Invalid data type: {data_type}")


class EnterpriseDataCollector:
    """Enterprise-grade financial data collector"""

    def __init__(self, config_manager: ConfigurationManager, cache_manager: Optional[CacheManager] = None):
        self.config_manager = config_manager
        self.cache_manager = cache_manager
        self.validator = DataValidator()
        self.logger = logging.getLogger(__name__)
        self.data_sources = self._initialize_data_sources()
        self.collection_stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "cache_hits": 0,
            "average_execution_time": 0.0,
            "last_reset": datetime.now()
        }

    def _initialize_data_sources(self) -> Dict[str, DataSource]:
        """Initialize data sources from configuration"""
        sources = {}

        # Get data source configurations
        data_sources_config = self.config_manager.get("data_sources", {})

        # Yahoo Finance
        if data_sources_config.get("yahoo_finance", {}).get("enabled", False):
            config = DataSourceConfig(
                api_key="",  # Yahoo Finance doesn't require API key
                rate_limit=data_sources_config["yahoo_finance"].get("rate_limit", 100),
                timeout=data_sources_config["yahoo_finance"].get("timeout", 30)
            )
            sources["yahoo_finance"] = YahooFinanceSource(config)

        # Alpha Vantage
        if data_sources_config.get("alpha_vantage", {}).get("enabled", False):
            api_key = self.config_manager.get("api_keys.alpha_vantage")
            if api_key:
                config = DataSourceConfig(
                    api_key=api_key,
                    rate_limit=data_sources_config["alpha_vantage"].get("rate_limit", 5),
                    timeout=data_sources_config["alpha_vantage"].get("timeout", 60)
                )
                sources["alpha_vantage"] = AlphaVantageSource(config)

        # Create composite source
        if sources:
            sources["composite"] = CompositeDataSource(list(sources.values()))

        return sources

    async def collect_data(self, request: CollectionRequest) -> CollectionResult:
        """Collect data for a single symbol"""
        start_time = time.time()
        self.collection_stats["total_requests"] += 1

        try:
            self.logger.info(f"Starting data collection for {request.symbol}")

            # Generate cache key
            cache_key = self._generate_cache_key(request)

            # Check cache first
            if request.use_cache and not request.force_refresh:
                cached_data = await self._get_cached_data(cache_key)
                if cached_data:
                    self.collection_stats["cache_hits"] += 1
                    self.logger.info(f"Cache hit for {request.symbol}")
                    return CollectionResult(
                        success=True,
                        symbol=request.symbol,
                        data=cached_data,
                        execution_time=time.time() - start_time,
                        data_sources_used=["cache"],
                        metadata={"cache_hit": True, "cache_key": cache_key}
                    )

            # Collect data from sources
            collected_data = await self._collect_from_sources(request)

            # Validate and enhance data
            if collected_data:
                validated_result = self._validate_and_enhance_data(collected_data, request)

                # Cache the result
                if request.use_cache and validated_result.success:
                    await self._cache_data(cache_key, validated_result.data)

                # Update statistics
                if validated_result.success:
                    self.collection_stats["successful_requests"] += 1

                validated_result.execution_time = time.time() - start_time
                return validated_result
            else:
                return CollectionResult(
                    success=False,
                    symbol=request.symbol,
                    errors=["No data collected from any source"],
                    execution_time=time.time() - start_time
                )

        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"Data collection failed for {request.symbol}: {str(e)}")
            return CollectionResult(
                success=False,
                symbol=request.symbol,
                errors=[str(e)],
                execution_time=execution_time
            )

    async def collect_multiple_symbols(self, requests: List[CollectionRequest]) -> List[CollectionResult]:
        """Collect data for multiple symbols with intelligent batching"""
        # Sort by priority
        sorted_requests = sorted(requests, key=lambda r: r.priority, reverse=True)

        # Create semaphore for concurrent request limiting
        max_concurrent = self.config_manager.get("performance.max_concurrent_requests", 10)
        semaphore = asyncio.Semaphore(max_concurrent)

        async def collect_with_semaphore(request: CollectionRequest) -> CollectionResult:
            async with semaphore:
                return await self.collect_data(request)

        # Execute collection tasks
        tasks = [collect_with_semaphore(request) for request in sorted_requests]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(CollectionResult(
                    success=False,
                    symbol=sorted_requests[i].symbol,
                    errors=[str(result)],
                    execution_time=0.0
                ))
            else:
                processed_results.append(result)

        return processed_results

    async def _collect_from_sources(self, request: CollectionRequest) -> Optional[FinancialData]:
        """Collect data from configured sources"""
        if "composite" not in self.data_sources:
            self.logger.error("No data sources configured")
            return None

        try:
            # Use composite source for data collection
            composite_source = self.data_sources["composite"]

            # Collect data
            raw_data = await composite_source.fetch_data(
                request.symbol,
                period=request.period,
                **request.context
            )

            # Transform raw data to FinancialData model
            financial_data = self._transform_to_financial_data(raw_data, request)

            return financial_data

        except Exception as e:
            self.logger.error(f"Data collection from sources failed: {str(e)}")
            return None

    def _transform_to_financial_data(self, raw_data: Dict[str, Any], request: CollectionRequest) -> FinancialData:
        """Transform raw data to FinancialData model"""
        financial_data = FinancialData(symbol=request.symbol)

        # Transform market data
        if "market_data" in raw_data:
            financial_data.market_data = self._transform_market_data(
                raw_data["market_data"],
                raw_data.get("symbol", request.symbol)
            )

        # Transform financial statements
        if "financial_statements" in raw_data:
            statements = raw_data["financial_statements"]
            if "income_statement" in statements:
                financial_data.income_statement = self._transform_financial_statement(
                    statements["income_statement"], "income", "annual"
                )
            if "balance_sheet" in statements:
                financial_data.balance_sheet = self._transform_financial_statement(
                    statements["balance_sheet"], "balance", "annual"
                )
            if "cash_flow" in statements:
                financial_data.cash_flow = self._transform_financial_statement(
                    statements["cash_flow"], "cash_flow", "annual"
                )

        # Transform quarterly statements
        if "quarterly_income" in raw_data.get("financial_statements", {}):
            financial_data.quarterly_income = self._transform_financial_statement(
                raw_data["financial_statements"]["quarterly_income"], "income", "quarterly"
            )

        # Add data quality
        if "data_quality" in raw_data:
            financial_data.data_quality = DataQuality(**raw_data["data_quality"])

        # Add metadata
        financial_data.data_sources = raw_data.get("sources_used", ["unknown"])
        financial_data.last_updated = datetime.now()

        return financial_data

    def _transform_market_data(self, market_data: Dict[str, Any], symbol: str) -> MarketData:
        """Transform market data to MarketData model"""
        return MarketData(
            symbol=symbol,
            current_price=market_data.get("current_price", 0.0),
            market_cap=market_data.get("market_cap"),
            enterprise_value=market_data.get("enterprise_value"),
            trailing_pe=market_data.get("trailing_pe"),
            forward_pe=market_data.get("forward_pe"),
            dividend_yield=market_data.get("dividend_yield"),
            beta=market_data.get("beta"),
            _52_week_high=market_data.get("52_week_high"),
            _52_week_low=market_data.get("52_week_low"),
            avg_volume=market_data.get("avg_volume"),
            currency=market_data.get("currency"),
            exchange=market_data.get("exchange"),
            price_history=self._transform_price_history(market_data.get("price_history", {}))
        )

    def _transform_price_history(self, price_history: Dict[str, Any]) -> List:
        """Transform price history data"""
        # This is a simplified transformation
        # In practice, you'd need to handle different data formats
        return []

    def _transform_financial_statement(self, statement_data: Dict[str, Any], statement_type: str, period: str):
        """Transform financial statement data"""
        from .data_models import FinancialStatement

        # Convert pandas DataFrame to dictionary format
        if hasattr(statement_data, 'to_dict'):
            data = statement_data.to_dict()
        else:
            data = statement_data

        return FinancialStatement(
            statement_type=statement_type,
            period=period,
            data=data,
            currency="USD"  # Default currency
        )

    def _validate_and_enhance_data(self, data: FinancialData, request: CollectionRequest) -> CollectionResult:
        """Validate and enhance collected data"""
        result = CollectionResult(
            success=True,
            symbol=request.symbol,
            data=data,
            data_sources_used=data.data_sources,
            metadata={"collection_time": datetime.now().isoformat()}
        )

        # Run validation
        validated_result = self.validator.validate_collection_result(result)

        # Add data quality assessment
        if validated_result.data:
            quality_score = self._assess_data_quality(validated_result.data)
            if validated_result.data.data_quality:
                validated_result.data.data_quality.overall_score = quality_score
            else:
                validated_result.data.data_quality = DataQuality(overall_score=quality_score)

        return validated_result

    def _assess_data_quality(self, data: FinancialData) -> float:
        """Assess overall data quality"""
        quality_factors = []

        # Market data quality
        if data.market_data:
            market_quality = 0.9  # Base quality
            if data.market_data.price_history:
                market_quality += 0.05  # Bonus for price history
            quality_factors.append(market_quality)

        # Financial statements quality
        statement_count = sum(1 for stmt in [data.income_statement, data.balance_sheet, data.cash_flow] if stmt)
        if statement_count > 0:
            statement_quality = 0.8 + (statement_count / 3) * 0.15  # 0.8 to 0.95
            quality_factors.append(statement_quality)

        # Data sources quality
        if data.data_sources:
            source_quality = min(1.0, len(data.data_sources) / 3)  # More sources = higher quality
            quality_factors.append(source_quality)

        # Recency
        if data.last_updated:
            age = datetime.now() - data.last_updated
            recency_quality = max(0.7, 1.0 - (age.days / 30))  # Penalty for old data
            quality_factors.append(recency_quality)

        return sum(quality_factors) / len(quality_factors) if quality_factors else 0.5

    def _generate_cache_key(self, request: CollectionRequest) -> str:
        """Generate cache key for request"""
        key_parts = [
            request.symbol,
            "_".join(sorted(request.data_types)),
            request.period
        ]
        return f"financial_data:{':'.join(key_parts)}"

    async def _get_cached_data(self, cache_key: str) -> Optional[FinancialData]:
        """Get data from cache"""
        if not self.cache_manager:
            return None

        try:
            cached_data = await self.cache_manager.get_cached_data(cache_key)
            if cached_data:
                return FinancialData.from_dict(cached_data)
        except Exception as e:
            self.logger.warning(f"Cache retrieval failed: {str(e)}")

        return None

    async def _cache_data(self, cache_key: str, data: FinancialData):
        """Cache data"""
        if not self.cache_manager:
            return

        try:
            await self.cache_manager.set_cached_data(cache_key, data.to_dict())
        except Exception as e:
            self.logger.warning(f"Cache storage failed: {str(e)}")

    def get_collection_statistics(self) -> Dict[str, Any]:
        """Get collection statistics"""
        stats = self.collection_stats.copy()

        # Calculate success rate
        if stats["total_requests"] > 0:
            stats["success_rate"] = stats["successful_requests"] / stats["total_requests"]
            stats["cache_hit_rate"] = stats["cache_hits"] / stats["total_requests"]
        else:
            stats["success_rate"] = 0.0
            stats["cache_hit_rate"] = 0.0

        # Calculate average execution time
        if stats["total_requests"] > 0:
            stats["average_execution_time"] = stats.get("average_execution_time", 0.0)

        return stats

    def reset_statistics(self):
        """Reset collection statistics"""
        self.collection_stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "cache_hits": 0,
            "average_execution_time": 0.0,
            "last_reset": datetime.now()
        }

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on data sources"""
        health_status = {
            "overall_status": "healthy",
            "data_sources": {},
            "cache_status": "unknown",
            "timestamp": datetime.now().isoformat()
        }

        # Check data sources
        unhealthy_sources = []
        for source_name, source in self.data_sources.items():
            try:
                metadata = source.get_metadata()
                health_status["data_sources"][source_name] = {
                    "status": "healthy",
                    "metadata": metadata
                }
            except Exception as e:
                health_status["data_sources"][source_name] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
                unhealthy_sources.append(source_name)

        # Check cache
        if self.cache_manager:
            try:
                # Simple cache test
                test_key = "health_check_test"
                test_data = {"test": True, "timestamp": datetime.now().isoformat()}
                await self.cache_manager.set_cached_data(test_key, test_data)
                retrieved_data = await self.cache_manager.get_cached_data(test_key)

                if retrieved_data == test_data:
                    health_status["cache_status"] = "healthy"
                else:
                    health_status["cache_status"] = "unhealthy"
                    unhealthy_sources.append("cache")
            except Exception as e:
                health_status["cache_status"] = "unhealthy"
                health_status["cache_error"] = str(e)
                unhealthy_sources.append("cache")

        # Determine overall status
        if unhealthy_sources:
            health_status["overall_status"] = "degraded"
            health_status["unhealthy_components"] = unhealthy_sources

        return health_status