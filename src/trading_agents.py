"""
Trading Agents — multi-agent trading system with bull/bear researchers and risk debates.

Extracted from TradingAgents: implements a multi-agent trading system where
fundamental, market, sentiment, and news analysts feed into bull/bear researchers,
who debate via risk managers before a portfolio manager makes the final decision.
"""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class Signal(Enum):
    STRONG_BUY = "strong_buy"
    BUY = "buy"
    HOLD = "hold"
    SELL = "sell"
    STRONG_SELL = "strong_sell"


@dataclass
class AnalysisResult:
    """Result from an analyst agent."""
    agent_type: str  # "fundamentals", "market", "sentiment", "news", "social_media"
    ticker: str
    signal: Signal
    confidence: float  # 0.0 to 1.0
    summary: str
    key_points: list
    data_sources: list


@dataclass
class ResearchResult:
    """Result from bull or bear researcher."""
    stance: str  # "bull" or "bear"
    ticker: str
    thesis: str
    supporting_evidence: list
    risks: list
    confidence: float


@dataclass
class RiskDebate:
    """Result from risk management debate."""
    ticker: str
    aggressive_view: str
    conservative_view: str
    neutral_view: str
    consensus: str
    risk_score: float  # 0.0 (low risk) to 1.0 (high risk)


@dataclass
class TradingDecision:
    """Final trading decision from portfolio manager."""
    ticker: str
    signal: Signal
    position_size: float  # percentage of portfolio
    entry_price: Optional[float]
    stop_loss: Optional[float]
    take_profit: Optional[float]
    rationale: str
    confidence: float
    risk_assessment: RiskDebate


class AnalystAgent:
    """Base class for analyst agents."""
    
    def __init__(self, agent_type: str):
        self.agent_type = agent_type
    
    def analyze(self, ticker: str, data: dict) -> AnalysisResult:
        """Analyze data and return result."""
        raise NotImplementedError


class FundamentalsAnalyst(AnalystAgent):
    """Analyzes fundamental financial data."""
    
    def __init__(self):
        super().__init__("fundamentals")
    
    def analyze(self, ticker: str, data: dict) -> AnalysisResult:
        pe_ratio = data.get("pe_ratio", 0)
        revenue_growth = data.get("revenue_growth", 0)
        debt_to_equity = data.get("debt_to_equity", 0)
        
        # Simple scoring
        score = 0
        if pe_ratio and pe_ratio < 20:
            score += 1
        if revenue_growth and revenue_growth > 0.1:
            score += 1
        if debt_to_equity and debt_to_equity < 1:
            score += 1
        
        if score >= 2:
            signal = Signal.BUY
        elif score <= 0:
            signal = Signal.SELL
        else:
            signal = Signal.HOLD
        
        return AnalysisResult(
            agent_type=self.agent_type,
            ticker=ticker,
            signal=signal,
            confidence=0.7,
            summary=f"Fundamental analysis for {ticker}",
            key_points=[f"PE: {pe_ratio}", f"Growth: {revenue_growth}", f"D/E: {debt_to_equity}"],
            data_sources=["financial_statements"],
        )


class MarketAnalyst(AnalystAgent):
    """Analyzes market/technical data."""
    
    def __init__(self):
        super().__init__("market")
    
    def analyze(self, ticker: str, data: dict) -> AnalysisResult:
        price_change = data.get("price_change_30d", 0)
        volume = data.get("volume", 0)
        rsi = data.get("rsi", 50)
        
        if rsi < 30 and price_change < -0.1:
            signal = Signal.BUY  # Oversold
        elif rsi > 70 and price_change > 0.1:
            signal = Signal.SELL  # Overbought
        else:
            signal = Signal.HOLD
        
        return AnalysisResult(
            agent_type=self.agent_type,
            ticker=ticker,
            signal=signal,
            confidence=0.6,
            summary=f"Technical analysis for {ticker}",
            key_points=[f"RSI: {rsi}", f"30d change: {price_change}"],
            data_sources=["price_data", "volume_data"],
        )


class SentimentAnalyst(AnalystAgent):
    """Analyzes news and social media sentiment."""
    
    def __init__(self):
        super().__init__("sentiment")
    
    def analyze(self, ticker: str, data: dict) -> AnalysisResult:
        sentiment_score = data.get("sentiment_score", 0)
        news_count = data.get("news_count", 0)
        
        if sentiment_score > 0.3:
            signal = Signal.BUY
        elif sentiment_score < -0.3:
            signal = Signal.SELL
        else:
            signal = Signal.HOLD
        
        return AnalysisResult(
            agent_type=self.agent_type,
            ticker=ticker,
            signal=signal,
            confidence=0.5,
            summary=f"Sentiment analysis for {ticker}",
            key_points=[f"Score: {sentiment_score}", f"Articles: {news_count}"],
            data_sources=["news", "social_media"],
        )


class BullResearcher:
    """Generates bullish thesis."""
    
    def research(self, ticker: str, analyses: list) -> ResearchResult:
        bullish_points = []
        for a in analyses:
            if a.signal in (Signal.BUY, Signal.STRONG_BUY):
                bullish_points.extend(a.key_points)
        
        return ResearchResult(
            stance="bull",
            ticker=ticker,
            thesis=f"Bullish case for {ticker} based on {len(bullish_points)} supporting points",
            supporting_evidence=bullish_points,
            risks=["Market downturn", "Competitive pressure"],
            confidence=min(1.0, len(bullish_points) * 0.2),
        )


class BearResearcher:
    """Generates bearish thesis."""
    
    def research(self, ticker: str, analyses: list) -> ResearchResult:
        bearish_points = []
        for a in analyses:
            if a.signal in (Signal.SELL, Signal.STRONG_SELL):
                bearish_points.extend(a.key_points)
        
        return ResearchResult(
            stance="bear",
            ticker=ticker,
            thesis=f"Bearish case for {ticker} based on {len(bearish_points)} risk factors",
            supporting_evidence=bearish_points,
            risks=["Valuation concerns", "Growth slowdown"],
            confidence=min(1.0, len(bearish_points) * 0.2),
        )


class RiskManager:
    """Manages risk debates between aggressive, conservative, and neutral views."""
    
    def debate(self, ticker: str, bull: ResearchResult, bear: ResearchResult) -> RiskDebate:
        # Calculate risk score
        bull_conf = bull.confidence
        bear_conf = bear.confidence
        risk_score = bear_conf / (bull_conf + bear_conf + 0.001)
        
        return RiskDebate(
            ticker=ticker,
            aggressive_view=f"Go long with {bull.confidence:.0%} confidence: {bull.thesis}",
            conservative_view=f"Reduce exposure with {bear.confidence:.0%} confidence: {bear.thesis}",
            neutral_view="Maintain current position, monitor closely",
            consensus=f"Risk score: {risk_score:.2f} — {'favor caution' if risk_score > 0.5 else 'favor opportunity'}",
            risk_score=round(risk_score, 4),
        )


class PortfolioManager:
    """Makes final trading decisions based on all inputs."""
    
    def decide(self, ticker: str, analyses: list, risk: RiskDebate) -> TradingDecision:
        # Count signals
        buy_votes = sum(1 for a in analyses if a.signal in (Signal.BUY, Signal.STRONG_BUY))
        sell_votes = sum(1 for a in analyses if a.signal in (Signal.SELL, Signal.STRONG_SELL))
        total = len(analyses)
        
        # Decision logic
        if buy_votes > sell_votes and risk.risk_score < 0.6:
            signal = Signal.BUY
            position = min(0.1, 0.05 * buy_votes)
        elif sell_votes > buy_votes or risk.risk_score > 0.7:
            signal = Signal.SELL
            position = 0.0
        else:
            signal = Signal.HOLD
            position = 0.05
        
        confidence = abs(buy_votes - sell_votes) / total if total > 0 else 0
        
        return TradingDecision(
            ticker=ticker,
            signal=signal,
            position_size=round(position, 4),
            entry_price=None,
            stop_loss=None,
            take_profit=None,
            rationale=f"Based on {buy_votes} buy, {sell_votes} sell signals with risk score {risk.risk_score:.2f}",
            confidence=round(confidence, 4),
            risk_assessment=risk,
        )


class TradingAgentSystem:
    """
    Complete multi-agent trading system.
    
    Usage:
        system = TradingAgentSystem()
        decision = system.analyze("AAPL", {"pe_ratio": 15, "revenue_growth": 0.15})
        print(decision.signal)  # Signal.BUY
    """
    
    def __init__(self):
        self.analysts = [
            FundamentalsAnalyst(),
            MarketAnalyst(),
            SentimentAnalyst(),
        ]
        self.bull_researcher = BullResearcher()
        self.bear_researcher = BearResearcher()
        self.risk_manager = RiskManager()
        self.portfolio_manager = PortfolioManager()
    
    def analyze(self, ticker: str, data: dict) -> TradingDecision:
        """Run full analysis pipeline."""
        # Phase 1: Analysts
        analyses = [a.analyze(ticker, data) for a in self.analysts]
        
        # Phase 2: Research
        bull = self.bull_researcher.research(ticker, analyses)
        bear = self.bear_researcher.research(ticker, analyses)
        
        # Phase 3: Risk debate
        risk = self.risk_manager.debate(ticker, bull, bear)
        
        # Phase 4: Decision
        return self.portfolio_manager.decide(ticker, analyses, risk)
