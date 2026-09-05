"""
Market volatility collector for 10Y Treasury intraday swings.
Tracks basis point movements on data release days as critical indicator.
"""

import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from .base import BaseCollector


class MarketVolatilityCollector(BaseCollector):
    """Collects 10Y Treasury intraday volatility data."""
    
    def __init__(self, config):
        super().__init__(config)
        self._name = "MarketVolatility"
        self.ticker = "^TNX"  # 10-Year Treasury Yield
        self.is_critical = True  # This is a critical indicator
        
    def collect(self) -> Optional[Dict[str, Any]]:
        """
        Collect 10Y Treasury intraday swing data.
        
        Returns:
            Dict with basis points swing or None if collection fails
        """
        try:
            swing_bp = self._fetch_intraday_swing()
            
            if swing_bp is None:
                return None
            
            return {
                'value': swing_bp,
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'collector': self.name,
                'metadata': {
                    'unit': 'basis_points',
                    'source': 'Yahoo_Finance',
                    'ticker': self.ticker,
                    'critical': True,
                    'description': f'{swing_bp} bp intraday swing',
                    'data_day': self._is_data_day()
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to collect market volatility: {e}")
            return None
    
    def _fetch_intraday_swing(self) -> Optional[float]:
        """Fetch intraday high-low swing for 10Y Treasury."""
        try:
            # Get today's data with 1-minute intervals
            ticker = yf.Ticker(self.ticker)
            
            # Get intraday data for today
            today_data = ticker.history(period="1d", interval="1m")
            
            if today_data.empty:
                self.logger.warning("No intraday data available yet")
                # Fall back to daily data
                daily_data = ticker.history(period="5d")
                if not daily_data.empty:
                    latest = daily_data.iloc[-1]
                    high = latest['High']
                    low = latest['Low']
                else:
                    return None
            else:
                high = today_data['High'].max()
                low = today_data['Low'].min()
            
            # Calculate swing in basis points (TNX is already in percentage)
            swing = (high - low) * 100  # Convert to basis points
            
            self.logger.info(f"10Y Treasury: High={high:.3f}%, Low={low:.3f}%, "
                           f"Swing={swing:.1f} bp")
            
            return round(swing, 1)
            
        except Exception as e:
            self.logger.error(f"Failed to fetch market data: {e}")
            return None
    
    def _is_data_day(self) -> bool:
        """
        Check if today is a major economic data release day.
        Major releases: CPI, PPI, NFP, FOMC days
        """
        # This would ideally check an economic calendar API
        # For now, we'll consider Tuesdays-Thursdays as potential data days
        weekday = datetime.now().weekday()
        return weekday in [1, 2, 3]  # Tuesday, Wednesday, Thursday
    
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate market volatility data."""
        if not data:
            return False
        return 'value' in data and isinstance(data['value'], (int, float))