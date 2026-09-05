"""
Intelligence Modules API — exposes the new standalone intelligence engines.

Skills applied: fastapi-python, python-best-practices, security-review, finance-expert
"""
from __future__ import annotations

from enum import Enum
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(
    tags=["Intelligence Modules"],
    responses={
        422: {"description": "Validation Error"},
        500: {"description": "Internal Server Error"},
    },
)


# --- Enums ---

class RiskLevel(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class Timeframe(str, Enum):
    INTRADAY = "1d"
    WEEKLY = "1w"
    MONTHLY = "1m"
    QUARTERLY = "1q"
    YEARLY = "1y"


# --- Response Models ---

class SentimentResponse(BaseModel):
    text: str
    sentiment_score: float = Field(ge=-1, le=1)
    label: str
    confidence: float = Field(ge=0, le=1)
    ticker: str | None = None


class GeopoliticalRiskResponse(BaseModel):
    region: str
    risk_level: RiskLevel
    risk_score: float = Field(ge=0, le=100)
    factors: list[dict[str, Any]]
    recommendations: list[str]


class TradingDebateResponse(BaseModel):
    ticker: str
    bull_argument: str
    bear_argument: str
    risk_assessment: str
    recommendation: str


class BacktestResponse(BaseModel):
    strategy: str
    total_return_pct: float
    sharpe_ratio: float
    max_drawdown_pct: float
    total_trades: int


class ModuleInfo(BaseModel):
    name: str
    description: str


# --- Input Validation ---

class SentimentRequest(BaseModel):
    text: str = Field(min_length=1, max_length=10000, description="Financial text to analyze")
    ticker: str | None = Field(default=None, max_length=10, description="Associated ticker symbol")


class GeopoliticalRiskRequest(BaseModel):
    region: str = Field(min_length=1, max_length=128, description="Region to assess")
    factors: list[str] = Field(default_factory=list, max_length=20)


class TradingDebateRequest(BaseModel):
    ticker: str = Field(min_length=1, max_length=10, description="Stock ticker symbol")
    timeframe: Timeframe = Timeframe.INTRADAY


class BacktestRequest(BaseModel):
    strategy: str = Field(min_length=1, max_length=128, description="Strategy name or code")
    start_date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$", description="YYYY-MM-DD")
    end_date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$", description="YYYY-MM-DD")
    initial_capital: float = Field(default=100000, ge=1000, le=100000000)


# --- Routes ---

@router.post(
    "/sentiment/analyze",
    response_model=SentimentResponse,
    summary="Analyze sentiment of financial text",
)
async def analyze_sentiment(req: SentimentRequest) -> SentimentResponse:
    """NLP sentiment scoring for financial news and social media."""
    try:
        from src.sentiment_analyzer import SentimentAnalyzer
        analyzer = SentimentAnalyzer()
        result = analyzer.analyze(req.text)
    except ImportError:
        raise HTTPException(status_code=501, detail="Sentiment analyzer not installed")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {exc}") from exc

    return SentimentResponse(
        text=req.text[:100],
        sentiment_score=result.score,
        label=result.label,
        confidence=result.confidence,
        ticker=req.ticker,
    )


@router.post(
    "/geopolitical/risk",
    response_model=GeopoliticalRiskResponse,
    summary="Assess geopolitical risk for a region",
)
async def assess_geopolitical_risk(req: GeopoliticalRiskRequest) -> GeopoliticalRiskResponse:
    """AI-powered geopolitical risk assessment with factor breakdown."""
    try:
        from src.geopolitical_risk import GeopoliticalRiskAssessor
        assessor = GeopoliticalRiskAssessor()
        result = assessor.assess(req.region, req.factors)
    except ImportError:
        raise HTTPException(status_code=501, detail="Geopolitical risk assessor not installed")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Assessment failed: {exc}") from exc

    return GeopoliticalRiskResponse(
        region=req.region,
        risk_level=RiskLevel(result.risk_level.value),
        risk_score=result.risk_score,
        factors=result.factors,
        recommendations=result.recommendations,
    )


@router.post(
    "/trading/debate",
    response_model=TradingDebateResponse,
    summary="Run bull/bear trading debate for a ticker",
)
async def trading_debate(req: TradingDebateRequest) -> TradingDebateResponse:
    """Multi-agent bull/bear debate with structured risk assessment."""
    try:
        from src.trading_agents import TradingDebateSystem
        system = TradingDebateSystem()
        result = system.run_debate(req.ticker, req.timeframe.value)
    except ImportError:
        raise HTTPException(status_code=501, detail="Trading debate system not installed")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Debate failed: {exc}") from exc

    return TradingDebateResponse(
        ticker=req.ticker,
        bull_argument=result.bull_argument,
        bear_argument=result.bear_argument,
        risk_assessment=result.risk_assessment,
        recommendation=result.recommendation,
    )


@router.post(
    "/backtest/run",
    response_model=BacktestResponse,
    summary="Run a backtest on a trading strategy",
)
async def run_backtest(req: BacktestRequest) -> BacktestResponse:
    """Run a historical backtest on a trading strategy."""
    if req.start_date >= req.end_date:
        raise HTTPException(status_code=422, detail="start_date must be before end_date")

    try:
        from src.backtest_engine import BacktestEngine
        engine = BacktestEngine()
        result = engine.run(req.strategy, req.start_date, req.end_date, req.initial_capital)
    except ImportError:
        raise HTTPException(status_code=501, detail="Backtest engine not installed")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Backtest failed: {exc}") from exc

    return BacktestResponse(
        strategy=req.strategy,
        total_return_pct=result.total_return_pct,
        sharpe_ratio=result.sharpe_ratio,
        max_drawdown_pct=result.max_drawdown_pct,
        total_trades=result.total_trades,
    )


@router.get(
    "/modules",
    response_model=list[ModuleInfo],
    summary="List available intelligence modules",
)
async def list_modules() -> list[ModuleInfo]:
    return [
        ModuleInfo(name="sentiment_analyzer", description="NLP sentiment scoring for financial news"),
        ModuleInfo(name="geopolitical_risk", description="AI geopolitical risk assessment"),
        ModuleInfo(name="trading_agents", description="Multi-agent bull/bear trading debate"),
        ModuleInfo(name="backtest_engine", description="Strategy backtesting framework"),
        ModuleInfo(name="route_risk_monitor", description="Supply chain route risk monitoring"),
    ]


@router.get("/health", summary="Check that all intelligence modules are importable")
async def modules_health() -> dict[str, Any]:
    modules = {
        "sentiment_analyzer": "src.sentiment_analyzer",
        "geopolitical_risk": "src.geopolitical_risk",
        "trading_agents": "src.trading_agents",
        "backtest_engine": "src.backtest_engine",
    }
    status = {}
    for name, path in modules.items():
        try:
            __import__(path)
            status[name] = "ok"
        except Exception as e:
            status[name] = f"error: {e}"
    all_ok = all(v == "ok" for v in status.values())
    return {"status": "healthy" if all_ok else "degraded", "modules": status}
