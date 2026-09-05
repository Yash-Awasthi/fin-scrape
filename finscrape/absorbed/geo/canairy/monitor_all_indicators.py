#!/usr/bin/env python3
"""
Comprehensive monitoring script for all 34 indicators in Brown Man Bunker.
Runs all collectors and displays HOPI-based threat assessment.
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent / "src"))

import time
import logging
from datetime import datetime
from typing import Dict, Any
import json
from collections import defaultdict

from utils.config_loader import ConfigLoader
from processors.threat_analyzer import ThreatAnalyzer
from processors.phase_manager_hopi import PhaseManagerHOPI
from processors.stale_handler import StaleDataHandler

# Import all collectors
from collectors import (
    TreasuryCollector, GroceryCPICollector, StrikeTrackerCollector,
    LegiScanCollector, CISACyberCollector, ACLEDProtestsCollector,
    GridOutageCollector, MarketVolatilityCollector, WHODiseaseCollector,
    CREAOilCollector, OFACDesignationsCollector, JODIOilCollector,
    AILayoffsCollector, AIRansomwareCollector, DeepfakeShocksCollector,
    GDPGrowthCollector, GlobalConflictCollector, TaiwanPLACollector,
    NATOReadinessCollector, NuclearTestsCollector, RussiaNATOCollector,
    DefenseSpendingCollector, DCControlCollector, GuardMetrosCollector,
    ICEDetentionsCollector, DHSRemovalCollector, HillLegislationCollector,
    LibertyLitigationCollector, StrikeTrackerScraperCollector,
    TaiwanPLAScraperCollector, ICEDetentionScraperCollector,
    NewsAggregatorCollector
)

# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    AMBER = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header():
    """Print monitor header."""
    print("\n" + "="*80)
    print(f"{Colors.BOLD}🏠 BROWN MAN BUNKER - COMPREHENSIVE MONITORING{Colors.END}")
    print("="*80)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80 + "\n")

def format_level_color(level: str) -> str:
    """Format threat level with color."""
    color_map = {
        'green': Colors.GREEN,
        'amber': Colors.AMBER,
        'red': Colors.RED
    }
    color = color_map.get(level, '')
    return f"{color}{level.upper()}{Colors.END}"

def format_value(value: Any, unit: str = '') -> str:
    """Format value with unit."""
    if value is None:
        return "NO DATA"
    
    if unit == 'percent':
        return f"{value:.1f}%"
    elif unit == 'billions_usd':
        return f"${value:.1f}B"
    elif unit == 'basis_points':
        return f"{value:.0f} bp"
    elif unit == 'incursions_per_week':
        return f"{value}/week"
    elif unit == 'count':
        return f"{value}"
    else:
        return str(value)

def main():
    """Run comprehensive monitoring."""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Load configuration
    config_path = Path(__file__).parent / "config" / "config_phase_based.yaml"
    config = ConfigLoader(str(config_path))
    
    # Initialize processors
    threat_analyzer = ThreatAnalyzer(config)
    phase_manager = PhaseManagerHOPI(config)
    stale_handler = StaleDataHandler(config)
    
    # Initialize all collectors
    collector_classes = {
        'Treasury': TreasuryCollector,
        'GroceryCPI': GroceryCPICollector,
        'StrikeTracker': StrikeTrackerCollector,
        'LegiScan': LegiScanCollector,
        'CISACyber': CISACyberCollector,
        'ACLEDProtests': ACLEDProtestsCollector,
        'GridOutages': GridOutageCollector,
        'MarketVolatility': MarketVolatilityCollector,
        'WHODisease': WHODiseaseCollector,
        'CREAOil': CREAOilCollector,
        'OFACDesignations': OFACDesignationsCollector,
        'JODIOil': JODIOilCollector,
        'AILayoffs': AILayoffsCollector,
        'AIRansomware': AIRansomwareCollector,
        'DeepfakeShocks': DeepfakeShocksCollector,
        'GDPGrowth': GDPGrowthCollector,
        'GlobalConflict': GlobalConflictCollector,
        'TaiwanPLA': TaiwanPLACollector,
        'NATOReadiness': NATOReadinessCollector,
        'NuclearTests': NuclearTestsCollector,
        'RussiaNATO': RussiaNATOCollector,
        'DefenseSpending': DefenseSpendingCollector,
        'DCControl': DCControlCollector,
        'GuardMetros': GuardMetrosCollector,
        'ICEDetentions': ICEDetentionsCollector,
        'DHSRemoval': DHSRemovalCollector,
        'HillLegislation': HillLegislationCollector,
        'LibertyLitigation': LibertyLitigationCollector,
        'StrikeTrackerScraper': StrikeTrackerScraperCollector,
        'TaiwanPLAScraper': TaiwanPLAScraperCollector,
        'ICEDetentionScraper': ICEDetentionScraperCollector,
        'NewsAggregator': NewsAggregatorCollector
    }
    
    collectors = {}
    for name, collector_class in collector_classes.items():
        try:
            collectors[name] = collector_class(config)
        except Exception as e:
            logging.error(f"Failed to initialize {name}: {e}")
    
    print_header()
    
    # Collect data from all sources
    print(f"{Colors.BOLD}📊 COLLECTING DATA FROM {len(collectors)} INDICATORS...{Colors.END}\n")
    
    readings = {}
    errors = []
    
    for name, collector in collectors.items():
        try:
            print(f"  Collecting {name}...", end="", flush=True)
            start_time = time.time()
            reading = collector.collect()
            elapsed = time.time() - start_time
            
            if reading:
                # Check staleness
                reading = stale_handler.check_staleness(reading)
                readings[name] = reading
                print(f" ✓ ({elapsed:.1f}s)")
            else:
                readings[name] = None
                print(f" ✗ No data")
                
        except Exception as e:
            readings[name] = None
            errors.append(f"{name}: {str(e)}")
            print(f" ✗ Error: {str(e)[:50]}...")
    
    print("\n" + "-"*80 + "\n")
    
    # Analyze threat levels
    threat_levels = threat_analyzer.analyze(readings)
    
    # Calculate HOPI and phase
    hopi_result = phase_manager.evaluate(readings, threat_levels)
    
    # Display HOPI Summary
    print(f"{Colors.BOLD}🎯 HOPI THREAT ASSESSMENT{Colors.END}\n")
    print(f"HOPI Score: {Colors.BOLD}{hopi_result['hopi']:.1f}{Colors.END}")
    print(f"Confidence: {hopi_result['confidence']:.1f}%")
    print(f"Current Phase: {Colors.BOLD}Phase {hopi_result['phase']} - {hopi_result['phase_name']}{Colors.END}")
    print(f"Headline: {hopi_result['headline']}")
    
    # Phase color
    phase_color = Colors.GREEN
    if hopi_result['phase'] >= 4:
        phase_color = Colors.RED
    elif hopi_result['phase'] >= 2:
        phase_color = Colors.AMBER
    
    print(f"\n{phase_color}{'▓' * int(hopi_result['phase'] * 10)}{Colors.END}")
    print(f"Phase 0 {'─'*60} Phase 9\n")
    
    # Domain scores
    print(f"{Colors.BOLD}📈 DOMAIN SCORES{Colors.END}\n")
    for domain, score in hopi_result['domain_scores'].items():
        print(f"  {domain.replace('_', ' ').title()}: {score:.1f}")
    
    print("\n" + "-"*80 + "\n")
    
    # Indicator status by domain
    print(f"{Colors.BOLD}📍 INDICATOR STATUS BY DOMAIN{Colors.END}\n")
    
    # Group indicators by domain
    domains = {
        'Economy': ['Treasury', 'GroceryCPI', 'MarketVolatility', 'JODIOil', 'GDPGrowth'],
        'AI & Tech': ['DeepfakeShocks', 'AILayoffs', 'AIRansomware'],
        'Global Conflict': ['GlobalConflict', 'TaiwanPLA', 'NATOReadiness', 'NuclearTests', 
                           'RussiaNATO', 'DefenseSpending'],
        'Domestic Control': ['DCControl', 'GuardMetros', 'ICEDetentions', 'DHSRemoval',
                            'HillLegislation', 'LibertyLitigation'],
        'Energy': ['CREAOil', 'GridOutages'],
        'Civil': ['ACLEDProtests', 'StrikeTracker'],
        'Security': ['CISACyber', 'LegiScan', 'OFACDesignations'],
        'Health': ['WHODisease']
    }
    
    for domain, indicators in domains.items():
        print(f"{Colors.BOLD}{domain}:{Colors.END}")
        for indicator in indicators:
            if indicator in readings and indicator in threat_levels:
                reading = readings[indicator]
                level = threat_levels[indicator]
                
                if reading:
                    value = reading.get('value')
                    unit = reading.get('metadata', {}).get('unit', '')
                    formatted_value = format_value(value, unit)
                    stale = reading.get('metadata', {}).get('stale', False)
                    stale_marker = " [STALE]" if stale else ""
                else:
                    formatted_value = "NO DATA"
                    stale_marker = ""
                
                level_str = format_level_color(level)
                print(f"  • {indicator:.<25} {formatted_value:>15} {level_str}{stale_marker}")
        print()
    
    # Critical alerts
    if hopi_result['critical_reds'] > 0:
        print(f"{Colors.RED}{Colors.BOLD}⚠️  CRITICAL ALERTS{Colors.END}\n")
        # Find which indicators are critical and red
        critical_red_indicators = []
        for name, reading in readings.items():
            if name in threat_levels and threat_levels[name] == 'red':
                # Check if it's a critical indicator
                for domain, info in phase_manager.hopi_calculator.domains.items():
                    if name in info.get('critical', []):
                        critical_red_indicators.append(name)
                        break
        
        for indicator in critical_red_indicators:
            print(f"  • {indicator} is in RED status (critical indicator)")
        print()
    
    # Recommended actions
    print(f"{Colors.BOLD}📋 RECOMMENDED ACTIONS{Colors.END}\n")
    actions = phase_manager.get_actions(hopi_result['phase'])
    for i, action in enumerate(actions, 1):
        print(f"  {i}. {action}")
    
    # Data quality warnings
    if hopi_result['stale_count'] > 0:
        print(f"\n{Colors.AMBER}⚠️  DATA QUALITY: {hopi_result['stale_count']} indicators have stale data{Colors.END}")
    
    if errors:
        print(f"\n{Colors.RED}❌ COLLECTION ERRORS:{Colors.END}")
        for error in errors[:5]:  # Show first 5 errors
            print(f"  • {error}")
        if len(errors) > 5:
            print(f"  • ... and {len(errors) - 5} more")
    
    # Save results
    results_file = Path(__file__).parent / "data" / "monitoring_results.json"
    results_file.parent.mkdir(exist_ok=True)
    
    with open(results_file, 'w') as f:
        json.dump({
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'hopi_result': hopi_result,
            'readings': {k: v for k, v in readings.items() if v is not None},
            'threat_levels': threat_levels,
            'errors': errors
        }, f, indent=2)
    
    print(f"\n{Colors.BLUE}💾 Results saved to: {results_file}{Colors.END}")
    print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    main()