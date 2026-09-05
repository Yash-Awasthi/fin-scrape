"""
Agent nodes — LLM-powered analysts, researchers, trader, risk team, and PM.

Each agent is a function that takes TradeState, calls an LLM via call_ai,
and mutates state with its report. Ported from TradingAgents framework
but using fin-scrape's own call_ai backend instead of langchain LLMs.
"""
from __future__ import annotations

import logging
from typing import Callable

from finscrape.analysis.ai_client import call_ai
from finscrape.trading.state import TradeState
from finscrape.trading import tools

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Type alias for the LLM caller
# ---------------------------------------------------------------------------
LLMCallable = Callable[[str, str], dict | None]


def _llm(prompt: str, system: str, model: str | None = None) -> str:
    """Call the LLM and return raw text. Returns empty string on failure."""
    result = call_ai(prompt, system, model=model)
    if result is None:
        return ""
    # call_ai returns parsed JSON; we want the raw text for reports
    # Fall back to reasoning field or stringify
    if isinstance(result, dict):
        return result.get("reasoning", "") or result.get("content", "") or str(result)
    return str(result)


def _llm_text(prompt: str, system: str) -> str:
    """Call LLM returning the raw text response for report-style agents."""
    try:
        from finscrape.analysis.ai_client import (
            OPENAI_BASE_URL, OPENROUTER_API_KEY, OPENAI_API_KEY,
            DEFAULT_MODEL, LLM_WIRE_API, _call_with_retry,
            _call_openai_proxy, _call_openrouter, _call_responses_api,
        )
        import requests, json, re, os

        model = DEFAULT_MODEL
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ]
        if OPENAI_BASE_URL and LLM_WIRE_API == "responses":
            resp = requests.post(
                f"{OPENAI_BASE_URL.rstrip('/')}/responses",
                headers={"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"},
                json={"model": model, "instructions": system, "input": prompt,
                      "store": False, "max_output_tokens": 3000},
                timeout=90,
            )
            if resp.status_code == 200:
                data = resp.json()
                if data.get("output_text"):
                    return data["output_text"]
                parts = []
                for item in data.get("output", []):
                    for c in item.get("content", []) if isinstance(item, dict) else []:
                        if c.get("type") in ("output_text", "text") and c.get("text"):
                            parts.append(c["text"])
                return "\n".join(parts)
        elif OPENAI_BASE_URL:
            resp = requests.post(
                f"{OPENAI_BASE_URL}/chat/completions",
                headers={"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"},
                json={"model": model, "messages": messages,
                      "temperature": float(os.getenv("FINSCRAPE_AI_TEMP", "0.1")),
                      "max_tokens": 3000},
                timeout=60,
            )
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"]
        elif OPENROUTER_API_KEY:
            resp = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"},
                json={"model": model, "messages": messages,
                      "temperature": float(os.getenv("FINSCRAPE_AI_TEMP", "0.1")),
                      "max_tokens": 3000},
                timeout=45,
            )
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"]
    except Exception as e:
        logger.error("LLM text call failed: %s", e)
    return ""


# ===========================================================================
# Analyst Nodes
# ===========================================================================

def market_analyst(state: TradeState) -> None:
    """Market analyst — technical analysis with price data and indicators."""
    logger.info("[Market Analyst] Analyzing %s", state.ticker)
    stock_data = tools.get_stock_data(state.ticker)
    indicators = tools.get_indicators(state.ticker)

    system = (
        "You are a senior market/technical analyst. Analyze the provided price data "
        "and technical indicators. Write a detailed report covering:\n"
        "- Current price trend and momentum\n"
        "- Key support and resistance levels\n"
        "- Technical indicator signals (RSI, SMA, ATR)\n"
        "- Volume analysis\n"
        "- Short-term outlook\n\n"
        "Be specific with numbers. End with a markdown summary table."
    )
    prompt = f"Ticker: {state.ticker}\nDate: {state.trade_date}\n\n{stock_data}\n\n{indicators}"
    state.market_report = _llm_text(prompt, system) or f"Unable to generate market report for {state.ticker}"


def sentiment_analyst(state: TradeState) -> None:
    """Sentiment analyst — social media and news sentiment."""
    logger.info("[Sentiment Analyst] Analyzing %s", state.ticker)
    news = tools.get_news(state.ticker)
    sentiment = tools.get_sentiment(state.ticker)

    system = (
        "You are a financial sentiment analyst. Analyze the news headlines and social "
        "media sentiment for the given ticker. Produce a structured sentiment report with:\n"
        "- Overall sentiment band: Bullish / Mildly Bullish / Neutral / Mixed / Mildly Bearish / Bearish\n"
        "- Sentiment score: 0 (max bearish) to 10 (max bullish), 5 = neutral\n"
        "- Confidence: low / medium / high\n"
        "- Narrative: source-by-source breakdown, divergences, dominant themes\n"
        "- Key catalysts and risks from social/news\n\n"
        "Cross-source divergences are important signals. Be honest about data quality."
    )
    prompt = f"Ticker: {state.ticker}\nDate: {state.trade_date}\n\n{news}\n\n{sentiment}"
    state.sentiment_report = _llm_text(prompt, system) or f"Unable to generate sentiment report for {state.ticker}"


def news_analyst(state: TradeState) -> None:
    """News analyst — macro events and global news impact."""
    logger.info("[News Analyst] Analyzing %s", state.ticker)
    news = tools.get_news(state.ticker, days=14)

    system = (
        "You are a financial news analyst focused on macro events and their impact. "
        "Analyze the news and write a report covering:\n"
        "- Key news events affecting this ticker\n"
        "- Macroeconomic context (rates, inflation, geopolitics)\n"
        "- Sector-wide implications\n"
        "- Regulatory or policy risks\n"
        "- Events timeline and expected catalysts\n\n"
        "Be specific about how each event could impact the stock."
    )
    prompt = f"Ticker: {state.ticker}\nDate: {state.trade_date}\n\n{news}"
    state.news_report = _llm_text(prompt, system) or f"Unable to generate news report for {state.ticker}"


def fundamentals_analyst(state: TradeState) -> None:
    """Fundamentals analyst — financial statements and valuation."""
    logger.info("[Fundamentals Analyst] Analyzing %s", state.ticker)
    fundamentals = tools.get_fundamentals(state.ticker)
    balance = tools.get_balance_sheet(state.ticker)
    cashflow = tools.get_cashflow(state.ticker)

    system = (
        "You are a fundamentals analyst. Analyze the company's financial data and write "
        "a detailed report covering:\n"
        "- Revenue and earnings trends\n"
        "- Valuation metrics (P/E, P/S, EV/EBITDA)\n"
        "- Balance sheet health (debt, cash, current ratio)\n"
        "- Cash flow quality (FCF, operating cash flow)\n"
        "- Competitive position and moat\n"
        "- Key risks from financial data\n\n"
        "Provide specific numbers. End with a markdown summary table."
    )
    prompt = f"Ticker: {state.ticker}\nDate: {state.trade_date}\n\n{fundamentals}\n\n{balance}\n\n{cashflow}"
    state.fundamentals_report = _llm_text(prompt, system) or f"Unable to generate fundamentals report for {state.ticker}"


# ===========================================================================
# Research Debate (Bull vs Bear)
# ===========================================================================

def bull_researcher(state: TradeState) -> None:
    """Bull researcher — advocates for investing."""
    logger.info("[Bull Researcher] Building bull case for %s", state.ticker)
    history = "\n".join(state.investment_debate_history) if state.investment_debate_history else "No prior debate."
    bear_last = state.bear_history[-1].split(": ", 1)[-1] if state.bear_history else "No bear argument yet."

    system = (
        "You are a Bull Analyst advocating for investing in this stock. Build a strong, "
        "evidence-based case emphasizing growth potential, competitive advantages, and positive "
        "market indicators. Counter the bear's arguments with specific data.\n\n"
        "Focus on: growth potential, competitive advantages, positive indicators, "
        "bear counterpoints. Be conversational and engaging."
    )
    prompt = (
        f"Ticker: {state.ticker}\n\n"
        f"Market Report:\n{state.market_report}\n\n"
        f"Sentiment Report:\n{state.sentiment_report}\n\n"
        f"News Report:\n{state.news_report}\n\n"
        f"Fundamentals Report:\n{state.fundamentals_report}\n\n"
        f"Debate History:\n{history}\n\n"
        f"Last Bear Argument:\n{bear_last}\n\n"
        "Deliver your bull argument."
    )
    response = _llm_text(prompt, system)
    state.add_debate_entry("Bull Researcher", response or "Unable to generate bull argument.")
    state.debate_round += 1


def bear_researcher(state: TradeState) -> None:
    """Bear researcher — advocates against investing."""
    logger.info("[Bear Researcher] Building bear case for %s", state.ticker)
    history = "\n".join(state.investment_debate_history) if state.investment_debate_history else "No prior debate."
    bull_last = state.bull_history[-1].split(": ", 1)[-1] if state.bull_history else "No bull argument yet."

    system = (
        "You are a Bear Analyst arguing against investing in this stock. Build a compelling "
        "case highlighting risks, overvaluation, competitive threats, and negative indicators. "
        "Counter the bull's arguments with specific data.\n\n"
        "Focus on: risks, overvaluation, competitive threats, macro headwinds, bull counterpoints. "
        "Be thorough but fair."
    )
    prompt = (
        f"Ticker: {state.ticker}\n\n"
        f"Market Report:\n{state.market_report}\n\n"
        f"Sentiment Report:\n{state.sentiment_report}\n\n"
        f"News Report:\n{state.news_report}\n\n"
        f"Fundamentals Report:\n{state.fundamentals_report}\n\n"
        f"Debate History:\n{history}\n\n"
        f"Last Bull Argument:\n{bull_last}\n\n"
        "Deliver your bear argument."
    )
    response = _llm_text(prompt, system)
    state.add_debate_entry("Bear Researcher", response or "Unable to generate bear argument.")
    state.debate_round += 1


def research_manager(state: TradeState) -> None:
    """Research manager — synthesizes the bull/bear debate into an investment plan."""
    logger.info("[Research Manager] Synthesizing debate for %s", state.ticker)
    debate = "\n".join(state.investment_debate_history)

    system = (
        "You are the Research Manager. Review the bull/bear debate and all analyst reports. "
        "Synthesize the arguments into a clear investment plan. State:\n"
        "- The strongest bull and bear points\n"
        "- Which side you agree with and why\n"
        "- Recommended position (direction and conviction level)\n"
        "- Key conditions that would change your view\n"
        "- Timeline for the trade thesis"
    )
    prompt = (
        f"Ticker: {state.ticker}\nDate: {state.trade_date}\n\n"
        f"Market Report:\n{state.market_report}\n\n"
        f"Sentiment Report:\n{state.sentiment_report}\n\n"
        f"News Report:\n{state.news_report}\n\n"
        f"Fundamentals Report:\n{state.fundamentals_report}\n\n"
        f"Full Bull/Bear Debate:\n{debate}\n\n"
        "Produce the investment plan."
    )
    state.investment_plan = _llm_text(prompt, system) or "Unable to generate investment plan."


# ===========================================================================
# Trader
# ===========================================================================

def trader(state: TradeState) -> None:
    """Trader — converts the investment plan into a concrete trade proposal."""
    logger.info("[Trader] Creating proposal for %s", state.ticker)

    system = (
        "You are a trading agent. Based on the investment plan and market data, provide "
        "a specific trade proposal with:\n"
        "- Action: BUY / HOLD / SELL\n"
        "- Entry price level\n"
        "- Stop-loss level\n"
        "- Target price(s)\n"
        "- Position sizing recommendation (% of portfolio)\n"
        "- Risk/reward ratio\n"
        "- Time horizon\n\n"
        "Ground price levels in the technical data provided. Be specific."
    )
    prompt = (
        f"Ticker: {state.ticker}\nDate: {state.trade_date}\n\n"
        f"Investment Plan:\n{state.investment_plan}\n\n"
        f"Market Report:\n{state.market_report}\n\n"
        "Create the trade proposal."
    )
    state.trader_proposal = _llm_text(prompt, system) or "Unable to generate trade proposal."


# ===========================================================================
# Risk Management Team
# ===========================================================================

def aggressive_analyst(state: TradeState) -> None:
    """Aggressive risk analyst — focuses on upside capture."""
    logger.info("[Aggressive Analyst] Assessing risk for %s", state.ticker)
    history = "\n".join(state.risk_debate_history) if state.risk_debate_history else "No prior risk discussion."

    system = (
        "You are an Aggressive Risk Analyst. You focus on maximizing upside while accepting "
        "calculated risks. Argue that the opportunity justifies the risk. Challenge conservative "
        "and neutral positions when the data supports aggression."
    )
    prompt = (
        f"Ticker: {state.ticker}\n\n"
        f"Trader Proposal:\n{state.trader_proposal}\n\n"
        f"Risk Debate History:\n{history}\n\n"
        "Present your aggressive risk assessment."
    )
    response = _llm_text(prompt, system)
    state.add_risk_entry("Aggressive Analyst", response or "Unable to generate aggressive assessment.")
    state.risk_round += 1


def conservative_analyst(state: TradeState) -> None:
    """Conservative risk analyst — focuses on downside protection."""
    logger.info("[Conservative Analyst] Assessing risk for %s", state.ticker)
    history = "\n".join(state.risk_debate_history) if state.risk_debate_history else "No prior risk discussion."

    system = (
        "You are a Conservative Risk Analyst. You focus on protecting capital and identifying "
        "downside risks. Argue for tighter stops, smaller positions, and hedging when appropriate. "
        "Challenge aggressive positions when data shows unpriced risk."
    )
    prompt = (
        f"Ticker: {state.ticker}\n\n"
        f"Trader Proposal:\n{state.trader_proposal}\n\n"
        f"Risk Debate History:\n{history}\n\n"
        "Present your conservative risk assessment."
    )
    response = _llm_text(prompt, system)
    state.add_risk_entry("Conservative Analyst", response or "Unable to generate conservative assessment.")
    state.risk_round += 1


def neutral_analyst(state: TradeState) -> None:
    """Neutral risk analyst — balanced view."""
    logger.info("[Neutral Analyst] Assessing risk for %s", state.ticker)
    history = "\n".join(state.risk_debate_history) if state.risk_debate_history else "No prior risk discussion."

    system = (
        "You are a Neutral Risk Analyst. You provide a balanced view between aggressive and "
        "conservative positions. Weigh both sides fairly and propose a risk-adjusted approach."
    )
    prompt = (
        f"Ticker: {state.ticker}\n\n"
        f"Trader Proposal:\n{state.trader_proposal}\n\n"
        f"Risk Debate History:\n{history}\n\n"
        "Present your balanced risk assessment."
    )
    response = _llm_text(prompt, system)
    state.add_risk_entry("Neutral Analyst", response or "Unable to generate neutral assessment.")
    state.risk_round += 1


def risk_manager(state: TradeState) -> None:
    """Risk manager — synthesizes risk debate into final risk assessment."""
    logger.info("[Risk Manager] Synthesizing risk for %s", state.ticker)
    debate = "\n".join(state.risk_debate_history)

    system = (
        "You are the Risk Manager. Review the risk debate between aggressive, conservative, "
        "and neutral analysts. Produce a final risk assessment with:\n"
        "- Overall risk level: LOW / MEDIUM / HIGH\n"
        "- Key risk factors\n"
        "- Recommended position adjustment (if any)\n"
        "- Hedging suggestions\n"
        "- Maximum drawdown tolerance"
    )
    prompt = (
        f"Ticker: {state.ticker}\n\n"
        f"Trader Proposal:\n{state.trader_proposal}\n\n"
        f"Risk Debate:\n{debate}\n\n"
        "Produce the final risk assessment."
    )
    state.risk_assessment = _llm_text(prompt, system) or "Unable to generate risk assessment."


# ===========================================================================
# Portfolio Manager (final decision)
# ===========================================================================

def portfolio_manager(state: TradeState) -> None:
    """Portfolio Manager — approves/rejects the trade proposal."""
    logger.info("[Portfolio Manager] Final decision for %s", state.ticker)

    system = (
        "You are the Portfolio Manager — the final decision maker. Review all reports, "
        "the investment plan, the trader's proposal, and the risk assessment. "
        "Produce a final decision:\n"
        "- DECISION: APPROVE / REJECT / MODIFY\n"
        "- ACTION: BUY / HOLD / SELL (if approved or modified)\n"
        "- Conviction: LOW / MEDIUM / HIGH\n"
        "- Position size (% of portfolio)\n"
        "- Entry/exit levels\n"
        "- Rationale (2-3 sentences)\n"
        "- Lessons for next analysis\n\n"
        "Be decisive. The team has done thorough analysis — synthesize it into action."
    )
    prompt = (
        f"Ticker: {state.ticker}\nDate: {state.trade_date}\n\n"
        f"=== ANALYST REPORTS ===\n"
        f"Market:\n{state.market_report}\n\n"
        f"Sentiment:\n{state.sentiment_report}\n\n"
        f"News:\n{state.news_report}\n\n"
        f"Fundamentals:\n{state.fundamentals_report}\n\n"
        f"=== INVESTMENT PLAN ===\n{state.investment_plan}\n\n"
        f"=== TRADER PROPOSAL ===\n{state.trader_proposal}\n\n"
        f"=== RISK ASSESSMENT ===\n{state.risk_assessment}\n\n"
        "Make the final decision."
    )
    response = _llm_text(prompt, system)
    state.final_decision = response or "Unable to generate final decision."

    # Extract signal
    decision_upper = state.final_decision.upper()
    if "SELL" in decision_upper or "REJECT" in decision_upper:
        state.signal = "Sell"
    elif "BUY" in decision_upper or "APPROVE" in decision_upper:
        state.signal = "Buy"
    else:
        state.signal = "Hold"
