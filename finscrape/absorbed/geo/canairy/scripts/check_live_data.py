#!/usr/bin/env python3
"""Check which indicators are using live data vs mock data"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.collectors.treasury import TreasuryCollector
from src.collectors.ice_detention import ICEDetentionCollector
from src.collectors.taiwan_zone import TaiwanZoneCollector
from src.collectors.hormuz_risk import HormuzRiskCollector
from src.collectors.dod_autonomy import DoDAutonomyCollector
from src.collectors.mbridge import MBridgeCollector
from src.collectors.jobless_claims import JoblessClaimsCollector
from src.collectors.luxury_collapse import LuxuryCollapseCollector
from src.collectors.pharmacy_shortage import PharmacyShortageCollector
from src.collectors.school_closures import SchoolClosureCollector
from src.collectors.agi_milestones import AGIMilestoneCollector
from src.collectors.labor_displacement import LaborDisplacementCollector
from src.utils.config_loader import ConfigLoader

def check_data_source(collector_name, collector_class):
    """Check if a collector is using live or mock data"""
    try:
        config_loader = ConfigLoader()
        collector = collector_class(config_loader)
        data = collector.collect()
        
        if data and 'metadata' in data:
            source = data['metadata'].get('source', 'Unknown')
            data_source = data['metadata'].get('data_source', 'MOCK')
            value = data.get('value', 'N/A')
            
            # Determine if it's live based on source description
            if 'Federal Reserve' in source or 'FRED' in source:
                data_source = 'LIVE'
            elif 'Alpha Vantage' in source:
                data_source = 'LIVE'
            elif 'News API' in source or 'news monitoring' in source:
                data_source = 'LIVE'
            elif 'Mock' in source or 'example' in source:
                data_source = 'MOCK'
            elif 'Manual' in source:
                data_source = 'MANUAL'
                
            print(f"\n{collector_name}:")
            print(f"  Status: {data_source}")
            print(f"  Value: {value}")
            print(f"  Source: {source}")
            
            return data_source
        else:
            print(f"\n{collector_name}: ERROR - No data returned")
            return 'ERROR'
            
    except Exception as e:
        print(f"\n{collector_name}: ERROR - {str(e)}")
        return 'ERROR'

def main():
    print("=== Household Resilience Monitor - Live Data Status ===")
    print("\nChecking all indicators for live data connections...\n")
    
    collectors = [
        ("Treasury Volatility", TreasuryCollector),
        ("ICE Detention", ICEDetentionCollector),
        ("Taiwan Exclusion Zone", TaiwanZoneCollector),
        ("Hormuz Risk Premium", HormuzRiskCollector),
        ("DoD AI Autonomy", DoDAutonomyCollector),
        ("mBridge Share", MBridgeCollector),
        ("Jobless Claims", JoblessClaimsCollector),
        ("Luxury Collapse Index", LuxuryCollapseCollector),
        ("Pharmacy Shortages", PharmacyShortageCollector),
        ("School Closures", SchoolClosureCollector),
        ("AGI Milestones", AGIMilestoneCollector),
        ("Labor Displacement", LaborDisplacementCollector)
    ]
    
    live_count = 0
    mock_count = 0
    manual_count = 0
    error_count = 0
    
    for name, collector_class in collectors:
        status = check_data_source(name, collector_class)
        if status == 'LIVE':
            live_count += 1
        elif status == 'MOCK':
            mock_count += 1
        elif status == 'MANUAL':
            manual_count += 1
        else:
            error_count += 1
    
    print("\n" + "="*50)
    print("\nSUMMARY:")
    print(f"  LIVE Data: {live_count} indicators")
    print(f"  MOCK Data: {mock_count} indicators")
    print(f"  MANUAL Entry Required: {manual_count} indicators")
    print(f"  ERRORS: {error_count} indicators")
    
    print("\n" + "="*50)
    print("\nTO ACTIVATE MORE LIVE DATA:")
    print("1. For mock indicators, use the Manual Input interface at http://localhost:5555/manual-input")
    print("2. FDA Drug Shortages can be scraped by clicking 'Scrape FDA Data' button")
    print("3. School closures, AGI milestones, and military indicators require manual monitoring")
    print("4. All API keys are already configured in config/secrets.yaml")

if __name__ == "__main__":
    main()