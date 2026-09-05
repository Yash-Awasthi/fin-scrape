"""
Alpha Vantage Market Dashboard with Visualizations
"""

from alpha_vantage_api import AlphaVantageClient
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import numpy as np

# Your Premium API Key
API_KEY = "H1UKYU1N148IZ94W"

class MarketDashboard:
    """Create market analysis visualizations"""
    
    def __init__(self, api_key: str):
        self.client = AlphaVantageClient(api_key)
        
    def plot_price_with_indicators(self, symbol: str, days: int = 100):
        """
        Plot stock price with SMA and Bollinger Bands
        
        Args:
            symbol: Stock ticker
            days: Number of days to display
        """
        print(f"Generating technical analysis chart for {symbol}...")
        
        # Get daily prices
        daily = self.client.get_daily(symbol, outputsize='full')
        daily = daily.head(days)
        
        # Get technical indicators
        sma20 = self.client.get_sma(symbol, interval='daily', time_period=20)
        sma50 = self.client.get_sma(symbol, interval='daily', time_period=50)
        bbands = self.client.get_bbands(symbol, interval='daily', time_period=20)
        
        # Create figure with subplots
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), height_ratios=[3, 1])
        
        # Plot prices and indicators
        ax1.plot(daily.index, daily['close'], label='Close Price', color='black', linewidth=2)
        ax1.plot(sma20.index[:days], sma20['SMA'][:days], label='SMA 20', color='blue', alpha=0.7)
        ax1.plot(sma50.index[:days], sma50['SMA'][:days], label='SMA 50', color='red', alpha=0.7)
        
        # Add Bollinger Bands
        ax1.fill_between(bbands.index[:days], 
                        bbands['Real Upper Band'][:days], 
                        bbands['Real Lower Band'][:days], 
                        alpha=0.2, color='gray', label='Bollinger Bands')
        
        ax1.set_title(f'{symbol} - Price Analysis', fontsize=14, fontweight='bold')
        ax1.set_ylabel('Price ($)', fontsize=11)
        ax1.legend(loc='best')
        ax1.grid(True, alpha=0.3)
        
        # Format x-axis
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax1.xaxis.set_major_locator(mdates.DayLocator(interval=20))
        plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)
        
        # Plot volume
        ax2.bar(daily.index, daily['volume'], color='steelblue', alpha=0.7)
        ax2.set_ylabel('Volume', fontsize=11)
        ax2.set_xlabel('Date', fontsize=11)
        ax2.grid(True, alpha=0.3)
        
        # Format x-axis
        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax2.xaxis.set_major_locator(mdates.DayLocator(interval=20))
        plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)
        
        plt.tight_layout()
        plt.savefig(f'{symbol}_technical_analysis.png', dpi=150, bbox_inches='tight')
        plt.show()
        
        print(f"✓ Chart saved as {symbol}_technical_analysis.png")
    
    def plot_rsi_macd(self, symbol: str, days: int = 100):
        """
        Plot RSI and MACD indicators
        
        Args:
            symbol: Stock ticker
            days: Number of days to display
        """
        print(f"Generating momentum indicators for {symbol}...")
        
        # Get data
        daily = self.client.get_daily(symbol, outputsize='full')
        daily = daily.head(days)
        rsi = self.client.get_rsi(symbol, interval='daily', time_period=14)
        macd = self.client.get_macd(symbol, interval='daily')
        
        # Create figure
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 10), height_ratios=[2, 1, 1])
        
        # Plot price
        ax1.plot(daily.index, daily['close'], color='black', linewidth=2)
        ax1.set_title(f'{symbol} - Momentum Indicators', fontsize=14, fontweight='bold')
        ax1.set_ylabel('Price ($)', fontsize=11)
        ax1.grid(True, alpha=0.3)
        
        # Plot RSI
        ax2.plot(rsi.index[:days], rsi['RSI'][:days], color='purple', linewidth=2)
        ax2.axhline(y=70, color='r', linestyle='--', alpha=0.5, label='Overbought')
        ax2.axhline(y=30, color='g', linestyle='--', alpha=0.5, label='Oversold')
        ax2.fill_between(rsi.index[:days], 30, 70, alpha=0.1, color='gray')
        ax2.set_ylabel('RSI', fontsize=11)
        ax2.set_ylim(0, 100)
        ax2.legend(loc='best')
        ax2.grid(True, alpha=0.3)
        
        # Plot MACD
        ax3.plot(macd.index[:days], macd['MACD'][:days], label='MACD', color='blue')
        ax3.plot(macd.index[:days], macd['MACD_Signal'][:days], label='Signal', color='red')
        ax3.bar(macd.index[:days], macd['MACD_Hist'][:days], label='Histogram', color='gray', alpha=0.3)
        ax3.set_ylabel('MACD', fontsize=11)
        ax3.set_xlabel('Date', fontsize=11)
        ax3.legend(loc='best')
        ax3.grid(True, alpha=0.3)
        
        # Format x-axes
        for ax in [ax1, ax2, ax3]:
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            ax.xaxis.set_major_locator(mdates.DayLocator(interval=20))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
        
        plt.tight_layout()
        plt.savefig(f'{symbol}_momentum_indicators.png', dpi=150, bbox_inches='tight')
        plt.show()
        
        print(f"✓ Chart saved as {symbol}_momentum_indicators.png")
    
    def compare_stocks(self, symbols: list, days: int = 30):
        """
        Compare performance of multiple stocks
        
        Args:
            symbols: List of stock tickers
            days: Number of days to compare
        """
        print(f"Comparing performance: {', '.join(symbols)}...")
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
        
        for symbol in symbols:
            try:
                # Get daily data
                daily = self.client.get_daily(symbol, outputsize='compact')
                daily = daily.head(days)
                
                # Calculate percentage change
                base_price = daily['close'].iloc[-1]
                pct_change = ((daily['close'] / base_price) - 1) * 100
                
                # Plot percentage change
                ax1.plot(daily.index, pct_change, label=symbol, linewidth=2)
                
                # Plot volume
                ax2.plot(daily.index, daily['volume'] / 1e6, label=symbol, alpha=0.7)
                
            except Exception as e:
                print(f"  ✗ Error loading {symbol}: {e}")
        
        # Format first subplot
        ax1.set_title('Stock Performance Comparison (% Change)', fontsize=14, fontweight='bold')
        ax1.set_ylabel('Change (%)', fontsize=11)
        ax1.axhline(y=0, color='black', linestyle='-', alpha=0.3)
        ax1.legend(loc='best')
        ax1.grid(True, alpha=0.3)
        
        # Format second subplot
        ax2.set_title('Volume Comparison (Millions)', fontsize=12)
        ax2.set_ylabel('Volume (M)', fontsize=11)
        ax2.set_xlabel('Date', fontsize=11)
        ax2.legend(loc='best')
        ax2.grid(True, alpha=0.3)
        
        # Format x-axes
        for ax in [ax1, ax2]:
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
            ax.xaxis.set_major_locator(mdates.DayLocator(interval=5))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
        
        plt.tight_layout()
        plt.savefig('stock_comparison.png', dpi=150, bbox_inches='tight')
        plt.show()
        
        print("✓ Comparison chart saved as stock_comparison.png")
    
    def sector_performance(self, sector_etfs: dict):
        """
        Compare sector performance using ETFs
        
        Args:
            sector_etfs: Dictionary of sector names and ETF symbols
        """
        print("Analyzing sector performance...")
        
        performances = []
        
        for sector, etf in sector_etfs.items():
            try:
                daily = self.client.get_daily(etf, outputsize='compact')
                
                # Calculate performance metrics
                latest = daily.iloc[0]['close']
                week_ago = daily.iloc[min(5, len(daily)-1)]['close']
                month_ago = daily.iloc[min(21, len(daily)-1)]['close']
                
                week_change = ((latest / week_ago) - 1) * 100
                month_change = ((latest / month_ago) - 1) * 100
                
                performances.append({
                    'Sector': sector,
                    'ETF': etf,
                    'Price': latest,
                    '1W %': week_change,
                    '1M %': month_change
                })
                
            except Exception as e:
                print(f"  ✗ Error loading {etf}: {e}")
        
        if performances:
            df = pd.DataFrame(performances)
            df = df.sort_values('1M %', ascending=False)
            
            # Create bar chart
            fig, ax = plt.subplots(figsize=(10, 6))
            
            x = np.arange(len(df))
            width = 0.35
            
            bars1 = ax.bar(x - width/2, df['1W %'], width, label='1 Week', color='steelblue')
            bars2 = ax.bar(x + width/2, df['1M %'], width, label='1 Month', color='darkgreen')
            
            # Add value labels on bars
            for bars in [bars1, bars2]:
                for bar in bars:
                    height = bar.get_height()
                    ax.annotate(f'{height:.1f}%',
                              xy=(bar.get_x() + bar.get_width() / 2, height),
                              xytext=(0, 3 if height > 0 else -15),
                              textcoords="offset points",
                              ha='center', va='bottom' if height > 0 else 'top',
                              fontsize=9)
            
            ax.set_xlabel('Sector', fontsize=11)
            ax.set_ylabel('Performance (%)', fontsize=11)
            ax.set_title('Sector Performance Analysis', fontsize=14, fontweight='bold')
            ax.set_xticks(x)
            ax.set_xticklabels(df['Sector'], rotation=45, ha='right')
            ax.legend()
            ax.grid(True, alpha=0.3, axis='y')
            ax.axhline(y=0, color='black', linestyle='-', alpha=0.3)
            
            plt.tight_layout()
            plt.savefig('sector_performance.png', dpi=150, bbox_inches='tight')
            plt.show()
            
            print("\nSector Performance Summary:")
            print(df.to_string(index=False))
            print("\n✓ Chart saved as sector_performance.png")


def main():
    """Run market dashboard examples"""
    
    dashboard = MarketDashboard(API_KEY)
    
    print("\n" + "=" * 60)
    print("ALPHA VANTAGE MARKET DASHBOARD")
    print("=" * 60)
    
    # Example 1: Technical analysis chart
    print("\n1. TECHNICAL ANALYSIS VISUALIZATION")
    print("-" * 40)
    try:
        dashboard.plot_price_with_indicators('AAPL', days=60)
    except Exception as e:
        print(f"Error: {e}")
    
    # Example 2: Momentum indicators
    print("\n2. MOMENTUM INDICATORS")
    print("-" * 40)
    try:
        dashboard.plot_rsi_macd('TSLA', days=60)
    except Exception as e:
        print(f"Error: {e}")
    
    # Example 3: Stock comparison
    print("\n3. STOCK COMPARISON")
    print("-" * 40)
    try:
        tech_stocks = ['AAPL', 'MSFT', 'GOOGL', 'META']
        dashboard.compare_stocks(tech_stocks, days=30)
    except Exception as e:
        print(f"Error: {e}")
    
    # Example 4: Sector performance
    print("\n4. SECTOR PERFORMANCE")
    print("-" * 40)
    try:
        sectors = {
            'Technology': 'XLK',
            'Healthcare': 'XLV',
            'Financials': 'XLF',
            'Energy': 'XLE',
            'Consumer': 'XLY',
            'Utilities': 'XLU'
        }
        dashboard.sector_performance(sectors)
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n" + "=" * 60)
    print("✓ DASHBOARD ANALYSIS COMPLETE")
    print("All visualizations have been saved as PNG files")


if __name__ == "__main__":
    main()