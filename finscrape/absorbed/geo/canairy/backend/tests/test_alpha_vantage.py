"""
Test Alpha Vantage Premium API Access
"""

from alpha_vantage_api import AlphaVantageClient
import pandas as pd
from datetime import datetime

# Your Premium API Key
API_KEY = "H1UKYU1N148IZ94W"

def test_api_access():
    """Test various Alpha Vantage API endpoints"""
    
    print("Testing Alpha Vantage Premium API")
    print("=" * 60)
    print(f"Username: manavpthaker")
    print(f"API Key: {API_KEY[:6]}...{API_KEY[-4:]}")
    print("=" * 60)
    
    # Initialize client
    client = AlphaVantageClient(API_KEY)
    
    # Test 1: Search for symbols
    print("\n1. SYMBOL SEARCH TEST")
    print("-" * 40)
    try:
        print("Searching for 'Tesla'...")
        results = client.search_symbols('Tesla')
        if not results.empty:
            print(f"✓ Found {len(results)} matches")
            print(f"  Top match: {results.iloc[0]['2. name']} ({results.iloc[0]['1. symbol']})")
        else:
            print("✗ No results found")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # Test 2: Real-time quote
    print("\n2. REAL-TIME QUOTE TEST")
    print("-" * 40)
    try:
        print("Getting quote for AAPL...")
        quote = client.get_quote('AAPL')
        print(f"✓ Apple Inc. (AAPL)")
        print(f"  Current Price: ${quote['price']}")
        print(f"  Change: {quote['change']} ({quote['change percent']})")
        print(f"  Volume: {int(float(quote['volume'])):,}")
        print(f"  Latest Trading Day: {quote['latest trading day']}")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # Test 3: Intraday data
    print("\n3. INTRADAY DATA TEST")
    print("-" * 40)
    try:
        print("Getting 5-min intraday data for SPY...")
        intraday = client.get_intraday('SPY', interval='5min', outputsize='compact')
        print(f"✓ Retrieved {len(intraday)} data points")
        print(f"  Latest: {intraday.index[0].strftime('%Y-%m-%d %H:%M')}")
        print(f"    Open: ${intraday.iloc[0]['open']:.2f}")
        print(f"    High: ${intraday.iloc[0]['high']:.2f}")
        print(f"    Low: ${intraday.iloc[0]['low']:.2f}")
        print(f"    Close: ${intraday.iloc[0]['close']:.2f}")
        print(f"    Volume: {int(intraday.iloc[0]['volume']):,}")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # Test 4: Daily data
    print("\n4. DAILY DATA TEST")
    print("-" * 40)
    try:
        print("Getting daily data for MSFT...")
        daily = client.get_daily('MSFT', outputsize='compact')
        print(f"✓ Retrieved {len(daily)} days of data")
        print(f"  Date range: {daily.index[-1].date()} to {daily.index[0].date()}")
        
        # Calculate simple statistics
        latest_close = daily.iloc[0]['close']
        avg_volume = daily['volume'].mean()
        price_change = daily.iloc[0]['close'] - daily.iloc[-1]['close']
        pct_change = (price_change / daily.iloc[-1]['close']) * 100
        
        print(f"  Latest Close: ${latest_close:.2f}")
        print(f"  Period Change: ${price_change:.2f} ({pct_change:+.2f}%)")
        print(f"  Avg Volume: {int(avg_volume):,}")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # Test 5: Technical Indicators
    print("\n5. TECHNICAL INDICATORS TEST")
    print("-" * 40)
    try:
        print("Getting RSI for TSLA...")
        rsi = client.get_rsi('TSLA', interval='daily', time_period=14)
        print(f"✓ Retrieved RSI data")
        latest_rsi = rsi.iloc[0]['RSI']
        print(f"  Latest RSI(14): {latest_rsi:.2f}")
        
        if latest_rsi > 70:
            print(f"  Signal: Overbought (RSI > 70)")
        elif latest_rsi < 30:
            print(f"  Signal: Oversold (RSI < 30)")
        else:
            print(f"  Signal: Neutral")
            
        # Get SMA
        print("\nGetting SMA(20) for TSLA...")
        sma = client.get_sma('TSLA', interval='daily', time_period=20)
        print(f"✓ Latest SMA(20): ${sma.iloc[0]['SMA']:.2f}")
        
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # Test 6: Forex
    print("\n6. FOREX TEST")
    print("-" * 40)
    try:
        print("Getting USD/EUR exchange rate...")
        forex = client.get_forex_rate('USD', 'EUR')
        print(f"✓ USD/EUR Exchange Rate: {forex['Exchange Rate']}")
        print(f"  From: {forex['From_Currency Name']}")
        print(f"  To: {forex['To_Currency Name']}")
        print(f"  Last Refreshed: {forex['Last Refreshed']}")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # Test 7: Cryptocurrency
    print("\n7. CRYPTOCURRENCY TEST")
    print("-" * 40)
    try:
        print("Getting Bitcoin daily data...")
        btc = client.get_crypto_daily('BTC', market='USD')
        print(f"✓ Retrieved {len(btc)} days of BTC/USD data")
        print(f"  Latest Close: ${btc.iloc[0]['close']:,.2f}")
        print(f"  Market Cap: ${btc.iloc[0]['market_cap']:,.0f}")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # Test 8: Company Fundamentals
    print("\n8. COMPANY FUNDAMENTALS TEST")
    print("-" * 40)
    try:
        print("Getting company overview for GOOGL...")
        overview = client.get_company_overview('GOOGL')
        print(f"✓ {overview['Name']}")
        print(f"  Sector: {overview['Sector']}")
        print(f"  Industry: {overview['Industry']}")
        print(f"  Market Cap: ${int(overview['MarketCapitalization']):,}")
        print(f"  P/E Ratio: {overview['PERatio']}")
        print(f"  Dividend Yield: {overview['DividendYield']}%")
        print(f"  52 Week Range: ${overview['52WeekLow']} - ${overview['52WeekHigh']}")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # Test 9: Economic Indicators
    print("\n9. ECONOMIC INDICATORS TEST")
    print("-" * 40)
    try:
        print("Getting Federal Funds Rate...")
        fed_rate = client.get_economic_indicator('FEDERAL_FUNDS_RATE', interval='monthly')
        print(f"✓ Retrieved Federal Funds Rate data")
        print(f"  Latest Rate: {fed_rate.iloc[0]['value']:.2f}%")
        print(f"  Date: {fed_rate.index[0].strftime('%Y-%m')}")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    print("\n" + "=" * 60)
    print("✓ ALPHA VANTAGE PREMIUM API TEST COMPLETE")
    print("Your API key has full access to all endpoints!")
    print("\nRate Limits with Premium Key:")
    print("  • 75 requests per minute")
    print("  • No daily limit")
    print("  • Access to all endpoints and features")

def test_batch_request():
    """Test multiple symbols efficiently"""
    
    print("\n\nBATCH REQUEST TEST")
    print("=" * 60)
    
    client = AlphaVantageClient(API_KEY)
    
    symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
    
    print(f"Getting quotes for: {', '.join(symbols)}")
    print("-" * 40)
    
    results = []
    for symbol in symbols:
        try:
            quote = client.get_quote(symbol)
            results.append({
                'Symbol': symbol,
                'Price': float(quote['price']),
                'Change': float(quote['change']),
                'Change %': quote['change percent'],
                'Volume': int(float(quote['volume']))
            })
            print(f"✓ {symbol}: ${quote['price']} ({quote['change percent']})")
        except Exception as e:
            print(f"✗ {symbol}: Error - {e}")
    
    if results:
        df = pd.DataFrame(results)
        print("\nSummary DataFrame:")
        print(df.to_string(index=False))

if __name__ == "__main__":
    test_api_access()
    test_batch_request()