"""
Backtesting Engine
Extracted from freqtrade's backtesting framework

Features:
- Historical data replay
- Signal generation and evaluation
- Performance metrics calculation
- Trade simulation
- Risk management
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Callable
from enum import Enum
import time
import math


class OrderSide(Enum):
    BUY = "buy"
    SELL = "sell"


class OrderStatus(Enum):
    PENDING = "pending"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


@dataclass
class Candle:
    """OHLCV candle data"""
    timestamp: float
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass
class Signal:
    """Trading signal"""
    timestamp: float
    side: OrderSide
    price: float
    strength: float  # 0-1
    metadata: Dict[str, Any]


@dataclass
class Order:
    """Trade order"""
    id: str
    side: OrderSide
    price: float
    amount: float
    status: OrderStatus
    timestamp: float
    filled_at: Optional[float]
    filled_price: Optional[float]


@dataclass
class Position:
    """Open position"""
    id: str
    side: OrderSide
    entry_price: float
    amount: float
    entry_time: float
    stop_loss: Optional[float]
    take_profit: Optional[float]
    metadata: Dict[str, Any]


@dataclass
class Trade:
    """Completed trade"""
    id: str
    side: OrderSide
    entry_price: float
    exit_price: float
    amount: float
    entry_time: float
    exit_time: float
    profit: float
    profit_pct: float
    fees: float
    metadata: Dict[str, Any]


@dataclass
class BacktestResult:
    """Backtest results"""
    trades: List[Trade]
    equity_curve: List[float]
    metrics: Dict[str, Any]
    drawdown: List[float]
    timestamps: List[float]


class BacktestingEngine:
    """
    Backtesting engine extracted from freqtrade
    """
    
    def __init__(self, initial_capital: float = 10000.0):
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.positions: List[Position] = []
        self.trades: List[Trade] = []
        self.equity_curve: List[float] = []
        self.order_counter = 0
    
    def run_backtest(
        self,
        candles: List[Candle],
        strategy: Callable[[List[Candle], int], Optional[Signal]],
        config: Dict[str, Any] = None
    ) -> BacktestResult:
        """
        Run backtest on historical data
        
        Args:
            candles: Historical OHLCV data
            strategy: Signal generation function
            config: Backtest configuration
        
        Returns:
            BacktestResult with trades and metrics
        """
        if config is None:
            config = {}
        
        lookback = config.get('lookback', 50)
        
        for i in range(lookback, len(candles)):
            current_candle = candles[i]
            historical_candles = candles[i-lookback:i]
            
            # Generate signal
            signal = strategy(historical_candles, i)
            
            # Execute signal
            if signal:
                self._execute_signal(signal, current_candle)
            
            # Update equity curve
            equity = self._calculate_equity(current_candle.close)
            self.equity_curve.append(equity)
            
            # Check stop loss and take profit
            self._check_exits(current_candle)
        
        # Close any remaining positions
        self._close_all_positions(candles[-1])
        
        # Calculate metrics
        metrics = self._calculate_metrics()
        
        return BacktestResult(
            trades=self.trades,
            equity_curve=self.equity_curve,
            metrics=metrics,
            drawdown=self._calculate_drawdown(),
            timestamps=[c.timestamp for c in candles[lookback:]]
        )
    
    def _execute_signal(self, signal: Signal, candle: Candle):
        """Execute a trading signal"""
        if signal.side == OrderSide.BUY and not self.positions:
            # Open long position
            position = Position(
                id=f"pos_{len(self.positions)}",
                side=OrderSide.BUY,
                entry_price=signal.price,
                amount=self.capital / signal.price,
                entry_time=signal.timestamp,
                stop_loss=signal.metadata.get('stop_loss'),
                take_profit=signal.metadata.get('take_profit'),
                metadata=signal.metadata
            )
            self.positions.append(position)
            self.capital = 0
        
        elif signal.side == OrderSide.SELL and self.positions:
            # Close long position
            for position in self.positions[:]:
                if position.side == OrderSide.BUY:
                    self._close_position(position, signal.price, signal.timestamp)
    
    def _check_exits(self, candle: Candle):
        """Check stop loss and take profit"""
        for position in self.positions[:]:
            if position.side == OrderSide.BUY:
                # Check stop loss
                if position.stop_loss and candle.low <= position.stop_loss:
                    self._close_position(position, position.stop_loss, candle.timestamp)
                
                # Check take profit
                elif position.take_profit and candle.high >= position.take_profit:
                    self._close_position(position, position.take_profit, candle.timestamp)
    
    def _close_position(self, position: Position, exit_price: float, exit_time: float):
        """Close a position and record trade"""
        profit = (exit_price - position.entry_price) * position.amount
        profit_pct = (exit_price / position.entry_price - 1) * 100
        fees = exit_price * position.amount * 0.001  # 0.1% fee
        
        trade = Trade(
            id=f"trade_{len(self.trades)}",
            side=position.side,
            entry_price=position.entry_price,
            exit_price=exit_price,
            amount=position.amount,
            entry_time=position.entry_time,
            exit_time=exit_time,
            profit=profit - fees,
            profit_pct=profit_pct,
            fees=fees,
            metadata=position.metadata
        )
        
        self.trades.append(trade)
        self.capital = exit_price * position.amount - fees
        self.positions.remove(position)
    
    def _close_all_positions(self, candle: Candle):
        """Close all remaining positions"""
        for position in self.positions[:]:
            self._close_position(position, candle.close, candle.timestamp)
    
    def _calculate_equity(self, current_price: float) -> float:
        """Calculate current equity"""
        equity = self.capital
        for position in self.positions:
            equity += position.amount * current_price
        return equity
    
    def _calculate_drawdown(self) -> List[float]:
        """Calculate drawdown curve"""
        if not self.equity_curve:
            return []
        
        peak = self.equity_curve[0]
        drawdown = []
        
        for equity in self.equity_curve:
            if equity > peak:
                peak = equity
            dd = (peak - equity) / peak * 100
            drawdown.append(dd)
        
        return drawdown
    
    def _calculate_metrics(self) -> Dict[str, Any]:
        """Calculate backtest metrics"""
        if not self.trades:
            return {}
        
        # Basic metrics
        total_trades = len(self.trades)
        winning_trades = sum(1 for t in self.trades if t.profit > 0)
        losing_trades = sum(1 for t in self.trades if t.profit < 0)
        
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        # Profit metrics
        total_profit = sum(t.profit for t in self.trades)
        total_fees = sum(t.fees for t in self.trades)
        
        avg_profit = total_profit / total_trades if total_trades > 0 else 0
        avg_profit_pct = sum(t.profit_pct for t in self.trades) / total_trades if total_trades > 0 else 0
        
        # Risk metrics
        drawdown_values = self._calculate_drawdown()
        max_drawdown = max(drawdown_values) if drawdown_values else 0
        
        # Sharpe ratio (simplified)
        if len(self.equity_curve) > 1:
            returns = [(self.equity_curve[i] - self.equity_curve[i-1]) / self.equity_curve[i-1] 
                      for i in range(1, len(self.equity_curve))]
            avg_return = sum(returns) / len(returns) if returns else 0
            std_return = math.sqrt(sum((r - avg_return) ** 2 for r in returns) / len(returns)) if returns else 1
            sharpe_ratio = avg_return / std_return * math.sqrt(252) if std_return > 0 else 0
        else:
            sharpe_ratio = 0
        
        # Profit factor
        gross_profit = sum(t.profit for t in self.trades if t.profit > 0)
        gross_loss = abs(sum(t.profit for t in self.trades if t.profit < 0))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'total_profit': total_profit,
            'total_fees': total_fees,
            'net_profit': total_profit - total_fees,
            'avg_profit': avg_profit,
            'avg_profit_pct': avg_profit_pct,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'profit_factor': profit_factor,
            'final_equity': self.equity_curve[-1] if self.equity_curve else self.initial_capital,
            'return_pct': ((self.equity_curve[-1] / self.initial_capital) - 1) * 100 if self.equity_curve else 0
        }


def create_backtesting_engine(initial_capital: float = 10000.0) -> BacktestingEngine:
    """
    Create a backtesting engine
    
    Args:
        initial_capital: Starting capital
    
    Returns:
        BacktestingEngine instance
    """
    return BacktestingEngine(initial_capital)