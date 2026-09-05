#!/usr/bin/env python3
"""
Quick Market Check - Get current market snapshot
"""

from alpha_vantage_api import AlphaVantageClient
import pandas as pd
from datetime import datetime

# Your Premium API Key
API_KEY = "H1UKYU1N148IZ94W"

def market_snapshot():
    """Get quick market overview"""
    
    client = AlphaVantageClient(API_KEY)
    
    print("\n" + "=" * 60)
    print(f"MARKET SNAPSHOT - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)
    
    # Major indices (using ETFs as proxies)
    indices = {
        'S&P 500': 'SPY',
        'NASDAQ': 'QQQ',
        'DOW': 'DIA',
        'Russell 2000': 'IWM',
        'VIX': 'VXX'
    }
    
    print("\n📊 MAJOR INDICES")
    print("-" * 40)
    for name, symbol in indices.items():
        try:
            quote = client.get_quote(symbol)
            price = float(quote['price'])
            change = float(quote['change'])
            change_pct = quote['change percent']
            
            # Format with color indicators
            indicator = "🟢" if change >= 0 else "🔴"
            sign = "+" if change >= 0 else ""
            
            print(f"{indicator} {name:15} ${price:8.2f}  {sign}{change:7.2f} ({change_pct})")
        except:
            print(f"⚪ {name:15} [Data unavailable]")
    
    # Top tech stocks
    tech_stocks = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA', 'TSLA']
    
    print("\n💻 TECH LEADERS")
    print("-" * 40)
    for symbol in tech_stocks:
        try:
            quote = client.get_quote(symbol)
            price = float(quote['price'])
            change = float(quote['change'])
            change_pct = quote['change percent']
            
            indicator = "🟢" if change >= 0 else "🔴"
            sign = "+" if change >= 0 else ""
            
            print(f"{indicator} {symbol:6} ${price:8.2f}  {sign}{change:7.2f} ({change_pct})")
        except:
            print(f"⚪ {symbol:6} [Data unavailable]")
    
    # Commodities & Crypto
    print("\n🏦 COMMODITIES & CRYPTO")
    print("-" * 40)
    
    # Gold, Oil, Bitcoin ETFs
    commodities = {
        'Gold': 'GLD',
        'Oil': 'USO',
        'Bitcoin': 'BITO',
        'Silver': 'SLV'
    }
    
    for name, symbol in commodities.items():
        try:
            quote = client.get_quote(symbol)
            price = float(quote['price'])
            change = float(quote['change'])
            change_pct = quote['change percent']
            
            indicator = "🟢" if change >= 0 else "🔴"
            sign = "+" if change >= 0 else ""
            
            print(f"{indicator} {name:8} ${price:8.2f}  {sign}{change:7.2f} ({change_pct})")
        except:
            print(f"⚪ {name:8} [Data unavailable]")
    
    # Forex rates
    print("\n💱 FOREX RATES")
    print("-" * 40)
    
    forex_pairs = [
        ('USD', 'EUR'),
        ('USD', 'GBP'),
        ('USD', 'JPY'),
        ('USD', 'CHF')
    ]
    
    for from_curr, to_curr in forex_pairs:
        try:
            forex = client.get_forex_rate(from_curr, to_curr)
            rate = float(forex['Exchange Rate'])
            print(f"  {from_curr}/{to_curr}: {rate:.4f}")
        except:
            print(f"  {from_curr}/{to_curr}: [Unavailable]")
    
    print("\n" + "=" * 60)
    print("Data provided by Alpha Vantage Premium API")
    print("=" * 60)

if __name__ == "__main__":
    market_snapshot()