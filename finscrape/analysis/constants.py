"""
Sentiment & impact lexicons and constants for heuristic validation.
"""

# Ticker symbols that are common English words or financial abbreviations
TICKER_STOPWORDS = frozenset({
    "A", "AN", "AND", "AS", "AT", "BE", "BUT", "BY", "DO", "FOR",
    "IF", "IN", "IS", "IT", "NO", "OF", "ON", "OR", "THE", "TO",
    "ARE", "CAN", "HAS", "HAD", "HAVE", "MAY", "NOT", "WAS", "WERE",
    "WILL", "BEEN", "ALSO", "BOTH", "EVEN", "FROM", "LAST", "MANY", "MOST", "MUCH",
    "NEXT", "NOW", "ONE", "OUT", "OVER", "SAID", "SAYS", "SUCH",
    "THAN", "THAT", "THIS", "TOLD", "TWO", "WITH", "ALL", "BANK", "BILL", "BOND",
    "CASH", "COST", "DATA", "DEAL", "DEBT", "FIRM", "FUND", "GAIN", "GO", "GOAL",
    "GOVT", "LOSS", "LAW", "MODEL", "NEW", "PLAN", "POWER", "RATE", "RISK", "ROLE",
    "SALE", "STOCK", "TEAM", "TECH", "TRADE", "UNIT", "UP", "VALUE", "YEAR",
    "EPS", "PE", "PB", "ROE", "ROA", "YOY", "QOQ", "MOM", "YTD",
    "TTM", "GAAP", "EBIT", "EBITDA", "FCF", "OCF", "CAPEX", "DPS",
    "NAV", "NIM", "NPL", "FY", "FQ", "IPO", "ETF", "OTC", "DOW", "NYSE", "NASDAQ",
    "CBOE", "FED", "FOMC", "FDIC", "ECB", "IMF", "IRS", "SEC", "GDP", "CPI", "PMI",
    "CEO", "CFO", "COO", "CTO", "CMO", "CRO", "EVP", "SVP", "VP",
    "AG", "INC", "LLC", "LP", "LTD", "NV", "PLC", "SA", "AI", "EU", "UK", "UN", "US", "USA", "UAE",
    "EST", "EDT", "PST", "PDT", "UTC", "GMT",
    "FREE", "GTA", "VI", "SHRM", "ARR", "ET",
})

POSITIVE_STRONG = frozenset({
    "record", "blowout", "blockbuster", "landmark", "historic",
    "unprecedented", "beat expectations", "beat estimates", "smashed",
    "crushes", "soared", "surged", "skyrocketed", "jumped", "rallied",
    "all-time high", "massive deal", "transformative", "profit jumped",
    "revenue grew", "raised guidance", "record revenue", "record profit",
})

POSITIVE_WEAK = frozenset({
    "beat", "exceeded", "above", "growth", "gain", "rose", "up",
    "improved", "strong", "positive", "agreed to acquire", "partnership",
    "launched", "increased", "expanded", "upgraded", "raised", "gained",
    "higher", "approved", "secured", "won", "awarded",
    "upgrade", "raised target", "price target raised", "initiated buy",
    "initiated coverage with buy", "reiterated buy", "reaffirmed buy",
})

NEGATIVE_STRONG = frozenset({
    "bankrupt", "bankruptcy", "collapse", "defaulted", "insolvent",
    "catastrophic", "plunged", "crashed", "imploded", "wiped out",
    "fraud", "scandal", "indicted", "missed estimates", "missed expectations",
    "cut guidance", "profit declined", "revenue declined",
})

NEGATIVE_WEAK = frozenset({
    "miss", "missed", "below", "fell", "dropped", "declined", "loss",
    "cut", "layoffs", "laid off", "job cuts", "restructuring", "fine",
    "penalty", "downgraded", "lowered", "warning", "concern", "lawsuit",
    "investigation", "probe", "deficit", "shortfall", "suspended",
    "resignation", "stepped down", "antitrust", "class action",
    "downgrade", "cut target", "price target cut", "initiated sell",
    "initiated underperform", "lowered target", "rating cut",
})

MAGNITUDE_WORDS = frozenset({
    "record", "massive", "major", "huge", "giant", "enormous",
    "landmark", "historic", "unprecedented", "transformative",
    "biggest", "largest", "biggest ever", "largest ever",
})

EVENT_BASE_IMPACT = {
    "merger_acquisition": 0.90,
    "earnings": 0.80,
    "guidance": 0.70,
    "bankrupt": 0.95,
    "ipo": 0.75,
    "regulatory_decision": 0.70,
    "management_change": 0.60,
    "product_launch": 0.40,
    "market_movement": 0.55,
    "analyst_upgrade": 0.50,
    "analyst_downgrade": 0.50,
    "price_target_change": 0.40,
    "investment_activity": 0.55,
    "geopolitical_event": 0.65,
    "other": 0.30,
}
