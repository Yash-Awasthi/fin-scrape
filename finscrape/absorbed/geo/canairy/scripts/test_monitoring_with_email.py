#!/usr/bin/env python3
"""
Test the monitoring system with email notifications enabled.
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from collectors import (
    TreasuryCollector,
    ICEDetentionCollector, 
    TaiwanZoneCollector,
    HormuzRiskCollector,
    DoDAutonomyCollector,
    MBridgeCollector
)
from processors.threat_analyzer import ThreatAnalyzer
from notifications.alert_manager import AlertManager
from utils.config_loader import ConfigLoader

# Create a custom config with email enabled
class EmailEnabledConfig(ConfigLoader):
    def __init__(self, config_path):
        super().__init__(config_path)
        # Override notification channels to include email
        self.config['notifications'] = {
            'enabled': True,
            'channels': ['console', 'file', 'email']
        }

def main():
    print("🏠 Testing Household Resilience Monitor with Email Notifications")
    print("=" * 60)
    
    # Use test config that triggers alerts
    config = EmailEnabledConfig("config/config_test_red_alert.yaml")
    
    # Initialize components
    collectors = [
        TreasuryCollector(config),
        ICEDetentionCollector(config),
        TaiwanZoneCollector(config),
        HormuzRiskCollector(config),
        DoDAutonomyCollector(config),
        MBridgeCollector(config)
    ]
    
    threat_analyzer = ThreatAnalyzer(config)
    alert_manager = AlertManager(config)
    
    print("\nCollecting data...")
    
    # Collect current data
    current_readings = {}
    for collector in collectors:
        try:
            reading = collector.collect()
            current_readings[collector.name] = reading
            print(f"✓ {collector.name}: {reading}")
        except Exception as e:
            print(f"✗ Failed to collect {collector.name}: {e}")
            current_readings[collector.name] = None
    
    # Analyze threat levels
    threat_levels = threat_analyzer.analyze(current_readings)
    
    # Check for TIGHTEN-UP condition
    red_count = sum(1 for level in threat_levels.values() if level == "red")
    
    print(f"\n🚨 Red Alert Count: {red_count}")
    
    if red_count >= 2:
        print("\n📧 Sending TIGHTEN-UP alert via email...")
        alert_manager.send_tighten_up_alert(threat_levels, current_readings)
        print("✅ Alert sent! Check your email.")
    else:
        print("\n✅ No TIGHTEN-UP condition detected.")
    
    print("\nDone!")

if __name__ == "__main__":
    main()