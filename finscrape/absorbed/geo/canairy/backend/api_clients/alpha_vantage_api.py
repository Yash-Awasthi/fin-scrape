"""
Alpha Vantage API Client
Premium API access for financial market data
"""

import requests
import pandas as pd
import json
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import time


class AlphaVantageClient:
    """Client for Alpha Vantage financial data API"""
    
    def __init__(self, api_key: str):
        """
        Initialize Alpha Vantage API client
        
        Args:
            api_key: Your Alpha Vantage API key
        """
        self.api_key = api_key
        self.base_url = "https://www.alphavantage.co/query"
        self.session = requests.Session()
        
    def _make_request(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make API request with error handling
        
        Args:
            params: Query parameters
            
        Returns:
            JSON response data
        """
        params['apikey'] = self.api_key
        
        try:
            response = self.session.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Check for API errors
            if "Error Message" in data:
                raise Exception(f"API Error: {data['Error Message']}")
            if "Note" in data:
                raise Exception(f"API Rate Limit: {data['Note']}")
            if "Information" in data:
                print(f"API Info: {data['Information']}")
                
            return data
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Request failed: {e}")
    
    # ==================== STOCK DATA ====================
    
    def get_quote(self, symbol: str) -> pd.Series:
        """
        Get real-time stock quote
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            Series with quote data
        """
        params = {
            'function': 'GLOBAL_QUOTE',
            'symbol': symbol
        }
        
        data = self._make_request(params)
        
        if 'Global Quote' in data:
            quote = data['Global Quote']
            # Map the actual keys to friendly names
            mapped_quote = {
                'symbol': quote.get('01. symbol', ''),
                'open': quote.get('02. open', ''),
                'high': quote.get('03. high', ''),
                'low': quote.get('04. low', ''),
                'price': quote.get('05. price', ''),
                'volume': quote.get('06. volume', ''),
                'latest trading day': quote.get('07. latest trading day', ''),
                'previous close': quote.get('08. previous close', ''),
                'change': quote.get('09. change', ''),
                'change percent': quote.get('10. change percent', '')
            }
            return pd.Series(mapped_quote)
        else:
            raise Exception(f"No data found for symbol {symbol}")
    
    def get_intraday(self, symbol: str, interval: str = '5min', outputsize: str = 'compact') -> pd.DataFrame:
        """
        Get intraday stock prices
        
        Args:
            symbol: Stock ticker symbol
            interval: Time interval (1min, 5min, 15min, 30min, 60min)
            outputsize: 'compact' (100 data points) or 'full' (full day)
            
        Returns:
            DataFrame with intraday prices
        """
        params = {
            'function': 'TIME_SERIES_INTRADAY',
            'symbol': symbol,
            'interval': interval,
            'outputsize': outputsize
        }
        
        data = self._make_request(params)
        
        # Extract time series data
        time_series_key = f'Time Series ({interval})'
        if time_series_key in data:
            df = pd.DataFrame.from_dict(data[time_series_key], orient='index')
            df.index = pd.to_datetime(df.index)
            df = df.astype(float)
            df.columns = ['open', 'high', 'low', 'close', 'volume']
            return df.sort_index()
        else:
            raise Exception(f"No intraday data found for {symbol}")
    
    def get_daily(self, symbol: str, outputsize: str = 'compact') -> pd.DataFrame:
        """
        Get daily stock prices
        
        Args:
            symbol: Stock ticker symbol
            outputsize: 'compact' (100 days) or 'full' (20+ years)
            
        Returns:
            DataFrame with daily prices
        """
        params = {
            'function': 'TIME_SERIES_DAILY',
            'symbol': symbol,
            'outputsize': outputsize
        }
        
        data = self._make_request(params)
        
        if 'Time Series (Daily)' in data:
            df = pd.DataFrame.from_dict(data['Time Series (Daily)'], orient='index')
            df.index = pd.to_datetime(df.index)
            df = df.astype(float)
            df.columns = ['open', 'high', 'low', 'close', 'volume']
            return df.sort_index()
        else:
            raise Exception(f"No daily data found for {symbol}")
    
    def get_weekly(self, symbol: str) -> pd.DataFrame:
        """
        Get weekly stock prices
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            DataFrame with weekly prices
        """
        params = {
            'function': 'TIME_SERIES_WEEKLY',
            'symbol': symbol
        }
        
        data = self._make_request(params)
        
        if 'Weekly Time Series' in data:
            df = pd.DataFrame.from_dict(data['Weekly Time Series'], orient='index')
            df.index = pd.to_datetime(df.index)
            df = df.astype(float)
            df.columns = ['open', 'high', 'low', 'close', 'volume']
            return df.sort_index()
        else:
            raise Exception(f"No weekly data found for {symbol}")
    
    def get_monthly(self, symbol: str) -> pd.DataFrame:
        """
        Get monthly stock prices
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            DataFrame with monthly prices
        """
        params = {
            'function': 'TIME_SERIES_MONTHLY',
            'symbol': symbol
        }
        
        data = self._make_request(params)
        
        if 'Monthly Time Series' in data:
            df = pd.DataFrame.from_dict(data['Monthly Time Series'], orient='index')
            df.index = pd.to_datetime(df.index)
            df = df.astype(float)
            df.columns = ['open', 'high', 'low', 'close', 'volume']
            return df.sort_index()
        else:
            raise Exception(f"No monthly data found for {symbol}")
    
    # ==================== TECHNICAL INDICATORS ====================
    
    def get_sma(self, symbol: str, interval: str = 'daily', time_period: int = 20, series_type: str = 'close') -> pd.DataFrame:
        """
        Get Simple Moving Average (SMA)
        
        Args:
            symbol: Stock ticker symbol
            interval: Time interval (1min, 5min, 15min, 30min, 60min, daily, weekly, monthly)
            time_period: Number of data points for calculation
            series_type: Price type (close, open, high, low)
            
        Returns:
            DataFrame with SMA values
        """
        params = {
            'function': 'SMA',
            'symbol': symbol,
            'interval': interval,
            'time_period': time_period,
            'series_type': series_type
        }
        
        data = self._make_request(params)
        
        if 'Technical Analysis: SMA' in data:
            df = pd.DataFrame.from_dict(data['Technical Analysis: SMA'], orient='index')
            df.index = pd.to_datetime(df.index)
            df = df.astype(float)
            df.columns = ['SMA']
            return df.sort_index()
        else:
            raise Exception(f"No SMA data found for {symbol}")
    
    def get_ema(self, symbol: str, interval: str = 'daily', time_period: int = 20, series_type: str = 'close') -> pd.DataFrame:
        """
        Get Exponential Moving Average (EMA)
        
        Args:
            symbol: Stock ticker symbol
            interval: Time interval
            time_period: Number of data points
            series_type: Price type
            
        Returns:
            DataFrame with EMA values
        """
        params = {
            'function': 'EMA',
            'symbol': symbol,
            'interval': interval,
            'time_period': time_period,
            'series_type': series_type
        }
        
        data = self._make_request(params)
        
        if 'Technical Analysis: EMA' in data:
            df = pd.DataFrame.from_dict(data['Technical Analysis: EMA'], orient='index')
            df.index = pd.to_datetime(df.index)
            df = df.astype(float)
            df.columns = ['EMA']
            return df.sort_index()
        else:
            raise Exception(f"No EMA data found for {symbol}")
    
    def get_rsi(self, symbol: str, interval: str = 'daily', time_period: int = 14, series_type: str = 'close') -> pd.DataFrame:
        """
        Get Relative Strength Index (RSI)
        
        Args:
            symbol: Stock ticker symbol
            interval: Time interval
            time_period: Number of data points
            series_type: Price type
            
        Returns:
            DataFrame with RSI values
        """
        params = {
            'function': 'RSI',
            'symbol': symbol,
            'interval': interval,
            'time_period': time_period,
            'series_type': series_type
        }
        
        data = self._make_request(params)
        
        if 'Technical Analysis: RSI' in data:
            df = pd.DataFrame.from_dict(data['Technical Analysis: RSI'], orient='index')
            df.index = pd.to_datetime(df.index)
            df = df.astype(float)
            df.columns = ['RSI']
            return df.sort_index()
        else:
            raise Exception(f"No RSI data found for {symbol}")
    
    def get_macd(self, symbol: str, interval: str = 'daily', series_type: str = 'close',
                 fastperiod: int = 12, slowperiod: int = 26, signalperiod: int = 9) -> pd.DataFrame:
        """
        Get MACD (Moving Average Convergence Divergence)
        
        Args:
            symbol: Stock ticker symbol
            interval: Time interval
            series_type: Price type
            fastperiod: Fast EMA period
            slowperiod: Slow EMA period
            signalperiod: Signal EMA period
            
        Returns:
            DataFrame with MACD values
        """
        params = {
            'function': 'MACD',
            'symbol': symbol,
            'interval': interval,
            'series_type': series_type,
            'fastperiod': fastperiod,
            'slowperiod': slowperiod,
            'signalperiod': signalperiod
        }
        
        data = self._make_request(params)
        
        if 'Technical Analysis: MACD' in data:
            df = pd.DataFrame.from_dict(data['Technical Analysis: MACD'], orient='index')
            df.index = pd.to_datetime(df.index)
            df = df.astype(float)
            return df.sort_index()
        else:
            raise Exception(f"No MACD data found for {symbol}")
    
    def get_bbands(self, symbol: str, interval: str = 'daily', time_period: int = 20, 
                   series_type: str = 'close', nbdevup: int = 2, nbdevdn: int = 2) -> pd.DataFrame:
        """
        Get Bollinger Bands
        
        Args:
            symbol: Stock ticker symbol
            interval: Time interval
            time_period: Number of data points
            series_type: Price type
            nbdevup: Upper band standard deviations
            nbdevdn: Lower band standard deviations
            
        Returns:
            DataFrame with Bollinger Bands
        """
        params = {
            'function': 'BBANDS',
            'symbol': symbol,
            'interval': interval,
            'time_period': time_period,
            'series_type': series_type,
            'nbdevup': nbdevup,
            'nbdevdn': nbdevdn
        }
        
        data = self._make_request(params)
        
        if 'Technical Analysis: BBANDS' in data:
            df = pd.DataFrame.from_dict(data['Technical Analysis: BBANDS'], orient='index')
            df.index = pd.to_datetime(df.index)
            df = df.astype(float)
            return df.sort_index()
        else:
            raise Exception(f"No Bollinger Bands data found for {symbol}")
    
    # ==================== FOREX ====================
    
    def get_forex_rate(self, from_currency: str, to_currency: str) -> pd.Series:
        """
        Get real-time forex exchange rate
        
        Args:
            from_currency: From currency code (e.g., 'USD')
            to_currency: To currency code (e.g., 'EUR')
            
        Returns:
            Series with exchange rate data
        """
        params = {
            'function': 'CURRENCY_EXCHANGE_RATE',
            'from_currency': from_currency,
            'to_currency': to_currency
        }
        
        data = self._make_request(params)
        
        if 'Realtime Currency Exchange Rate' in data:
            rate = data['Realtime Currency Exchange Rate']
            # Map the actual keys to friendly names
            mapped_rate = {
                'From_Currency Code': rate.get('1. From_Currency Code', ''),
                'From_Currency Name': rate.get('2. From_Currency Name', ''),
                'To_Currency Code': rate.get('3. To_Currency Code', ''),
                'To_Currency Name': rate.get('4. To_Currency Name', ''),
                'Exchange Rate': rate.get('5. Exchange Rate', ''),
                'Last Refreshed': rate.get('6. Last Refreshed', ''),
                'Time Zone': rate.get('7. Time Zone', ''),
                'Bid Price': rate.get('8. Bid Price', ''),
                'Ask Price': rate.get('9. Ask Price', '')
            }
            return pd.Series(mapped_rate)
        else:
            raise Exception(f"No forex data found for {from_currency}/{to_currency}")
    
    def get_forex_daily(self, from_symbol: str, to_symbol: str, outputsize: str = 'compact') -> pd.DataFrame:
        """
        Get daily forex prices
        
        Args:
            from_symbol: From currency code
            to_symbol: To currency code
            outputsize: 'compact' or 'full'
            
        Returns:
            DataFrame with daily forex prices
        """
        params = {
            'function': 'FX_DAILY',
            'from_symbol': from_symbol,
            'to_symbol': to_symbol,
            'outputsize': outputsize
        }
        
        data = self._make_request(params)
        
        if 'Time Series FX (Daily)' in data:
            df = pd.DataFrame.from_dict(data['Time Series FX (Daily)'], orient='index')
            df.index = pd.to_datetime(df.index)
            df = df.astype(float)
            df.columns = ['open', 'high', 'low', 'close']
            return df.sort_index()
        else:
            raise Exception(f"No daily forex data found")
    
    # ==================== CRYPTOCURRENCY ====================
    
    def get_crypto_rating(self, symbol: str) -> pd.Series:
        """
        Get cryptocurrency rating
        
        Args:
            symbol: Cryptocurrency symbol (e.g., 'BTC')
            
        Returns:
            Series with rating data
        """
        params = {
            'function': 'CRYPTO_RATING',
            'symbol': symbol
        }
        
        data = self._make_request(params)
        
        if 'Crypto Rating (FCAS)' in data:
            return pd.Series(data['Crypto Rating (FCAS)'])
        else:
            raise Exception(f"No rating data found for {symbol}")
    
    def get_crypto_daily(self, symbol: str, market: str = 'USD') -> pd.DataFrame:
        """
        Get daily cryptocurrency prices
        
        Args:
            symbol: Cryptocurrency symbol (e.g., 'BTC')
            market: Market currency (e.g., 'USD')
            
        Returns:
            DataFrame with daily prices
        """
        params = {
            'function': 'DIGITAL_CURRENCY_DAILY',
            'symbol': symbol,
            'market': market
        }
        
        data = self._make_request(params)
        
        if 'Time Series (Digital Currency Daily)' in data:
            ts = data['Time Series (Digital Currency Daily)']
            # Extract relevant columns
            df_data = {}
            for date, values in ts.items():
                df_data[date] = {
                    'open': float(values[f'1a. open ({market})']),
                    'high': float(values[f'2a. high ({market})']),
                    'low': float(values[f'3a. low ({market})']),
                    'close': float(values[f'4a. close ({market})']),
                    'volume': float(values['5. volume']),
                    'market_cap': float(values['6. market cap (USD)'])
                }
            df = pd.DataFrame.from_dict(df_data, orient='index')
            df.index = pd.to_datetime(df.index)
            return df.sort_index()
        else:
            raise Exception(f"No crypto data found for {symbol}")
    
    # ==================== FUNDAMENTAL DATA ====================
    
    def get_company_overview(self, symbol: str) -> pd.Series:
        """
        Get company fundamental data
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            Series with company information
        """
        params = {
            'function': 'OVERVIEW',
            'symbol': symbol
        }
        
        data = self._make_request(params)
        
        if data and 'Symbol' in data:
            return pd.Series(data)
        else:
            raise Exception(f"No company overview found for {symbol}")
    
    def get_earnings(self, symbol: str) -> Dict[str, pd.DataFrame]:
        """
        Get company earnings data
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            Dictionary with annual and quarterly earnings DataFrames
        """
        params = {
            'function': 'EARNINGS',
            'symbol': symbol
        }
        
        data = self._make_request(params)
        
        result = {}
        
        if 'annualEarnings' in data:
            result['annual'] = pd.DataFrame(data['annualEarnings'])
            if not result['annual'].empty:
                result['annual']['fiscalDateEnding'] = pd.to_datetime(result['annual']['fiscalDateEnding'])
                
        if 'quarterlyEarnings' in data:
            result['quarterly'] = pd.DataFrame(data['quarterlyEarnings'])
            if not result['quarterly'].empty:
                result['quarterly']['fiscalDateEnding'] = pd.to_datetime(result['quarterly']['fiscalDateEnding'])
                result['quarterly']['reportedDate'] = pd.to_datetime(result['quarterly']['reportedDate'])
                
        return result
    
    def get_income_statement(self, symbol: str) -> Dict[str, pd.DataFrame]:
        """
        Get income statement data
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            Dictionary with annual and quarterly income statements
        """
        params = {
            'function': 'INCOME_STATEMENT',
            'symbol': symbol
        }
        
        data = self._make_request(params)
        
        result = {}
        
        if 'annualReports' in data:
            result['annual'] = pd.DataFrame(data['annualReports'])
            
        if 'quarterlyReports' in data:
            result['quarterly'] = pd.DataFrame(data['quarterlyReports'])
            
        return result
    
    def get_balance_sheet(self, symbol: str) -> Dict[str, pd.DataFrame]:
        """
        Get balance sheet data
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            Dictionary with annual and quarterly balance sheets
        """
        params = {
            'function': 'BALANCE_SHEET',
            'symbol': symbol
        }
        
        data = self._make_request(params)
        
        result = {}
        
        if 'annualReports' in data:
            result['annual'] = pd.DataFrame(data['annualReports'])
            
        if 'quarterlyReports' in data:
            result['quarterly'] = pd.DataFrame(data['quarterlyReports'])
            
        return result
    
    def get_cash_flow(self, symbol: str) -> Dict[str, pd.DataFrame]:
        """
        Get cash flow statement data
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            Dictionary with annual and quarterly cash flow statements
        """
        params = {
            'function': 'CASH_FLOW',
            'symbol': symbol
        }
        
        data = self._make_request(params)
        
        result = {}
        
        if 'annualReports' in data:
            result['annual'] = pd.DataFrame(data['annualReports'])
            
        if 'quarterlyReports' in data:
            result['quarterly'] = pd.DataFrame(data['quarterlyReports'])
            
        return result
    
    # ==================== ECONOMIC INDICATORS ====================
    
    def get_economic_indicator(self, function: str, interval: str = 'monthly') -> pd.DataFrame:
        """
        Get economic indicator data
        
        Args:
            function: Indicator function (e.g., 'REAL_GDP', 'UNEMPLOYMENT', 'CPI', 'FEDERAL_FUNDS_RATE')
            interval: Data interval
            
        Returns:
            DataFrame with indicator data
        """
        params = {
            'function': function,
            'interval': interval
        }
        
        data = self._make_request(params)
        
        if 'data' in data:
            df = pd.DataFrame(data['data'])
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            df['value'] = pd.to_numeric(df['value'])
            return df.sort_index()
        else:
            raise Exception(f"No data found for {function}")
    
    def search_symbols(self, keywords: str) -> pd.DataFrame:
        """
        Search for symbols
        
        Args:
            keywords: Search keywords
            
        Returns:
            DataFrame with search results
        """
        params = {
            'function': 'SYMBOL_SEARCH',
            'keywords': keywords
        }
        
        data = self._make_request(params)
        
        if 'bestMatches' in data:
            return pd.DataFrame(data['bestMatches'])
        else:
            return pd.DataFrame()


def main():
    """Example usage of Alpha Vantage API client"""
    
    # Your API key
    API_KEY = "H1UKYU1N148IZ94W"
    
    # Initialize client
    client = AlphaVantageClient(API_KEY)
    
    print("Alpha Vantage API Client - Premium Access")
    print("=" * 50)
    
    # Example 1: Get real-time quote
    print("\n1. Getting real-time quote for AAPL...")
    try:
        quote = client.get_quote('AAPL')
        print(f"Apple Inc. (AAPL)")
        print(f"  Price: ${quote['price']}")
        print(f"  Change: {quote['change']} ({quote['change percent']})")
        print(f"  Volume: {quote['volume']}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Example 2: Get daily prices
    print("\n2. Getting daily prices for MSFT...")
    try:
        daily = client.get_daily('MSFT', outputsize='compact')
        print(f"Microsoft (MSFT) - Last 5 days:")
        print(daily.head())
    except Exception as e:
        print(f"Error: {e}")
    
    # Example 3: Get technical indicators
    print("\n3. Getting RSI for SPY...")
    try:
        rsi = client.get_rsi('SPY', interval='daily', time_period=14)
        print(f"SPY RSI (14-day):")
        print(rsi.head())
    except Exception as e:
        print(f"Error: {e}")
    
    # Example 4: Get forex rate
    print("\n4. Getting USD/EUR exchange rate...")
    try:
        forex = client.get_forex_rate('USD', 'EUR')
        print(f"USD/EUR: {forex['Exchange Rate']}")
        print(f"Last Refreshed: {forex['Last Refreshed']}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Example 5: Get company overview
    print("\n5. Getting company overview for GOOGL...")
    try:
        overview = client.get_company_overview('GOOGL')
        print(f"{overview['Name']} ({overview['Symbol']})")
        print(f"  Market Cap: ${int(overview['MarketCapitalization']):,}")
        print(f"  P/E Ratio: {overview['PERatio']}")
        print(f"  52 Week High: ${overview['52WeekHigh']}")
        print(f"  52 Week Low: ${overview['52WeekLow']}")
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n" + "=" * 50)
    print("✓ Alpha Vantage API client ready!")
    print("Premium features available with your API key.")


if __name__ == "__main__":
    main()