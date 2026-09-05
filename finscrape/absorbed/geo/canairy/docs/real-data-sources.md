# Real Data Sources Configuration Guide

## Overview
This guide shows how to connect real data sources to replace mock data in the monitoring system.

## Quick Start

1. **Get API Keys** (5 minutes)
   ```bash
   python scripts/configure_data_sources.py
   ```

2. **Test Real Data**
   ```bash
   python src/main.py --check-status
   ```

## Data Source Status

### ✅ READY - No API Key Needed

| Indicator | Source | Status | Implementation |
|-----------|---------|---------|----------------|
| Treasury Tail | Treasury Direct API | **WORKING** | Already implemented |
| FDA Drug Shortages | FDA Database | Available | Needs web scraping |
| ICE Detention | ICE.gov PDFs | Available | Manual download |

### 🔑 API KEY REQUIRED - Free Tier Available

| Indicator | Source | API Key | Status |
|-----------|---------|----------|---------|
| Jobless Claims | FRED API | [Get Key](https://fred.stlouisfed.org/docs/api/api_key.html) | Implemented |
| Taiwan/Hormuz | News API | [Get Key](https://newsapi.org/register) | Implemented |
| Luxury Collapse | Alpha Vantage | [Get Key](https://www.alphavantage.co/support/#api-key) | Needs implementation |

### 📊 MANUAL DATA ENTRY

| Indicator | Source | Frequency | Process |
|-----------|---------|-----------|----------|
| DoD Autonomy | SAM.gov | Weekly | Search for "autonomous decision" |
| mBridge | BIS Reports | Monthly | Check mBridge project updates |
| School Closures | District Sites | Daily | Monitor major districts |
| AGI Milestones | AI Papers/News | Weekly | Track announcements |
| Labor Displacement | BLS + Layoffs.fyi | Weekly | Compile statistics |

## Step-by-Step Setup

### 1. Federal Reserve Economic Data (FRED)
```yaml
# config/secrets.yaml
fred_api_key: "your-key-here"
```
- **What it provides**: Jobless claims, treasury rates, economic indicators
- **Free tier**: 120 requests/minute
- **Already implemented**: JoblessClaimsCollector

### 2. News API
```yaml
# config/secrets.yaml
news_api_key: "your-key-here"
```
- **What it provides**: Taiwan Strait, Hormuz shipping news
- **Free tier**: 100 requests/day
- **Already implemented**: TaiwanNewsCollector, HormuzNewsCollector

### 3. Treasury Direct (NO KEY NEEDED)
- **URL**: https://api.fiscaldata.treasury.gov/
- **What it provides**: Treasury auction results
- **Status**: Already working in TreasuryCollector

### 4. FDA Drug Shortages (NO KEY NEEDED)
- **URL**: https://www.fda.gov/drugs/drug-shortages
- **RSS Feed**: Available for automation
- **Implementation needed**: Web scraping or RSS parser

## Data Collection Scripts

### Automated Collection (runs hourly)
```bash
# Already set up via cron
0 * * * * cd /path/to/project && source venv/bin/activate && python src/main.py
```

### Manual Data Entry
```bash
# Update manual indicators
python scripts/update_manual_data.py
```

## Testing Real Data

### Check which sources are live:
```bash
python src/main.py --check-status | grep -E "(source|API)"
```

### Monitor API usage:
```bash
tail -f logs/monitor.log | grep -E "(API|Real data)"
```

## Troubleshooting

### "API key not found"
- Check `config/secrets.yaml` exists
- Verify key name matches exactly

### "Rate limit exceeded"
- FRED: 120/minute (very generous)
- News API: 100/day (use sparingly)
- Alpha Vantage: 5/minute

### "Connection timeout"
- Check internet connection
- Some APIs may be blocked by firewalls
- Try using a VPN if needed

## Priority Implementation Order

1. **FRED API** - Easy, immediate value for jobless claims
2. **News API** - Real geopolitical monitoring
3. **FDA Scraper** - Important but requires coding
4. **Manual Entry UI** - For DoD, mBridge, schools

## Next Steps

1. Run `python scripts/configure_data_sources.py`
2. Add at least FRED API key
3. Test with `python src/main.py --check-status`
4. Look for "FRED_API" or "news_analysis" in metadata
5. Set up daily manual checks for other indicators