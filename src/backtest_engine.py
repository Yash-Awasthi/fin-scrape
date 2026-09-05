"""
Backtesting Engine — test trading strategies against historical data.

Extracted from ai-hedge-fund: provides a framework for backtesting trading
strategies with performance metrics, position tracking, and risk analysis.
"""

from dataclasses import dataclass, field
from typing import Optional, Callable
from datetime import datetime, timedelta


@dataclass
class Trade:
    """A single trade."""
    ticker: str
    side: str  # "buy" or "sell"
    quantity: float
    price: float
    timestamp: datetime
    signal: str
    rationale: str


@dataclass
class Position:
    """Current position in a ticker."""
    ticker: str
    quantity: float
    avg_entry_price: float
    current_price: float
    
    @property
    def market_value(self) -> float:
        return self.quantity * self.current_price
    
    @property
    def unrealized_pnl(self) -> float:
        return self.quantity * (self.current_price - self.avg_entry_price)
    
    @property
    def unrealized_pnl_pct(self) -> float:
        if self.avg_entry_price == 0:
            return 0.0
        return (self.current_price - self.avg_entry_price) / self.avg_entry_price


@dataclass
class BacktestResult:
    """Results of a backtest run."""
    strategy_name: str
    start_date: datetime
    end_date: datetime
    initial_capital: float
    final_capital: float
    total_return: float
    annualized_return: float
    sharpe_ratio: float
    max_drawdown: float
    max_drawdown_duration: timedelta
    win_rate: float
    profit_factor: float
    total_trades: int
    avg_trade_return: float
    trades: list
    equity_curve: list
    positions_history: list


class BacktestEngine:
    """
    Backtesting engine for trading strategies.
    
    Usage:
        engine = BacktestEngine(initial_capital=100000)
        
        def my_strategy(data):
            if data["rsi"] < 30:
                return {"action": "buy", "ticker": "AAPL", "quantity": 10}
            return None
        
        result = engine.run(my_strategy, historical_data)
        print(f"Total return: {result.total_return:.2%}")
    """
    
    def __init__(self, initial_capital: float = 100000, commission: float = 0.001):
        self.initial_capital = initial_capital
        self.commission = commission
        self.capital = initial_capital
        self.positions: dict = {}
        self.trades: list = []
        self.equity_curve: list = []
    
    def run(self, strategy_fn: Callable, data: list, ticker: str = "AAPL") -> BacktestResult:
        """Run backtest with given strategy and data."""
        self.capital = self.initial_capital
        self.positions = {}
        self.trades = []
        self.equity_curve = []
        
        start_date = data[0]["date"] if data else datetime.now()
        end_date = data[-1]["date"] if data else datetime.now()
        
        for i, bar in enumerate(data):
            # Get strategy signal
            signal = strategy_fn(bar)
            
            if signal:
                self._execute_signal(signal, bar)
            
            # Update equity curve
            portfolio_value = self._calculate_portfolio_value(bar)
            self.equity_curve.append({
                "date": bar["date"],
                "value": portfolio_value,
            })
        
        # Calculate metrics
        return self._calculate_metrics(start_date, end_date)
    
    def _execute_signal(self, signal: dict, bar: dict):
        """Execute a trading signal."""
        action = signal.get("action")
        ticker = signal.get("ticker", "AAPL")
        quantity = signal.get("quantity", 0)
        price = bar.get("close", 0)
        
        if action == "buy" and quantity > 0:
            cost = quantity * price * (1 + self.commission)
            if cost <= self.capital:
                self.capital -= cost
                if ticker in self.positions:
                    pos = self.positions[ticker]
                    total_qty = pos.quantity + quantity
                    pos.avg_entry_price = (pos.avg_entry_price * pos.quantity + price * quantity) / total_qty
                    pos.quantity = total_qty
                else:
                    self.positions[ticker] = Position(
                        ticker=ticker,
                        quantity=quantity,
                        avg_entry_price=price,
                        current_price=price,
                    )
                
                self.trades.append(Trade(
                    ticker=ticker,
                    side="buy",
                    quantity=quantity,
                    price=price,
                    timestamp=bar["date"],
                    signal=signal.get("signal", ""),
                    rationale=signal.get("rationale", ""),
                ))
        
        elif action == "sell" and ticker in self.positions:
            pos = self.positions[ticker]
            sell_qty = min(quantity, pos.quantity)
            proceeds = sell_qty * price * (1 - self.commission)
            self.capital += proceeds
            pos.quantity -= sell_qty
            
            if pos.quantity <= 0:
                del self.positions[ticker]
            
            self.trades.append(Trade(
                ticker=ticker,
                side="sell",
                quantity=sell_qty,
                price=price,
                timestamp=bar["date"],
                signal=signal.get("signal", ""),
                rationale=signal.get("rationale", ""),
            ))
    
    def _calculate_portfolio_value(self, bar: dict) -> float:
        """Calculate total portfolio value."""
        value = self.capital
        for ticker, pos in self.positions.items():
            pos.current_price = bar.get("close", pos.current_price)
            value += pos.market_value
        return value
    
    def _calculate_metrics(self, start_date: datetime, end_date: datetime) -> BacktestResult:
        """Calculate backtest performance metrics."""
        if not self.equity_curve:
            return BacktestResult(
                strategy_name="backtest",
                start_date=start_date,
                end_date=end_date,
                initial_capital=self.initial_capital,
                final_capital=self.capital,
                total_return=0.0,
                annualized_return=0.0,
                sharpe_ratio=0.0,
                max_drawdown=0.0,
                max_drawdown_duration=timedelta(0),
                win_rate=0.0,
                profit_factor=0.0,
                total_trades=0,
                avg_trade_return=0.0,
                trades=[],
                equity_curve=[],
                positions_history=[],
            )
        
        final_value = self.equity_curve[-1]["value"]
        total_return = (final_value - self.initial_capital) / self.initial_capital
        
        # Calculate max drawdown
        peak = self.initial_capital
        max_drawdown = 0
        max_dd_duration = timedelta(0)
        dd_start = None
        
        for point in self.equity_curve:
            if point["value"] > peak:
                peak = point["value"]
                dd_start = point["date"]
            
            drawdown = (peak - point["value"]) / peak
            if drawdown > max_drawdown:
                max_drawdown = drawdown
                if dd_start:
                    max_dd_duration = point["date"] - dd_start
        
        # Win rate
        wins = sum(1 for t in self.trades if t.side == "sell")
        total_trades = len(self.trades)
        win_rate = wins / total_trades if total_trades > 0 else 0
        
        # Sharpe ratio (simplified)
        if len(self.equity_curve) > 1:
            returns = []
            for i in range(1, len(self.equity_curve)):
                r = (self.equity_curve[i]["value"] - self.equity_curve[i-1]["value"]) / self.equity_curve[i-1]["value"]
                returns.append(r)
            
            avg_return = sum(returns) / len(returns) if returns else 0
            std_return = (sum((r - avg_return)**2 for r in returns) / len(returns))**0.5 if returns else 1
            sharpe = (avg_return / std_return) * (252**0.5) if std_return > 0 else 0
        else:
            sharpe = 0
        
        # Annualized return
        days = (end_date - start_date).days or 1
        annualized = (1 + total_return) ** (365 / days) - 1
        
        return BacktestResult(
            strategy_name="backtest",
            start_date=start_date,
            end_date=end_date,
            initial_capital=self.initial_capital,
            final_capital=round(final_value, 2),
            total_return=round(total_return, 4),
            annualized_return=round(annualized, 4),
            sharpe_ratio=round(sharpe, 4),
            max_drawdown=round(max_drawdown, 4),
            max_drawdown_duration=max_dd_duration,
            win_rate=round(win_rate, 4),
            profit_factor=0.0,
            total_trades=total_trades,
            avg_trade_return=round(total_return / total_trades, 4) if total_trades > 0 else 0,
            trades=self.trades,
            equity_curve=self.equity_curve,
            positions_history=[],
        )
