# Canairy Data Sources Documentation

## Overview

Canairy monitors 22 critical indicators by aggregating data from multiple reliable sources. This document details each indicator, its data sources, update frequencies, and fallback mechanisms.

## Data Collection Architecture

```
Primary Source → Validation → Normalization → Storage
       ↓ (if fails)
Fallback Source → Validation → Normalization → Storage
       ↓ (if fails)
Manual Entry → Admin Review → Storage
```

## Financial Indicators

### 1. Treasury Tail Risk

**What it Measures**: Stress in US Treasury markets indicating banking system pressure

**Primary Source**: US Treasury Direct API
- **Endpoint**: `https://api.treasurydirect.gov/services/v2/accounting/od/avg_interest_rates`
- **Authentication**: None required
- **Update Frequency**: Daily at 3:30 PM ET
- **Data Format**: JSON

**Fallback Sources**:
1. Federal Reserve Economic Data (FRED)
   - API Key required
   - Endpoint: `https://api.stlouisfed.org/fred/series/observations`
   - Series ID: `DGS10` (10-Year Treasury)

2. Alpha Vantage
   - API Key required
   - Function: `TREASURY_YIELD`

**Calculation Method**:
```python
def calculate_tail_risk(yields_10y, yields_2y):
    spread = yields_10y - yields_2y
    volatility = calculate_volatility(spread, window=20)
    tail_risk = volatility * abs(spread) / historical_avg
    return tail_risk
```

### 2. VIX Volatility Index

**What it Measures**: Market fear gauge predicting S&P 500 volatility

**Primary Source**: CBOE Direct Feed
- **Endpoint**: `https://cdn.cboe.com/api/global/delayed_quotes/VIX.json`
- **Authentication**: None for delayed (15-min)
- **Update Frequency**: Every 15 minutes during market hours
- **Data Format**: JSON

**Fallback Sources**:
1. Yahoo Finance API
   - Symbol: `^VIX`
   - No authentication required

2. Alpha Vantage
   - Function: `DIGITAL_CURRENCY_DAILY`
   - Symbol: `VIX`

**Alert Thresholds**:
- Green: < 20 (Low volatility)
- Amber: 20-30 (Elevated concern)
- Red: > 30 (High fear/uncertainty)

### 3. mBridge Settlement Volume

**What it Measures**: Central bank digital currency transactions threatening USD dominance

**Primary Source**: BIS Innovation Hub Reports
- **URL**: `https://www.bis.org/about/bisih/topics/cbdc/mcbdc_bridge.htm`
- **Method**: Web scraping for monthly reports
- **Authentication**: None
- **Update Frequency**: Monthly

**Fallback Sources**:
1. People's Bank of China English Reports
2. Bank of Thailand Statistics
3. Manual entry from official announcements

**Data Extraction**:
```python
def extract_mbridge_volume(html_content):
    # Parse HTML for transaction volume table
    # Extract USD equivalent values
    # Calculate month-over-month growth
    return {
        'volume_usd': extracted_volume,
        'growth_rate': mom_growth,
        'participating_banks': bank_count
    }
```

### 4. Unemployment Rate (Regional)

**What it Measures**: Local job market health

**Primary Source**: Bureau of Labor Statistics (BLS) API
- **Endpoint**: `https://api.bls.gov/publicAPI/v2/timeseries/data/`
- **Authentication**: API key recommended for higher limits
- **Series ID**: Dynamic based on user location
- **Update Frequency**: Monthly, first Friday

**Location Mapping**:
```javascript
const BLS_SERIES_MAP = {
  'CA': 'LASST060000000000003', // California
  'TX': 'LASST480000000000003', // Texas
  'NY': 'LASST360000000000003', // New York
  // ... all states
}
```

**Fallback Sources**:
1. State employment websites
2. FRED API with local series
3. News aggregation for announcements

## Supply Chain Indicators

### 5. Taiwan Exclusion Zone Status

**What it Measures**: Military activity affecting semiconductor supply

**Primary Sources**:
1. **Taiwan Ministry of Defense**
   - URL: `https://www.mnd.gov.tw/english/`
   - Method: RSS feed parsing
   - Update: As events occur

2. **Maritime Traffic APIs**
   - MarineTraffic API (paid)
   - Checks ship diversions around Taiwan Strait

**Binary Indicator Logic**:
```python
def check_exclusion_zone():
    # Check for keywords in MOD announcements
    keywords = ['exclusion', 'no-fly', 'exercise', 'drill']
    # Check ship routing anomalies
    # Return True if active, False if normal
```

### 6. Strait of Hormuz War Risk Premium

**What it Measures**: Insurance costs for oil tankers indicating conflict risk

**Primary Source**: Baltic Exchange
- **Service**: Tanker freight assessments
- **Authentication**: Subscription required
- **Update Frequency**: Daily
- **Specific Route**: TD3C (Middle East to China)

**Fallback Sources**:
1. Ship & Bunker API for fuel prices
2. CME Group crude futures implied volatility
3. News sentiment analysis

**Premium Calculation**:
```python
def calculate_war_risk_premium():
    current_rate = get_current_tanker_rate()
    baseline_rate = get_historical_average(days=90)
    premium = (current_rate - baseline_rate) / baseline_rate * 100
    return premium
```

### 7. Baltic Dry Index

**What it Measures**: Global shipping costs and trade health

**Primary Source**: Baltic Exchange
- **Endpoint**: Via licensed data vendors
- **Update Frequency**: Daily at 1:00 PM London time

**Free Alternatives**:
1. **TradingEconomics**
   - URL: `https://tradingeconomics.com/commodity/baltic`
   - Method: Web scraping
   - Delay: 1 day

2. **InvestmentTools**
   - Public charts available
   - Manual extraction needed

### 8. Global Food Price Index

**What it Measures**: Food affordability and supply stress

**Primary Source**: UN FAO
- **URL**: `https://www.fao.org/worldfoodsituation/foodpricesindex/en/`
- **Update Frequency**: Monthly
- **Components**: Cereals, oils, dairy, meat, sugar

**API Access**:
```python
FAO_API = "https://fenixservices.fao.org/faostat/api/v1/"
FOOD_PRICE_DATASET = "PP"  # Producer Prices
```

## Energy Indicators

### 9. Natural Gas Prices (Regional)

**What it Measures**: Heating/cooling cost pressures

**Primary Sources by Region**:
1. **Henry Hub (US)**: CME Group
   - Symbol: `NG`
   - API: Via broker APIs

2. **TTF (Europe)**: ICE
   - Symbol: `TFM`
   - Requires subscription

3. **JKM (Asia)**: Platts
   - Paid service only

**Free Alternative**: EIA (Energy Information Administration)
- **API**: `https://api.eia.gov/v2/natural-gas/pri/fut/data/`
- **API Key**: Required (free)
- **Update**: Weekly

### 10. Renewable Energy Grid Percentage

**What it Measures**: Grid stability from renewable intermittency

**Primary Source by Region**:

**US - EIA**:
```python
EIA_RENEWABLE_API = "https://api.eia.gov/v2/electricity/operating-generator-capacity/data/"
filters = {
    "frequency": "monthly",
    "fuel_type": ["SUN", "WND", "HYD"],
    "sector": "electric_power"
}
```

**Europe - ENTSO-E**:
- Transparency platform API
- Real-time generation mix

**Real-time Calculation**:
```python
def get_renewable_percentage():
    total_generation = get_total_generation()
    renewable_generation = get_renewable_generation()
    percentage = (renewable_generation / total_generation) * 100
    return percentage
```

### 11. US Power Grid Frequency Stability

**What it Measures**: Electrical grid stress and blackout risk

**Primary Sources**:
1. **FNET/GridEye** (UTK/ORNL)
   - Real-time frequency data
   - Academic access required

2. **ISO/RTO Public Data**:
   - CAISO: `http://www.caiso.com/Pages/default.aspx`
   - ERCOT: `http://www.ercot.com/`
   - PJM: `https://www.pjm.com/`

**Monitoring Logic**:
```python
NOMINAL_FREQUENCY = 60.0  # Hz
THRESHOLD_DEVIATION = 0.05  # Hz

def check_grid_stability(frequency_data):
    deviations = abs(frequency_data - NOMINAL_FREQUENCY)
    if max(deviations) > THRESHOLD_DEVIATION:
        return "RED"
    elif max(deviations) > THRESHOLD_DEVIATION * 0.5:
        return "AMBER"
    return "GREEN"
```

## Social/Geopolitical Indicators

### 12. ICE Detention Capacity

**What it Measures**: Immigration enforcement activity levels

**Primary Source**: ICE FOIA Reading Room
- **URL**: `https://www.ice.gov/foia/library`
- **Update**: Weekly detention statistics
- **Format**: PDF reports requiring parsing

**Data Extraction Process**:
```python
def extract_detention_stats(pdf_path):
    # Extract total detained
    # Extract facility capacity
    # Calculate percentage
    capacity_percentage = (total_detained / total_capacity) * 100
    return capacity_percentage
```

**Fallback**: TRAC Immigration
- Syracuse University data
- Court records analysis
- Monthly updates

### 13. Global Conflict Index

**What it Measures**: Worldwide military tensions

**Primary Source**: ACLED (Armed Conflict Location & Event Data)
- **API**: `https://api.acleddata.com/acled/read`
- **Authentication**: API key required (free academic)
- **Update**: Weekly

**Calculation Method**:
```python
def calculate_conflict_index():
    events = get_acled_events(days=7)
    weighted_score = 0
    
    for event in events:
        weight = EVENT_TYPE_WEIGHTS[event.type]
        proximity_factor = calculate_proximity(event.location)
        weighted_score += weight * proximity_factor
    
    return normalize_score(weighted_score)
```

### 14. Civil Unrest Tracker (US)

**What it Measures**: Domestic social stability

**Primary Sources**:
1. **ACLED US Dataset**
   - Protests and demonstrations
   - Updated weekly

2. **CCC (Crowd Counting Consortium)**
   - Real-time protest data
   - Academic partnership

3. **News Aggregation**
   - Keywords: "protest", "demonstration", "unrest"
   - Sentiment analysis

### 15. Cyber Attack Frequency

**What it Measures**: Digital infrastructure threats

**Primary Sources**:

1. **CISA Advisories**
   - **RSS**: `https://www.cisa.gov/uscert/ncas/current-activity.xml`
   - Real-time updates
   - Severity ratings included

2. **IBM X-Force Exchange**
   - API available
   - Threat intelligence feed

3. **DigitalAttackMap**
   - Aggregated DDoS data
   - Visual API available

**Scoring Algorithm**:
```python
def calculate_cyber_threat_level():
    cisa_alerts = get_cisa_recent_advisories()
    active_campaigns = count_active_apt_campaigns()
    ddos_activity = get_ddos_intensity()
    
    threat_score = (
        cisa_alerts * 0.4 +
        active_campaigns * 0.4 +
        ddos_activity * 0.2
    )
    
    return threat_score
```

## Market Indicators

### 16. Cryptocurrency Adoption Rate

**What it Measures**: Alternative financial system growth

**Primary Sources**:

1. **Blockchain.com API**
   - Active addresses
   - Transaction volume
   - No auth required for basic

2. **Glassnode API**
   - Advanced metrics
   - Subscription required

**Key Metrics**:
```python
ADOPTION_METRICS = {
    'active_addresses': 0.3,
    'transaction_volume': 0.2,
    'new_addresses': 0.2,
    'institutional_holdings': 0.3
}
```

### 17. Gold/Silver Ratio

**What it Measures**: Precious metals indicating systemic fear

**Primary Source**: Metals-API
- **Endpoint**: `https://metals-api.com/api/latest`
- **Symbols**: `XAU` (Gold), `XAG` (Silver)
- **API Key**: Required (free tier available)

**Simple Calculation**:
```python
def calculate_gold_silver_ratio():
    gold_price = get_spot_price('XAU')
    silver_price = get_spot_price('XAG')
    ratio = gold_price / silver_price
    return ratio
```

**Historical Context**:
- Normal: 50-80
- Elevated: 80-100
- Crisis: > 100

### 18. Dollar Strength Index (DXY)

**What it Measures**: USD dominance and global trade

**Primary Sources**:

1. **TradingView API**
   - Symbol: `DXY`
   - Real-time quotes

2. **Federal Reserve H.10**
   - Official exchange rates
   - Daily updates

### 19. Corporate Insider Selling Ratio

**What it Measures**: Executive confidence in markets

**Primary Source**: SEC EDGAR
- **API**: `https://data.sec.gov/api/`
- **Forms**: Form 4 filings
- **Real-time**: As filed

**Calculation**:
```python
def calculate_insider_ratio():
    sales = get_insider_transactions(type='S')
    purchases = get_insider_transactions(type='P')
    
    ratio = sum(sales.value) / sum(purchases.value)
    return ratio
```

## Infrastructure Indicators

### 20. Commercial Real Estate Vacancy

**What it Measures**: Economic health and banking exposure

**Primary Sources by Market**:

1. **CoStar** (Paid)
   - Most comprehensive
   - Quarterly reports

2. **Local MLS APIs**
   - Varies by region
   - Monthly updates

3. **REIS Reports**
   - Major markets only

### 21. Hospital ICU Capacity

**What it Measures**: Healthcare system stress

**Primary Source**: HHS Protect
- **URL**: `https://healthdata.gov/Hospital/COVID-19-Reported-Patient-Impact-and-Hospital-Cap/g62h-syeh`
- **API**: Socrata Open Data API
- **Update**: Weekly

**Query Example**:
```python
HHS_API = "https://healthdata.gov/resource/g62h-syeh.json"
params = {
    "$where": f"state='{user_state}'",
    "$order": "collection_week DESC",
    "$limit": 100
}
```

### 22. Supply Chain Pressure Index

**What it Measures**: Global supply chain stress

**Primary Source**: NY Fed
- **URL**: `https://www.newyorkfed.org/research/gscpi`
- **Update**: Monthly
- **Format**: Excel download

**Components**:
- Baltic Dry Index
- Airfreight costs
- Delivery times
- Backlogs
- Inventory levels

## Data Quality Assurance

### Validation Rules

Each data point must pass:
1. **Range Check**: Within historical bounds
2. **Timestamp**: Not stale (> 48 hours)
3. **Source Verification**: From approved source
4. **Anomaly Detection**: < 5 standard deviations

### Missing Data Protocol

```python
def handle_missing_data(indicator_id):
    # Try primary source
    # Try each fallback in order
    # If all fail, use last known good
    # If > 72 hours old, mark as "STALE"
    # Alert admin for manual intervention
```

### Manual Override System

Administrators can:
- Input data manually with justification
- Adjust thresholds temporarily
- Disable indicators during known issues
- Force refresh from specific source

## API Rate Limits

| Source | Free Tier | Calls/Day | Upgrade Path |
|--------|-----------|-----------|--------------|
| Alpha Vantage | Yes | 500 | $50/month unlimited |
| News API | Yes | 100 | $449/month |
| BLS | Yes | 500 | Register for 500 more |
| EIA | Yes | 10,000 | N/A |
| FRED | Yes | 120,000 | N/A |

## Implementation Notes

### Collector Template

```python
class BaseCollector:
    def __init__(self):
        self.primary_source = None
        self.fallback_sources = []
        self.cache_ttl = 3600  # 1 hour default
    
    async def collect(self):
        try:
            data = await self.fetch_primary()
        except SourceException:
            data = await self.try_fallbacks()
        
        validated = self.validate(data)
        normalized = self.normalize(validated)
        
        await self.store(normalized)
        return normalized
```

### Error Handling

All collectors implement:
- Exponential backoff
- Circuit breaker pattern
- Graceful degradation
- Error alerting

## Security Considerations

1. **API Keys**: Stored encrypted, rotated monthly
2. **Data Validation**: Prevent injection attacks
3. **Rate Limiting**: Respect source limits
4. **Caching**: Reduce API calls, improve reliability
5. **Audit Trail**: Log all data modifications

## Future Enhancements

### Planned Sources
- Satellite imagery for shipping
- Social media sentiment analysis
- Weather pattern disruption
- Cryptocurrency flow analysis
- Dark web monitoring

### ML Integration
- Anomaly detection improvement
- Cross-indicator correlation
- Predictive modeling
- Natural language alerts

---

*This document is updated quarterly. For real-time source status, check the admin dashboard.*