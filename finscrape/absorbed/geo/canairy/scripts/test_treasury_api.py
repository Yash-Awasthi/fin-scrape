#!/usr/bin/env python3
"""
Test script to debug Treasury API connection and find correct endpoints.
"""

import requests
import json
from datetime import datetime, timedelta

def test_treasury_endpoints():
    """Test various Treasury API endpoints to find working ones."""
    
    print("🔍 Testing Treasury API Endpoints...")
    print("=" * 60)
    
    # List of potential endpoints to test
    endpoints = [
        {
            'name': 'Auction Results v2',
            'url': 'https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v2/accounting/od/auction_results',
            'params': {
                'fields': 'record_date,security_term,security_type,high_rate,interest_rate,auction_date',
                'filter': 'security_term:eq:10-Year',
                'sort': '-auction_date',
                'page[size]': '5'
            }
        },
        {
            'name': 'Auction Results v1',
            'url': 'https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/od/auction_results',
            'params': {
                'fields': 'record_date,security_term,security_type,high_rate,interest_rate',
                'filter': 'security_term:eq:10-Year',
                'sort': '-auction_date',
                'page[size]': '5'
            }
        },
        {
            'name': 'Securities Outstanding',
            'url': 'https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/od/securities_outstanding',
            'params': {
                'sort': '-record_date',
                'page[size]': '5'
            }
        },
        {
            'name': 'Debt to Penny',
            'url': 'https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v2/accounting/od/debt_to_penny',
            'params': {
                'sort': '-record_date',
                'page[size]': '1'
            }
        }
    ]
    
    # Test each endpoint
    for endpoint in endpoints:
        print(f"\n📡 Testing: {endpoint['name']}")
        print(f"URL: {endpoint['url']}")
        print(f"Params: {json.dumps(endpoint['params'], indent=2)}")
        
        try:
            response = requests.get(
                endpoint['url'],
                params=endpoint['params'],
                timeout=10
            )
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print("✅ Success!")
                
                # Show sample data structure
                if 'data' in data and len(data['data']) > 0:
                    print(f"Records found: {len(data['data'])}")
                    print("Sample record:")
                    print(json.dumps(data['data'][0], indent=2))
                    
                    # For auction results, calculate tail if possible
                    if 'high_rate' in data['data'][0] and 'interest_rate' in data['data'][0]:
                        try:
                            high = float(data['data'][0]['high_rate'])
                            stop = float(data['data'][0]['interest_rate'])
                            tail_bp = (high - stop) * 100
                            print(f"\n📊 Calculated Tail: {tail_bp:.2f} basis points")
                            print(f"   High Rate: {high}%")
                            print(f"   Stop Rate: {stop}%")
                        except:
                            pass
                else:
                    print("No data returned")
                    
            else:
                print(f"❌ Failed with status {response.status_code}")
                print(f"Response: {response.text[:200]}...")
                
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print("-" * 60)

def test_alternative_sources():
    """Test alternative data sources for Treasury information."""
    
    print("\n🔍 Testing Alternative Data Sources...")
    print("=" * 60)
    
    # Test FRED API (Federal Reserve Economic Data)
    print("\n📡 Testing FRED API (no key required for basic access)")
    fred_url = "https://api.stlouisfed.org/fred/series/observations"
    params = {
        'series_id': 'DGS10',  # 10-Year Treasury Constant Maturity Rate
        'limit': '5',
        'sort_order': 'desc',
        'file_type': 'json'
    }
    
    try:
        # Note: FRED requires API key for production use
        print("Note: FRED API requires registration for API key")
        print("Visit: https://fred.stlouisfed.org/docs/api/api_key.html")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_treasury_endpoints()
    test_alternative_sources()
    
    print("\n📋 Summary:")
    print("- Treasury Direct API provides auction data")
    print("- Look for 'high_rate' and 'interest_rate' fields")
    print("- Calculate tail as: (high_rate - interest_rate) * 100")
    print("- Filter by security_term='10-Year' for relevant data")