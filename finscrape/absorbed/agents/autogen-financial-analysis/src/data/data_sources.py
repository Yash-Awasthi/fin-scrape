"""
Data Sources
Abstract base class and implementations for financial data sources
"""

import asyncio
import aiohttp
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
import pandas as pd
import yfinance as yf
from dataclasses import dataclass, field


@dataclass
class DataSourceConfig:
    """Configuration for data sources"""
    api_key: str
    rate_limit: int = 100
    timeout: int = 30
    enabled: bool = True
    retry_attempts: int = 3
    backoff_factor: float = 2.0


class DataSource(ABC):
    """Abstract base class for financial data sources"""

    def __init__(self, config: DataSourceConfig):
        self.config = config
        self.request_count = 0
        self.last_request_time = None
        self.logger = logging.getLogger(self.__class__.__name__)
        self.session = None

    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.config.timeout))
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    @abstractmethod
    async def fetch_data(self, symbol: str, **kwargs) -> Dict[str, Any]:
        """Fetch data from the source"""
        pass

    async def _rate_limit_check(self):
        """Rate limiting check"""
        if self.last_request_time:
            time_diff = datetime.now() - self.last_request_time
            min_interval = 1.0 / self.config.rate_limit
            if time_diff.total_seconds() < min_interval:
                await asyncio.sleep(min_interval - time_diff.total_seconds())

        self.last_request_time = datetime.now()
        self.request_count += 1

    async def _make_request(self, url: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make HTTP request with error handling and retries"""
        await self._rate_limit_check()

        for attempt in range(self.config.retry_attempts):
            try:
                async with self.session.get(url, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 429:  # Rate limited
                        wait_time = self.config.backoff_factor ** attempt
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        response.raise_for_status()
            except Exception as e:
                if attempt == self.config.retry_attempts - 1:
                    raise
                wait_time = self.config.backoff_factor ** attempt
                await asyncio.sleep(wait_time)

        raise Exception(f"Max retries exceeded for request: {url}")

    def get_metadata(self) -> Dict[str, Any]:
        """Get data source metadata"""
        return {
            "name": self.__class__.__name__,
            "enabled": self.config.enabled,
            "rate_limit": self.config.rate_limit,
            "timeout": self.config.timeout,
            "request_count": self.request_count,
            "last_request": self.last_request_time.isoformat() if self.last_request_time else None
        }


class YahooFinanceSource(DataSource):
    """Yahoo Finance data source implementation"""

    def __init__(self, config: DataSourceConfig):
        super().__init__(config)
        self.base_url = "https://query1.finance.yahoo.com"

    async def fetch_data(self, symbol: str, **kwargs) -> Dict[str, Any]:
        """Fetch comprehensive financial data from Yahoo Finance"""
        await self._rate_limit_check()

        try:
            period = kwargs.get("period", "5y")
            interval = kwargs.get("interval", "1d")

            # Get stock data
            stock = yf.Ticker(symbol)

            # Parallel data collection
            tasks = [
                self._get_financial_statements(stock),
                self._get_market_data(stock, period, interval),
                self._get_analyst_data(stock),
                self._get_ownership_data(stock),
                self._get_options_data(stock)
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            data = {
                "symbol": symbol,
                "source": "yahoo_finance",
                "timestamp": datetime.now().isoformat(),
                "data_quality": self._calculate_data_quality(results)
            }

            # Add successful results
            for i, result in enumerate(results):
                if not isinstance(result, Exception):
                    data.update(result)

            return data

        except Exception as e:
            self.logger.error(f"Yahoo Finance data fetch failed for {symbol}: {str(e)}")
            raise

    async def _get_financial_statements(self, stock: yf.Ticker) -> Dict[str, Any]:
        """Get financial statements"""
        try:
            return {
                "financial_statements": {
                    "income_statement": stock.financials.to_dict() if stock.financials is not None else {},
                    "balance_sheet": stock.balance_sheet.to_dict() if stock.balance_sheet is not None else {},
                    "cash_flow": stock.cashflow.to_dict() if stock.cashflow is not None else {},
                    "quarterly_income": stock.quarterly_financials.to_dict() if stock.quarterly_financials is not None else {},
                    "quarterly_balance": stock.quarterly_balance_sheet.to_dict() if stock.quarterly_balance_sheet is not None else {},
                    "quarterly_cashflow": stock.quarterly_cashflow.to_dict() if stock.quarterly_cashflow is not None else {}
                }
            }
        except Exception as e:
            self.logger.warning(f"Financial statements fetch failed: {str(e)}")
            return {"financial_statements": {}}

    async def _get_market_data(self, stock: yf.Ticker, period: str, interval: str) -> Dict[str, Any]:
        """Get market data"""
        try:
            history = stock.history(period=period, interval=interval)
            info = stock.info

            return {
                "market_data": {
                    "price_history": history.to_dict() if history is not None else {},
                    "current_price": info.get("currentPrice"),
                    "market_cap": info.get("marketCap"),
                    "enterprise_value": info.get("enterpriseValue"),
                    "trailing_pe": info.get("trailingPE"),
                    "forward_pe": info.get("forwardPE"),
                    "dividend_yield": info.get("dividendYield"),
                    "beta": info.get("beta"),
                    "52_week_high": info.get("fiftyTwoWeekHigh"),
                    "52_week_low": info.get("fiftyTwoWeekLow"),
                    "avg_volume": info.get("averageVolume"),
                    "currency": info.get("currency"),
                    "exchange": info.get("exchange")
                }
            }
        except Exception as e:
            self.logger.warning(f"Market data fetch failed: {str(e)}")
            return {"market_data": {}}

    async def _get_analyst_data(self, stock: yf.Ticker) -> Dict[str, Any]:
        """Get analyst recommendations and earnings data"""
        try:
            return {
                "analyst_data": {
                    "recommendations": stock.recommendations.to_dict() if stock.recommendations is not None else {},
                    "earnings": stock.earnings.to_dict() if stock.earnings is not None else {},
                    "earnings_dates": stock.earnings_dates.to_dict() if stock.earnings_dates is not None else {},
                    "calendar": stock.calendar.to_dict() if stock.calendar is not None else {}
                }
            }
        except Exception as e:
            self.logger.warning(f"Analyst data fetch failed: {str(e)}")
            return {"analyst_data": {}}

    async def _get_ownership_data(self, stock: yf.Ticker) -> Dict[str, Any]:
        """Get ownership data"""
        try:
            return {
                "ownership_data": {
                    "institutional_holders": stock.institutional_holders.to_dict() if stock.institutional_holders is not None else {},
                    "major_holders": stock.major_holders.to_dict() if stock.major_holders is not None else {},
                    "mutualfund_holders": stock.mutualfund_holders.to_dict() if stock.mutualfund_holders is not None else {}
                }
            }
        except Exception as e:
            self.logger.warning(f"Ownership data fetch failed: {str(e)}")
            return {"ownership_data": {}}

    async def _get_options_data(self, stock: yf.Ticker) -> Dict[str, Any]:
        """Get options data"""
        try:
            return {
                "options_data": {
                    "options": stock.options,
                    "option_chain": {exp: stock.option_chain(exp).to_dict() for exp in stock.options[:3]} if stock.options else {}
                }
            }
        except Exception as e:
            self.logger.warning(f"Options data fetch failed: {str(e)}")
            return {"options_data": {}}

    def _calculate_data_quality(self, results: List) -> Dict[str, float]:
        """Calculate data quality metrics"""
        total_fields = 5  # financial_statements, market_data, analyst_data, ownership_data, options_data
        successful_fields = sum(1 for result in results if not isinstance(result, Exception))

        return {
            "completeness": successful_fields / total_fields,
            "accuracy": 0.95,  # Yahoo Finance generally has high accuracy
            "timeliness": 0.98,  # Real-time data
            "consistency": 0.90,
            "overall_score": (successful_fields / total_fields) * 0.95
        }


class AlphaVantageSource(DataSource):
    """Alpha Vantage data source implementation"""

    def __init__(self, config: DataSourceConfig):
        super().__init__(config)
        self.base_url = "https://www.alphavantage.co/query"

    async def fetch_data(self, symbol: str, **kwargs) -> Dict[str, Any]:
        """Fetch data from Alpha Vantage API"""
        await self._rate_limit_check()

        try:
            # Alpha Vantage has strict rate limits (5 calls per minute for free tier)
            # We'll fetch essential data with delays between calls

            tasks = [
                self._get_income_statement(symbol),
                self._get_balance_sheet(symbol),
                self._get_cash_flow(symbol),
                self._get_company_overview(symbol),
                self._get_time_series_data(symbol)
            ]

            # Sequential execution to respect rate limits
            results = {}
            for task in tasks:
                try:
                    result = await task
                    results.update(result)
                    await asyncio.sleep(12)  # Wait 12 seconds between calls
                except Exception as e:
                    self.logger.warning(f"Alpha Vantage task failed: {str(e)}")

            results.update({
                "symbol": symbol,
                "source": "alpha_vantage",
                "timestamp": datetime.now().isoformat(),
                "data_quality": self._calculate_data_quality(results)
            })

            return results

        except Exception as e:
            self.logger.error(f"Alpha Vantage data fetch failed for {symbol}: {str(e)}")
            raise

    async def _get_income_statement(self, symbol: str) -> Dict[str, Any]:
        """Get income statement data"""
        params = {
            "function": "INCOME_STATEMENT",
            "symbol": symbol,
            "apikey": self.config.api_key
        }

        data = await self._make_request(self.base_url, params)
        return {"alpha_vantage_income_statement": data}

    async def _get_balance_sheet(self, symbol: str) -> Dict[str, Any]:
        """Get balance sheet data"""
        params = {
            "function": "BALANCE_SHEET",
            "symbol": symbol,
            "apikey": self.config.api_key
        }

        data = await self._make_request(self.base_url, params)
        return {"alpha_vantage_balance_sheet": data}

    async def _get_cash_flow(self, symbol: str) -> Dict[str, Any]:
        """Get cash flow data"""
        params = {
            "function": "CASH_FLOW",
            "symbol": symbol,
            "apikey": self.config.api_key
        }

        data = await self._make_request(self.base_url, params)
        return {"alpha_vantage_cash_flow": data}

    async def _get_company_overview(self, symbol: str) -> Dict[str, Any]:
        """Get company overview data"""
        params = {
            "function": "OVERVIEW",
            "symbol": symbol,
            "apikey": self.config.api_key
        }

        data = await self._make_request(self.base_url, params)
        return {"alpha_vantage_overview": data}

    async def _get_time_series_data(self, symbol: str) -> Dict[str, Any]:
        """Get time series data"""
        params = {
            "function": "TIME_SERIES_DAILY",
            "symbol": symbol,
            "outputsize": "compact",
            "apikey": self.config.api_key
        }

        data = await self._make_request(self.base_url, params)
        return {"alpha_vantage_time_series": data}

    def _calculate_data_quality(self, results: Dict) -> Dict[str, float]:
        """Calculate data quality metrics"""
        expected_functions = ["INCOME_STATEMENT", "BALANCE_SHEET", "CASH_FLOW", "OVERVIEW", "TIME_SERIES_DAILY"]
        successful_functions = sum(1 for key in results.keys() if "alpha_vantage_" in key)

        return {
            "completeness": successful_functions / len(expected_functions),
            "accuracy": 0.92,
            "timeliness": 0.85,  # Slight delay in data
            "consistency": 0.88,
            "overall_score": (successful_functions / len(expected_functions)) * 0.90
        }


class QuandlSource(DataSource):
    """Quandl data source implementation"""

    def __init__(self, config: DataSourceConfig):
        super().__init__(config)
        self.base_url = "https://www.quandl.com/api/v3/datasets"

    async def fetch_data(self, symbol: str, **kwargs) -> Dict[str, Any]:
        """Fetch data from Quandl API"""
        await self._rate_limit_check()

        try:
            # Quandl uses different ticker formats, we'll need to map symbols
            quandl_symbol = self._map_to_quandl_symbol(symbol)

            params = {
                "api_key": self.config.api_key,
                "limit": 100,
                "order": "desc"
            }

            url = f"{self.base_url}/{quandl_symbol}/data.json"
            data = await self._make_request(url, params)

            return {
                "symbol": symbol,
                "quandl_symbol": quandl_symbol,
                "source": "quandl",
                "data": data,
                "timestamp": datetime.now().isoformat(),
                "data_quality": {
                    "completeness": 0.85,
                    "accuracy": 0.90,
                    "timeliness": 0.80,
                    "consistency": 0.85,
                    "overall_score": 0.85
                }
            }

        except Exception as e:
            self.logger.error(f"Quandl data fetch failed for {symbol}: {str(e)}")
            raise

    def _map_to_quandl_symbol(self, symbol: str) -> str:
        """Map standard symbol to Quandl format"""
        # This is a simplified mapping - in practice, you'd need a comprehensive mapping
        return f"WIKI/{symbol}"


class CompositeDataSource(DataSource):
    """Composite data source that aggregates from multiple sources"""

    def __init__(self, sources: List[DataSource]):
        # Use a dummy config for the composite source
        dummy_config = DataSourceConfig(api_key="composite")
        super().__init__(dummy_config)
        self.sources = [source for source in sources if source.config.enabled]
        self.logger = logging.getLogger(self.__class__.__name__)

    async def fetch_data(self, symbol: str, **kwargs) -> Dict[str, Any]:
        """Fetch and aggregate data from multiple sources"""
        try:
            # Parallel data collection from all sources
            tasks = []
            async with aiohttp.ClientSession() as session:
                for source in self.sources:
                    source.session = session
                    task = source.fetch_data(symbol, **kwargs)
                    tasks.append(task)

                results = await asyncio.gather(*tasks, return_exceptions=True)

            # Aggregate results
            aggregated_data = self._aggregate_results(results, symbol)

            return aggregated_data

        except Exception as e:
            self.logger.error(f"Composite data fetch failed for {symbol}: {str(e)}")
            raise

    def _aggregate_results(self, results: List[Dict], symbol: str) -> Dict[str, Any]:
        """Aggregate results from multiple sources"""
        aggregated = {
            "symbol": symbol,
            "source": "composite",
            "timestamp": datetime.now().isoformat(),
            "sources_used": [],
            "data_quality": self._calculate_aggregated_quality(results)
        }

        for result in results:
            if isinstance(result, Exception):
                self.logger.warning(f"Source returned error: {str(result)}")
                continue

            if isinstance(result, dict):
                source_name = result.get("source", "unknown")
                aggregated["sources_used"].append(source_name)

                # Merge data from different sources
                for key, value in result.items():
                    if key not in ["symbol", "source", "timestamp", "data_quality"]:
                        if key in aggregated:
                            # Data already exists from another source - implement merging logic
                            aggregated[key] = self._merge_data(aggregated[key], value, source_name)
                        else:
                            aggregated[key] = value

        return aggregated

    def _merge_data(self, existing_data: Any, new_data: Any, source: str) -> Any:
        """Merge data from different sources with conflict resolution"""
        if isinstance(existing_data, dict) and isinstance(new_data, dict):
            merged = existing_data.copy()
            for key, value in new_data.items():
                if key in merged:
                    # Priority: Yahoo Finance > Alpha Vantage > Quandl
                    if source == "yahoo_finance":
                        merged[key] = value
                else:
                    merged[key] = value
            return merged
        else:
            # For non-dict data, prefer Yahoo Finance
            return new_data if source == "yahoo_finance" else existing_data

    def _calculate_aggregated_quality(self, results: List[Dict]) -> Dict[str, float]:
        """Calculate aggregated data quality metrics"""
        quality_scores = []
        for result in results:
            if isinstance(result, dict) and "data_quality" in result:
                quality_scores.append(result["data_quality"].get("overall_score", 0.5))

        if quality_scores:
            avg_quality = sum(quality_scores) / len(quality_scores)
            completeness = len([r for r in results if isinstance(r, dict)]) / len(results)
        else:
            avg_quality = 0.0
            completeness = 0.0

        return {
            "completeness": completeness,
            "accuracy": avg_quality * 0.95,
            "timeliness": avg_quality * 0.90,
            "consistency": avg_quality * 0.85,
            "overall_score": avg_quality
        }