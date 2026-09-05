"""WorldFin — Free Geopolitical Market Intelligence.
Standalone modules: sentiment_analyzer, geopolitical_risk, trading_agents, backtest_engine, route_risk_monitor.
"""
__version__ = "1.0.0"

# Trading pipeline (multi-agent analysis)
from finscrape.trading.pipeline import run_analysis as run_trading_analysis
from finscrape.trading.state import TradeState
