"""
API key configuration for real data sources.

Store your API keys in config/secrets.yaml:
fred_api_key: "your-key-here"
news_api_key: "your-key-here"
"""

# API Endpoints
FRED_API_BASE = "https://api.stlouisfed.org/fred/series/observations"
FDA_SHORTAGE_API = "https://api.fda.gov/drug/drugsfda.json"
TREASURY_AUCTION_API = "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/od/auction_results"

# News monitoring endpoints
NEWS_API_BASE = "https://newsapi.org/v2/everything"

# Free data sources (no API key needed)
FRED_PUBLIC_SERIES = {
    'ICSA': 'Initial Jobless Claims',  # Weekly jobless claims
    'DGS10': '10-Year Treasury Rate',   # Treasury market stress
    'DEXCHUS': 'China Exchange Rate',   # USD/CNY for mBridge monitoring
}

# Instructions for getting API keys:
"""
1. FRED API (Federal Reserve Economic Data):
   - Go to: https://fred.stlouisfed.org/docs/api/api_key.html
   - Register for free account
   - Get API key instantly
   - Add to secrets.yaml: fred_api_key: "your-key"

2. News API (for Taiwan/Hormuz monitoring):
   - Go to: https://newsapi.org/register
   - Free tier: 100 requests/day
   - Get API key instantly
   - Add to secrets.yaml: news_api_key: "your-key"

3. FDA Drug Shortages:
   - No API key needed!
   - Direct access to: https://www.accessdata.fda.gov/scripts/drugshortages/

4. Treasury Direct:
   - No API key needed!
   - Public data at: https://api.fiscaldata.treasury.gov/

5. ICE Detention Statistics:
   - Manual download from: https://www.ice.gov/detain/detention-management
   - Weekly PDF reports need parsing
"""