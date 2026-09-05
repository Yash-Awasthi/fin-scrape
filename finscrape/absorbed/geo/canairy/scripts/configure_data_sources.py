#!/usr/bin/env python3
"""
Configure real data sources for the monitoring system.

This script helps you set up API keys and configure data sources
for real-time monitoring instead of mock data.
"""

import os
import sys
import yaml
from pathlib import Path

def main():
    """Guide user through data source configuration."""
    print("=" * 60)
    print("HOUSEHOLD RESILIENCE DATA SOURCE CONFIGURATION")
    print("=" * 60)
    print()
    
    # Load existing secrets
    secrets_path = Path("config/secrets.yaml")
    if secrets_path.exists():
        with open(secrets_path, 'r') as f:
            secrets = yaml.safe_load(f) or {}
    else:
        secrets = {}
    
    print("This wizard will help you configure real data sources.")
    print("Leave blank to skip any API key.\n")
    
    # 1. FRED API (Federal Reserve Economic Data)
    print("1. FRED API - For economic indicators (jobless claims, treasury rates)")
    print("   Register at: https://fred.stlouisfed.org/docs/api/api_key.html")
    print("   Current status:", "Configured" if secrets.get('fred_api_key') else "Not configured")
    
    fred_key = input("   Enter FRED API key (or press Enter to skip): ").strip()
    if fred_key:
        secrets['fred_api_key'] = fred_key
        print("   ✓ FRED API key saved")
    print()
    
    # 2. News API (for geopolitical monitoring)
    print("2. News API - For Taiwan/Hormuz/global conflict monitoring")
    print("   Register at: https://newsapi.org/register")
    print("   Free tier: 100 requests/day")
    print("   Current status:", "Configured" if secrets.get('news_api_key') else "Not configured")
    
    news_key = input("   Enter News API key (or press Enter to skip): ").strip()
    if news_key:
        secrets['news_api_key'] = news_key
        print("   ✓ News API key saved")
    print()
    
    # 3. Alpha Vantage (for financial data)
    print("3. Alpha Vantage - For luxury market indicators")
    print("   Register at: https://www.alphavantage.co/support/#api-key")
    print("   Free tier: 5 API requests/minute")
    print("   Current status:", "Configured" if secrets.get('alpha_vantage_key') else "Not configured")
    
    av_key = input("   Enter Alpha Vantage key (or press Enter to skip): ").strip()
    if av_key:
        secrets['alpha_vantage_key'] = av_key
        print("   ✓ Alpha Vantage key saved")
    print()
    
    # Save updated secrets
    with open(secrets_path, 'w') as f:
        yaml.dump(secrets, f, default_flow_style=False)
    
    print("\n" + "=" * 60)
    print("DATA SOURCES REQUIRING NO API KEY:")
    print("=" * 60)
    print()
    print("✓ Treasury Auction Results")
    print("  URL: https://api.fiscaldata.treasury.gov/")
    print("  Status: Public API, no key needed")
    print()
    print("✓ FDA Drug Shortages")
    print("  URL: https://www.fda.gov/drugs/drug-shortages")
    print("  Status: Public data, web scraping needed")
    print()
    print("✓ ICE Detention Statistics")
    print("  URL: https://www.ice.gov/detain/detention-management")
    print("  Status: Weekly PDFs, manual download needed")
    print()
    
    print("\n" + "=" * 60)
    print("MANUAL DATA SOURCES:")
    print("=" * 60)
    print()
    print("Some indicators require manual data collection:")
    print()
    print("1. ICE Detention Fill Rate")
    print("   - Download weekly PDF from ICE website")
    print("   - Extract detention statistics")
    print("   - Update in dashboard manually")
    print()
    print("2. DoD Autonomous Systems")
    print("   - Monitor SAM.gov for solicitations")
    print("   - Search for 'autonomous decision' keywords")
    print("   - Track policy changes")
    print()
    print("3. School Closures")
    print("   - Monitor major district websites")
    print("   - Track non-weather closures")
    print("   - Aggregate district-days")
    print()
    
    print("\n" + "=" * 60)
    print("NEXT STEPS:")
    print("=" * 60)
    print()
    print("1. Run monitoring system to test real data:")
    print("   python src/main.py --check-status")
    print()
    print("2. Check logs for any API errors:")
    print("   tail -f logs/monitor.log")
    print()
    print("3. Set up automated monitoring:")
    print("   python scripts/setup_automation.py")
    print()
    print("Configuration complete!")

if __name__ == "__main__":
    main()