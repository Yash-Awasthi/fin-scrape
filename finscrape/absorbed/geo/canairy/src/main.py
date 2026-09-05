#!/usr/bin/env python3
"""
Household Resilience Trip-Wire Monitoring System

Main entry point for the monitoring system. Checks all 6 trip-wire metrics
and triggers alerts based on thresholds defined in the research document.

Based on "Risk and Household Resilience" analysis (H1-H6 hypotheses).
"""

import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime

# Add src to Python path for imports
sys.path.append(str(Path(__file__).parent))

from collectors import (
    TreasuryCollector,
    ICEDetentionCollector, 
    TaiwanZoneCollector,
    HormuzRiskCollector,
    DoDAutonomyCollector,
    MBridgeCollector,
    JoblessClaimsCollector,
    LuxuryCollapseCollector,
    PharmacyShortageCollector,
    SchoolClosureCollector,
    AGIMilestoneCollector,
    LaborDisplacementCollector
)
from processors.threat_analyzer import ThreatAnalyzer
from notifications.alert_manager import AlertManager
from utils.config_loader import ConfigLoader
from utils.logger import setup_logging


def main():
    """Main application entry point."""
    parser = argparse.ArgumentParser(
        description="Household Resilience Trip-Wire Monitoring System"
    )
    parser.add_argument(
        "--check-status", 
        action="store_true",
        help="Run single status check and exit"
    )
    parser.add_argument(
        "--config", 
        default="config/config.yaml",
        help="Path to configuration file"
    )
    parser.add_argument(
        "--verbose", 
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    setup_logging(log_level)
    logger = logging.getLogger(__name__)
    
    logger.info("Starting Household Resilience Monitoring System")
    
    try:
        # Load configuration
        config = ConfigLoader(args.config)
        
        # Initialize components
        collectors = [
            TreasuryCollector(config),
            ICEDetentionCollector(config),
            TaiwanZoneCollector(config),
            HormuzRiskCollector(config),
            DoDAutonomyCollector(config),
            MBridgeCollector(config),
            JoblessClaimsCollector(config),
            LuxuryCollapseCollector(config),
            PharmacyShortageCollector(config),
            SchoolClosureCollector(config),
            AGIMilestoneCollector(config),
            LaborDisplacementCollector(config)
        ]
        
        threat_analyzer = ThreatAnalyzer(config)
        alert_manager = AlertManager(config)
        
        if args.check_status:
            # Single status check
            run_status_check(collectors, threat_analyzer, alert_manager)
        else:
            # Continuous monitoring mode
            run_continuous_monitoring(collectors, threat_analyzer, alert_manager)
            
    except Exception as e:
        logger.error(f"Critical error in main application: {e}")
        sys.exit(1)


def run_status_check(collectors, threat_analyzer, alert_manager):
    """Run a single status check of all trip-wires."""
    logger = logging.getLogger(__name__)
    logger.info("Running single status check...")
    
    # Collect current data
    current_readings = {}
    for collector in collectors:
        try:
            reading = collector.collect()
            current_readings[collector.name] = reading
            logger.info(f"{collector.name}: {reading}")
        except Exception as e:
            logger.error(f"Failed to collect {collector.name}: {e}")
            current_readings[collector.name] = None
    
    # Analyze threat levels
    threat_levels = threat_analyzer.analyze(current_readings)
    
    # Check for TIGHTEN-UP condition (≥2 reds)
    red_count = sum(1 for level in threat_levels.values() if level == "red")
    
    if red_count >= 2:
        logger.warning(f"TIGHTEN-UP CONDITION: {red_count} red alerts detected!")
        alert_manager.send_tighten_up_alert(threat_levels, current_readings)
    
    # Generate status report
    generate_status_report(current_readings, threat_levels, red_count)


def run_continuous_monitoring(collectors, threat_analyzer, alert_manager):
    """Run continuous monitoring with scheduled checks."""
    logger = logging.getLogger(__name__)
    logger.info("Starting continuous monitoring mode...")
    
    import schedule
    import time
    
    def scheduled_check():
        """Scheduled monitoring check."""
        run_status_check(collectors, threat_analyzer, alert_manager)
    
    # Schedule checks every hour (configurable)
    schedule.every(1).hours.do(scheduled_check)
    
    logger.info("Monitoring scheduled. Press Ctrl+C to stop.")
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute for scheduled jobs
    except KeyboardInterrupt:
        logger.info("Monitoring stopped by user")


def generate_status_report(readings, threat_levels, red_count):
    """Generate and display current status report."""
    print("\n" + "="*60)
    print("HOUSEHOLD RESILIENCE TRIP-WIRE STATUS REPORT")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    for name, reading in readings.items():
        level = threat_levels.get(name, "unknown")
        status_symbol = {"green": "✅", "amber": "⚠️", "red": "🚨"}.get(level, "❓")
        
        # Format the reading value
        if reading and isinstance(reading, dict):
            # Get the appropriate collector to format the reading
            formatted_value = reading.get('value', 'N/A')
            if 'metadata' in reading:
                # Use metadata to format appropriately
                unit = reading['metadata'].get('unit', '')
                if unit == 'billions_usd':
                    formatted_value = f"${formatted_value}B"
                elif unit == 'percent':
                    formatted_value = f"{formatted_value}%"
                elif unit == 'incursions_per_week':
                    formatted_value = f"{formatted_value} incursions/week"
                elif unit == 'systems':
                    formatted_value = f"{formatted_value} systems"
        else:
            formatted_value = "No data"
        
        print(f"{status_symbol} {name}: {formatted_value} ({level.upper()})")
    
    print("\n" + "-"*60)
    if red_count >= 2:
        print(f"🚨 TIGHTEN-UP ALERT: {red_count} red conditions detected!")
        print("IMMEDIATE ACTIONS REQUIRED:")
        print("- Top off fuel & cash reserves")
        print("- Charge all power banks and devices") 
        print("- Conduct family group briefing")
        print("- Review trusted OSINT information feeds")
    else:
        print(f"✅ Normal monitoring status ({red_count} red alerts)")
    
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
