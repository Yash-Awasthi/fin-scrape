"""
Natural language finance queries from finance-query.
"""
from dataclasses import dataclass
from typing import List, Optional, Dict
import re


@dataclass
class QueryResult:
    query: str
    intent: str
    entity: str
    period: str
    answer: str
    confidence: float
    data: Optional[Dict] = None


INTENT_PATTERNS = {
    "revenue": r"(revenue|sales|income|earnings)",
    "profit": r"(profit|margin|net income|earnings)",
    "price": r"(price|stock price|share price|market price)",
    "market_cap": r"(market cap|market capitalization|valuation)",
    "pe_ratio": r"(pe ratio|price.to.earnings|p/e)",
    "dividend": r"(dividend|yield|payout)",
    "growth": r"(growth|increase|expand|rise|grew)",
    "debt": r"(debt|liabilities|borrowing|leverage)",
    "cash_flow": r"(cash flow|free cash|operating cash)",
}

PERIOD_PATTERNS = {
    "quarterly": r"(quarter|q[1-4])",
    "annual": r"(annual|yearly|year|fy|full.year)",
    "monthly": r"(month|monthly)",
    "ttm": r"(ttm|trailing|last.12)",
}

STOCK_DATA = {
    "AAPL": {"revenue": 383_000_000_000, "profit": 97_000_000_000, "market_cap": 2_800_000_000_000, "pe_ratio": 28.5, "price": 178.50},
    "MSFT": {"revenue": 212_000_000_000, "profit": 72_000_000_000, "market_cap": 2_700_000_000_000, "pe_ratio": 35.2, "price": 362.00},
    "GOOGL": {"revenue": 307_000_000_000, "profit": 76_000_000_000, "market_cap": 1_900_000_000_000, "pe_ratio": 25.1, "price": 142.00},
    "AMZN": {"revenue": 574_000_000_000, "profit": 30_000_000_000, "market_cap": 1_500_000_000_000, "pe_ratio": 50.0, "price": 145.00},
    "NVDA": {"revenue": 60_000_000_000, "profit": 30_000_000_000, "market_cap": 1_200_000_000_000, "pe_ratio": 40.0, "price": 480.00},
}


def parse_query(query: str) -> Dict[str, str]:
    q = query.lower()
    intent = "unknown"
    for key, pattern in INTENT_PATTERNS.items():
        if re.search(pattern, q):
            intent = key
            break
    entity = ""
    for ticker in STOCK_DATA:
        if ticker.lower() in q:
            entity = ticker
            break
    if not entity:
        for word in q.split():
            if word.isupper() and len(word) <= 5:
                entity = word
                break
    period = "ttm"
    for key, pattern in PERIOD_PATTERNS.items():
        if re.search(pattern, q):
            period = key
            break
    return {"intent": intent, "entity": entity, "period": period}


def execute_query(query: str) -> QueryResult:
    parsed = parse_query(query)
    intent, entity, period = parsed["intent"], parsed["entity"], parsed["period"]
    data = STOCK_DATA.get(entity, {})
    if not data:
        return QueryResult(query=query, intent=intent, entity=entity, period=period, answer=f"Could not find data for '{entity}'", confidence=0.3)
    if intent in data:
        value = data[intent]
        formatted = f"${value:,.0f}" if isinstance(value, (int, float)) and value > 1000 else str(value)
        return QueryResult(query=query, intent=intent, entity=entity, period=period, answer=f"{entity} {intent}: {formatted}", confidence=0.9, data={intent: value})
    return QueryResult(query=query, intent=intent, entity=entity, period=period, answer=f"Data for {intent} not available for {entity}", confidence=0.5)
